from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.models.enums import OrigemCampo

Grupo = Literal["aquisicao", "dividas", "posse", "carregamento", "venda"]
Veredito = Literal["aprovado", "reprovado", "incompleto"]


class CampoSnapshot(BaseModel):
    valor: Decimal | None
    origem: OrigemCampo


class ParametrosSnapshot(BaseModel):
    prazo_carregamento_meses: int
    comissao_corretor_pct: Decimal
    piso_margem_pct: Decimal
    ir_aliquota_pct: Decimal
    itbi_aliquota_padrao_pct: Decimal
    comissao_leiloeiro_padrao_pct: Decimal


class ItbiReferencia(BaseModel):
    uf: str
    cidade: str
    aliquota_pct: Decimal


class EmolumentoFaixaReferencia(BaseModel):
    limite_superior: Decimal
    valor: Decimal


class TabelasSnapshot(BaseModel):
    itbi: list[ItbiReferencia]
    emolumentos: list[EmolumentoFaixaReferencia]
    versao_emolumentos: str


class Snapshot(BaseModel):
    """Entrada do motor de cálculo (BACKEND.md "Motor de cálculo"). Função pura, sem I/O:
    tudo que o cálculo precisa vem embutido aqui — nada é buscado por fora."""

    arremate: Decimal
    cidade: str
    uf: str
    campos: dict[str, CampoSnapshot]
    parametros: ParametrosSnapshot
    tabelas: TabelasSnapshot
    dividas_sao_do_arrematante: bool = True


class Linha(BaseModel):
    chave: str
    grupo: Grupo
    rotulo: str
    valor: Decimal | None
    assumido: bool
    fonte: str
    campo_para_confirmar: str | None = None


class GrupoResultado(BaseModel):
    grupo: Grupo
    subtotal: Decimal
    linhas: list[Linha]


class Resultado(BaseModel):
    grupos: list[GrupoResultado]
    aquisicao: Decimal
    dividas: Decimal
    posse: Decimal
    carregamento: Decimal
    investimento: Decimal
    comissao_corretor: Decimal
    ganho_capital: Decimal
    ir: Decimal
    lucro: Decimal | None
    margem_investimento_pct: Decimal | None
    margem_revenda_pct: Decimal | None
    veredito: Veredito
    campos_em_branco: list[str]
    premissas: list[str]
    versao_tabela_emolumentos: str
    calculado_em: datetime
