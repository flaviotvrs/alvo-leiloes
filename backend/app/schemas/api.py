from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import AceitaFgts, Etapa, FonteLeilao, OrigemCampo, StatusImportacao, TipoEvento, TipoImovel
from app.schemas.calculo import Resultado


class ResumoCampos(BaseModel):
    preenchidos: int
    total: int
    faltando: list[str]


class ImovelListItem(BaseModel):
    lote_id: UUID
    imovel_id: UUID
    avaliacao_id: UUID
    codigo_externo: str
    fonte: FonteLeilao
    endereco: str
    cidade: str
    bairro: str | None
    uf: str
    tipo: TipoImovel
    area_privativa_m2: Decimal | None
    quartos: int | None
    preco_venda: Decimal
    valor_avaliacao: Decimal | None
    desconto_pct: Decimal | None
    modalidade: str | None
    aceita_financiamento: bool
    aceita_fgts: AceitaFgts | None
    etapa: Etapa
    motivo_descarte: str | None
    resumo_campos: ResumoCampos
    ativo: bool


class ImoveisListResponse(BaseModel):
    items: list[ImovelListItem]
    next_cursor: str | None
    total: int


class FacetasResponse(BaseModel):
    cidades: list[str]
    tipos: list[TipoImovel]


class CampoDTO(BaseModel):
    chave: str
    valor: Decimal | str | None
    origem: OrigemCampo
    fonte_declarada: str | None
    preenchido_por: UUID | None
    preenchido_em: datetime | None
    sugestao_valor: Decimal | None
    sugestao_origem: str | None


class ImovelReadOnly(BaseModel):
    imovel_id: UUID
    uf: str
    cidade: str
    bairro: str | None
    endereco: str
    tipo: TipoImovel
    area_total_m2: Decimal | None
    area_privativa_m2: Decimal | None
    area_terreno_m2: Decimal | None
    quartos: int | None
    descricao_oficial: str | None


class LoteReadOnly(BaseModel):
    lote_id: UUID
    fonte: FonteLeilao
    codigo_externo: str
    modalidade: str | None
    preco_venda: Decimal
    valor_avaliacao: Decimal | None
    desconto_pct: Decimal | None
    aceita_financiamento: bool
    aceita_fgts: AceitaFgts | None
    praca_1_valor: Decimal | None
    praca_1_data: date | None
    praca_2_valor: Decimal | None
    praca_2_data: date | None
    url_fonte: str | None
    ativo: bool


class AvaliacaoDTO(BaseModel):
    id: UUID
    etapa: Etapa
    etapa_desde: datetime
    motivo_descarte: str | None
    teto_lance: Decimal | None
    margem_desejada_pct: Decimal | None
    anotacoes: str
    checklist: dict[str, bool]


class FichaResponse(BaseModel):
    imovel: ImovelReadOnly
    lote: LoteReadOnly
    avaliacao: AvaliacaoDTO
    campos: dict[str, CampoDTO]
    resultado_calculo: Resultado
    lance_maximo_sugerido: Decimal | None


class PatchCampoRequest(BaseModel):
    valor: str | None
    fonte_declarada: str | None = None


class PatchAvaliacaoRequest(BaseModel):
    anotacoes: str | None = None
    checklist: dict[str, bool] | None = None
    teto_lance: Decimal | None = None
    margem_desejada_pct: Decimal | None = None


class EtapaRequest(BaseModel):
    etapa: Etapa
    motivo: str | None = None


class DescartarRequest(BaseModel):
    motivo: str


class EventoDTO(BaseModel):
    id: UUID
    tipo: TipoEvento
    ator_id: UUID | None
    payload: dict[str, Any]
    criado_em: datetime


class FunilCard(BaseModel):
    lote_id: UUID
    endereco: str
    cidade: str
    preco_venda: Decimal
    desconto_pct: Decimal | None
    resumo_campos: ResumoCampos
    pilula_estado: str
    ativo: bool


class FunilColuna(BaseModel):
    etapa: Etapa
    contagem: int
    nota: str
    barra_pct: int
    cards: list[FunilCard]


class FunilResponse(BaseModel):
    colunas: list[FunilColuna]
    base_para_aprovados_pct: Decimal
    tempo_medio_pesquisa_dias: Decimal | None


class ImportacaoDTO(BaseModel):
    id: UUID
    fonte: FonteLeilao
    arquivo_nome: str | None
    arquivo_gerado_em: date | None
    linhas_lidas: int
    criados: int
    atualizados: int
    inalterados: int
    inativados: int
    reativados: int
    erros: list[dict[str, Any]]
    status: StatusImportacao
    iniciada_em: datetime
    concluida_em: datetime | None


class ParametroDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    prazo_carregamento_meses: int
    comissao_corretor_pct: Decimal
    piso_margem_pct: Decimal
    ir_aliquota_pct: Decimal
    itbi_aliquota_padrao_pct: Decimal
    comissao_leiloeiro_padrao_pct: Decimal


class PatchParametroRequest(BaseModel):
    prazo_carregamento_meses: int | None = None
    comissao_corretor_pct: Decimal | None = None
    piso_margem_pct: Decimal | None = None
    ir_aliquota_pct: Decimal | None = None
    itbi_aliquota_padrao_pct: Decimal | None = None
    comissao_leiloeiro_padrao_pct: Decimal | None = None


class ItbiMunicipioDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    uf: str
    cidade: str
    aliquota_pct: Decimal
    fonte: str
    confianca: str
    observacao: str | None


class PatchItbiRequest(BaseModel):
    aliquota_pct: Decimal | None = None
    confianca: str | None = None
    observacao: str | None = None
