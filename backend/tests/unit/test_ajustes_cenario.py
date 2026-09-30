from decimal import Decimal

from app.models.enums import OrigemCampo
from app.services.calculo import calcular
from tests.unit.factories import build_snapshot

# mesmo cenário do golden (test_calculo_golden.py): corretor 6% e prazo 12 pelos parâmetros
CAMPOS_BASE = {
    "itbi_aliquota_pct": ("3.0", OrigemCampo.MANUAL),
    "iptu_atraso": ("3400.00", OrigemCampo.MANUAL),
    "iptu_mensal": ("285.00", OrigemCampo.MANUAL),
    "reforma": ("22000.00", OrigemCampo.MANUAL),
    "desocupacao": ("15000.00", OrigemCampo.MANUAL),
    "valor_mercado": ("190000.00", OrigemCampo.MANUAL),
}


def _calcular(**extras: tuple[str, OrigemCampo]):
    return calcular(build_snapshot(arremate="49647.00", campos={**CAMPOS_BASE, **extras}))


def _linha(resultado, chave):
    return next(l for g in resultado.grupos for l in g.linhas if l.chave == chave)


def test_sem_ajustes_usa_parametros_do_usuario():
    resultado = _calcular()
    assert resultado.comissao_corretor_pct == Decimal("6")
    assert resultado.prazo_carregamento_meses == 12
    assert _linha(resultado, "outros_gastos").valor is None
    assert "outros_gastos" not in resultado.campos_em_branco  # em branco é o normal, não lacuna


def test_comissao_do_corretor_ajustada_no_imovel():
    resultado = _calcular(comissao_corretor_pct=("5", OrigemCampo.MANUAL))
    assert resultado.comissao_corretor_pct == Decimal("5")
    assert resultado.comissao_corretor == Decimal("9500")
    assert resultado.ganho_capital == Decimal("102892")
    assert resultado.ir == Decimal("15434")
    assert resultado.lucro == Decimal("65638")
    assert _linha(resultado, "comissao_corretor").fonte == "5,0% sobre a revenda"


def test_prazo_de_carregamento_ajustado_no_imovel():
    resultado = _calcular(prazo_carregamento_meses=("6", OrigemCampo.MANUAL))
    assert resultado.prazo_carregamento_meses == 6
    assert resultado.carregamento == Decimal("1710")
    assert resultado.investimento == Decimal("97718")
    assert _linha(resultado, "iptu_mensal").rotulo == "IPTU mensal × 6 meses"


def test_outros_gastos_entram_na_aquisicao_mas_nao_abatem_o_ir():
    snapshot = build_snapshot(
        arremate="49647.00",
        campos={**CAMPOS_BASE, "outros_gastos": ("3000.00", OrigemCampo.MANUAL)},
    ).model_copy(update={"outros_gastos_descricao": "caminhão de mudança do morador"})
    resultado = calcular(snapshot)

    assert resultado.aquisicao == Decimal("58608")
    assert resultado.investimento == Decimal("102428")
    assert resultado.ganho_capital == Decimal("100992")  # igual ao golden
    assert resultado.ir == Decimal("15149")
    assert resultado.lucro == Decimal("61023")
    linha = _linha(resultado, "outros_gastos")
    assert linha.valor == Decimal("3000")
    assert linha.fonte == "caminhão de mudança do morador"
