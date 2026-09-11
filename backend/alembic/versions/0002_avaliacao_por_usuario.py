"""avaliacao por usuario

Revision ID: f7571fba38bf
Revises: 0bc0adf9ac13
Create Date: 2026-09-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f7571fba38bf'
down_revision: Union[str, Sequence[str], None] = '0bc0adf9ac13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """`Avaliacao` passa de uma linha por lote para uma linha por (lote, usuário) —
    ver docs/requisitos/mvp1-ajustes/05-dados-globais-vs-dados-do-usuario.md."""
    op.add_column('avaliacao', sa.Column('usuario_id', sa.Uuid(), nullable=True))

    # backfill: atribui todas as avaliações hoje existentes ao usuário seed mais antigo,
    # preservando o histórico atual sem perda de dado.
    op.execute(
        "UPDATE avaliacao SET usuario_id = "
        "(SELECT id FROM usuario ORDER BY criado_em LIMIT 1) "
        "WHERE usuario_id IS NULL"
    )

    op.alter_column('avaliacao', 'usuario_id', nullable=False)
    op.create_foreign_key(
        'avaliacao_usuario_id_fkey', 'avaliacao', 'usuario', ['usuario_id'], ['id']
    )
    op.create_index(op.f('ix_avaliacao_usuario_id'), 'avaliacao', ['usuario_id'], unique=False)
    op.create_unique_constraint(
        'uq_avaliacao_lote_usuario', 'avaliacao', ['lote_id', 'usuario_id']
    )

    op.drop_constraint('avaliacao_responsavel_id_fkey', 'avaliacao', type_='foreignkey')
    op.drop_column('avaliacao', 'responsavel_id')


def downgrade() -> None:
    op.add_column('avaliacao', sa.Column('responsavel_id', sa.Uuid(), nullable=True))
    op.create_foreign_key(
        'avaliacao_responsavel_id_fkey', 'avaliacao', 'usuario', ['responsavel_id'], ['id']
    )

    op.drop_constraint('uq_avaliacao_lote_usuario', 'avaliacao', type_='unique')
    op.drop_index(op.f('ix_avaliacao_usuario_id'), table_name='avaliacao')
    op.drop_constraint('avaliacao_usuario_id_fkey', 'avaliacao', type_='foreignkey')
    op.drop_column('avaliacao', 'usuario_id')
