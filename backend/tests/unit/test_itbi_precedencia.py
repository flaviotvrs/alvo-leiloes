from decimal import Decimal

from app.models.enums import OrigemCampo
from app.services.calculo import calcular
from tests.unit.factories import build_snapshot


def _linha_itbi(resultado):
    return next(l for g in resultado.grupos for l in g.linhas if l.chave == "itbi")


def test_campo_digitado_tem_precedencia_sobre_tabela_e_padrao():
    snapshot = build_snapshot(
        arremate="100000.00",
        cidade="Belo Horizonte",  # tabela diria 3% — o campo digitado deve vencer
        campos={"itbi_aliquota_pct": ("4.0", OrigemCampo.MANUAL)},
    )
    resultado = calcular(snapshot)
    linha = _linha_itbi(resultado)
    assert linha.valor == Decimal("4000")  # 4% de 100.000
    assert linha.assumido is False


def test_tabela_do_municipio_tem_precedencia_sobre_padrao():
    snapshot = build_snapshot(arremate="100000.00", cidade="Belo Horizonte")
    resultado = calcular(snapshot)
    linha = _linha_itbi(resultado)
    assert linha.valor == Decimal("3000")  # 3% confirmado na tabela de BH
    assert linha.assumido is False  # tabela do município não é palpite


def test_cidade_sem_tabela_cai_no_padrao_e_fica_assumido():
    snapshot = build_snapshot(arremate="100000.00", cidade="Juatuba")
    resultado = calcular(snapshot)
    linha = _linha_itbi(resultado)
    assert linha.valor == Decimal("3000")  # padrao 3%, mesmo valor de BH, mas por outro motivo
    assert linha.assumido is True
    assert linha.campo_para_confirmar == "itbi_aliquota_pct"
    assert any("itbi" in p.lower() for p in resultado.premissas)
