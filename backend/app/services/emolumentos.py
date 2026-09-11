from decimal import Decimal

from app.schemas.calculo import EmolumentoFaixaReferencia


def buscar_faixa(arremate: Decimal, faixas: list[EmolumentoFaixaReferencia]) -> tuple[Decimal, bool]:
    """Devolve (valor_do_registro, estimativa). `estimativa=True` quando o arremate excede
    o teto conhecido da tabela: acima de R$ 3.700.000 a Tabela 4-2026 TJMG é progressiva por
    faixas adicionais de R$ 500.000 (Nota XVII); o MVP calcula pelo teto conhecido (a última
    faixa cadastrada) e marca a linha como estimativa, em vez de fabricar a progressão."""
    faixas_ordenadas = sorted(faixas, key=lambda f: f.limite_superior)
    for faixa in faixas_ordenadas:
        if arremate <= faixa.limite_superior:
            return faixa.valor, False
    return faixas_ordenadas[-1].valor, True
