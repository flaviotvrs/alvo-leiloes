import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import TipoEvento
from app.models.mixins import UUIDPk
from app.models.types import str_enum


class EventoAvaliacao(UUIDPk, Base):
    """Trilha de auditoria: alimenta o "Histórico do registro" da Ficha. `payload` guarda
    `{chave, de, para}` para mudanças de campo, e a lista de campos em branco quando uma
    etapa avança com lacuna (README.md "Regras de negócio que a interface reflete")."""

    __tablename__ = "evento_avaliacao"

    avaliacao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("avaliacao.id"))
    tipo: Mapped[TipoEvento] = mapped_column(str_enum(TipoEvento, "tipo_evento"))
    ator_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
