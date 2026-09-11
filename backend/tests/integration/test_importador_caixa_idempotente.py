from pathlib import Path

import openpyxl

from app.importers.caixa import importar_caixa
from app.models.campo_avaliacao import CampoAvaliacao
from app.models.enums import OrigemCampo
from app.models.lote_leilao import LoteLeilao

FIXTURE = Path(__file__).parent.parent.parent / "app" / "seeds" / "fixtures" / "sample_caixa.xlsx"

CABECALHO_MINIMO = [
    "Nº do imóvel", "UF", "Cidade", "Bairro", "Endereço", "Descrição",
    "Preço", "Avaliação", "Desconto", "Modalidade de Venda", "Aceita Financiamento", "Link de acesso",
]


def _escrever_planilha(caminho: Path, codigos_externos: list[str]) -> None:
    livro = openpyxl.Workbook()
    aba = livro.active
    aba.append(CABECALHO_MINIMO)
    for codigo in codigos_externos:
        aba.append([codigo, "MG", "Belo Horizonte", "Centro", "Rua Central, 1", "Apartamento com área privativa de 50,00 m², 2 quartos", 90000.00, 150000.00, 40.0, "Venda Direta Online", 0, "https://exemplo/" + codigo])
    livro.save(caminho)


def test_importacao_cria_15_lotes_sem_avaliacao(db_session, tmp_path):
    from app.models.avaliacao import Avaliacao

    arquivo = tmp_path / "carga_15_lotes.xlsx"
    _escrever_planilha(arquivo, [f"NOVO-{i}" for i in range(15)])

    importacao = importar_caixa(db_session, arquivo)

    assert importacao.criados == 15
    assert importacao.atualizados == 0
    assert importacao.erros == []
    lotes = db_session.query(LoteLeilao).filter(LoteLeilao.codigo_externo.like("NOVO-%")).all()
    assert len(lotes) == 15
    assert all(lote.ativo for lote in lotes)
    # Avaliacao é dado por usuário, nasce sob demanda no primeiro acesso — não na importação.
    lote_ids = [lote.id for lote in lotes]
    assert db_session.query(Avaliacao).filter(Avaliacao.lote_id.in_(lote_ids)).count() == 0


def test_reimportar_o_mesmo_arquivo_nao_duplica_nem_reprocessa(db_session):
    primeira = importar_caixa(db_session, FIXTURE)
    total_lotes_apos_primeira = db_session.query(LoteLeilao).count()

    segunda = importar_caixa(db_session, FIXTURE)

    assert db_session.query(LoteLeilao).count() == total_lotes_apos_primeira
    # hash idêntico -> dedup: devolve o mesmo registro de importação, sem reprocessar
    assert segunda.id == primeira.id
    from app.models.importacao import Importacao

    assert db_session.query(Importacao).count() == 1


def test_reimportacao_nunca_sobrescreve_campo_avaliacao_do_usuario(db_session, tmp_path):
    from app.models.usuario import Usuario
    from app.services.avaliacoes import obter_ou_criar_avaliacao

    arquivo = tmp_path / "carga_reimportacao.xlsx"
    _escrever_planilha(arquivo, ["REIMPORT-1"])

    importacao = importar_caixa(db_session, arquivo)
    lote = db_session.query(LoteLeilao).filter_by(codigo_externo="REIMPORT-1").one()
    usuario = Usuario(nome="Teste", email="teste@exemplo.com")
    db_session.add(usuario)
    db_session.flush()
    avaliacao = obter_ou_criar_avaliacao(db_session, lote.id, usuario.id)
    db_session.add(
        CampoAvaliacao(
            avaliacao_id=avaliacao.id,
            chave="valor_mercado",
            valor_numerico=999999,
            origem=OrigemCampo.MANUAL,
            fonte_declarada="3 anúncios da região",
        )
    )
    db_session.commit()

    # reimporta o mesmo arquivo (idempotente) — upsert não deve tocar em campo_avaliacao
    importar_caixa(db_session, arquivo)

    campo = (
        db_session.query(CampoAvaliacao)
        .filter_by(avaliacao_id=avaliacao.id, chave="valor_mercado")
        .one()
    )
    assert campo.valor_numerico == 999999
    assert campo.origem == OrigemCampo.MANUAL
    assert importacao.criados == 1


def test_lote_ausente_na_nova_carga_fica_inativo(db_session, tmp_path):
    arquivo_v1 = tmp_path / "carga_v1.xlsx"
    arquivo_v2 = tmp_path / "carga_v2.xlsx"
    _escrever_planilha(arquivo_v1, ["COD-1", "COD-2"])
    _escrever_planilha(arquivo_v2, ["COD-1"])  # COD-2 some da carga nova

    importar_caixa(db_session, arquivo_v1)
    importar_caixa(db_session, arquivo_v2)

    lote_1 = db_session.query(LoteLeilao).filter_by(codigo_externo="COD-1").one()
    lote_2 = db_session.query(LoteLeilao).filter_by(codigo_externo="COD-2").one()
    assert lote_1.ativo is True
    assert lote_2.ativo is False
