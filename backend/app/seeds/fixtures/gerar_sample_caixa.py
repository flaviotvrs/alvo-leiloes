"""Gera `sample_caixa.csv` — planilha fictícia pequena para dev/seed/teste do importador,
sem depender da planilha real da Caixa. Rode com `uv run python -m
app.seeds.fixtures.gerar_sample_caixa` sempre que quiser regenerar o arquivo.

Formato espelha o arquivo real da Caixa (ver
docs/requisitos/mvp1-ajustes/04-importacao-caixa-e-historico.md): CSV `;`, ISO-8859-1,
linha de metadado com a data de geração, cabeçalho, linha em branco, depois os dados.

Dataset construído de propósito para exercitar a interface com dado plausível: cidades com
ITBI confirmado (Belo Horizonte, Contagem) e desconhecido (Juatuba, Itaúna — cai no palpite
de 3% em âmbar), faixas de preço/desconto variadas, descrições com tipo/área/quartos para
testar o parser. A primeira linha usa os mesmos números do exemplo da Ficha no README.md
(imóvel 8444403570957, R$ 49.647, avaliação R$ 176.000, 71,8% de desconto, 63,96 m²)."""

from pathlib import Path

CABECALHO = (
    "N° do imóvel;UF;Cidade;Bairro;Endereço;Preço;Valor de avaliação;Desconto;Financiamento;"
    "Descrição;Modalidade de venda;Link de acesso"
)

LINHAS = [
    ("8444403570957", "MG", "Belo Horizonte", "Aimorés", "Rua dos Aimorés, 500", "49.647,00", "176.000,00", "71.8", "Não", "Apartamento, 63.96 de área privativa, 2 qto(s), WC, sala, cozinha.", "Venda Direta Online", "https://venda-imoveis.caixa.gov.br/8444403570957"),
    ("8444403570958", "MG", "Belo Horizonte", "Castelo", "Av. Castelo, 120", "210.000,00", "350.000,00", "40.0", "Sim", "Casa, 180.00 de área total, 3 qto(s), WC, sala, cozinha.", "Licitação Aberta", "https://venda-imoveis.caixa.gov.br/8444403570958"),
    ("8444403570959", "MG", "Contagem", "Eldorado", "Rua Eldorado, 45", "95.000,00", "150.000,00", "36.7", "Não", "Apartamento, 55.00 de área privativa, 2 qto(s), WC, sala, cozinha.", "Venda Direta Online", "https://venda-imoveis.caixa.gov.br/8444403570959"),
    ("8444403570960", "MG", "Contagem", "Riacho", "Rua do Riacho, 300", "60.000,00", "120.000,00", "50.0", "Não", "Terreno, 0.00 de área total, 0.00 de área privativa, 300.00 de área do terreno.", "Leilão SFI", "https://venda-imoveis.caixa.gov.br/8444403570960"),
    ("8444403570961", "MG", "Juatuba", "Centro", "Rua Central, 10", "80.000,00", "130.000,00", "38.5", "Sim", "Casa, 120.00 de área total, 2 qto(s), WC, sala, cozinha.", "Venda Direta Online", "https://venda-imoveis.caixa.gov.br/8444403570961"),
    ("8444403570962", "MG", "Juatuba", "São José", "Rua São José, 88", "45.000,00", "70.000,00", "35.7", "Não", "Loja, 40.00 de área total.", "Licitação Aberta", "https://venda-imoveis.caixa.gov.br/8444403570962"),
    ("8444403570963", "MG", "Itaúna", "Centro", "Praça Central, 5", "60.000,00", "110.000,00", "45.5", "Não", "Apartamento, 48.00 de área privativa, 1 qto(s), WC, sala, cozinha.", "Venda Direta Online", "https://venda-imoveis.caixa.gov.br/8444403570963"),
    ("8444403570964", "MG", "Belo Horizonte", "Barreiro", "Rua Barreiro, 700", "130.000,00", "200.000,00", "35.0", "Sim", "Casa, 90.00 de área total, 2 qto(s), WC, sala, cozinha.", "Venda Direta Online", "https://venda-imoveis.caixa.gov.br/8444403570964"),
    ("8444403570965", "MG", "Betim", "Icaivera", "Rua Icaivera, 22", "105.000,00", "160.000,00", "34.4", "Não", "Apartamento, 60.00 de área privativa, 2 qto(s), WC, sala, cozinha.", "Licitação Aberta", "https://venda-imoveis.caixa.gov.br/8444403570965"),
    ("8444403570966", "MG", "Sete Lagoas", "Cidade Industrial", "Rua Industrial, 400", "40.000,00", "90.000,00", "55.6", "Não", "Terreno, 0.00 de área total, 0.00 de área privativa, 500.00 de área do terreno.", "Venda Direta Online", "https://venda-imoveis.caixa.gov.br/8444403570966"),
    ("8444403570967", "MG", "Belo Horizonte", "Buritis", "Rua Buritis, 900", "320.000,00", "480.000,00", "33.3", "Sim", "Apartamento, 75.00 de área privativa, 3 qto(s), WC, sala, cozinha.", "Leilão SFI", "https://venda-imoveis.caixa.gov.br/8444403570967"),
    ("8444403570968", "MG", "Contagem", "Petrolândia", "Rua Petrolândia, 33", "88.000,00", "140.000,00", "37.1", "Não", "Casa, 100.00 de área total, 2 qto(s), WC, sala, cozinha.", "Venda Direta Online", "https://venda-imoveis.caixa.gov.br/8444403570968"),
    ("8444403570969", "MG", "Betim", "Centro", "Rua Centro, 15", "99.000,00", "155.000,00", "36.1", "Não", "Apartamento, 52.00 de área privativa, 2 qto(s), WC, sala, cozinha.", "Venda Direta Online", "https://venda-imoveis.caixa.gov.br/8444403570969"),
    ("8444403570970", "MG", "Belo Horizonte", "Venda Nova", "Rua Venda Nova, 250", "70.000,00", "100.000,00", "30.0", "Não", "Loja, 35.00 de área total.", "Licitação Aberta", "https://venda-imoveis.caixa.gov.br/8444403570970"),
    ("8444403570971", "MG", "Juatuba", "Industrial", "Rua Industrial, 8", "55.000,00", "95.000,00", "42.1", "Sim", "Casa, 75.00 de área total, 2 qto(s), WC, sala, cozinha.", "Venda Direta Online", "https://venda-imoveis.caixa.gov.br/8444403570971"),
]


def gerar(caminho: Path, gerado_em: str = "14/08/2026") -> None:
    linhas = [
        "",
        f" Lista de Imóveis da Caixa;;Data de geração:;{gerado_em};;;;;;;",
        f" {CABECALHO}",
        "",
        *(" " + ";".join(campos) + " " for campos in LINHAS),
    ]
    caminho.write_bytes(("\n".join(linhas) + "\n").encode("ISO-8859-1"))


if __name__ == "__main__":
    destino = Path(__file__).parent / "sample_caixa.csv"
    gerar(destino)
    print(f"Gerado: {destino}")
