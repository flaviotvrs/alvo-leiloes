from decimal import Decimal

from app.models.enums import OrigemCampo
from app.services.calculo import calcular
from app.services.lance_maximo import calcular_lance_maximo
from tests.unit.factories import PARAMETROS_PADRAO, build_snapshot


def test_lance_maximo_bate_com_o_piso_de_margem():
    """No lance máximo, a margem ainda atinge o piso (20% padrão); um real a mais já não
    atinge — é o comportamento de busca binária no limite descrito no requisito."""
    snapshot = build_snapshot(
        arremate="49647.00",
        campos={
            "itbi_aliquota_pct": ("3.0", OrigemCampo.MANUAL),
            "iptu_atraso": ("3400.00", OrigemCampo.MANUAL),
            "iptu_mensal": ("285.00", OrigemCampo.MANUAL),
            "reforma": ("22000.00", OrigemCampo.MANUAL),
            "desocupacao": ("15000.00", OrigemCampo.MANUAL),
            "valor_mercado": ("190000.00", OrigemCampo.MANUAL),
        },
    )

    lance_maximo = calcular_lance_maximo(snapshot)

    resultado_no_limite = calcular(snapshot.model_copy(update={"arremate": lance_maximo}))
    resultado_acima = calcular(snapshot.model_copy(update={"arremate": lance_maximo + 1}))
    assert resultado_no_limite.margem_investimento_pct >= Decimal("20.0")
    assert resultado_acima.margem_investimento_pct < Decimal("20.0")


def test_lance_maximo_none_sem_valor_de_mercado():
    snapshot = build_snapshot(arremate="49647.00")

    assert calcular_lance_maximo(snapshot) is None


def test_lance_maximo_zero_quando_custos_fixos_superam_a_revenda():
    """Reforma sozinha já supera a revenda — nenhum arremate, nem R$ 0, atinge a margem."""
    snapshot = build_snapshot(
        arremate="49647.00",
        campos={
            "reforma": ("500000.00", OrigemCampo.MANUAL),
            "valor_mercado": ("190000.00", OrigemCampo.MANUAL),
        },
    )

    assert calcular_lance_maximo(snapshot) == Decimal(0)


def test_lance_maximo_usa_piso_por_imovel_em_vez_do_global():
    """Uma margem desejada menor (resolvida em snapshot.py a partir de
    Avaliacao.margem_desejada_pct) libera um lance máximo maior do que o piso global."""
    parametros_piso_baixo = PARAMETROS_PADRAO.model_copy(update={"piso_margem_pct": Decimal("5")})
    campos = {"valor_mercado": ("190000.00", OrigemCampo.MANUAL)}

    snapshot_piso_global = build_snapshot(arremate="49647.00", campos=campos)
    snapshot_piso_baixo = build_snapshot(arremate="49647.00", campos=campos, parametros=parametros_piso_baixo)

    lance_piso_global = calcular_lance_maximo(snapshot_piso_global)
    lance_piso_baixo = calcular_lance_maximo(snapshot_piso_baixo)

    assert lance_piso_baixo > lance_piso_global
