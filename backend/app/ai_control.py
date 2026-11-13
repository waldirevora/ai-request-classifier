"""Conservative, durable budgets across visitors and workers. Never retries paid calls."""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, ROUND_CEILING
import hashlib, json, os, re

from app.database import conectar
from app import ia
from app.identity import rate_limit
from app.routing import event, finalize

GLOBAL_LOCK = 826160


def flag(name):
    return os.getenv(name, 'false').strip().lower() == 'true'


@dataclass(frozen=True)
class Policy:
    daily_calls: int
    workspace_calls: int
    hourly_ip_calls: int
    daily_tokens: int
    daily_usd: Decimal
    concurrent: int
    input_price: Decimal
    output_price: Decimal

    @classmethod
    def load(cls):
        policy = cls(
            int(os.getenv('SF_AI_DAILY_CALLS', '10')),
            int(os.getenv('SF_AI_WORKSPACE_CALLS', '4')),
            int(os.getenv('SF_AI_HOURLY_IP_CALLS', '10')),
            int(os.getenv('SF_AI_DAILY_TOKENS', '100000')),
            Decimal(os.getenv('SF_AI_DAILY_USD', '0.05')),
            int(os.getenv('SF_AI_CONCURRENT', '1')),
            Decimal(os.getenv('SF_AI_INPUT_USD_PER_M', '0.60')),
            Decimal(os.getenv('SF_AI_OUTPUT_USD_PER_M', '2.40')),
        )
        valid_counts = all(0 < value <= 10000 for value in (policy.daily_calls, policy.workspace_calls, policy.hourly_ip_calls))
        if not valid_counts or not (1 <= policy.concurrent <= 4 and 1 <= policy.daily_tokens <= 10000000):
            raise ValueError('Invalid AI policy limits')
        if not policy.daily_usd.is_finite() or not 0 < policy.daily_usd <= 10:
            raise ValueError('Invalid AI budget')
        # Conservative floor above the verified peak/cache-miss prices (2026-11).
        if not policy.input_price.is_finite() or policy.input_price < Decimal('0.30'):
            raise ValueError('Invalid input reservation price')
        if not policy.output_price.is_finite() or policy.output_price < Decimal('1.20'):
            raise ValueError('Invalid output reservation price')
        return policy


def fingerprint(title, description):
    return hashlib.sha256(json.dumps([title, description], ensure_ascii=False).encode()).hexdigest()


def reservation(title, description, policy):
    # UTF-8 byte upper bound plus protocol allowance; output capped by ia.MAX_OUTPUT.
    input_bound = len(json.dumps({'titulo':title,'descricao':description}, ensure_ascii=False).encode()) + len(ia.INSTRUCOES.encode()) + 2048
    cost = (Decimal(input_bound)*policy.input_price + Decimal(ia.MAX_OUTPUT)*policy.output_price)/1000000
    return input_bound + ia.MAX_OUTPUT, cost.quantize(Decimal('0.00000001'),rounding=ROUND_CEILING)


@contextmanager
def capacity(policy):
    """Session lock plus the durable reservation gate protects connection loss."""
    import psycopg
    lock_conn=conectar();slot=None
    try:
        for index in range(policy.concurrent):
            if lock_conn.execute('SELECT pg_try_advisory_lock(%s,%s) AS ok',(GLOBAL_LOCK,index)).fetchone()['ok']:
                slot=index;break
        lock_conn.commit()
        yield slot is not None
    finally:
        try:
            if slot is not None:
                lock_conn.execute('SELECT pg_advisory_unlock(%s,%s)',(GLOBAL_LOCK,slot));lock_conn.commit()
        except psycopg.Error:pass
        finally:lock_conn.close()


def configuration_error():
    if not flag('AI_ENABLED') or not flag('SF_REAL_AI_ENABLED'):
        return 'ia_desabilitada'
    if not os.getenv('DEEPSEEK_API_KEY','').strip(): return 'chave_ausente'
    if os.getenv('AI_MODEL','deepseek-flash').strip() != 'deepseek-flash': return 'modelo_nao_aprovado'
    return None


