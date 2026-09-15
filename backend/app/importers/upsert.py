import uuid
from datetime import UTC, date, datetime

from sqlalchemy.orm import Session

from app.importers.base import LoteNormalizado
from app.models.enums import FonteLeilao, StatusImportacao, TipoEvento
from app.models.evento_lote import EventoLote
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
    arquivo_gerado_em: date | None = None,
    erros_iniciais: list[dict] | None = None,
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
        arquivo_gerado_em=arquivo_gerado_em,
        executada_por=executada_por,
        status=StatusImportacao.PROCESSANDO,
    )
    db.add(importacao)
    db.flush()

    codigos_na_carga: set[str] = set()
    criados = atualizados = inalterados = reativados = 0
    erros: list[dict] = list(erros_iniciais or [])

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
                _criar_lote(db, fonte=fonte, lote=lote, importacao_id=importacao.id)
            else:
                estava_inativo = not lote_existente.ativo
                mudancas = _atualizar_lote(lote_existente, lote)
                lote_existente.ativo = True
                if mudancas:
                    atualizados += 1
                    db.add(
                        EventoLote(
                            lote_id=lote_existente.id,
                            tipo=TipoEvento.IMPORTACAO,
                            importacao_id=importacao.id,
                            payload={"acao": "atualizado", "mudancas": mudancas},
                        )
                    )
                else:
                    inalterados += 1
                if estava_inativo:
                    reativados += 1
                    db.add(
                        EventoLote(
                            lote_id=lote_existente.id,
                            tipo=TipoEvento.IMPORTACAO,
                            importacao_id=importacao.id,
                            payload={"acao": "reativado", "importacao_id": str(importacao.id)},
                        )
                    )
        except Exception as exc:  # noqa: BLE001 -- erro por linha não deve abortar a carga
            erros.append({"codigo_externo": lote.codigo_externo, "erro": str(exc)})

    inativados = 0
    lotes_ativos_da_fonte = db.query(LoteLeilao).filter_by(fonte=fonte, ativo=True).all()
    for lote_db in lotes_ativos_da_fonte:
        if lote_db.codigo_externo not in codigos_na_carga:
            lote_db.ativo = False
            inativados += 1
            db.add(
                EventoLote(
                    lote_id=lote_db.id,
                    tipo=TipoEvento.IMPORTACAO,
                    importacao_id=importacao.id,
                    payload={"acao": "inativado", "importacao_id": str(importacao.id)},
                )
            )

    importacao.linhas_lidas = len(lotes) + len(erros_iniciais or [])
    importacao.criados = criados
    importacao.atualizados = atualizados
    importacao.inalterados = inalterados
    importacao.inativados = inativados
    importacao.reativados = reativados
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

    db.add(
        EventoLote(
            lote_id=lote_db.id,
            tipo=TipoEvento.IMPORTACAO,
            importacao_id=importacao_id,
            payload={"acao": "criado", "fonte": fonte.value, "codigo_externo": lote.codigo_externo},
        )
    )


def _atualizar_lote(lote_existente: LoteLeilao, novo: LoteNormalizado) -> dict[str, dict[str, str | None]]:
    mudancas: dict[str, dict[str, str | None]] = {}
    for campo in _CAMPOS_ATUALIZAVEIS:
        valor_anterior = getattr(lote_existente, campo)
        valor_novo = getattr(novo, campo)
        if valor_anterior != valor_novo:
            setattr(lote_existente, campo, valor_novo)
            mudancas[campo] = {
                "de": str(valor_anterior) if valor_anterior is not None else None,
                "para": str(valor_novo) if valor_novo is not None else None,
            }
    return mudancas
