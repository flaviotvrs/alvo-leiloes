import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.enums import FonteLeilao, StatusImportacao
from app.models.mixins import UUIDPk
from app.models.types import str_enum


class Importacao(UUIDPk, Base):
    """Uma carga de dados de uma fonte (planilha da Caixa, scraping Zukerman). Base da
    futura tela de Importações — o único lugar do produto onde volume/status de importação
    deve aparecer (README.md "Navegação global")."""

    __tablename__ = "importacao"

    fonte: Mapped[FonteLeilao] = mapped_column(str_enum(FonteLeilao, "fonte_leilao"))
    arquivo_nome: Mapped[str | None]
    arquivo_hash: Mapped[str | None] = mapped_column(index=True)
    arquivo_gerado_em: Mapped[date | None] = mapped_column(Date)
    linhas_lidas: Mapped[int] = mapped_column(Integer, default=0)
    criados: Mapped[int] = mapped_column(Integer, default=0)
    atualizados: Mapped[int] = mapped_column(Integer, default=0)
    inalterados: Mapped[int] = mapped_column(Integer, default=0)
    inativados: Mapped[int] = mapped_column(Integer, default=0)
    reativados: Mapped[int] = mapped_column(Integer, default=0)
    erros: Mapped[list] = mapped_column(JSONB, default=list)
    iniciada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    concluida_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[StatusImportacao] = mapped_column(
        str_enum(StatusImportacao, "status_importacao"), default=StatusImportacao.PROCESSANDO
    )
    executada_por: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"))
