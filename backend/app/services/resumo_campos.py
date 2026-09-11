import uuid
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.campo_avaliacao import CampoAvaliacao
from app.schemas.api import ResumoCampos

# As cinco chaves que valem para o resumo "dados de campo" da Triagem/Funil (README: "cinco
# quadrados de procedência, um por campo-chave: mercado, IPTU, condomínio, ocupação,
# reforma"). O backend decide essa regra — não é responsabilidade do cliente (BACKEND.md).
CHAVES_RESUMO = ("valor_mercado", "iptu_atraso", "condominio_atraso", "ocupacao", "reforma")


def resumo_de_uma_avaliacao(db: Session, avaliacao_id: uuid.UUID) -> ResumoCampos:
    preenchidas = {
        row[0]
        for row in db.execute(
            select(CampoAvaliacao.chave).where(
                CampoAvaliacao.avaliacao_id == avaliacao_id,
                CampoAvaliacao.chave.in_(CHAVES_RESUMO),
            )
        )
    }
    faltando = [c for c in CHAVES_RESUMO if c not in preenchidas]
    return ResumoCampos(preenchidos=len(preenchidas), total=len(CHAVES_RESUMO), faltando=faltando)


def resumo_de_varias_avaliacoes(
    db: Session, avaliacao_ids: list[uuid.UUID]
) -> dict[uuid.UUID, ResumoCampos]:
    if not avaliacao_ids:
        return {}
    preenchidas_por_avaliacao: dict[uuid.UUID, set[str]] = defaultdict(set)
    linhas = db.execute(
        select(CampoAvaliacao.avaliacao_id, CampoAvaliacao.chave).where(
            CampoAvaliacao.avaliacao_id.in_(avaliacao_ids),
            CampoAvaliacao.chave.in_(CHAVES_RESUMO),
        )
    )
    for avaliacao_id, chave in linhas:
        preenchidas_por_avaliacao[avaliacao_id].add(chave)

    return {
        avaliacao_id: ResumoCampos(
            preenchidos=len(preenchidas_por_avaliacao[avaliacao_id]),
            total=len(CHAVES_RESUMO),
            faltando=[c for c in CHAVES_RESUMO if c not in preenchidas_por_avaliacao[avaliacao_id]],
        )
        for avaliacao_id in avaliacao_ids
    }
