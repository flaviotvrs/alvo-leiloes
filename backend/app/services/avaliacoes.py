import uuid

from sqlalchemy.orm import Session

from app.models.avaliacao import Avaliacao
from app.models.enums import Etapa


def obter_ou_criar_avaliacao(db: Session, lote_id: uuid.UUID, usuario_id: uuid.UUID) -> Avaliacao:
    avaliacao = db.query(Avaliacao).filter_by(lote_id=lote_id, usuario_id=usuario_id).one_or_none()
    if avaliacao is None:
        avaliacao = Avaliacao(lote_id=lote_id, usuario_id=usuario_id, etapa=Etapa.NAO_AVALIADO)
        db.add(avaliacao)
        db.flush()
    return avaliacao


def obter_ou_criar_avaliacoes(
    db: Session, lote_ids: list[uuid.UUID], usuario_id: uuid.UUID
) -> dict[uuid.UUID, Avaliacao]:
    """Versão em lote, para paginação — só cria as que realmente faltam na página atual."""
    existentes = (
        db.query(Avaliacao)
        .filter(Avaliacao.usuario_id == usuario_id, Avaliacao.lote_id.in_(lote_ids))
        .all()
    )
    por_lote = {a.lote_id: a for a in existentes}
    faltando = [lid for lid in lote_ids if lid not in por_lote]
    for lid in faltando:
        nova = Avaliacao(lote_id=lid, usuario_id=usuario_id, etapa=Etapa.NAO_AVALIADO)
        db.add(nova)
        por_lote[lid] = nova
    if faltando:
        db.flush()
    return por_lote
