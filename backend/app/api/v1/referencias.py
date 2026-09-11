from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_usuario, get_db
from app.models.enums import ConfiancaItbi
from app.models.referencia import ItbiMunicipio
from app.models.usuario import Usuario
from app.schemas.api import ItbiMunicipioDTO, PatchItbiRequest

router = APIRouter(prefix="/referencias", tags=["referencias"])


@router.get("/itbi", response_model=list[ItbiMunicipioDTO])
def listar_itbi(
    db: Session = Depends(get_db), _usuario: Usuario = Depends(get_current_usuario)
) -> list[ItbiMunicipio]:
    return db.query(ItbiMunicipio).order_by(ItbiMunicipio.uf, ItbiMunicipio.cidade).all()


@router.patch("/itbi/{item_id}", response_model=ItbiMunicipioDTO)
def atualizar_itbi(
    item_id: UUID,
    body: PatchItbiRequest,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_usuario),
) -> ItbiMunicipio:
    item = db.get(ItbiMunicipio, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Referência de ITBI não encontrada")
    if body.aliquota_pct is not None:
        item.aliquota_pct = body.aliquota_pct
    if body.confianca is not None:
        item.confianca = ConfiancaItbi(body.confianca)
    if body.observacao is not None:
        item.observacao = body.observacao
    db.commit()
    db.refresh(item)
    return item
