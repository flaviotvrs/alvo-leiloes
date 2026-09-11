"""Seed de desenvolvimento: referências (ITBI, emolumentos), parâmetros padrão, usuário de
dev, e uma importação real da planilha fictícia da Caixa — para navegar as 3 telas com dado
plausível sem a planilha real. Rode com `uv run python -m app.seeds.seed`."""

from decimal import Decimal
from pathlib import Path

from app.db import SessionLocal
from app.importers.caixa import importar_caixa
from app.models.avaliacao import Avaliacao
from app.models.campo_avaliacao import CampoAvaliacao
from app.models.enums import Etapa, OrigemCampo
from app.models.lote_leilao import LoteLeilao
from app.models.parametro import ParametroUsuario
from app.models.usuario import Usuario
from app.seeds.referencias import carregar_emolumentos, carregar_itbi

FIXTURE_CAIXA = Path(__file__).parent / "fixtures" / "sample_caixa.xlsx"

USUARIO_DEV_EMAIL = "flaviotvrs@gmail.com"
USUARIO_DEV_NOME = "Flavio"


def _usuario_dev(db):
    usuario = db.query(Usuario).filter_by(email=USUARIO_DEV_EMAIL).one_or_none()
    if usuario is None:
        usuario = Usuario(nome=USUARIO_DEV_NOME, email=USUARIO_DEV_EMAIL)
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    return usuario


def _parametros_padrao(db, usuario: Usuario) -> None:
    if db.query(ParametroUsuario).filter_by(usuario_id=usuario.id).first():
        return
    db.add(ParametroUsuario(usuario_id=usuario.id))
    db.commit()


def _avancar_funil_de_exemplo(db, usuario: Usuario) -> None:
    """Move algumas avaliações seedadas por etapas diferentes do funil e preenche campos
    parciais, para que a Triagem/Ficha/Funil tenham dado plausível em todo estado desde o
    primeiro `npm run dev` — sem isso, tudo ficaria em "não avaliado"."""
    lotes = db.query(LoteLeilao).order_by(LoteLeilao.codigo_externo).all()
    if len(lotes) < 5:
        return

    def avaliacao_de(lote: LoteLeilao) -> Avaliacao:
        return db.query(Avaliacao).filter_by(lote_id=lote.id).one()

    def preencher(avaliacao: Avaliacao, chave: str, valor: Decimal, origem: OrigemCampo = OrigemCampo.MANUAL) -> None:
        ja_existe = db.query(CampoAvaliacao).filter_by(avaliacao_id=avaliacao.id, chave=chave).first()
        if ja_existe:
            return
        db.add(
            CampoAvaliacao(
                avaliacao_id=avaliacao.id,
                chave=chave,
                valor_numerico=valor,
                origem=origem,
                fonte_declarada="seed de desenvolvimento",
                preenchido_por=usuario.id,
            )
        )

    # 1) o imóvel do exemplo do README, com a ficha quase completa, em análise financeira
    a1 = avaliacao_de(lotes[0])
    a1.etapa = Etapa.ANALISE_FINANCEIRA
    a1.responsavel_id = usuario.id
    for chave, valor in (
        ("valor_mercado", "168000"),
        ("iptu_atraso", "3400"),
        ("iptu_mensal", "285"),
        ("reforma", "22000"),
        ("desocupacao", "15000"),
    ):
        preencher(a1, chave, Decimal(valor))

    # 2) pesquisa de campo em andamento, poucos campos preenchidos
    a2 = avaliacao_de(lotes[1])
    a2.etapa = Etapa.PESQUISA_CAMPO
    a2.responsavel_id = usuario.id
    preencher(a2, "iptu_atraso", Decimal("1200"))

    # 3) decisão pendente, ficha completa
    a3 = avaliacao_de(lotes[2])
    a3.etapa = Etapa.DECISAO
    a3.responsavel_id = usuario.id
    for chave, valor in (
        ("valor_mercado", "150000"),
        ("iptu_atraso", "0"),
        ("iptu_mensal", "180"),
        ("reforma", "8000"),
        ("desocupacao", "0"),
    ):
        preencher(a3, chave, Decimal(valor))

    # 4) aprovado para lance, teto já definido
    a4 = avaliacao_de(lotes[3])
    a4.etapa = Etapa.APROVADO_LANCE
    a4.responsavel_id = usuario.id
    a4.teto_lance = Decimal("115000")
    for chave, valor in (
        ("valor_mercado", "150000"),
        ("iptu_atraso", "0"),
        ("iptu_mensal", "150"),
        ("reforma", "5000"),
        ("desocupacao", "0"),
    ):
        preencher(a4, chave, Decimal(valor))

    # 5) descartado
    a5 = avaliacao_de(lotes[4])
    a5.etapa = Etapa.DESCARTADO
    a5.motivo_descarte = "Margem abaixo do piso de 20% após pesquisa de campo."
    a5.responsavel_id = usuario.id

    db.commit()


def seed() -> None:
    db = SessionLocal()
    try:
        carregar_itbi(db)
        carregar_emolumentos(db)
        db.commit()

        usuario = _usuario_dev(db)
        _parametros_padrao(db, usuario)

        importar_caixa(db, FIXTURE_CAIXA, executada_por=usuario.id)
        _avancar_funil_de_exemplo(db, usuario)

        print("Seed concluído.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
