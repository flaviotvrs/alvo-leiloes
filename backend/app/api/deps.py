from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.models.usuario import Usuario

security = HTTPBearer()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_usuario(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> Usuario:
    """Autenticação mínima do MVP1: um único bearer token estático mapeado para o usuário
    seedado — não é multiusuário (fora de escopo), só evita FKs (ator_id, preenchido_por)
    soltas ou nullable demais."""
    if credentials.credentials != settings.api_bearer_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    usuario = db.query(Usuario).order_by(Usuario.criado_em).first()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Nenhum usuário seedado — rode `python -m app.seeds.seed`",
        )
    return usuario
