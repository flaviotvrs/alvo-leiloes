import re
import unicodedata
from decimal import Decimal

from app.models.enums import TipoImovel

_PALAVRAS_TIPO: tuple[tuple[TipoImovel, tuple[str, ...]], ...] = (
    (TipoImovel.APARTAMENTO, ("apartamento", "apto", "flat", "kitnet")),
    (TipoImovel.CASA, ("casa", "sobrado")),
    (TipoImovel.TERRENO, ("terreno", "lote", "área de terra", "area de terra")),
    (TipoImovel.LOJA, ("loja", "sala comercial", "ponto comercial")),
)

_RE_AREA_TOTAL = re.compile(r"(\d+(?:[.,]\d+)?)\s*de\s+[aá]rea\s+total", re.IGNORECASE)
_RE_AREA_PRIVATIVA = re.compile(r"(\d+(?:[.,]\d+)?)\s*de\s+[aá]rea\s+privativa", re.IGNORECASE)
_RE_AREA_TERRENO = re.compile(r"(\d+(?:[.,]\d+)?)\s*de\s+[aá]rea\s+d[eo]\s+terreno", re.IGNORECASE)
_RE_QUARTOS = re.compile(r"(\d+)\s*qto", re.IGNORECASE)


def normalizar_texto(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return " ".join(sem_acento.strip().lower().split())


def inferir_tipo(descricao: str) -> TipoImovel:
    normalizado = normalizar_texto(descricao)
    for tipo, palavras in _PALAVRAS_TIPO:
        if any(normalizar_texto(p) in normalizado for p in palavras):
            return tipo
    return TipoImovel.OUTRO


def _parse_decimal_area(texto: str) -> Decimal | None:
    # descrição da Caixa usa "." como separador decimal nas áreas (ex. "37.21"), não o
    # formato BR de milhar — diferente de Preço/Valor de avaliação na planilha.
    numero = Decimal(texto.replace(",", "."))
    # a Caixa sempre preenche as três áreas, mesmo quando não se aplica ao tipo do imóvel
    # (ex. terreno com área privativa "0.00") — 0 é "não informado", não um valor real.
    return numero if numero != 0 else None


def extrair_area_privativa(descricao: str) -> Decimal | None:
    m = _RE_AREA_PRIVATIVA.search(descricao)
    return _parse_decimal_area(m.group(1)) if m else None


def extrair_area_terreno(descricao: str) -> Decimal | None:
    m = _RE_AREA_TERRENO.search(descricao)
    return _parse_decimal_area(m.group(1)) if m else None


def extrair_area_total(descricao: str) -> Decimal | None:
    m = _RE_AREA_TOTAL.search(descricao)
    return _parse_decimal_area(m.group(1)) if m else None


def extrair_quartos(descricao: str) -> int | None:
    m = _RE_QUARTOS.search(descricao)
    return int(m.group(1)) if m else None
