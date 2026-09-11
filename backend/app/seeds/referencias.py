import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.enums import ConfiancaItbi, FonteItbi
from app.models.referencia import EmolumentoFaixa, ItbiMunicipio

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def carregar_itbi(db: Session) -> None:
    dados = json.loads((FIXTURES_DIR / "itbi.json").read_text())
    for item in dados:
        existente = (
            db.query(ItbiMunicipio)
            .filter_by(uf=item["uf"], cidade=item["cidade"])
            .one_or_none()
        )
        if existente:
            continue
        db.add(
            ItbiMunicipio(
                uf=item["uf"],
                cidade=item["cidade"],
                aliquota_pct=item["aliquota_pct"],
                fonte=FonteItbi(item["fonte"]),
                confianca=ConfiancaItbi(item["confianca"]),
                observacao=item.get("observacao"),
            )
        )


def carregar_emolumentos(db: Session) -> None:
    dados = json.loads((FIXTURES_DIR / "emolumentos_tjmg_4_2026.json").read_text())
    tabela = dados["tabela"]
    item = dados["item"]
    ja_existe = db.query(EmolumentoFaixa).filter_by(tabela=tabela, item=item).first()
    if ja_existe:
        return
    for faixa in dados["faixas"]:
        db.add(
            EmolumentoFaixa(
                tabela=tabela,
                item=item,
                limite_superior=faixa["limite_superior"],
                valor=faixa["valor"],
                vigencia_inicio=dados["vigencia_inicio"],
                vigencia_fim=None,
            )
        )
