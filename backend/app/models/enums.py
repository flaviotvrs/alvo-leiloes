from enum import Enum


class TipoImovel(str, Enum):
    CASA = "casa"
    APARTAMENTO = "apartamento"
    TERRENO = "terreno"
    LOJA = "loja"
    OUTRO = "outro"


class FonteLeilao(str, Enum):
    CAIXA = "caixa"
    ZUKERMAN = "zukerman"


class Etapa(str, Enum):
    TRIAGEM = "triagem"
    NAO_AVALIADO = "nao_avaliado"
    PESQUISA_CAMPO = "pesquisa_campo"
    ANALISE_FINANCEIRA = "analise_financeira"
    DECISAO = "decisao"
    APROVADO_LANCE = "aprovado_lance"
    DESCARTADO = "descartado"


class OrigemCampo(str, Enum):
    BASE = "base"
    MANUAL = "manual"
    COLETA_GUIADA = "coleta_guiada"
    AUTOMACAO = "automacao"


class Ocupacao(str, Enum):
    NAO_VERIFICADO = "nao_verificado"
    DESOCUPADO = "desocupado"
    OCUPADO_MUTUARIO = "ocupado_mutuario"
    OCUPADO_TERCEIROS = "ocupado_terceiros"
    LOCADO_COM_CONTRATO = "locado_com_contrato"


class AceitaFgts(str, Enum):
    NAO_VERIFICADO = "nao_verificado"
    ACEITA = "aceita"
    NAO_ACEITA = "nao_aceita"


class TipoEvento(str, Enum):
    IMPORTACAO = "importacao"
    CAMPO_ALTERADO = "campo_alterado"
    ETAPA_ALTERADA = "etapa_alterada"
    CALCULO = "calculo"
    DESCARTE = "descarte"
    SUGESTAO_ACEITA = "sugestao_aceita"


class StatusImportacao(str, Enum):
    PROCESSANDO = "processando"
    CONCLUIDA = "concluida"
    FALHOU = "falhou"


class FonteItbi(str, Enum):
    LEGISLACAO = "legislacao"
    AGREGADOR = "agregador"


class ConfiancaItbi(str, Enum):
    CONFIRMADA = "confirmada"
    A_CONFIRMAR = "a_confirmar"
    DESCONHECIDA = "desconhecida"