def reserve(conn, record, policy, title, description, peer):
    # One global transaction serializes reservations across ALL workspaces.
    conn.execute('SELECT pg_advisory_xact_lock(%s)', (GLOBAL_LOCK,))
    now = datetime.now(timezone.utc)
    day = now.date()
    if conn.execute('SELECT 1 FROM sf_ai_attempts WHERE request_id=%s', (record['request_id'],)).fetchone():
        return 'tentativa_ja_reservada'
    usage = conn.execute('''SELECT count(*) AS calls,coalesce(sum(reserved_tokens),0) AS tokens,
        coalesce(sum(reserved_usd),0) AS usd FROM sf_ai_attempts WHERE day=%s''', (day,)).fetchone()
    workspace = conn.execute('SELECT count(*) AS calls FROM sf_ai_attempts WHERE workspace_id=%s', (record['workspace_id'],)).fetchone()['calls']
    pending=conn.execute("SELECT count(*) AS n,min(created_at)<now()-interval '5 minutes' AS stale FROM sf_ai_attempts WHERE status='reserved'").fetchone()
    if pending['n']>=policy.concurrent:return 'consumo_pendente' if pending['stale'] else 'capacidade_ocupada'
    tokens, usd = reservation(title, description, policy)
    if workspace >= policy.workspace_calls: return 'cota_ambiente'
    if usage['calls'] >= policy.daily_calls: return 'cota_global'
    if usage['tokens']+tokens > policy.daily_tokens or usage['usd']+usd > policy.daily_usd: return 'orcamento_esgotado'
    if not rate_limit(conn, 'ai-call:'+peer, policy.hourly_ip_calls, now=now): return 'limite_rede'
    conn.execute('''INSERT INTO sf_ai_attempts(request_id,workspace_id,case_id,day,status,reserved_tokens,reserved_usd)
        VALUES(%s,%s,%s,%s,'reserved',%s,%s)''',
        (record['request_id'],record['workspace_id'],record.get('id'),day,tokens,usd))
    return None


def controlled_call(record, title, description, peer):
    """Returns (result,code); failed/unknown usage retains the FULL reservation."""
    code = configuration_error()
    if code: return None, code
    try: policy = Policy.load()
    except (ValueError, AssertionError, ArithmeticError): return None, 'politica_invalida'
    with capacity(policy) as available:
        if not available: return None, 'capacidade_ocupada'
        with conectar() as conn:
            code = reserve(conn,record,policy,title,description,peer)
        if code: return None, code
        try:
            result = ia.classificar_solicitacao(title,description)
            # Validate again even if an adapter or a test double bypasses ia.py.
            ia.RespostaLLM(categoria=result.categoria,impacto=result.impacto,urgencia=result.urgencia,justificativa=result.justificativa)
            if not 0 <= result.tokens_entrada <= reservation(title,description,policy)[0]-ia.MAX_OUTPUT or not 0 <= result.tokens_saida <= ia.MAX_OUTPUT:
                raise ia.ErroClassificacao('uso_invalido')
        except Exception as error:
            # Never persist provider text, prompts, headers or credentials.
            code = str(error) if isinstance(error,ia.ErroClassificacao) else 'falha_integracao'
            safe_codes={'configuracao_ausente','falha_rede','resposta_http_invalida','resposta_incompleta','resposta_vazia','json_ou_campos_invalidos','uso_invalido'}
            if code not in safe_codes and not re.fullmatch(r'http_[1-5][0-9]{2}',code):code='falha_integracao'
            with conectar() as conn:
                conn.execute("UPDATE sf_ai_attempts SET status='failed',error_code=%s,finished_at=now() WHERE request_id=%s", (code,record['request_id']))
            return None, code
        with conectar() as conn:
            conn.execute("UPDATE sf_ai_attempts SET status='succeeded',input_tokens=%s,output_tokens=%s,model=%s,finished_at=now() WHERE request_id=%s",
                (result.tokens_entrada,result.tokens_saida,result.modelo,record['request_id']))
        return result, None


def analyze(case_id, peer):
    with conectar() as conn:
        case = conn.execute('SELECT * FROM sf_cases WHERE id=%s FOR UPDATE', (case_id,)).fetchone()
        if not case or case['analysis_status'] != 'queued': return
        request = conn.execute('SELECT titulo,descricao FROM solicitacoes WHERE id=%s', (case['request_id'],)).fetchone()
        conn.execute("UPDATE sf_cases SET analysis_status='running',analysis_started_at=now() WHERE id=%s", (case_id,))
        event(conn,case,'ia_analisando',{'message':'A solicitação foi recebida. Verificando limites e iniciando a análise DeepSeek.'})
    try:
        result, code = controlled_call(case,request['titulo'],request['descricao'],peer)
    except Exception:
        result, code = None, 'falha_integracao'
    with conectar() as conn:
        current = conn.execute('SELECT * FROM sf_cases WHERE id=%s FOR UPDATE', (case_id,)).fetchone()
        if current['state'] != 'analisando': return
        blocked = code in ('ia_desabilitada','chave_ausente','modelo_nao_aprovado','politica_invalida','capacidade_ocupada','cota_ambiente','cota_global','orcamento_esgotado','limite_rede','tentativa_ja_reservada','consumo_pendente')
        conn.execute('UPDATE sf_cases SET analysis_status=%s,analysis_code=%s,analysis_finished_at=now() WHERE id=%s',
            ('succeeded' if result else 'blocked' if blocked else 'failed',code,case_id))
        event(conn,case,'ia_concluida' if result else 'ia_nao_concluida',{'code':code,'message':'A DeepSeek concluiu a análise. As regras Python validarão a prioridade e o destino.' if result else 'A análise não foi concluída. O pedido está salvo e seguirá para a Central de Exceções.'})
        finalize(conn,case_id,result)
