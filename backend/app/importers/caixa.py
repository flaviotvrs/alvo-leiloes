"""Conector da planilha de imóveis da Caixa.

Formato real (confirmado contra `docs/requisitos/Planilha_Caixa_Sample.csv`,
docs/requisitos/mvp1-ajustes/04-importacao-caixa-e-historico.md): CSV delimitado por `;`,
codificado em ISO-8859-1 (Latin-1) — não XLSX, apesar do nome "planilha". Linha de metadado
com a data de geração, cabeçalho de 12 colunas, linha em branco, depois os dados.
"""

import hashlib
import uuid
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

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
    "valor de avaliacao": "valor_avaliacao",
    "desconto": "desconto_pct",
    "modalidade de venda": "modalidade",
    "modalidade": "modalidade",
    "financiamento": "aceita_financiamento",
    "aceita financiamento": "aceita_financiamento",
    "link de acesso": "url_fonte",
    "link": "url_fonte",
}

CAMPOS_OBRIGATORIOS = {"codigo_externo", "uf", "cidade", "endereco", "preco_venda"}

_ROTULO_DATA_GERACAO = "data de geracao"


@dataclass
class LoteExtraido:
    lotes: list[LoteNormalizado]
    gerado_em: date | None
    erros: list[dict]


def hash_arquivo(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


def _parse_percentual(valor: str | None) -> Decimal | None:
    if not valor:
        return None
    try:
        numero = Decimal(valor.replace("%", "").replace(",", ".").strip())
    except InvalidOperation:
        raise ValueError(f"Desconto ilegível: {valor!r}") from None
    # planilha pode trazer 0.718 (fração) ou 71.8 (já em %); normaliza para "71.8"
    return numero * 100 if numero <= 1 else numero


def _parse_decimal(valor: str | None) -> Decimal | None:
    if not valor:
        return None
    try:
        return Decimal(valor.replace(".", "").replace(",", "."))
    except InvalidOperation:
        raise ValueError(f"Valor numérico ilegível: {valor!r}") from None


def _parse_bool_sim_nao(valor: str | None) -> bool:
    return (valor or "").strip().lower() == "sim"


def _parse_data_br(valor: str) -> date | None:
    try:
        return datetime.strptime(valor.strip(), "%d/%m/%Y").date()
    except ValueError:
        return None


def _linhas_csv(caminho: Path) -> list[list[str]]:
    texto = caminho.read_bytes().decode("ISO-8859-1")
    linhas = []
    for linha in texto.splitlines():
        if not linha.strip():
            linhas.append([])
            continue
        linhas.append([campo.strip() for campo in linha.split(";")])
    return linhas


def extrair_lotes_caixa(caminho: Path) -> LoteExtraido:
    linhas = _linhas_csv(caminho)

    gerado_em: date | None = None
    indice_cabecalho: int | None = None
    for i, linha in enumerate(linhas):
        rotulos = [normalizar_texto(campo).rstrip(":") for campo in linha]
        if _ROTULO_DATA_GERACAO in rotulos:
            pos = rotulos.index(_ROTULO_DATA_GERACAO)
            if pos + 1 < len(linha):
                gerado_em = _parse_data_br(linha[pos + 1])
            continue
        if linha and indice_cabecalho is None and any(normalizar_texto(c) in COLUNAS for c in linha):
            indice_cabecalho = i
            break

    if indice_cabecalho is None:
        raise ValueError("Planilha da Caixa sem linha de cabeçalho reconhecível")

    cabecalho = linhas[indice_cabecalho]
    indice_por_campo: dict[str, int] = {}
    for i, titulo in enumerate(cabecalho):
        campo = COLUNAS.get(normalizar_texto(titulo))
        if campo:
            indice_por_campo[campo] = i

    faltando = CAMPOS_OBRIGATORIOS - indice_por_campo.keys()
    if faltando:
        raise ValueError(f"Planilha da Caixa sem as colunas obrigatórias: {sorted(faltando)}")

    lotes: list[LoteNormalizado] = []
    erros: list[dict] = []
    for linha in linhas[indice_cabecalho + 1 :]:
        if not linha:
            continue

        def campo(nome: str) -> str | None:
            idx = indice_por_campo.get(nome)
            if idx is None or idx >= len(linha):
                return None
            valor = linha[idx].strip()
            return valor or None

        codigo_externo = campo("codigo_externo")
        if not codigo_externo:
            continue

        # uma linha malformada (ex. preço ilegível) não derruba a carga inteira — erro fica
        # registrado por linha e as demais seguem sendo processadas.
        try:
            preco_venda = _parse_decimal(campo("preco_venda"))
            if preco_venda is None:
                raise ValueError("Preço ausente ou ilegível")

            descricao = campo("descricao_oficial") or ""
            endereco = campo("endereco") or ""
            cidade = normalizar_texto(campo("cidade") or "").title()

            lotes.append(
                LoteNormalizado(
                    codigo_externo=codigo_externo,
                    uf=(campo("uf") or "").upper(),
                    cidade=cidade,
                    bairro=campo("bairro"),
                    endereco=endereco,
                    tipo=inferir_tipo(descricao or endereco),
                    area_total_m2=extrair_area_total(descricao),
                    area_privativa_m2=extrair_area_privativa(descricao),
                    area_terreno_m2=extrair_area_terreno(descricao),
                    quartos=extrair_quartos(descricao),
                    descricao_oficial=descricao,
                    modalidade=campo("modalidade"),
                    preco_venda=preco_venda,
                    valor_avaliacao=_parse_decimal(campo("valor_avaliacao")),
                    desconto_pct=_parse_percentual(campo("desconto_pct")),
                    aceita_financiamento=_parse_bool_sim_nao(campo("aceita_financiamento")),
                    praca_1_valor=None,
                    praca_1_data=None,
                    praca_2_valor=None,
                    praca_2_data=None,
                    url_fonte=campo("url_fonte"),
                )
            )
        except Exception as exc:  # noqa: BLE001 -- erro por linha não deve abortar a carga
            erros.append({"codigo_externo": codigo_externo, "erro": str(exc)})
    return LoteExtraido(lotes=lotes, gerado_em=gerado_em, erros=erros)


def importar_caixa(db: Session, caminho: Path, executada_por: uuid.UUID | None = None) -> Importacao:
    extraido = extrair_lotes_caixa(caminho)
    return aplicar_importacao(
        db,
        fonte=FonteLeilao.CAIXA,
        lotes=extraido.lotes,
        arquivo_nome=caminho.name,
        arquivo_hash=hash_arquivo(caminho),
        arquivo_gerado_em=extraido.gerado_em,
        erros_iniciais=extraido.erros,
        executada_por=executada_por,
    )
