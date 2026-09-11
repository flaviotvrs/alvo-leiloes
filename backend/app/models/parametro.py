import uuid

from sqlalchemy import ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.models.mixins import UUIDPk


class ParametroUsuario(UUIDPk, Base):
    """Parâmetros do cenário financeiro, por usuário. Os quatro últimos são os "valores de
    palpite" (BACKEND.md): ficarem em tabela, e não em código, é o que permite a interface
    dizer "usando palpite de 3%" com um número que o usuário pode mudar."""

    __tablename__ = "parametro_usuario"

    usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"), unique=True)
    prazo_carregamento_meses: Mapped[int] = mapped_column(Integer, default=12)
    comissao_corretor_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=6)
    piso_margem_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=20)
    ir_aliquota_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=15)
    itbi_aliquota_padrao_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=3)
    comissao_leiloeiro_padrao_pct: Mapped[float] = mapped_column(Numeric(5, 2), default=5)
