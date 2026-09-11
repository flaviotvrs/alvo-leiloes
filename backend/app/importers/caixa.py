"""Conector da planilha de imóveis da Caixa.

O mapeamento de colunas abaixo é um placeholder razoável (cabeçalhos em português, os
mesmos nomes de campo que `LoteNormalizado` espera) — **valide contra a planilha real da
Caixa assim que ela estiver disponível** e ajuste `COLUNAS` conforme necessário; a busca de
coluna já normaliza acento/caixa/espaço para tolerar pequenas variações de cabeçalho.
"""

import hashlib
import uuid
from decimal import Decimal
from pathlib import Path

import openpyxl
from sqlalchemy.orm import Session

from app.importers.base import LoteNormalizado
from app.importers.parsing import (
    extrair_area_privativa,
    extrair_area_terreno,
    extrair_area_total,
    extrair_quartos,
    inferir_tipo,
    normalizar_texto,
)
from app.importers.upsert import aplicar_importacao
from app.models.enums import FonteLeilao
from app.models.importacao import Importacao

# cabeçalho normalizado (normalizar_texto) -> nome do campo em LoteNormalizado
COLUNAS = {
    "no do imovel": "codigo_externo",
    "n do imovel": "codigo_externo",
    "numero do imovel": "codigo_externo",
    "uf": "uf",
    "cidade": "cidade",
    "bairro": "bairro",
    "endereco": "endereco",
    "descricao": "descricao_oficial",
    "preco": "preco_venda",
    "valor de venda": "preco_venda",
    "avaliacao": "valor_avaliacao",
    "desconto": "desconto_pct",
    "modalidade de venda": "modalidade",
    "modalidade": "modalidade",
    "aceita financiamento": "aceita_financiamento",
    "link de acesso": "url_fonte",
    "link": "url_fonte",
}

CAMPOS_OBRIGATORIOS = {"codigo_externo", "uf", "cidade", "endereco", "preco_venda"}


def hash_arquivo(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _parse_percentual(valor) -> Decimal | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, str):
        valor = valor.replace("%", "").replace(",", ".").strip()
    numero = Decimal(str(valor))
    # planilha pode trazer 0.718 (fração) ou 71.8 (já em %); normaliza para "71.8"
    return numero * 100 if numero <= 1 else numero


def _parse_decimal(valor) -> Decimal | None:
    if valor is None or valor == "":
        return None
    if isinstance(valor, str):
        valor = valor.replace(".", "").replace(",", ".").strip()
    return Decimal(str(valor))


def extrair_lotes_caixa(caminho: Path) -> list[LoteNormalizado]:
    planilha = openpyxl.load_workbook(caminho, data_only=True)
    aba = planilha.active

    linhas = aba.iter_rows(values_only=True)
    cabecalho = next(linhas)
    indice_por_campo: dict[str, int] = {}
    for i, titulo in enumerate(cabecalho):
        if titulo is None:
            continue
        campo = COLUNAS.get(normalizar_texto(str(titulo)))
        if campo:
            indice_por_campo[campo] = i

    faltando = CAMPOS_OBRIGATORIOS - indice_por_campo.keys()
    if faltando:
        raise ValueError(f"Planilha da Caixa sem as colunas obrigatórias: {sorted(faltando)}")

    lotes: list[LoteNormalizado] = []
    for linha in linhas:
        if linha[indice_por_campo["codigo_externo"]] in (None, ""):
            continue

        def campo(nome: str):
            idx = indice_por_campo.get(nome)
            return linha[idx] if idx is not None else None

        descricao = str(campo("descricao_oficial") or "")
        endereco = str(campo("endereco") or "")
        cidade = normalizar_texto(str(campo("cidade") or "")).title()

        lotes.append(
            LoteNormalizado(
                codigo_externo=str(campo("codigo_externo")),
                uf=str(campo("uf") or "").strip().upper(),
                cidade=cidade,
                bairro=(str(campo("bairro")).strip() if campo("bairro") else None),
                endereco=endereco,
                tipo=inferir_tipo(descricao or endereco),
                area_total_m2=extrair_area_total(descricao),
                area_privativa_m2=extrair_area_privativa(descricao),
                area_terreno_m2=extrair_area_terreno(descricao),
                quartos=extrair_quartos(descricao),
                descricao_oficial=descricao,
                modalidade=(str(campo("modalidade")).strip() if campo("modalidade") else None),
                preco_venda=_parse_decimal(campo("preco_venda")),
                valor_avaliacao=_parse_decimal(campo("valor_avaliacao")),
                desconto_pct=_parse_percentual(campo("desconto_pct")),
                aceita_financiamento=bool(campo("aceita_financiamento")),
                praca_1_valor=None,
                praca_1_data=None,
                praca_2_valor=None,
                praca_2_data=None,
                url_fonte=(str(campo("url_fonte")).strip() if campo("url_fonte") else None),
            )
        )
    return lotes


def importar_caixa(db: Session, caminho: Path, executada_por: uuid.UUID | None = None) -> Importacao:
    lotes = extrair_lotes_caixa(caminho)
    return aplicar_importacao(
        db,
        fonte=FonteLeilao.CAIXA,
        lotes=lotes,
        arquivo_nome=caminho.name,
        arquivo_hash=hash_arquivo(caminho),
        executada_por=executada_por,
    )
