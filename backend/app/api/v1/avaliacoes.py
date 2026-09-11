from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_usuario, get_db
from app.models.avaliacao import Avaliacao
from app.models.campo_avaliacao import CHAVES_CAMPO_MVP1, CampoAvaliacao
from app.models.enums import Etapa, OrigemCampo, TipoEvento
from app.models.evento_avaliacao import EventoAvaliacao
from app.models.usuario import Usuario
from app.schemas.api import DescartarRequest, EtapaRequest, EventoDTO, PatchAvaliacaoRequest, PatchCampoRequest
from app.schemas.calculo import Resultado
from app.services.calculo import calcular
from app.services.numeros import parse_decimal_br
from app.services.resumo_campos import resumo_de_uma_avaliacao
from app.services.snapshot import montar_snapshot

router = APIRouter(prefix="/avaliacoes", tags=["avaliacoes"])

# Campos cujo valor é um enum de texto, não um número — README Bloco B (aceita_fgts, ocupacao)
CHAVES_TEXTO = {"aceita_fgts", "ocupacao"}

TRANSICOES_VALIDAS: dict[Etapa, set[Etapa]] = {
    Etapa.NAO_AVALIADO: {Etapa.PESQUISA_CAMPO, Etapa.DESCARTADO},
    Etapa.PESQUISA_CAMPO: {Etapa.ANALISE_FINANCEIRA, Etapa.DESCARTADO},
    Etapa.ANALISE_FINANCEIRA: {Etapa.DECISAO, Etapa.PESQUISA_CAMPO, Etapa.DESCARTADO},
    Etapa.DECISAO: {Etapa.APROVADO_LANCE, Etapa.ANALISE_FINANCEIRA, Etapa.DESCARTADO},
    Etapa.APROVADO_LANCE: {Etapa.DESCARTADO},
    Etapa.DESCARTADO: set(),
}


def _get_avaliacao_ou_404(db: Session, avaliacao_id: UUID, usuario: Usuario) -> Avaliacao:
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None or avaliacao.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    return avaliacao


