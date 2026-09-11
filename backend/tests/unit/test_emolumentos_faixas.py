from decimal import Decimal

import pytest

from app.services.emolumentos import buscar_faixa
from tests.unit.factories import FAIXAS_TJMG_4_2026_5E


@pytest.mark.parametrize(
    ("arremate", "valor_esperado", "estimativa_esperada"),
    [
        # borda exata da 1ª faixa
        (Decimal("1400.00"), Decimal("227.95"), False),
        # 1 centavo acima cai na 2ª faixa
        (Decimal("1400.01"), Decimal("371.84"), False),
        # dentro do teto conhecido
        (Decimal("3700000.00"), Decimal("13034.69"), False),
        # 1 centavo acima do teto -> caso especial progressivo (BACKEND.md), usa o teto
        # conhecido e marca como estimativa
        (Decimal("3700000.01"), Decimal("13034.69"), True),
    ],
)
def test_faixas_de_emolumento_nas_bordas(arremate, valor_esperado, estimativa_esperada):
    valor, estimativa = buscar_faixa(arremate, FAIXAS_TJMG_4_2026_5E)
    assert valor == valor_esperado
    assert estimativa is estimativa_esperada
