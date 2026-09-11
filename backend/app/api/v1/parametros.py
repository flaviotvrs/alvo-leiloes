from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_usuario, get_db
from app.models.parametro import ParametroUsuario
from app.models.usuario import Usuario
from app.schemas.api import ParametroDTO, PatchParametroRequest

router = APIRouter(prefix="/parametros", tags=["parametros"])


def _get_ou_criar(db: Session, usuario: Usuario) -> ParametroUsuario:
    parametros = db.query(ParametroUsuario).filter_by(usuario_id=usuario.id).one_or_none()
    if parametros is None:
        parametros = ParametroUsuario(usuario_id=usuario.id)
        db.add(parametros)
        db.commit()
        db.refresh(parametros)
    return parametros


@router.get("", response_model=ParametroDTO)
def obter_parametros(
    db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_usuario)
) -> ParametroUsuario:
    return _get_ou_criar(db, usuario)


@router.patch("", response_model=ParametroDTO)
def atualizar_parametros(
    body: PatchParametroRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ParametroUsuario:
    parametros = _get_ou_criar(db, usuario)
    for campo, valor in body.model_dump(exclude_unset=True).items():
        setattr(parametros, campo, valor)
    db.commit()
    db.refresh(parametros)
    return parametros
