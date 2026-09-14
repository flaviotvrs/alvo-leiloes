import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import Etapa
from app.models.mixins import UUIDPk
from app.models.types import str_enum

CHECKLIST_PADRAO = {
    "matricula": False,
    "visita": False,
    "iptu": False,
    "condominio": False,
    "edital": False,
    "comparaveis": False,
}


class Avaliacao(UUIDPk, Base):
    """O agregado que a Ficha do imóvel edita: etapa no funil, anotações de visita e
    checklist de campo. Uma linha por (lote, usuário) — nasce sob demanda no primeiro acesso
    daquele usuário àquele imóvel, não na importação (dado por usuário, não global)."""

    __tablename__ = "avaliacao"
    __table_args__ = (UniqueConstraint("lote_id", "usuario_id", name="uq_avaliacao_lote_usuario"),)

    lote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lote_leilao.id"))
    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"), index=True)
    etapa: Mapped[Etapa] = mapped_column(str_enum(Etapa, "etapa"), default=Etapa.TRIAGEM, index=True)
    etapa_desde: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    motivo_descarte: Mapped[str | None]
    teto_lance: Mapped[float | None] = mapped_column(Numeric(14, 2))
    anotacoes: Mapped[str] = mapped_column(default="")
    checklist: Mapped[dict] = mapped_column(JSONB, default=lambda: dict(CHECKLIST_PADRAO))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
