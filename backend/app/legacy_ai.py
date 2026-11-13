"""The secondary technical form shares the same GLOBAL cost envelope as the demo."""
from uuid import UUID, uuid4
from fastapi import HTTPException
from app.identity import actor, require
from app.database import conectar
from app.ai_control import controlled_call, fingerprint
from app.ia import ErroClassificacao
from app.triagem import processar_solicitacao, CAMPOS_RETORNO


def create_legacy(data, request):
    who=actor(request)
    require(who,'central')
    if who['kind']!='local':raise HTTPException(403,'Acesso técnico local obrigatório')
    try:key=UUID(request.headers.get('Idempotency-Key') or str(uuid4()))
    except ValueError:raise HTTPException(422,'Identificador de envio inválido')
    digest=fingerprint(data.titulo,data.descricao)
    with conectar() as conn:
        conn.execute('SELECT pg_advisory_xact_lock(hashtextextended(%s,0))',(str(who['workspace_id'])+str(key),))
        old=conn.execute('SELECT * FROM sf_legacy_submissions WHERE workspace_id=%s AND client_key=%s',(who['workspace_id'],key)).fetchone()
        if old:
            if old['payload_hash']!=digest:raise HTTPException(409,'Identificador usado para outro envio')
            return conn.execute(f'SELECT {CAMPOS_RETORNO} FROM solicitacoes WHERE id=%s',(old['request_id'],)).fetchone()
        record=conn.execute(f'INSERT INTO solicitacoes(titulo,descricao) VALUES(%s,%s) RETURNING {CAMPOS_RETORNO}',(data.titulo,data.descricao)).fetchone()
        conn.execute('INSERT INTO sf_legacy_submissions(workspace_id,client_key,request_id,payload_hash) VALUES(%s,%s,%s,%s)',(who['workspace_id'],key,record['id'],digest))
    codes=[]
    def classify(title,description):
        result,code=controlled_call({'request_id':record['id'],'workspace_id':who['workspace_id']},title,description,request.client.host)
        codes.append(code)
        if code:raise ErroClassificacao(code)
        return result
    result=processar_solicitacao(record,classifier=classify)
    code=codes[0] if codes else 'falha_integracao'
    with conectar() as conn:
        conn.execute('UPDATE sf_legacy_submissions SET analysis_code=%s WHERE request_id=%s',(code,record['id']))
    if code:result['analysis_notice']='A análise não foi concluída ou foi impedida pelos limites de uso. O pedido foi salvo para revisão humana.'
    return result
