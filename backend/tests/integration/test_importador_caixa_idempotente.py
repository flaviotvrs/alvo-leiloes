from pathlib import Path

from app.importers.caixa import importar_caixa
from app.models.campo_avaliacao import CampoAvaliacao
from app.models.enums import OrigemCampo
from app.models.evento_lote import EventoLote
from app.models.lote_leilao import LoteLeilao

FIXTURE = Path(__file__).parent.parent.parent / "app" / "seeds" / "fixtures" / "sample_caixa.csv"

CABECALHO = (
    "N° do imóvel;UF;Cidade;Bairro;Endereço;Preço;Valor de avaliação;Desconto;Financiamento;"
    "Descrição;Modalidade de venda;Link de acesso"
)


def _escrever_planilha(caminho: Path, codigos_externos: list[str], gerado_em: str = "14/08/2026") -> None:
    linhas = [
        "",
        f" Lista de Imóveis da Caixa;;Data de geração:;{gerado_em};;;;;;;",
        f" {CABECALHO}",
        "",
    ]
    for codigo in codigos_externos:
        linhas.append(
            f" {codigo};MG;Belo Horizonte;Centro;Rua Central, 1;90.000,00;150.000,00;40.0;Não;"
            "Apartamento, 50.00 de área privativa, 2 qto(s).;Venda Direta Online;https://exemplo/" + codigo
        )
    caminho.write_bytes(("\n".join(linhas) + "\n").encode("ISO-8859-1"))


def test_importacao_cria_15_lotes_sem_avaliacao(db_session, tmp_path):
    from app.models.avaliacao import Avaliacao

    arquivo = tmp_path / "carga_15_lotes.csv"
    _escrever_planilha(arquivo, [f"NOVO-{i}" for i in range(15)])

    importacao = importar_caixa(db_session, arquivo)

    assert importacao.criados == 15
    assert importacao.atualizados == 0
    assert importacao.erros == []
    assert importacao.arquivo_gerado_em is not None
    lotes = db_session.query(LoteLeilao).filter(LoteLeilao.codigo_externo.like("NOVO-%")).all()
    assert len(lotes) == 15
    assert all(lote.ativo for lote in lotes)
    # Avaliacao é dado por usuário, nasce sob demanda no primeiro acesso — não na importação.
    lote_ids = [lote.id for lote in lotes]
    assert db_session.query(Avaliacao).filter(Avaliacao.lote_id.in_(lote_ids)).count() == 0
    eventos = db_session.query(EventoLote).filter(EventoLote.lote_id.in_(lote_ids)).all()
    assert len(eventos) == 15
    assert all(e.payload["acao"] == "criado" for e in eventos)


def test_fixture_de_seed_importa_sem_erros(db_session):
    importacao = importar_caixa(db_session, FIXTURE)
    assert importacao.status.value == "concluida"
    assert importacao.criados == 15
    assert importacao.erros == []


def test_reimportar_o_mesmo_arquivo_nao_duplica_nem_reprocessa(db_session, tmp_path):
    from app.models.importacao import Importacao

    # arquivo com conteúdo próprio deste teste (não o FIXTURE compartilhado) — evita
    # colidir por hash com dado já seedado no banco de dev usado pelos testes.
    arquivo = tmp_path / "carga_dedup.csv"
    _escrever_planilha(arquivo, ["DEDUP-1", "DEDUP-2"])

    total_importacoes_antes = db_session.query(Importacao).count()

    primeira = importar_caixa(db_session, arquivo)
    total_lotes_apos_primeira = db_session.query(LoteLeilao).count()

    segunda = importar_caixa(db_session, arquivo)

    assert db_session.query(LoteLeilao).count() == total_lotes_apos_primeira
    # hash idêntico -> dedup: devolve o mesmo registro de importação, sem reprocessar
    assert segunda.id == primeira.id
    assert db_session.query(Importacao).count() == total_importacoes_antes + 1


def test_reimportacao_nunca_sobrescreve_campo_avaliacao_do_usuario(db_session, tmp_path):
    from app.models.usuario import Usuario
    from app.services.avaliacoes import obter_ou_criar_avaliacao

    arquivo = tmp_path / "carga_reimportacao.csv"
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
    arquivo_v1 = tmp_path / "carga_v1.csv"
    arquivo_v2 = tmp_path / "carga_v2.csv"
    _escrever_planilha(arquivo_v1, ["COD-1", "COD-2"])
    _escrever_planilha(arquivo_v2, ["COD-1"])  # COD-2 some da carga nova

    importar_caixa(db_session, arquivo_v1)
    importacao_v2 = importar_caixa(db_session, arquivo_v2)

    lote_1 = db_session.query(LoteLeilao).filter_by(codigo_externo="COD-1").one()
    lote_2 = db_session.query(LoteLeilao).filter_by(codigo_externo="COD-2").one()
    assert lote_1.ativo is True
    assert lote_2.ativo is False
    assert importacao_v2.inativados == 1

    evento = db_session.query(EventoLote).filter_by(lote_id=lote_2.id, importacao_id=importacao_v2.id).one()
    assert evento.payload["acao"] == "inativado"


