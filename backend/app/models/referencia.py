from datetime import date, datetime

from sqlalchemy import CHAR, Date, DateTime, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import ConfiancaItbi, FonteItbi
from app.models.mixins import UUIDPk
from app.models.types import str_enum


class ItbiMunicipio(UUIDPk, Base):
    """Alíquota de ITBI por município. Ausência de linha para um município é o
    comportamento correto (não um dado faltando): o motor de cálculo cai no
    `itbi_aliquota_padrao_pct` de `parametro_usuario` e marca a linha como palpite."""

    __tablename__ = "itbi_municipio"
    __table_args__ = (UniqueConstraint("uf", "cidade", name="uq_itbi_municipio_uf_cidade"),)

    uf: Mapped[str] = mapped_column(CHAR(2))
    cidade: Mapped[str]
    aliquota_pct: Mapped[float] = mapped_column(Numeric(5, 2))
    fonte: Mapped[FonteItbi] = mapped_column(str_enum(FonteItbi, "fonte_itbi"))
    confianca: Mapped[ConfiancaItbi] = mapped_column(str_enum(ConfiancaItbi, "confianca_itbi"))
    observacao: Mapped[str | None]
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class EmolumentoFaixa(UUIDPk, Base):
    """Faixa de valor da tabela de emolumentos de registro em cartório (ex.: TJMG 4-2026,
    item 5-e). Versionada por `vigencia_inicio`/`vigencia_fim` para que uma conta antiga
    possa ser reexplicada com a tabela vigente na data do cálculo (BACKEND.md princípio 3)."""

    __tablename__ = "emolumento_faixa"

    tabela: Mapped[str]
    item: Mapped[str]
    limite_superior: Mapped[float | None] = mapped_column(Numeric(14, 2))
    valor: Mapped[float] = mapped_column(Numeric(14, 2))
    vigencia_inicio: Mapped[date] = mapped_column(Date)
    vigencia_fim: Mapped[date | None] = mapped_column(Date)
