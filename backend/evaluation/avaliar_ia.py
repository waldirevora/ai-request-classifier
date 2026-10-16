"""P15: avaliação reprodutível dos casos P12. Sem rede por padrão.

Rodar desde backend:
  .\\.venv\\Scripts\\python.exe evaluation\\avaliar_ia.py
  .\\.venv\\Scripts\\python.exe evaluation\\avaliar_ia.py --live

--live chama a API DeepSeek UMA VEZ por caso e pode gerar custos.
Não altera registros do PostgreSQL e não imprime credenciais.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.classificacao import Categoria, Impacto, Urgencia, Prioridade, calcular_prioridade

ARQUIVO_CASOS = Path(__file__).resolve().with_name("casos_referencia.json")
CAMPOS = ("categoria", "impacto", "urgencia", "prioridade")


def carregar_casos(caminho: Path = ARQUIVO_CASOS) -> list[dict]:
    casos = json.loads(caminho.read_text(encoding="utf-8"))
    if not isinstance(casos, list) or not casos:
        raise ValueError("O arquivo de referência deve conter uma lista não vazia")
    ids = set()
    for caso in casos:
        identificador = caso["id"]
        if identificador in ids:
            raise ValueError(f"ID de referência duplicado: {identificador}")
        ids.add(identificador)
        if not 3 <= len(caso["titulo"].strip()) <= 120:
            raise ValueError(f"Título inválido: {identificador}")
        if not 10 <= len(caso["descricao"].strip()) <= 2000:
            raise ValueError(f"Descrição inválida: {identificador}")
        Categoria(caso["categoria_esperada"])
        impacto = Impacto(caso["impacto"])
        urgencia = Urgencia(caso["urgencia"])
        prioridade = Prioridade(caso["prioridade_esperada"])
        if calcular_prioridade(impacto, urgencia) != prioridade:
            raise ValueError(f"Matriz inconsistente: {identificador}")
    return casos


def avaliar_casos(casos: list[dict], classificador) -> dict:
    """Classificador recebe (titulo, descricao) e retorna ResultadoIA compatível."""
    acertos = {campo: 0 for campo in CAMPOS}
    resultados = []
    tokens_entrada = 0
    tokens_saida = 0
    latencias = []
    falhas = 0

    for caso in casos:
        esperado = {
            "categoria": caso["categoria_esperada"],
            "impacto": caso["impacto"],
            "urgencia": caso["urgencia"],
            "prioridade": caso["prioridade_esperada"],
        }
        try:
            resposta = classificador(caso["titulo"], caso["descricao"])
            obtido = {campo: getattr(resposta, campo) for campo in CAMPOS}
            acerto = {campo: obtido[campo] == esperado[campo] for campo in CAMPOS}
            for campo in CAMPOS:
                acertos[campo] += int(acerto[campo])
            tokens_entrada += resposta.tokens_entrada
            tokens_saida += resposta.tokens_saida
            latencias.append(resposta.latencia_ms)
            resultados.append({
                "id": caso["id"], "esperado": esperado, "obtido": obtido,
                "acertos": acerto, "completo": all(acerto.values()),
            })
        except Exception as exc:
            # Não imprimir texto do caso nem mensagem completa de exceção:
            # alguns provedores podem incluir dados ou detalhes sensíveis.
            falhas += 1
            resultados.append({"id": caso["id"], "erro_tipo": type(exc).__name__, "completo": False})

    total = len(casos)
    completos = sum(int(resultado["completo"]) for resultado in resultados)
    return {
        "total": total,
        "sucessos_api": total - falhas,
        "falhas_api": falhas,
        "acertos": acertos,
        "completos": completos,
        "taxas_percentuais": {
            **{campo: round(100 * acertos[campo] / total, 1) for campo in CAMPOS},
            "completo": round(100 * completos / total, 1),
        },
        "tokens_entrada": tokens_entrada,
        "tokens_saida": tokens_saida,
        "latencia_media_ms": round(sum(latencias) / len(latencias)) if latencias else None,
        "latencia_min_ms": min(latencias) if latencias else None,
        "latencia_max_ms": max(latencias) if latencias else None,
        "resultados": resultados,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Avaliação P15; sem chamadas externas por padrão")
    parser.add_argument("--live", action="store_true", help="Executa chamadas reais à DeepSeek; pode ter custo")
    parser.add_argument("--limit", type=int, default=10, help="Quantidade de casos (1 a 10)")
    args = parser.parse_args()

    casos = carregar_casos()
    if not 1 <= args.limit <= len(casos):
        parser.error(f"--limit deve estar entre 1 e {len(casos)}")
    casos = casos[:args.limit]
    print(f"Casos válidos: {len(casos)} | modo: {'LIVE (pago)' if args.live else 'PRÉVIA (sem API)'}")
    if not args.live:
        print("Nenhuma requisição foi enviada. Para avaliação real, repita com --live.")
        return

    # Evita rodar por acidente com uma chave não configurada. O módulo carrega o .env local.
    from app.ia import classificar_solicitacao
    if not os.getenv("DEEPSEEK_API_KEY", "").strip():
        raise SystemExit("DEEPSEEK_API_KEY não configurada. Verifique backend/.env sem compartilhar a chave.")
    relatorio = avaliar_casos(casos, classificar_solicitacao)
    print("\nResultados (denominador: todos os casos, inclusive falhas):")
    print(f"Sucessos de API: {relatorio['sucessos_api']}/{relatorio['total']}")
    print(f"Falhas de API: {relatorio['falhas_api']}/{relatorio['total']}")
    for campo, taxa in relatorio["taxas_percentuais"].items():
        print(f"Acerto {campo}: {taxa:.1f}%")
    print(f"Tokens de entrada: {relatorio['tokens_entrada']}")
    print(f"Tokens de saída: {relatorio['tokens_saida']}")
    print(f"Latência média: {relatorio['latencia_media_ms']} ms")
    print(f"Latência mínima/máxima: {relatorio['latencia_min_ms']}/{relatorio['latencia_max_ms']} ms")
    print("Casos que exigem revisão:")
    achados = [r for r in relatorio["resultados"] if not r["completo"]]
    for r in achados:
        if "erro_tipo" in r:
            print(f"  {r['id']}: falha técnica ({r['erro_tipo']})")
        else:
            incorretos = [c for c, ok in r["acertos"].items() if not ok]
            print(f"  {r['id']}: divergência em {', '.join(incorretos)}")
    if not achados:
        print("  nenhum")
    print("\nAtenção: 10 casos são apenas uma amostra didática; não provam qualidade em produção.")
    print("Custo monetário não calculado: depende da tarifa e modalidade de tokens vigentes no provedor.")


if __name__ == "__main__":
    main()