def test_lote_reativado_ao_voltar_na_carga(db_session, tmp_path):
    arquivo_v1 = tmp_path / "carga_v1.csv"
    arquivo_v2 = tmp_path / "carga_v2.csv"
    arquivo_v3 = tmp_path / "carga_v3.csv"
    _escrever_planilha(arquivo_v1, ["COD-1", "COD-2"], gerado_em="14/08/2026")
    _escrever_planilha(arquivo_v2, ["COD-1"], gerado_em="15/08/2026")  # COD-2 some
    _escrever_planilha(arquivo_v3, ["COD-1", "COD-2"], gerado_em="16/08/2026")  # COD-2 volta, conteúdo diferente de v1

    importar_caixa(db_session, arquivo_v1)
    importar_caixa(db_session, arquivo_v2)
    importacao_v3 = importar_caixa(db_session, arquivo_v3)

    lote_2 = db_session.query(LoteLeilao).filter_by(codigo_externo="COD-2").one()
    assert lote_2.ativo is True
    assert importacao_v3.reativados == 1

    evento = (
        db_session.query(EventoLote)
        .filter_by(lote_id=lote_2.id, importacao_id=importacao_v3.id)
        .filter(EventoLote.payload["acao"].astext == "reativado")
        .one()
    )
    assert evento.payload["acao"] == "reativado"


def test_atualizacao_de_campo_registra_evento_com_mudancas(db_session, tmp_path):
    arquivo_v1 = tmp_path / "carga_v1.csv"
    arquivo_v2 = tmp_path / "carga_v2.csv"
    _escrever_planilha(arquivo_v1, ["COD-PRECO"])
    caminho_v2 = arquivo_v2
    linhas = [
        "",
        " Lista de Imóveis da Caixa;;Data de geração:;15/08/2026;;;;;;;",
        f" {CABECALHO}",
        "",
        " COD-PRECO;MG;Belo Horizonte;Centro;Rua Central, 1;80.000,00;150.000,00;46.7;Não;"
        "Apartamento, 50.00 de área privativa, 2 qto(s).;Venda Direta Online;https://exemplo/COD-PRECO",
    ]
    caminho_v2.write_bytes(("\n".join(linhas) + "\n").encode("ISO-8859-1"))

    importar_caixa(db_session, arquivo_v1)
    importacao_v2 = importar_caixa(db_session, arquivo_v2)

    assert importacao_v2.atualizados == 1
    lote = db_session.query(LoteLeilao).filter_by(codigo_externo="COD-PRECO").one()
    assert float(lote.preco_venda) == 80000.00

    evento = (
        db_session.query(EventoLote)
        .filter_by(lote_id=lote.id, importacao_id=importacao_v2.id)
        .filter(EventoLote.payload["acao"].astext == "atualizado")
        .one()
    )
    assert "preco_venda" in evento.payload["mudancas"]


def test_linha_malformada_nao_derruba_a_carga_inteira(db_session, tmp_path):
    arquivo = tmp_path / "carga_com_erro.csv"
    linhas = [
        "",
        " Lista de Imóveis da Caixa;;Data de geração:;14/08/2026;;;;;;;",
        f" {CABECALHO}",
        "",
        " BOM-1;MG;Belo Horizonte;Centro;Rua 1;90.000,00;150.000,00;40.0;Não;"
        "Apartamento, 50.00 de área privativa, 2 qto(s).;Venda Direta Online;https://exemplo/BOM-1",
        " MAL-1;MG;Belo Horizonte;Centro;Rua 2;NAO-E-UM-PRECO;150.000,00;40.0;Não;"
        "Apartamento;Venda Direta Online;https://exemplo/MAL-1",
        " BOM-2;MG;Belo Horizonte;Centro;Rua 3;95.000,00;150.000,00;40.0;Não;"
        "Apartamento, 50.00 de área privativa, 2 qto(s).;Venda Direta Online;https://exemplo/BOM-2",
    ]
    arquivo.write_bytes(("\n".join(linhas) + "\n").encode("ISO-8859-1"))

    importacao = importar_caixa(db_session, arquivo)

    assert importacao.status.value == "concluida"
    assert importacao.criados == 2
    assert len(importacao.erros) == 1
    assert importacao.erros[0]["codigo_externo"] == "MAL-1"
    assert db_session.query(LoteLeilao).filter_by(codigo_externo="BOM-1").one()
    assert db_session.query(LoteLeilao).filter_by(codigo_externo="BOM-2").one()
    assert db_session.query(LoteLeilao).filter_by(codigo_externo="MAL-1").one_or_none() is None
