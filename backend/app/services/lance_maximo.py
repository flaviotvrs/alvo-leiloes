"""Lance máximo sugerido, por margem de lucro desejada (BACKEND.md "Motor de cálculo").

`calcular()` (calculo.py) é uma função pura `Snapshot -> Resultado`. Fixando tudo no
snapshot exceto `arremate`, `margem_investimento_pct` é monotonicamente decrescente
conforme `arremate` sobe (investimento cresce, lucro cai) — dá para achar por busca
binária inteira o maior arremate que ainda atinge a margem-alvo, sem fórmula fechada
(ver docs/requisitos/mvp1-ajustes/03-lance-maximo-sugerido.md, seção "Por que dá para
calcular por busca binária").
"""

from decimal import Decimal

from app.schemas.calculo import Snapshot
from app.services.calculo import calcular


def calcular_lance_maximo(snapshot: Snapshot) -> Decimal | None:
    """Maior arremate inteiro (em reais) para o qual `margem_investimento_pct` ainda atinge
    `snapshot.parametros.piso_margem_pct`. `None` se não houver valor de mercado (não dá pra
    calcular margem sem revenda). `Decimal(0)` é um resultado válido: sinal explícito de
    "nenhum lance atinge a margem, nem de graça" — quem chama deve tratar esse caso com uma
    mensagem própria, não mostrar "R$ 0" sem contexto."""
    campo_revenda = snapshot.campos.get("valor_mercado")
    if campo_revenda is None or campo_revenda.valor is None:
        return None
    revenda = campo_revenda.valor
    alvo = snapshot.parametros.piso_margem_pct

    def margem_em(arremate: Decimal) -> Decimal | None:
        resultado = calcular(snapshot.model_copy(update={"arremate": arremate}))
        return resultado.margem_investimento_pct

    lo, hi = Decimal(0), revenda.to_integral_value(rounding="ROUND_CEILING")
    margem_no_zero = margem_em(lo)
    if margem_no_zero is None or margem_no_zero < alvo:
        return Decimal(0)
    while hi - lo > 1:
        mid = (lo + hi) // 2
        margem = margem_em(mid)
        if margem is not None and margem >= alvo:
            lo = mid
        else:
            hi = mid
    return lo
