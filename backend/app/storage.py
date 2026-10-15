from itertools import count


solicitacoes = []
contador_ids = count(1)


def encontrar_solicitacao(id_solicitacao: int):
    for solicitacao in solicitacoes:
        if solicitacao["id"] == id_solicitacao:
            return solicitacao

    return None
