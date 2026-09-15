import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import TipoEvento
from app.models.mixins import UUIDPk
from app.models.types import str_enum


class EventoLote(UUIDPk, Base):
    """Trilha de auditoria em escopo de `LoteLeilao` — a metade do "histórico do imóvel"
    que é dado global (criado/atualizado/inativado/reativado pela importação), espelhando
    `EventoAvaliacao` (a metade por usuário). `ator_id` fica `None` para importações
    automáticas — ver docs/requisitos/mvp1-ajustes/04-importacao-caixa-e-historico.md."""

    __tablename__ = "evento_lote"

    lote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lote_leilao.id"), index=True)
    tipo: Mapped[TipoEvento] = mapped_column(str_enum(TipoEvento, "tipo_evento"))
    importacao_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("importacao.id"))
    ator_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
