from decimal import Decimal

from app.models.enums import OrigemCampo
from app.services.calculo import calcular
from tests.unit.factories import build_snapshot


def test_cenario_completo_bate_com_backend_md():
    """BACKEND.md "Testes que valem a pena escrever primeiro" #3: arremate 49.647, ITBI a
    3% (manual), registro pela faixa de 56.000, IPTU em atraso 3.400, condomínio em atraso
    nulo, IPTU mensal 285, condomínio mensal nulo, reforma 22.000, desocupação 15.000,
    revenda 190.000, corretor 6%, prazo 12 meses — comissão do leiloeiro não informada
    (usa o palpite padrão de 5%)."""
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

    resultado = calcular(snapshot)

    assert resultado.aquisicao == Decimal("55608")
    assert resultado.dividas == Decimal("3400")
    assert resultado.posse == Decimal("37000")
    assert resultado.carregamento == Decimal("3420")
    assert resultado.investimento == Decimal("99428")
    assert resultado.comissao_corretor == Decimal("11400")
    assert resultado.ganho_capital == Decimal("100992")
    assert resultado.ir == Decimal("15149")
    assert resultado.lucro == Decimal("64023")
    assert resultado.margem_investimento_pct == Decimal("64.4")
    assert resultado.margem_revenda_pct == Decimal("33.7")
    assert resultado.veredito == "aprovado"

    # comissão do leiloeiro não foi informada -> linha assumida com o palpite de 5%
    assert "comissao_leiloeiro_pct" not in resultado.campos_em_branco  # não é um campo "em branco"
    linha_leiloeiro = next(l for g in resultado.grupos for l in g.linhas if l.chave == "comissao_leiloeiro")
    assert linha_leiloeiro.assumido is True
    assert linha_leiloeiro.campo_para_confirmar == "comissao_leiloeiro_pct"

    # ITBI foi confirmado manualmente -> não é palpite
    linha_itbi = next(l for g in resultado.grupos for l in g.linhas if l.chave == "itbi")
    assert linha_itbi.assumido is False

    # condominio_atraso e condominio_mensal ficaram em branco
    assert "condominio_atraso" in resultado.campos_em_branco
    assert "condominio_mensal" in resultado.campos_em_branco
