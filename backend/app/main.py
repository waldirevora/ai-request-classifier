import json


id_solicitacao = 1
titulo = "Meu computador não liga"
descricao = "O notebook desligou durante uma reunião"
classificada = False

print("ID:", id_solicitacao)
print("Titulo:", titulo)
print("Descrição:", descricao)
print("Classificada:", classificada)


def sugerir_categoria(titulo):
    if "computador" in titulo.lower():
        return "Suporte de TI"
    else:
        return "Outros"


categoria = sugerir_categoria(titulo)
print("Categoria provisória:", categoria)

solicitacao = {
    "titulo": "Meu computador não liga",
    "descricao": "Preciso de ajuda para trabalhar"
}

corpo_json = json.dumps(solicitacao, ensure_ascii=False)

print("JSON para envio:", corpo_json)