from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import UUIDPk


class Usuario(UUIDPk, Base):
    """Tabela mínima: BACKEND.md referencia FKs para "o usuário" (responsavel_id,
    preenchido_por, ator_id, executada_por) mas nunca especifica esta tabela.
    Autenticação do MVP1 é um único bearer token estático mapeado para um usuário seed."""

    __tablename__ = "usuario"

    nome: Mapped[str]
    email: Mapped[str] = mapped_column(unique=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