@router.patch("/{avaliacao_id}/campos/{chave}", response_model=Resultado)
def gravar_campo(
    avaliacao_id: UUID,
    chave: str,
    body: PatchCampoRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> Resultado:
    avaliacao = _get_avaliacao_ou_404(db, avaliacao_id, usuario)
    if chave not in CHAVES_CAMPO_MVP1:
        raise HTTPException(status_code=400, detail=f"Campo desconhecido: {chave}")

    existente = db.query(CampoAvaliacao).filter_by(avaliacao_id=avaliacao_id, chave=chave).one_or_none()
    valor_anterior = existente.valor_numerico if existente and existente.valor_numerico is not None else (
        existente.valor_texto if existente else None
    )

    if body.valor is None or body.valor == "":
        if existente is not None:
            db.delete(existente)
            db.add(
                EventoAvaliacao(
                    avaliacao_id=avaliacao_id,
                    tipo=TipoEvento.CAMPO_ALTERADO,
                    ator_id=usuario.id,
                    payload={"chave": chave, "de": str(valor_anterior) if valor_anterior is not None else None, "para": None},
                )
            )
    else:
        if existente is None:
            existente = CampoAvaliacao(avaliacao_id=avaliacao_id, chave=chave)
            db.add(existente)
        if chave in CHAVES_TEXTO:
            existente.valor_texto = body.valor
            existente.valor_numerico = None
        else:
            try:
                existente.valor_numerico = parse_decimal_br(body.valor)
            except ValueError as exc:
                raise HTTPException(status_code=422, detail=str(exc)) from exc
            existente.valor_texto = None
        existente.origem = OrigemCampo.MANUAL
        existente.fonte_declarada = body.fonte_declarada
        existente.preenchido_por = usuario.id
        existente.preenchido_em = datetime.now(UTC)
        db.add(
            EventoAvaliacao(
                avaliacao_id=avaliacao_id,
                tipo=TipoEvento.CAMPO_ALTERADO,
                ator_id=usuario.id,
                payload={"chave": chave, "de": str(valor_anterior) if valor_anterior is not None else None, "para": body.valor},
            )
        )

    db.commit()
    return calcular(montar_snapshot(db, avaliacao))


@router.post("/{avaliacao_id}/campos/{chave}/aceitar-sugestao", response_model=Resultado)
def aceitar_sugestao(
    avaliacao_id: UUID,
    chave: str,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> Resultado:
    avaliacao = _get_avaliacao_ou_404(db, avaliacao_id, usuario)
    campo = db.query(CampoAvaliacao).filter_by(avaliacao_id=avaliacao_id, chave=chave).one_or_none()
    if campo is None or campo.sugestao_valor is None:
        raise HTTPException(status_code=400, detail="Não há sugestão de automação para este campo")

    valor_anterior = campo.valor_numerico
    campo.valor_numerico = campo.sugestao_valor
    campo.origem = OrigemCampo.AUTOMACAO
    campo.fonte_declarada = campo.sugestao_origem
    campo.preenchido_por = usuario.id
    campo.preenchido_em = datetime.now(UTC)

    db.add(
        EventoAvaliacao(
            avaliacao_id=avaliacao_id,
            tipo=TipoEvento.SUGESTAO_ACEITA,
            ator_id=usuario.id,
            payload={
                "chave": chave,
                "de": str(valor_anterior) if valor_anterior is not None else None,
                "para": str(campo.valor_numerico),
            },
        )
    )
    db.commit()
    return calcular(montar_snapshot(db, avaliacao))


@router.patch("/{avaliacao_id}")
def atualizar_avaliacao(
    avaliacao_id: UUID,
    body: PatchAvaliacaoRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> dict[str, str]:
    avaliacao = _get_avaliacao_ou_404(db, avaliacao_id, usuario)
    if body.anotacoes is not None:
        avaliacao.anotacoes = body.anotacoes
    if body.checklist is not None:
        avaliacao.checklist = {**avaliacao.checklist, **body.checklist}
    if body.teto_lance is not None:
        avaliacao.teto_lance = body.teto_lance
    db.commit()
    return {"status": "ok"}


@router.post("/{avaliacao_id}/etapa", response_model=Resultado)
def mover_etapa(
    avaliacao_id: UUID,
    body: EtapaRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> Resultado:
    avaliacao = _get_avaliacao_ou_404(db, avaliacao_id, usuario)
    permitidas = TRANSICOES_VALIDAS.get(avaliacao.etapa, set())
    if body.etapa not in permitidas:
        raise HTTPException(
            status_code=400,
            detail=f"Transição inválida: {avaliacao.etapa.value} -> {body.etapa.value}",
        )

    resumo = resumo_de_uma_avaliacao(db, avaliacao_id)
    etapa_anterior = avaliacao.etapa
    avaliacao.etapa = body.etapa
    avaliacao.etapa_desde = datetime.now(UTC)

    db.add(
        EventoAvaliacao(
            avaliacao_id=avaliacao_id,
            tipo=TipoEvento.ETAPA_ALTERADA,
            ator_id=usuario.id,
            payload={
                "de": etapa_anterior.value,
                "para": body.etapa.value,
                "motivo": body.motivo,
                "campos_em_branco_no_momento": resumo.faltando,
            },
        )
    )
    db.commit()
    return calcular(montar_snapshot(db, avaliacao))


@router.post("/{avaliacao_id}/descartar")
def descartar(
    avaliacao_id: UUID,
    body: DescartarRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> dict[str, str]:
    avaliacao = _get_avaliacao_ou_404(db, avaliacao_id, usuario)
    etapa_anterior = avaliacao.etapa
    avaliacao.etapa = Etapa.DESCARTADO
    avaliacao.motivo_descarte = body.motivo
    avaliacao.etapa_desde = datetime.now(UTC)
    db.add(
        EventoAvaliacao(
            avaliacao_id=avaliacao_id,
            tipo=TipoEvento.DESCARTE,
            ator_id=usuario.id,
            payload={"de": etapa_anterior.value, "motivo": body.motivo},
        )
    )
    db.commit()
    return {"status": "ok"}


@router.get("/{avaliacao_id}/calculo", response_model=Resultado)
def calculo(
    avaliacao_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> Resultado:
    avaliacao = _get_avaliacao_ou_404(db, avaliacao_id, usuario)
    return calcular(montar_snapshot(db, avaliacao))


@router.get("/{avaliacao_id}/eventos", response_model=list[EventoDTO])
def eventos(
    avaliacao_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> list[EventoDTO]:
    _get_avaliacao_ou_404(db, avaliacao_id, usuario)
    linhas = (
        db.query(EventoAvaliacao)
        .filter_by(avaliacao_id=avaliacao_id)
        .order_by(EventoAvaliacao.criado_em.desc())
        .all()
    )
    return [
        EventoDTO(id=e.id, tipo=e.tipo, ator_id=e.ator_id, payload=e.payload, criado_em=e.criado_em)
        for e in linhas
    ]
