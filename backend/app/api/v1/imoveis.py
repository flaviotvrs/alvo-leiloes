from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import exists, or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_usuario, get_db
from app.models.avaliacao import Avaliacao
from app.models.campo_avaliacao import CampoAvaliacao
from app.models.enums import AceitaFgts, Etapa, TipoImovel
from app.models.evento_lote import EventoLote
from app.models.imovel import Imovel
from app.models.lote_leilao import LoteLeilao
from app.models.usuario import Usuario
from app.schemas.api import (
    CampoDTO,
    EventoDTO,
    FacetasResponse,
    FichaResponse,
    ImovelListItem,
    ImovelReadOnly,
    ImoveisListResponse,
    LoteReadOnly,
)
from app.schemas.api import AvaliacaoDTO
from app.services.avaliacoes import obter_ou_criar_avaliacao, obter_ou_criar_avaliacoes
from app.services.calculo import calcular
from app.services.resumo_campos import CHAVES_RESUMO, resumo_de_varias_avaliacoes
from app.services.snapshot import montar_snapshot

router = APIRouter(tags=["imoveis"])


@router.get("/imoveis", response_model=ImoveisListResponse)
def listar_imoveis(
    uf: str | None = None,
    cidade: str | None = None,
    bairro: str | None = None,
    preco_min: Decimal | None = None,
    preco_max: Decimal | None = None,
    tipo: list[TipoImovel] | None = Query(None),
    financiamento: str = "indiferente",
    fgts: str = "indiferente",
    desconto_min: Decimal | None = None,
    sem_dados_campo: bool = False,
    etapa: list[Etapa] | None = Query(None),
    incluir_inativos: bool = False,
    cursor: str | None = None,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> ImoveisListResponse:
    query = (
        db.query(LoteLeilao, Imovel, Avaliacao)
        .join(Imovel, LoteLeilao.imovel_id == Imovel.id)
        .outerjoin(
            Avaliacao,
            (Avaliacao.lote_id == LoteLeilao.id) & (Avaliacao.usuario_id == usuario.id),
        )
    )
    if not incluir_inativos:
        # lote inativo = saiu da planilha de origem (leilão finalizado/descontinuado) — some
        # da Triagem por padrão, mas continua acessível com `incluir_inativos=true`
        # (ver docs/requisitos/mvp1-ajustes/04-importacao-caixa-e-historico.md).
        query = query.filter(LoteLeilao.ativo.is_(True))
    if uf:
        query = query.filter(Imovel.uf == uf)
    if cidade:
        query = query.filter(Imovel.cidade == cidade)
    if bairro:
        query = query.filter(Imovel.bairro.ilike(f"%{bairro}%"))
    if preco_min is not None:
        query = query.filter(LoteLeilao.preco_venda >= preco_min)
    if preco_max is not None:
        query = query.filter(LoteLeilao.preco_venda <= preco_max)
    if tipo:
        query = query.filter(Imovel.tipo.in_(tipo))
    if financiamento == "aceita":
        query = query.filter(LoteLeilao.aceita_financiamento.is_(True))
    elif financiamento == "nao_aceita":
        query = query.filter(LoteLeilao.aceita_financiamento.is_(False))
    if fgts == "aceita":
        query = query.filter(LoteLeilao.aceita_fgts == AceitaFgts.ACEITA)
    elif fgts == "nao_aceita":
        query = query.filter(LoteLeilao.aceita_fgts == AceitaFgts.NAO_ACEITA)
    if desconto_min is not None:
        query = query.filter(LoteLeilao.desconto_pct >= desconto_min)
    if etapa:
        condicoes = [Avaliacao.etapa.in_(etapa)]
        if Etapa.TRIAGEM in etapa:
            condicoes.append(Avaliacao.id.is_(None))
        query = query.filter(or_(*condicoes))
    if sem_dados_campo:
        tem_campo = exists().where(
            CampoAvaliacao.avaliacao_id == Avaliacao.id,
            CampoAvaliacao.chave.in_(CHAVES_RESUMO),
        )
        query = query.filter(~tem_campo)

    total = query.count()
    offset = int(cursor) if cursor else 0
    query = query.order_by(LoteLeilao.desconto_pct.desc().nullslast())
    linhas = query.offset(offset).limit(limit + 1).all()
    tem_proxima_pagina = len(linhas) > limit
    linhas = linhas[:limit]

    lotes_sem_avaliacao = [lote.id for lote, _, avaliacao in linhas if avaliacao is None]
    if lotes_sem_avaliacao:
        avaliacoes_criadas = obter_ou_criar_avaliacoes(db, lotes_sem_avaliacao, usuario.id)
        db.commit()
        linhas = [
            (lote, imovel, avaliacao if avaliacao is not None else avaliacoes_criadas[lote.id])
            for lote, imovel, avaliacao in linhas
        ]

    resumos = resumo_de_varias_avaliacoes(db, [a.id for _, _, a in linhas])

    items = [
        ImovelListItem(
            lote_id=lote.id,
            imovel_id=imovel.id,
            avaliacao_id=avaliacao.id,
            codigo_externo=lote.codigo_externo,
            fonte=lote.fonte,
            endereco=imovel.endereco,
            cidade=imovel.cidade,
            bairro=imovel.bairro,
            uf=imovel.uf,
            tipo=imovel.tipo,
            area_privativa_m2=imovel.area_privativa_m2,
            quartos=imovel.quartos,
            preco_venda=lote.preco_venda,
            valor_avaliacao=lote.valor_avaliacao,
            desconto_pct=lote.desconto_pct,
            modalidade=lote.modalidade,
            aceita_financiamento=lote.aceita_financiamento,
            aceita_fgts=lote.aceita_fgts,
            etapa=avaliacao.etapa,
            motivo_descarte=avaliacao.motivo_descarte,
            resumo_campos=resumos[avaliacao.id],
            ativo=lote.ativo,
        )
        for lote, imovel, avaliacao in linhas
    ]

    return ImoveisListResponse(
        items=items,
        next_cursor=str(offset + limit) if tem_proxima_pagina else None,
        total=total,
    )


@router.get("/imoveis/facetas", response_model=FacetasResponse)
def facetas(
    db: Session = Depends(get_db), _usuario: Usuario = Depends(get_current_usuario)
) -> FacetasResponse:
    cidades = [
        row[0]
        for row in db.query(Imovel.cidade).distinct().order_by(Imovel.cidade).all()
    ]
    tipos = [row[0] for row in db.query(Imovel.tipo).distinct().all()]
    return FacetasResponse(cidades=cidades, tipos=tipos)


@router.get("/imoveis/{lote_id}/eventos", response_model=list[EventoDTO])
def eventos_do_lote(
    lote_id: UUID,
    db: Session = Depends(get_db),
    _usuario: Usuario = Depends(get_current_usuario),
) -> list[EventoDTO]:
    # dado global (criado/atualizado/inativado/reativado pela importação) — qualquer
    # usuário autenticado pode ver, sem checagem de posse (ver item 04 dos ajustes de MVP1).
    linhas = db.query(EventoLote).filter_by(lote_id=lote_id).order_by(EventoLote.criado_em.desc()).all()
    return [
        EventoDTO(id=e.id, tipo=e.tipo, ator_id=e.ator_id, payload=e.payload, criado_em=e.criado_em)
        for e in linhas
    ]


@router.get("/imoveis/{lote_id}", response_model=FichaResponse)
def ficha(
    lote_id: UUID,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_usuario),
) -> FichaResponse:
    lote = db.get(LoteLeilao, lote_id)
    if lote is None:
        raise HTTPException(status_code=404, detail="Lote não encontrado")
    imovel = db.get(Imovel, lote.imovel_id)
    avaliacao = obter_ou_criar_avaliacao(db, lote.id, usuario.id)
    db.commit()

    campos_db = db.query(CampoAvaliacao).filter_by(avaliacao_id=avaliacao.id).all()
    campos = {
        c.chave: CampoDTO(
            chave=c.chave,
            valor=c.valor_numerico if c.valor_numerico is not None else c.valor_texto,
            origem=c.origem,
            fonte_declarada=c.fonte_declarada,
            preenchido_por=c.preenchido_por,
            preenchido_em=c.preenchido_em,
            sugestao_valor=c.sugestao_valor,
            sugestao_origem=c.sugestao_origem,
        )
        for c in campos_db
    }

    resultado = calcular(montar_snapshot(db, avaliacao))

    return FichaResponse(
        imovel=ImovelReadOnly(
            imovel_id=imovel.id,
            uf=imovel.uf,
            cidade=imovel.cidade,
            bairro=imovel.bairro,
            endereco=imovel.endereco,
            tipo=imovel.tipo,
            area_total_m2=imovel.area_total_m2,
            area_privativa_m2=imovel.area_privativa_m2,
            area_terreno_m2=imovel.area_terreno_m2,
            quartos=imovel.quartos,
            descricao_oficial=imovel.descricao_oficial,
        ),
        lote=LoteReadOnly(
            lote_id=lote.id,
            fonte=lote.fonte,
            codigo_externo=lote.codigo_externo,
            modalidade=lote.modalidade,
            preco_venda=lote.preco_venda,
            valor_avaliacao=lote.valor_avaliacao,
            desconto_pct=lote.desconto_pct,
            aceita_financiamento=lote.aceita_financiamento,
            aceita_fgts=lote.aceita_fgts,
            praca_1_valor=lote.praca_1_valor,
            praca_1_data=lote.praca_1_data,
            praca_2_valor=lote.praca_2_valor,
            praca_2_data=lote.praca_2_data,
            url_fonte=lote.url_fonte,
            ativo=lote.ativo,
        ),
        avaliacao=AvaliacaoDTO(
            id=avaliacao.id,
            etapa=avaliacao.etapa,
            etapa_desde=avaliacao.etapa_desde,
            motivo_descarte=avaliacao.motivo_descarte,
            teto_lance=avaliacao.teto_lance,
            anotacoes=avaliacao.anotacoes,
            checklist=avaliacao.checklist,
        ),
        campos=campos,
        resultado_calculo=resultado,
    )
