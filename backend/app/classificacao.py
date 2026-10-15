from enum import Enum


class Categoria(str, Enum):
    SUPORTE_TI = "suporte_ti"
    ACESSOS_PERMISSOES = "acessos_permissoes"
    FINANCEIRO = "financeiro"
    RECURSOS_HUMANOS = "recursos_humanos"
    OUTROS = "outros"


class Impacto(str, Enum):
    INDIVIDUAL = "individual"
    EQUIPE = "equipe"
    EMPRESA = "empresa"


class Urgencia(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


class Prioridade(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"


MATRIZ = {
    (Impacto.INDIVIDUAL, Urgencia.BAIXA): Prioridade.BAIXA,
    (Impacto.INDIVIDUAL, Urgencia.MEDIA): Prioridade.BAIXA,
    (Impacto.INDIVIDUAL, Urgencia.ALTA): Prioridade.MEDIA,
    (Impacto.EQUIPE, Urgencia.BAIXA): Prioridade.BAIXA,
    (Impacto.EQUIPE, Urgencia.MEDIA): Prioridade.MEDIA,
    (Impacto.EQUIPE, Urgencia.ALTA): Prioridade.ALTA,
    (Impacto.EMPRESA, Urgencia.BAIXA): Prioridade.MEDIA,
    (Impacto.EMPRESA, Urgencia.MEDIA): Prioridade.ALTA,
    (Impacto.EMPRESA, Urgencia.ALTA): Prioridade.ALTA,
}


def calcular_prioridade(impacto: Impacto, urgencia: Urgencia) -> Prioridade:
    return MATRIZ[(impacto, urgencia)]
