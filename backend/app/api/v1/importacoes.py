import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_usuario, get_db
from app.importers.caixa import importar_caixa
from app.models.importacao import Importacao
from app.models.usuario import Usuario
from app.schemas.api import ImportacaoDTO

router = APIRouter(prefix="/importacoes", tags=["importacoes"])


def _to_dto(i: Importacao) -> ImportacaoDTO:
    return ImportacaoDTO(
        id=i.id,
        fonte=i.fonte,
        arquivo_nome=i.arquivo_nome,
        linhas_lidas=i.linhas_lidas,
        criados=i.criados,
        atualizados=i.atualizados,
        inalterados=i.inalterados,
        erros=i.erros,
        status=i.status,
        iniciada_em=i.iniciada_em,
        concluida_em=i.concluida_em,
    )


@router.post("", response_model=ImportacaoDTO)
def disparar_importacao(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ImportacaoDTO:
    if not arquivo.filename or not arquivo.filename.lower().endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=422, detail="Envie uma planilha .xlsx da Caixa")

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        tmp.write(arquivo.file.read())
        caminho = Path(tmp.name)
    try:
        importacao = importar_caixa(db, caminho, executada_por=usuario.id)
        if importacao.arquivo_nome != arquivo.filename:
            importacao.arquivo_nome = arquivo.filename
            db.commit()
            db.refresh(importacao)
    finally:
        caminho.unlink(missing_ok=True)
    return _to_dto(importacao)


@router.get("", response_model=list[ImportacaoDTO])
def listar_importacoes(
    db: Session = Depends(get_db), _usuario: Usuario = Depends(get_current_usuario)
) -> list[ImportacaoDTO]:
    linhas = db.query(Importacao).order_by(Importacao.iniciada_em.desc()).all()
    return [_to_dto(i) for i in linhas]
