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