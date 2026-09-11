from decimal import Decimal

from app.models.enums import OrigemCampo
from app.schemas.calculo import (
    CampoSnapshot,
    EmolumentoFaixaReferencia,
    ItbiReferencia,
    ParametrosSnapshot,
    Snapshot,
    TabelasSnapshot,
)

FAIXAS_TJMG_4_2026_5E = [
    EmolumentoFaixaReferencia(limite_superior=Decimal("1400.00"), valor=Decimal("227.95")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("2720.00"), valor=Decimal("371.84")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("5440.00"), valor=Decimal("538.85")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("7000.00"), valor=Decimal("745.98")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("14000.00"), valor=Decimal("994.78")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("28000.00"), valor=Decimal("1285.21")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("42000.00"), valor=Decimal("1597.11")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("56000.00"), valor=Decimal("1989.94")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("70000.00"), valor=Decimal("2404.60")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("105000.00"), valor=Decimal("3026.34")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("140000.00"), valor=Decimal("3839.67")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("175000.00"), valor=Decimal("4106.03")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("210000.00"), valor=Decimal("4372.88")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("280000.00"), valor=Decimal("4914.86")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("350000.00"), valor=Decimal("5050.25")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("420000.00"), valor=Decimal("5186.26")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("560000.00"), valor=Decimal("5677.78")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("700000.00"), valor=Decimal("5989.84")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("840000.00"), valor=Decimal("6302.53")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("1120000.00"), valor=Decimal("7046.73")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("1400000.00"), valor=Decimal("7632.83")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("1680000.00"), valor=Decimal("8219.92")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("3200000.00"), valor=Decimal("8808.22")),
    EmolumentoFaixaReferencia(limite_superior=Decimal("3700000.00"), valor=Decimal("13034.69")),
]

ITBI_REFERENCIA = [
    ItbiReferencia(uf="MG", cidade="Belo Horizonte", aliquota_pct=Decimal("3.0")),
    ItbiReferencia(uf="MG", cidade="Contagem", aliquota_pct=Decimal("3.0")),
    ItbiReferencia(uf="MG", cidade="Betim", aliquota_pct=Decimal("3.0")),
    ItbiReferencia(uf="MG", cidade="Sete Lagoas", aliquota_pct=Decimal("2.5")),
]

PARAMETROS_PADRAO = ParametrosSnapshot(
    prazo_carregamento_meses=12,
    comissao_corretor_pct=Decimal("6"),
    piso_margem_pct=Decimal("20"),
    ir_aliquota_pct=Decimal("15"),
    itbi_aliquota_padrao_pct=Decimal("3"),
    comissao_leiloeiro_padrao_pct=Decimal("5"),
)


def build_snapshot(
    *,
    arremate: str,
    cidade: str = "Belo Horizonte",
    uf: str = "MG",
    campos: dict[str, tuple[str | None, OrigemCampo]] | None = None,
    parametros: ParametrosSnapshot | None = None,
    faixas: list[EmolumentoFaixaReferencia] | None = None,
    itbi_ref: list[ItbiReferencia] | None = None,
    dividas_sao_do_arrematante: bool = True,
) -> Snapshot:
    campos = campos or {}
    return Snapshot(
        arremate=Decimal(arremate),
        cidade=cidade,
        uf=uf,
        campos={
            chave: CampoSnapshot(valor=Decimal(valor) if valor is not None else None, origem=origem)
            for chave, (valor, origem) in campos.items()
        },
        parametros=parametros or PARAMETROS_PADRAO,
        tabelas=TabelasSnapshot(
            itbi=itbi_ref if itbi_ref is not None else ITBI_REFERENCIA,
            emolumentos=faixas if faixas is not None else FAIXAS_TJMG_4_2026_5E,
            versao_emolumentos="tjmg_4_2026_5e",
        ),
        dividas_sao_do_arrematante=dividas_sao_do_arrematante,
    )
