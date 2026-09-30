"""comissao do corretor padrao 5%

Revision ID: 3a9e4f7c21b0
Revises: 2401d8f8d029
Create Date: 2026-09-29 23:30:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '3a9e4f7c21b0'
down_revision: Union[str, Sequence[str], None] = '2401d8f8d029'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # o padrão era 6% no código; ainda não há tela de parâmetros, então quem está em 6%
    # nunca escolheu esse valor — passa para o novo padrão de 5%
    op.execute("UPDATE parametro_usuario SET comissao_corretor_pct = 5 WHERE comissao_corretor_pct = 6")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("UPDATE parametro_usuario SET comissao_corretor_pct = 6 WHERE comissao_corretor_pct = 5")
