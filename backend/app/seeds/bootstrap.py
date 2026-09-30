"""Bootstrap mínimo para qualquer ambiente (dev ou produção): carrega as referências reais
(ITBI, emolumentos), cria o usuário único do MVP1 e seus parâmetros padrão. Sem isso nenhum
endpoint autenticado funciona (`get_current_usuario` depende de haver um `Usuario` na base).
Não inclui nenhum dado fictício — a importação de exemplo fica em `seed.py`, só para dev.
Rode com `uv run python -m app.seeds.bootstrap`."""

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models.parametro import ParametroUsuario
from app.models.usuario import Usuario
from app.seeds.referencias import carregar_emolumentos, carregar_itbi

USUARIO_EMAIL = "flaviotvrs@gmail.com"
USUARIO_NOME = "Flavio"


def _usuario_unico(db: Session) -> Usuario:
    usuario = db.query(Usuario).filter_by(email=USUARIO_EMAIL).one_or_none()
    if usuario is None:
        usuario = Usuario(nome=USUARIO_NOME, email=USUARIO_EMAIL)
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    return usuario


def _parametros_padrao(db: Session, usuario: Usuario) -> None:
    if db.query(ParametroUsuario).filter_by(usuario_id=usuario.id).first():
        return
    db.add(ParametroUsuario(usuario_id=usuario.id))
    db.commit()


def bootstrap(db: Session) -> Usuario:
    carregar_itbi(db)
    carregar_emolumentos(db)
    db.commit()

    usuario = _usuario_unico(db)
    _parametros_padrao(db, usuario)
    return usuario


def main() -> None:
    db = SessionLocal()
    try:
        usuario = bootstrap(db)
        print(f"Bootstrap concluído — usuário {usuario.email} (id={usuario.id}).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
