from decimal import Decimal, InvalidOperation


def parse_decimal_br(texto: str) -> Decimal:
    """README "Formatação de número": o usuário digita `3.400` (milhar por ponto) ou `2,5`
    (decimal por vírgula)."""
    texto = texto.strip()
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    else:
        partes = texto.split(".")
        if len(partes) > 1 and len(partes[-1]) == 3 and all(p.isdigit() for p in partes):
            texto = texto.replace(".", "")
    try:
        return Decimal(texto)
    except InvalidOperation as exc:
        raise ValueError(f"Não foi possível interpretar o número: {texto!r}") from exc
