from decimal import Decimal

from app.models.enums import OrigemCampo
from app.services.calculo import calcular
from tests.unit.factories import build_snapshot


def test_campo_em_branco_entra_como_zero_na_conta_mas_fica_marcado():
    """BACKEND.md princípio 5: null é ausência, a conta trata como zero para fechar, mas
    marca a linha como incompleta — nunca um R$ 0 silencioso e indistinguível de "confirmei
    que é zero"."""
    snapshot = build_snapshot(
        arremate="100000.00",
        campos={
            "valor_mercado": ("150000.00", OrigemCampo.MANUAL),
            # condominio_atraso e condominio_mensal ficam de fora -> em branco
        },
    )

    resultado = calcular(snapshot)

    linha_condominio_atraso = next(
        l for g in resultado.grupos for l in g.linhas if l.chave == "condominio_atraso"
    )
    linha_condominio_mensal = next(
        l for g in resultado.grupos for l in g.linhas if l.chave == "condominio_mensal"
    )
    # a linha mostra ausência (None), não zero
    assert linha_condominio_atraso.valor is None
    assert linha_condominio_mensal.valor is None

    # mas a conta fecha como se fossem zero
    assert resultado.dividas == Decimal("0")

    # e a lacuna fica registrada explicitamente
    assert "condominio_atraso" in resultado.campos_em_branco
    assert "condominio_mensal" in resultado.campos_em_branco


def test_valor_mercado_em_branco_deixa_veredito_incompleto_nao_reprovado():
    snapshot = build_snapshot(arremate="100000.00")

    resultado = calcular(snapshot)

    assert resultado.veredito == "incompleto"
    assert resultado.lucro is None
    assert resultado.margem_investimento_pct is None
    assert "valor_mercado" in resultado.campos_em_branco
