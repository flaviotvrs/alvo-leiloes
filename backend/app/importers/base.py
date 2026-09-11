from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.models.enums import TipoImovel


@dataclass
class LoteNormalizado:
    """Superfície de saída comum a todo conector de fonte (Caixa, Zukerman): mesma forma,
    mesmo destino (BACKEND.md "Importador"). Um conector por fonte, sem tentar reaproveitar
    parsing entre elas — só esta forma de saída é compartilhada."""

    codigo_externo: str
    uf: str
    cidade: str
    bairro: str | None
    endereco: str
    tipo: TipoImovel
    area_total_m2: Decimal | None
    area_privativa_m2: Decimal | None
    area_terreno_m2: Decimal | None
    quartos: int | None
    descricao_oficial: str
    modalidade: str | None
    preco_venda: Decimal
    valor_avaliacao: Decimal | None
    desconto_pct: Decimal | None
    aceita_financiamento: bool
    praca_1_valor: Decimal | None
    praca_1_data: date | None
    praca_2_valor: Decimal | None
    praca_2_data: date | None
    url_fonte: str | None
