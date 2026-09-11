import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, Numeric, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import AceitaFgts, FonteLeilao
from app.models.mixins import UUIDPk
from app.models.types import str_enum


class LoteLeilao(UUIDPk, Base):
    """A oferta específica de um imóvel em um leilão: tem preço, datas de praça e pertence
    a uma fonte (Caixa, Zukerman). Um imóvel pode voltar a leilão em mais de um lote."""

    __tablename__ = "lote_leilao"
    __table_args__ = (
        UniqueConstraint("fonte", "codigo_externo", name="uq_lote_fonte_codigo"),
        # partial index: a triagem só lista lotes ativos (BACKEND.md "Performance").
        Index("ix_lote_leilao_ativo", "ativo", postgresql_where=text("ativo = true")),
    )

    imovel_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("imovel.id"))
    fonte: Mapped[FonteLeilao] = mapped_column(str_enum(FonteLeilao, "fonte_leilao"))
    codigo_externo: Mapped[str]
    modalidade: Mapped[str | None]
    preco_venda: Mapped[float] = mapped_column(Numeric(14, 2), index=True)
    valor_avaliacao: Mapped[float | None] = mapped_column(Numeric(14, 2))
    desconto_pct: Mapped[float | None] = mapped_column(Numeric(5, 2), index=True)
    aceita_financiamento: Mapped[bool] = mapped_column(Boolean, default=False)
    aceita_fgts: Mapped[AceitaFgts | None] = mapped_column(str_enum(AceitaFgts, "aceita_fgts"))
    praca_1_valor: Mapped[float | None] = mapped_column(Numeric(14, 2))
    praca_1_data: Mapped[date | None] = mapped_column(Date)
    praca_2_valor: Mapped[float | None] = mapped_column(Numeric(14, 2))
    praca_2_data: Mapped[date | None] = mapped_column(Date)
    url_fonte: Mapped[str | None]
    importacao_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("importacao.id"))
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
