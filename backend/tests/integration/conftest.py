import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.db import engine


@pytest.fixture()
def db_session():
    """Uma transação por teste, com rollback ao final — nada de um teste vaza para outro,
    sem precisar de um banco de teste separado."""
    connection = engine.connect()
    transaction = connection.begin()
    # join_transaction_mode="create_savepoint": session.commit() dentro do código testado
    # usa um SAVEPOINT em vez de encerrar a transação externa, que é a que damos rollback.
    TestSessionLocal = sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
    session: Session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
