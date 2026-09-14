from datetime import UTC, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_usuario, get_db
from app.models.avaliacao import Avaliacao
from app.models.enums import Etapa
from app.models.imovel import Imovel
from app.models.lote_leilao import LoteLeilao
from app.models.usuario import Usuario
from app.schemas.api import FunilCard, FunilColuna, FunilResponse
from app.services.calculo import calcular
from app.services.resumo_campos import resumo_de_uma_avaliacao
from app.services.snapshot import montar_snapshot

router = APIRouter(tags=["funil"])

# Coluna do quadro (README "Tela 3 — Funil de aprovação"). Descartado não é uma coluna do
# quadro — fica de fora do funil visual, mas continua contando para base_para_aprovados_pct.
COLUNAS_FUNIL: tuple[tuple[Etapa, str], ...] = (
    (Etapa.NAO_AVALIADO, "Avaliação ainda não iniciada"),
    (Etapa.PESQUISA_CAMPO, "Alguém está preenchendo à mão"),
    (Etapa.ANALISE_FINANCEIRA, "Conta fechada com os dados manuais"),
    (Etapa.DECISAO, "Aguardando aval de investimento"),
    (Etapa.APROVADO_LANCE, "Teto de lance definido"),
)


def _pilula(db: Session, avaliacao: Avaliacao, resumo) -> str:
    if avaliacao.etapa == Etapa.NAO_AVALIADO:
        return "Sem pesquisa"
    if avaliacao.etapa == Etapa.PESQUISA_CAMPO:
        return f"{resumo.preenchidos}/{resumo.total} campos" if resumo.preenchidos else "Sem pesquisa"
    if avaliacao.etapa == Etapa.APROVADO_LANCE:
        return f"Teto R$ {avaliacao.teto_lance:,.0f}".replace(",", ".") if avaliacao.teto_lance else "Aprovado"
    resultado = calcular(montar_snapshot(db, avaliacao))
    if resultado.margem_investimento_pct is None:
        return "Falta valor de mercado"
    return f"Margem {resultado.margem_investimento_pct}%".replace(".", ",")


@router.get("/funil", response_model=FunilResponse)
def funil(
    db: Session = Depends(get_db), usuario: Usuario = Depends(get_current_usuario)
) -> FunilResponse:
    avaliacoes_ativas = (
        db.query(Avaliacao, LoteLeilao, Imovel)
        .join(LoteLeilao, Avaliacao.lote_id == LoteLeilao.id)
        .join(Imovel, LoteLeilao.imovel_id == Imovel.id)
        .filter(LoteLeilao.ativo.is_(True))
        .filter(Avaliacao.usuario_id == usuario.id)
        .filter(Avaliacao.etapa != Etapa.TRIAGEM)
        .all()
    )

    por_etapa: dict[Etapa, list[tuple[Avaliacao, LoteLeilao, Imovel]]] = {etapa: [] for etapa, _ in COLUNAS_FUNIL}
    for avaliacao, lote, imovel in avaliacoes_ativas:
        if avaliacao.etapa in por_etapa:
            por_etapa[avaliacao.etapa].append((avaliacao, lote, imovel))

    total_primeira_coluna = len(por_etapa[COLUNAS_FUNIL[0][0]]) or 1

    colunas = []
    for etapa, nota in COLUNAS_FUNIL:
        grupo = por_etapa[etapa]
        cards = []
        for avaliacao, lote, imovel in grupo:
            resumo = resumo_de_uma_avaliacao(db, avaliacao.id)
            cards.append(
                FunilCard(
                    lote_id=lote.id,
                    endereco=imovel.endereco,
                    cidade=imovel.cidade,
                    preco_venda=lote.preco_venda,
                    desconto_pct=lote.desconto_pct,
                    resumo_campos=resumo,
                    pilula_estado=_pilula(db, avaliacao, resumo),
                )
            )
        colunas.append(
            FunilColuna(
                etapa=etapa,
                contagem=len(grupo),
                nota=nota,
                barra_pct=round(len(grupo) / total_primeira_coluna * 100),
                cards=cards,
            )
        )

    total_avaliacoes = len(avaliacoes_ativas) or 1
    aprovados = len(por_etapa[Etapa.APROVADO_LANCE])
    base_para_aprovados_pct = Decimal(aprovados) / Decimal(total_avaliacoes) * 100

    em_pesquisa = [
        a for a, _, _ in avaliacoes_ativas if a.etapa in (Etapa.PESQUISA_CAMPO, Etapa.ANALISE_FINANCEIRA)
    ]
    if em_pesquisa:
        agora = datetime.now(UTC)
        media_dias = sum((agora - a.etapa_desde).days for a in em_pesquisa) / len(em_pesquisa)
        tempo_medio_pesquisa_dias = Decimal(str(round(media_dias, 1)))
    else:
        tempo_medio_pesquisa_dias = None

    return FunilResponse(
        colunas=colunas,
        base_para_aprovados_pct=Decimal(str(round(base_para_aprovados_pct, 1))),
        tempo_medio_pesquisa_dias=tempo_medio_pesquisa_dias,
    )
