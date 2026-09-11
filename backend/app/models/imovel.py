from datetime import datetime

from sqlalchemy import CHAR, DateTime, Index, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import TipoImovel
from app.models.mixins import UUIDPk
from app.models.types import str_enum


class Imovel(UUIDPk, Base):
    """Identidade e fatos estruturais do imóvel, independentes de leilão. `id` é o
    imovel_id estável (BACKEND.md princípio 1): reimportar a mesma planilha atualiza o
    registro existente via lote_leilao, nunca recria o imóvel."""

    __tablename__ = "imovel"
    __table_args__ = (
        Index("ix_imovel_uf_cidade", "uf", "cidade"),
        # busca de bairro é substring case-insensitive (README "Painel de filtros") —
        # trigram GIN index; requer a extensão pg_trgm (criada na migration inicial).
        Index(
            "ix_imovel_bairro_trgm",
            "bairro",
            postgresql_using="gin",
            postgresql_ops={"bairro": "gin_trgm_ops"},
        ),
    )

    uf: Mapped[str] = mapped_column(CHAR(2))
    cidade: Mapped[str]
    bairro: Mapped[str | None]
    endereco: Mapped[str]
    tipo: Mapped[TipoImovel] = mapped_column(str_enum(TipoImovel, "tipo_imovel"))
    area_total_m2: Mapped[float | None] = mapped_column(Numeric(10, 2))
    area_privativa_m2: Mapped[float | None] = mapped_column(Numeric(10, 2))
    area_terreno_m2: Mapped[float | None] = mapped_column(Numeric(10, 2))
    quartos: Mapped[int | None]
    descricao_oficial: Mapped[str | None]
    inscricao_municipal: Mapped[str | None]
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
