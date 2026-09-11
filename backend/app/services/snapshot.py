from datetime import date

from sqlalchemy.orm import Session

from app.models.avaliacao import Avaliacao
from app.models.campo_avaliacao import CampoAvaliacao
from app.models.imovel import Imovel
from app.models.lote_leilao import LoteLeilao
from app.models.parametro import ParametroUsuario
from app.models.referencia import EmolumentoFaixa, ItbiMunicipio
from app.schemas.calculo import (
    CampoSnapshot,
    EmolumentoFaixaReferencia,
    ItbiReferencia,
    ParametrosSnapshot,
    Snapshot,
    TabelasSnapshot,
)


def montar_snapshot(db: Session, avaliacao: Avaliacao) -> Snapshot:
    """Monta o Snapshot de entrada do motor de cálculo a partir do estado atual em banco.
    O motor em si continua puro (calculo.py não conhece o banco) — a ponte fica aqui."""
    lote = db.get(LoteLeilao, avaliacao.lote_id)
    imovel = db.get(Imovel, lote.imovel_id)

    campos_db = db.query(CampoAvaliacao).filter_by(avaliacao_id=avaliacao.id).all()
    campos = {
        c.chave: CampoSnapshot(valor=c.valor_numerico, origem=c.origem)
        for c in campos_db
        if c.valor_numerico is not None
    }

    parametros_db = db.query(ParametroUsuario).filter_by(usuario_id=avaliacao.responsavel_id).one_or_none()
    if parametros_db is None:
        parametros_db = db.query(ParametroUsuario).first()
    parametros = ParametrosSnapshot(
        prazo_carregamento_meses=parametros_db.prazo_carregamento_meses,
        comissao_corretor_pct=parametros_db.comissao_corretor_pct,
        piso_margem_pct=parametros_db.piso_margem_pct,
        ir_aliquota_pct=parametros_db.ir_aliquota_pct,
        itbi_aliquota_padrao_pct=parametros_db.itbi_aliquota_padrao_pct,
        comissao_leiloeiro_padrao_pct=parametros_db.comissao_leiloeiro_padrao_pct,
    )

    itbi_refs = [
        ItbiReferencia(uf=r.uf, cidade=r.cidade, aliquota_pct=r.aliquota_pct)
        for r in db.query(ItbiMunicipio).all()
    ]

    hoje = date.today()
    faixas_db = (
        db.query(EmolumentoFaixa)
        .filter(EmolumentoFaixa.vigencia_inicio <= hoje)
        .filter((EmolumentoFaixa.vigencia_fim.is_(None)) | (EmolumentoFaixa.vigencia_fim >= hoje))
        .all()
    )
    versao = f"{faixas_db[0].tabela}_{faixas_db[0].item}" if faixas_db else "sem_tabela_vigente"
    faixas = [
        EmolumentoFaixaReferencia(limite_superior=f.limite_superior, valor=f.valor) for f in faixas_db
    ]

    return Snapshot(
        arremate=lote.preco_venda,
        cidade=imovel.cidade,
        uf=imovel.uf,
        campos=campos,
        parametros=parametros,
        tabelas=TabelasSnapshot(itbi=itbi_refs, emolumentos=faixas, versao_emolumentos=versao),
        dividas_sao_do_arrematante=True,
    )
