import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.importers.base import LoteNormalizado
from app.models.avaliacao import Avaliacao
from app.models.enums import Etapa, FonteLeilao, StatusImportacao, TipoEvento
from app.models.evento_avaliacao import EventoAvaliacao
from app.models.imovel import Imovel
from app.models.importacao import Importacao
from app.models.lote_leilao import LoteLeilao

_CAMPOS_ATUALIZAVEIS = (
    "modalidade",
    "preco_venda",
    "valor_avaliacao",
    "desconto_pct",
    "aceita_financiamento",
    "praca_1_valor",
    "praca_1_data",
    "praca_2_valor",
    "praca_2_data",
    "url_fonte",
)


def aplicar_importacao(
    db: Session,
    *,
    fonte: FonteLeilao,
    lotes: list[LoteNormalizado],
    arquivo_nome: str | None,
    arquivo_hash: str | None,
    executada_por: uuid.UUID | None,
) -> Importacao:
    """Upsert por (fonte, codigo_externo). Nunca escreve em `campo_avaliacao` — dado do
    usuário sempre vence dado importado (BACKEND.md "Regras de negócio"). Dedup de carga
    idêntica pelo hash do arquivo: reimportar o mesmo arquivo é uma operação barata e não
    reprocessa nada."""
    if arquivo_hash:
        existente = (
            db.query(Importacao)
            .filter_by(fonte=fonte, arquivo_hash=arquivo_hash, status=StatusImportacao.CONCLUIDA)
            .first()
        )
        if existente:
            return existente

    importacao = Importacao(
        fonte=fonte,
        arquivo_nome=arquivo_nome,
        arquivo_hash=arquivo_hash,
        executada_por=executada_por,
        status=StatusImportacao.PROCESSANDO,
    )
    db.add(importacao)
    db.flush()

    codigos_na_carga: set[str] = set()
    criados = atualizados = inalterados = 0
    erros: list[dict] = []

    for lote in lotes:
        try:
            codigos_na_carga.add(lote.codigo_externo)
            lote_existente = (
                db.query(LoteLeilao)
                .filter_by(fonte=fonte, codigo_externo=lote.codigo_externo)
                .one_or_none()
            )
            if lote_existente is None:
                criados += 1
                _criar_lote(db, fonte=fonte, lote=lote, importacao_id=importacao.id, executada_por=executada_por)
            else:
                mudou = _atualizar_lote(lote_existente, lote)
                lote_existente.ativo = True
                if mudou:
                    atualizados += 1
                else:
                    inalterados += 1
        except Exception as exc:  # noqa: BLE001 -- erro por linha não deve abortar a carga
            erros.append({"codigo_externo": lote.codigo_externo, "erro": str(exc)})

    lotes_ativos_da_fonte = db.query(LoteLeilao).filter_by(fonte=fonte, ativo=True).all()
    for lote_db in lotes_ativos_da_fonte:
        if lote_db.codigo_externo not in codigos_na_carga:
            lote_db.ativo = False

    importacao.linhas_lidas = len(lotes)
    importacao.criados = criados
    importacao.atualizados = atualizados
    importacao.inalterados = inalterados
    importacao.erros = erros
    importacao.status = StatusImportacao.CONCLUIDA
    importacao.concluida_em = datetime.now(UTC)

    db.commit()
    db.refresh(importacao)
    return importacao


def _criar_lote(
    db: Session,
    *,
    fonte: FonteLeilao,
    lote: LoteNormalizado,
    importacao_id: uuid.UUID,
    executada_por: uuid.UUID | None,
) -> None:
    imovel = Imovel(
        uf=lote.uf,
        cidade=lote.cidade,
        bairro=lote.bairro,
        endereco=lote.endereco,
        tipo=lote.tipo,
        area_total_m2=lote.area_total_m2,
        area_privativa_m2=lote.area_privativa_m2,
        area_terreno_m2=lote.area_terreno_m2,
        quartos=lote.quartos,
        descricao_oficial=lote.descricao_oficial,
    )
    db.add(imovel)
    db.flush()

    lote_db = LoteLeilao(
        imovel_id=imovel.id,
        fonte=fonte,
        codigo_externo=lote.codigo_externo,
        modalidade=lote.modalidade,
        preco_venda=lote.preco_venda,
        valor_avaliacao=lote.valor_avaliacao,
        desconto_pct=lote.desconto_pct,
        aceita_financiamento=lote.aceita_financiamento,
        aceita_fgts=None,  # planilha da Caixa não traz este campo — nasce nulo, é dado manual
        praca_1_valor=lote.praca_1_valor,
        praca_1_data=lote.praca_1_data,
        praca_2_valor=lote.praca_2_valor,
        praca_2_data=lote.praca_2_data,
        url_fonte=lote.url_fonte,
        importacao_id=importacao_id,
        ativo=True,
    )
    db.add(lote_db)
    db.flush()

    avaliacao = Avaliacao(lote_id=lote_db.id, etapa=Etapa.NAO_AVALIADO)
    db.add(avaliacao)
    db.flush()

    db.add(
        EventoAvaliacao(
            avaliacao_id=avaliacao.id,
            tipo=TipoEvento.IMPORTACAO,
            ator_id=executada_por,
            payload={"fonte": fonte.value, "codigo_externo": lote.codigo_externo},
        )
    )


def _atualizar_lote(lote_existente: LoteLeilao, novo: LoteNormalizado) -> bool:
    mudou = False
    for campo in _CAMPOS_ATUALIZAVEIS:
        valor_novo = getattr(novo, campo)
        if getattr(lote_existente, campo) != valor_novo:
            setattr(lote_existente, campo, valor_novo)
            mudou = True
    return mudou
