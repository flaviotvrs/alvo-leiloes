import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import OrigemCampo
from app.models.mixins import UUIDPk
from app.models.types import str_enum

# Catálogo das onze chaves da Ficha (README.md "Bloco B"), para referência — não é um
# CHECK constraint no banco porque o catálogo pode crescer sem migration (BACKEND.md
# já prevê campos de edital fora do MVP1: responsabilidade por dívida, foro/laudêmio, etc).
CHAVES_CAMPO_MVP1 = (
    "aceita_fgts",
    "valor_mercado",
    "itbi_aliquota_pct",
    "comissao_leiloeiro_pct",
    "iptu_atraso",
    "condominio_atraso",
    "iptu_mensal",
    "condominio_mensal",
    "ocupacao",
    "reforma",
    "desocupacao",
)


class CampoAvaliacao(UUIDPk, Base):
    """Uma linha por campo preenchido à mão — o coração da procedência do dado. `sugestao_valor`
    / `sugestao_origem` já existem aqui porque o MVP1 mostra a "sugestão de automação" mockada
    no valor de mercado; é o gancho do MVP2 (agente de valor de mercado), que só escreve
    sugestão e nunca sobrescreve o valor do usuário."""

    __tablename__ = "campo_avaliacao"
    __table_args__ = (UniqueConstraint("avaliacao_id", "chave", name="uq_campo_avaliacao_chave"),)

    avaliacao_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("avaliacao.id"))
    chave: Mapped[str]
    valor_numerico: Mapped[float | None] = mapped_column(Numeric(14, 2))
    valor_texto: Mapped[str | None]
    origem: Mapped[OrigemCampo] = mapped_column(str_enum(OrigemCampo, "origem_campo"))
    fonte_declarada: Mapped[str | None]
    preenchido_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"))
    preenchido_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sugestao_valor: Mapped[float | None] = mapped_column(Numeric(14, 2))
    sugestao_origem: Mapped[str | None]
