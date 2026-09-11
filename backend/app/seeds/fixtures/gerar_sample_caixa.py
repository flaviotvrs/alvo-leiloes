"""Gera `sample_caixa.xlsx` — planilha fictícia pequena para dev/seed/teste do importador,
sem depender da planilha real da Caixa. Rode com `uv run python -m
app.seeds.fixtures.gerar_sample_caixa` sempre que quiser regenerar o arquivo.

Dataset construído de propósito para exercitar a interface com dado plausível: cidades com
ITBI confirmado (Belo Horizonte, Contagem) e desconhecido (Juatuba, Itaúna — cai no palpite
de 3% em âmbar), faixas de preço/desconto variadas, descrições com tipo/área/quartos para
testar o parser. A primeira linha usa os mesmos números do exemplo da Ficha no README.md
(imóvel 8444403570957, R$ 49.647, avaliação R$ 176.000, 71,8% de desconto, 63,96 m²)."""

from pathlib import Path

import openpyxl

CABECALHO = [
    "Nº do imóvel",
    "UF",
    "Cidade",
    "Bairro",
    "Endereço",
    "Descrição",
    "Preço",
    "Avaliação",
    "Desconto",
    "Modalidade de Venda",
    "Aceita Financiamento",
    "Link de acesso",
]

LINHAS = [
    ["8444403570957", "MG", "Belo Horizonte", "Aimorés", "Rua dos Aimorés, 500", "Apartamento com área privativa de 63,96 m², 2 quartos", 49647.00, 176000.00, 71.8, "Venda Direta Online", 0, "https://venda-imoveis.caixa.gov.br/8444403570957"],
    ["8444403570958", "MG", "Belo Horizonte", "Castelo", "Av. Castelo, 120", "Casa com área total de 180,00 m², 3 quartos", 210000.00, 350000.00, 40.0, "Licitação Aberta", 1, "https://venda-imoveis.caixa.gov.br/8444403570958"],
    ["8444403570959", "MG", "Contagem", "Eldorado", "Rua Eldorado, 45", "Apartamento com área privativa de 55,00 m², 2 quartos", 95000.00, 150000.00, 36.7, "Venda Direta Online", 0, "https://venda-imoveis.caixa.gov.br/8444403570959"],
    ["8444403570960", "MG", "Contagem", "Riacho", "Rua do Riacho, 300", "Terreno com área de terreno de 300,00 m²", 60000.00, 120000.00, 50.0, "Leilão SFI", 0, "https://venda-imoveis.caixa.gov.br/8444403570960"],
    ["8444403570961", "MG", "Juatuba", "Centro", "Rua Central, 10", "Casa com área total de 120,00 m², 2 quartos", 80000.00, 130000.00, 38.5, "Venda Direta Online", 1, "https://venda-imoveis.caixa.gov.br/8444403570961"],
    ["8444403570962", "MG", "Juatuba", "São José", "Rua São José, 88", "Loja com área total de 40,00 m²", 45000.00, 70000.00, 35.7, "Licitação Aberta", 0, "https://venda-imoveis.caixa.gov.br/8444403570962"],
    ["8444403570963", "MG", "Itaúna", "Centro", "Praça Central, 5", "Apartamento com área privativa de 48,00 m², 1 quartos", 60000.00, 110000.00, 45.5, "Venda Direta Online", 0, "https://venda-imoveis.caixa.gov.br/8444403570963"],
    ["8444403570964", "MG", "Belo Horizonte", "Barreiro", "Rua Barreiro, 700", "Casa com área total de 90,00 m², 2 quartos", 130000.00, 200000.00, 35.0, "Venda Direta Online", 1, "https://venda-imoveis.caixa.gov.br/8444403570964"],
    ["8444403570965", "MG", "Betim", "Icaivera", "Rua Icaivera, 22", "Apartamento com área privativa de 60,00 m², 2 quartos", 105000.00, 160000.00, 34.4, "Licitação Aberta", 0, "https://venda-imoveis.caixa.gov.br/8444403570965"],
    ["8444403570966", "MG", "Sete Lagoas", "Cidade Industrial", "Rua Industrial, 400", "Terreno com área de terreno de 500,00 m²", 40000.00, 90000.00, 55.6, "Venda Direta Online", 0, "https://venda-imoveis.caixa.gov.br/8444403570966"],
    ["8444403570967", "MG", "Belo Horizonte", "Buritis", "Rua Buritis, 900", "Apartamento com área privativa de 75,00 m², 3 quartos", 320000.00, 480000.00, 33.3, "Leilão SFI", 1, "https://venda-imoveis.caixa.gov.br/8444403570967"],
    ["8444403570968", "MG", "Contagem", "Petrolândia", "Rua Petrolândia, 33", "Casa com área total de 100,00 m², 2 quartos", 88000.00, 140000.00, 37.1, "Venda Direta Online", 0, "https://venda-imoveis.caixa.gov.br/8444403570968"],
    ["8444403570969", "MG", "Betim", "Centro", "Rua Centro, 15", "Apartamento com área privativa de 52,00 m², 2 quartos", 99000.00, 155000.00, 36.1, "Venda Direta Online", 0, "https://venda-imoveis.caixa.gov.br/8444403570969"],
    ["8444403570970", "MG", "Belo Horizonte", "Venda Nova", "Rua Venda Nova, 250", "Loja com área total de 35,00 m²", 70000.00, 100000.00, 30.0, "Licitação Aberta", 0, "https://venda-imoveis.caixa.gov.br/8444403570970"],
    ["8444403570971", "MG", "Juatuba", "Industrial", "Rua Industrial, 8", "Casa com área total de 75,00 m², 2 quartos", 55000.00, 95000.00, 42.1, "Venda Direta Online", 1, "https://venda-imoveis.caixa.gov.br/8444403570971"],
]


def gerar(caminho: Path) -> None:
    livro = openpyxl.Workbook()
    aba = livro.active
    aba.append(CABECALHO)
    for linha in LINHAS:
        aba.append(linha)
    livro.save(caminho)


if __name__ == "__main__":
    destino = Path(__file__).parent / "sample_caixa.xlsx"
    gerar(destino)
    print(f"Gerado: {destino}")
