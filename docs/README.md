# Handoff: Alvo Leilões — triagem, ficha do imóvel e funil de aprovação

## Visão geral

Ferramenta interna para garimpo de imóveis em leilão extrajudicial (Lei 9.514/97). O usuário
recebe uma base de imóveis (hoje a planilha da Caixa), filtra o que vale a pena olhar,
preenche à mão os dados que só existem em campo (visita, prefeitura, administradora,
anúncios comparáveis), e o sistema fecha a conta do negócio e diz se a margem passa do piso
de 20%. Três telas: **Triagem**, **Ficha do imóvel** e **Funil de aprovação**.

Duas regras de produto atravessam a interface inteira:

1. **Procedência do dado é visível.** Todo valor mostra de onde veio: base importada,
   digitado pelo usuário, ou automação futura. O usuário precisa saber em que número confiar.
2. **Palpite nunca se disfarça de fato.** Quando o sistema assume um valor (alíquota de ITBI
   não cadastrada, comissão do leiloeiro antes de ler o edital), a linha aparece em âmbar,
   diz que é palpite e aponta o campo onde o usuário confirma. Ao confirmar, vira verde.

## Sobre os arquivos de design

Os `.dc.html` deste pacote são **referências de design feitas em HTML** — protótipos que
mostram aparência e comportamento pretendidos, não código de produção para copiar. A tarefa é
**recriar esses designs no ambiente do codebase de destino** (React, Vue, etc.) com os padrões
e bibliotecas já estabelecidos lá. Se ainda não existe codebase, escolha a stack e implemente.
O HTML usa um runtime interno de prototipagem (`support.js`, tags `<x-dc>`, `<sc-for>`,
`<sc-if>`) que **não deve** ser reproduzido: `<sc-for list>` é um `.map()`, `<sc-if value>` é
uma renderização condicional, e o que o protótipo chama de `renderVals()` é apenas o cálculo
de props do componente.

Abrir `Alvo Leiloes v4.dc.html` em um navegador é a forma mais rápida de ver o comportamento
real (filtros, recálculo da conta, expandir/fechar detalhe).

## Fidelidade

**Alta fidelidade (hifi).** Cores, tipografia, espaçamentos e estados são finais e devem ser
recriados fielmente, adaptando-se aos componentes existentes do codebase. Os dados são reais
(linhas da planilha da Caixa de MG), mas os números de KPI e as contagens do funil são
ilustrativos.

## Design tokens

### Cores

| Token | Hex | Uso |
|---|---|---|
| `ink` | `#1B1A16` | texto principal, barra de navegação, chips ativos, coluna lateral escura |
| `ink-2` | `#332F27` | aba ativa na navegação, hover na coluna escura |
| `ink-3` | `#3D3A31` | texto de botão inativo |
| `text-muted` | `#5C584C` | valores secundários, texto de apoio |
| `text-soft` | `#6E6A5E` | parágrafos de apoio, item concluído |
| `label` | `#7C7768` | rótulos monoespaçados, cabeçalho de tabela |
| `label-soft` | `#8A8577` | valor em branco, hints |
| `green` | `#1F6F4A` | institucional: sucesso, margem aprovada, dado manual, links |
| `green-dark` | `#123F2A` | hover de link |
| `green-bg` | `#E6EEE9` | fundo de sucesso, botão primário claro |
| `green-bg-2` | `#D9E6DE` | hover do botão primário claro |
| `green-border` | `#C7D6C9` | borda do botão primário claro |
| `red` | `#8C2F2F` | custo assumido, margem reprovada, avisos |
| `red-bg` | `#F6EFEC` | fundo de reprovação |
| `red-bg-2` | `#F0E2DD` | hover do botão de descarte |
| `amber` | `#8A6B14` | palpite, pendência, automação futura |
| `amber-bg` | `#F7EFDC` | fundo de palpite/automação |
| `amber-bg-2` | `#F0E5C9` | hover |
| `amber-border` | `#E0D3AC` | borda de palpite |
| `auto-dot` | `#D9B84F` / borda `#B79A2F` | marcador do dado de automação |
| `page` | `#EFEDE7` | fundo da página |
| `surface` | `#FCFBF8` | cartões, linhas de tabela |
| `surface-2` | `#F2F0EB` | cabeçalhos de cartão e de tabela, hover neutro |
| `surface-3` | `#F5F3ED` | hover de linha da tabela |
| `surface-4` | `#F7F5F0` | fundo de input vazio |
| `col-bg` | `#E7E4DB` | fundo das colunas do funil |
| `border` | `#DDD9CF` | borda padrão |
| `border-2` | `#C9C4B6` | borda de input e de botão neutro |
| `border-3` | `#B8B2A3` | borda de input vazio, marcador de base |
| `divider` | `#EAE7DE` | divisória de linha de tabela |
| `divider-2` | `#EFEDE6` | divisória entre campos |
| `divider-dash` | `#E4E0D6` | divisória tracejada da conta; também chip neutro |
| `on-dark` | `#F2F0EB` | texto sobre `ink` |
| `on-dark-2` | `#D7D3C8` / `#B5B0A2` / `#9C978A` | texto secundário sobre `ink` |
| `on-dark-border` | `#4A463A` | borda sobre `ink` |
| `track` | `#D4CFC3` | trilha da barra de progresso do funil |

### Tipografia

- **Serifada — Source Serif 4** (Google Fonts, pesos 400/500/600/700, eixo opsz 8..60):
  toda a interface textual. Fallback `Georgia, serif`.
- **Monoespaçada — IBM Plex Mono** (pesos 400/500/600): todo número, rótulo em caixa alta,
  código de imóvel, valor monetário, percentual, e todo `input`/`select`/`textarea`.

Escala usada (px):

| Papel | Tamanho | Peso | Tracking | Família |
|---|---|---|---|---|
| H1 de tela | 30 | 600 | -0.015em | serif |
| H1 da ficha | 26 | 600 | -0.015em | serif |
| Valor de KPI | 23 | 600 | -0.01em | serif |
| Métrica da ficha | 19 | 600 | — | mono |
| Margem (número grande) | 30 | 600 | — | mono |
| Lucro líquido | 17 | 600 | — | mono |
| Título de card/coluna | 14–14.5 | 600 | -0.01em | serif |
| Corpo | 13–13.5 | 400 | — | serif |
| Valor em tabela/conta | 12.5–13 | 400–600 | — | mono |
| Hint | 11.5–12 | 400 | — | serif |
| Rótulo de seção | 10 | 400 | 0.16em, uppercase | mono |
| Rótulo de campo/coluna | 9.5 | 400 | 0.13em, uppercase | mono |
| Chip de procedência | 9.5 | 400 | 0.1em, uppercase | mono |

Mínimo absoluto de 9.5px, e só para rótulo monoespaçado em caixa alta.

### Espaçamento, raio, sombra

- Padding de tela: `24px 28px 60px` (triagem/funil), `22px 28px 60px` (ficha).
- Padding de cartão: `18px 22px`; cabeçalho de cartão `10px 20px`.
- Gaps: 20px entre blocos da ficha, 14px entre colunas do funil, 16–18px na grade de filtros.
- Raio: **3px** em controles, inputs, chips retangulares e cartões internos; **4px** em
  cartões de primeiro nível; **99px** em pílulas; **50%** em avatares.
- **Sem sombras.** A hierarquia vem de borda de 1px e do contraste entre `surface` e `page`.
- Bordas: sempre 1px `solid` `border`, exceto o marcador de dado em branco (1px `dashed`
  `border-3`) e as divisórias tracejadas da conta.

### Formatação de número (pt-BR, obrigatório)

- Moeda: `R$ 49.647` — sem centavos (`maximumFractionDigits: 0`).
- Percentual: uma decimal com **vírgula** — `71,8%`, `+64,8%`, `2,5%`.
- Entrada de valor: o usuário digita `3.400` ou `2,5`; o parser aceita separador de milhar por
  ponto e decimal por vírgula.
- Metragem: `63,96 m²`.

## Marcadores de procedência do dado

Quatro estados, usados como quadrado de 9–12px (raio 2px) ao lado do rótulo, e como chip de
texto ao lado do input. Aparecem também nos cards do funil e nas linhas da tabela.

| Estado | Quadrado | Chip | Fundo / texto do chip |
|---|---|---|---|
| Base importada | `#C9C4B6`, borda sólida `#B8B2A3` | `Caixa` | `#E4E0D6` / `#5C584C` |
| Digitado pelo usuário | `#1F6F4A` sólido | `Manual` | `#E6EEE9` / `#1F6F4A` |
| Automação (futuro) | `#D9B84F`, borda `#B79A2F` | `Automático` | `#F7EFDC` / `#8A6B14` |
| Em branco | transparente, borda **tracejada** `#B8B2A3` | `A preencher` | `#F2F0EB` / `#8A8577` |

Legenda fixa acima da tabela de triagem, com os quatro estados, prefixada por
"Procedência do dado:".

Um quinto tipo está previsto nos requisitos e **ainda não está desenhado**: *coleta manual
guiada* — IPTU e condomínio, onde o sistema mostra um tutorial ("acesse tal site, informe a
inscrição, copie o valor") e o usuário cola o resultado. Hoje esses campos usam o estado
"digitado pelo usuário". Ver `BACKEND.md` para o modelo já preparado para isso.

---

## Navegação global

Barra fixa (`position: sticky; top: 0; z-index: 20`), altura 60px, fundo `ink`, padding
lateral 28px, `justify-content: space-between`.

- Esquerda: logotipo `ALVO` (20px, 600, tracking 0.2em) + `Leilões` (11px, uppercase,
  tracking 0.22em, `#9C978A`); depois abas **Triagem** e **Funil de aprovação** (13.5px serif,
  padding `7px 14px`, raio 3px; ativa = fundo `ink-2` + texto `on-dark`, inativa = transparente
  + `#9C978A`).
- Direita: contador da base — `981 IMÓVEIS COM ANÁLISE NA BASE` (mono 11px, `#9C978A`,
  tracking 0.04em) — e avatar circular de 27px em `green` com iniciais + nome do usuário
  (13px, `#D7D3C8`).

O contador é deliberadamente uma prova de uso ("temos base analisada"), **não** um número de
importação. Volume e status de importação pertencem só à futura tela de Importações.

A ficha do imóvel não é uma aba: chega-se a ela clicando em uma linha da triagem ou em um card
do funil, e o retorno é pelo breadcrumb.

---

## Tela 1 — Triagem

**Objetivo:** cortar cedo. Reduzir uma base de centenas de imóveis à dezena que vale visita e
pesquisa.

### Cabeçalho

Linha `space-between`, alinhada por `flex-end`:

- Esquerda: sobre-título `FILA DE TRIAGEM` (mono 10.5px, tracking 0.18em, uppercase, `label`) e
  H1 "O que vale a pena visitar e pesquisar".
- Direita: quatro KPIs em `grid-template-columns: repeat(4, auto)`, gap 26px, alinhados à
  direita — rótulo mono 9.5px uppercase sobre valor 23px/600.

KPIs: **Não avaliados 935** · **Com dados de campo 46** · **Prontos p/ decisão 11** (em
`green`) · **Desconto ≥ 40% 207**.

### Painel de filtros

Cartão `surface` + borda, raio 4px, padding `16px 18px`. Cabeçalho do painel com
`BUSCAR IMÓVEIS` à esquerda e, à direita, duas pílulas: **Só sem dados de campo** (toggle;
ativa = fundo `ink`, texto `on-dark`) e **Limpar filtros** (contorno `border-2`, hover
`#E6E3DA`).

Grade `repeat(4, minmax(0,1fr))`, gap `16px 18px`. Cada controle tem rótulo mono 9.5px
uppercase e, quando útil, um sufixo explicativo em caixa baixa `#8A8577`:

| # | Controle | Tipo | Rótulo / sufixo | Comportamento |
|---|---|---|---|---|
| 1 | Estado | `select` | "Estado · só MG na base" | `Todos os estados` \| `MG` |
| 2 | Cidade | `select` | "Cidade" | `Todas as cidades` + cidades distintas da base, ordenadas |
| 3 | Bairro | `input` | "Bairro", placeholder "parte do nome" | substring, case-insensitive |
| 4 | Desconto mínimo | `range` 0–75 step 5 | "Desconto mínimo · valor da planilha" | valor à direita em mono `green` 12.5px: `≥ 35%` ou `qualquer` |
| 5 | Faixa de preço | dois `range` 0–1.600.000 step 10.000 | "Faixa de preço" | ocupa 2 colunas; leitura `R$ 0 até R$ 1.600.000+` no canto |
| 6 | Tipo de imóvel | chips multi | "Tipo de imóvel" | 2 colunas; `Casa` `Apartamento` `Terreno` `Loja`; ativo = `ink` |
| 7 | Financiamento | segmentado | "Financiamento" | 2 colunas; `Indiferente` \| `Aceita` \| `Não aceita` |
| 8 | FGTS | segmentado | "FGTS · dado manual, não vem na planilha" | 2 colunas; `Indiferente` \| `Aceita FGTS` \| `Não aceita` |

A faixa de preço tem uma trilha visual própria acima dos dois inputs: barra de 4px em
`divider-dash`, raio 2px, com o intervalo selecionado preenchido em `green`
(`left: min%`, `right: 100 - max%`). Os dois `range` ficam em `grid 1fr 1fr` sob a trilha.
`accent-color: #1F6F4A` em todos os `range`.

Não existe filtro de modalidade — decisão de produto, não omissão.

### Resumo da busca

Abaixo do painel, `space-between`:

- Esquerda (13px, `text-muted`): lista dos filtros ativos, unida por ` · ` — ex.
  "Filtrando por Areado · desconto ≥ 35%". Sem filtro: "Sem filtros: mostrando toda a base".
- Direita (mono 11px, `label`): `N de 981 imóveis`.

### Tabela

Borda 1px, raio 4px, `overflow: hidden`, fundo `surface`. Oito colunas, `grid-template-columns:
2.4fr 0.75fr 1fr 1fr 0.7fr 1.15fr 1.35fr 0.95fr`, gap 14px, padding lateral 18px.

Cabeçalho em `surface-2`, mono 9.5px uppercase tracking 0.13em: Imóvel · nº Caixa / Tipo /
Preço (dir.) / Avaliação (dir.) / Desc. (dir.) / Modalidade / Dados de campo / Triagem (dir.).

Linha: padding vertical 13px (8px no modo denso), divisória `divider`, hover `surface-3`,
cursor pointer, clique abre a ficha.

- **Imóvel:** endereço 14px, truncado com ellipsis; abaixo, meta em mono 10.5px `label`:
  `nº · CIDADE · BAIRRO · área/quartos`, também truncada.
- **Preço / Avaliação:** mono 12.5px, direita; avaliação em `text-muted`.
- **Desc.:** mono 12.5px/600, direita. Cor: `green` se ≥ 45%, `ink` se ≥ 35%, `label` abaixo
  disso; `—` quando não há desconto.
- **Modalidade:** nome 12px + linha mono 10px `label-soft` com
  "aceita financiamento · aceita fgts".
- **Dados de campo:** cinco quadrados de 12px de procedência (um por campo-chave: mercado,
  IPTU, condomínio, ocupação, reforma), contador `3/5` em mono 10.5px colorido (verde se 5,
  `label-soft` se 0, âmbar no meio) e uma nota de 11px em `label` dizendo o que falta
  ("falta condomínio e reforma", "avaliação não iniciada").
- **Triagem:** botão **Preencher** (`green-bg` / `green-border` / `green`) e botão **Corta**
  (`red-bg` / `border` / `red`); o segundo faz `stopPropagation`.

Estado vazio (padding 38px, centralizado): "Nenhum imóvel atende a esses filtros." +
"Tente ampliar a faixa de preço ou reduzir o desconto mínimo." + botão **Limpar filtros**.

Rodapé da tabela, mono 11px `label`, `space-between`: "Ordenado por desconto" e
"Nenhuma automação ativa · todos os dados de campo são manuais".

---

## Tela 2 — Ficha do imóvel

**Objetivo:** preencher os dados que só existem fora da base e ver, a cada tecla, se o negócio
passa do piso de margem.

Breadcrumb no topo (mono 11px): `← Triagem` (botão em `green`) `/` `IMÓVEL 8444403570957`.

Layout `grid-template-columns: minmax(0,1fr) 352px`, gap 20px, `align-items: start`. Coluna
esquerda em `flex column` gap 20px com três blocos; coluna direita `position: sticky; top: 76px`
com três cartões.

### Bloco A — Dados do imóvel (somente leitura)

Cabeçalho `surface-2`: `DADOS DO IMÓVEL · SOMENTE LEITURA` à esquerda e, à direita, em mono
10.5px `label-soft`, "importado da planilha da Caixa em 28/08/2026" — procedência do registro,
não contagem.

Corpo: H1 com o endereço (26px/600), linha de local 13.5px `text-muted`, descrição oficial
13px `text-soft` separada por uma divisória tracejada `1px dashed #E0DCD2`.

Quatro métricas em `grid repeat(4,1fr)` com gap de 1px sobre fundo `border` (cria hairlines),
raio 3px: **Preço de venda** `R$ 49.647` · **Valor de avaliação** `R$ 176.000` · **Desconto**
`71,8%` (em `green`) · **Área privativa** `63,96 m²`. Cada célula: rótulo mono 9.5px, valor
mono 19px/600, hint 11.5px dizendo a origem do número ("campo Preço", "calculado pela Caixa",
"extraído da descrição").

Abaixo, duas pílulas neutras (`divider-dash` / `text-muted`) com modalidade e financiamento, e
o link "Abrir no site da Caixa ↗".

### Bloco B — Dados de campo (o usuário preenche)

Cabeçalho: `DADOS DE CAMPO · VOCÊ PREENCHE` e, à direita, `7/11 campos preenchidos` — verde
quando completo, âmbar quando não.

Cada campo é uma linha `grid minmax(170px,236px) minmax(0,1fr)`, gap 18px, padding vertical
14px, divisória `divider-2`. À esquerda: marcador de procedência + rótulo 13.5px, e abaixo
(recuado 17px) o hint 11.5px `label-soft` dizendo **onde se consegue esse dado**. À direita: o
controle, o chip de procedência, e eventuais extras.

Onze campos, na ordem:

| Campo | Controle | Hint | Observações |
|---|---|---|---|
| Aceita FGTS? | select | "Confirmado na página do imóvel ou no edital" | `Não verificado` \| `Aceita FGTS` \| `Não aceita` |
| Valor real de mercado | texto, R$, 130px, dir. | "Sua estimativa a partir de anúncios da região" | tem sugestão de automação (abaixo) |
| IPTU em atraso | texto, R$, 110px, dir. | "Consulta na prefeitura ou no edital" | entra na conta como dívida assumida |
| Débito de condomínio | texto, R$, 110px, dir. | "Casa isolada normalmente não tem" | vazio → aviso em `red` 12px: "Sem esse valor a conta abaixo assume zero." |
| Alíquota de ITBI · Aimorés | texto, %, 90px, dir. | "Não cadastrada. Enquanto em branco, a conta usa 3% como palpite" | aceita decimal com vírgula |
| Comissão do leiloeiro | texto, %, 90px, dir. | "Está no edital. Em branco, a conta usa 5%" | idem |
| IPTU mensal atual | texto, R$, 110px, dir. | "Consulta guiada no site da prefeitura, por nº de inscrição" | alimenta o carregamento |
| Condomínio mensal atual | texto, R$, 110px, dir. | "Confirmar com administradora ou síndico" | idem |
| Ocupação | select | "Confirmada em visita ou com vizinhos" | `Não verificado` \| `Desocupado` \| `Ocupado — antigo mutuário` \| `Ocupado — terceiros` \| `Locado com contrato` |
| Reforma estimada | texto, R$, 110px, dir. | "Orçamento aproximado após a visita" | |
| Custo de desocupação | texto, R$, 110px, dir. | "Acordo amigável ou ação judicial" | |

Input: 13px, padding `7px 9px`, borda `border-2`, raio 3px, fundo branco. **Vazio:** borda
`border-3` e fundo `surface-4` — o campo em branco é visivelmente diferente do preenchido.
Foco: `outline: 2px solid green; outline-offset: -2px`. Select: largura 100%, máx 260px.

**Sugestão de automação** (só no valor de mercado, e só quando o campo já tem valor manual):
texto 12px em `amber` "Automação futura sugeriria R$ 168.000" + botão **Usar valor da
automação** (`amber-bg` / `amber-border` / `amber`, hover `amber-bg-2`). Aceitar troca o
marcador do campo para o estado *automação*. É a prova visual de que, quando a automação
existir, ela **sugere** e o número do usuário continua valendo até ele aceitar.

Ao final do bloco, `ANOTAÇÕES DA VISITA`: `textarea` de altura mínima 74px, 13px,
`line-height 1.5`, `resize: vertical`, placeholder "O que você viu no local, com quem falou, o
que ainda falta confirmar."

### Bloco C — Conta do negócio

Cabeçalho: `CONTA DO NEGÓCIO` e, à direita, o cenário — "cenário à vista · revenda em 12
meses". Só cenário à vista está no escopo; financiado fica para depois.

Corpo em `grid repeat(auto-fit, minmax(280px,1fr))`, gap 26px:

**Coluna resumo** — quatro linhas `space-between` com divisória tracejada `divider-dash`,
rótulo serif 13px e valor mono 13px:

1. Investimento total até a revenda — `R$ 99.428` (peso 600)
2. Revenda estimada — `R$ 190.000` (peso 500; "em branco" em `label-soft` se vazio)
3. Comissão do corretor (6%) — `– R$ 11.400`
4. IR sobre ganho de capital (15%) — `– R$ 15.149`

Depois, sem divisória, **Lucro líquido** (13.5px/600) com valor mono 17px/600 na cor do
resultado. Negativo é prefixado por `– ` sobre o módulo do valor.

**Cartão de margem** — fundo `green-bg` se aprovado, `red-bg` se reprovado, `surface-2` se
ainda não há revenda estimada; raio 3px, padding `16px 18px`:

- Rótulo mono 10px uppercase: "Margem sobre o investimento"
- Número mono 30px/600: `+64,4%`
- Nota 12.5px: "Acima do piso de 20% — segue no funil." / "Abaixo do piso de 20% — a regra é
  não participar." / "Preencha o valor de revenda para ver a margem."
- Rodapé separado por `1px solid rgba(0,0,0,0.08)`, mono 10.5px: "equivale a 33,7% sobre a
  revenda"

**Detalhe expansível.** Botão de largura total (contorno `border-2`, mono 10.5px uppercase,
padding 9px, hover `surface-2`) alternando "Abrir a conta detalhada ▾" / "Fechar a conta
detalhada ▴". Aberto por padrão. Ao abrir, cinco grupos, cada um com cabeçalho
`space-between` (título mono 9.5px uppercase na cor do grupo + subtotal mono 12px/600) e suas
linhas em `grid minmax(0,1fr) auto`, cada linha com rótulo 13px, hint 11.5px e valor mono 13px:

1. **Aquisição** (cor `ink`) — Preço de venda (Caixa) · Comissão do leiloeiro · ITBI · Cidade ·
   Registro em cartório. Os hints carregam a fonte de cada número: "importado da planilha",
   "5% sobre o arremate, conforme edital" **ou** o texto de palpite, "alíquota confirmada por
   você: 2,5%", "Tabela 4-2026 TJMG, item 5-e · faixa R$ 56.000".
2. **Dívidas anteriores assumidas** (cor `red` se > 0, senão `label-soft`) — IPTU em atraso
   ("só entra se o edital passar a dívida ao arrematante") · Condomínio em atraso.
3. **Recuperação e posse** (cor `ink`) — Reforma · Desocupação.
4. **Carregamento · 12 meses** (cor `amber` se > 0) — "IPTU mensal × 12" com hint
   "R$ 285 por mês" · "Condomínio mensal × 12" com hint "em branco vira zero na conta".
5. **Venda** (cor `green`, subtotal = líquido recebido) — Valor de revenda · Comissão do
   corretor · IR sobre ganho de capital, com o hint mostrando a base: "15% sobre ganho de
   R$ 100.992 (custo de aquisição + reforma como base)".

Toda linha cujo campo esteja vazio mostra "em branco" em `label-soft` em vez de `R$ 0` — o
usuário precisa distinguir "é zero" de "não sei ainda".

**Linha em palpite.** Quando o valor é assumido, rótulo, valor e hint ficam em `amber` e o
hint diz o que fazer: "palpite de 3% — alíquota não cadastrada; confirme na prefeitura e lance
no campo acima". Ao preencher o campo correspondente, a linha volta a `text-muted` e o hint
passa a confirmar a origem.

### Coluna direita

**Cartão de etapa** (fundo `ink`, texto `on-dark`, raio 4px, padding `18px 20px`):
`ETAPA ATUAL`, nome da etapa 19px/600, responsável e tempo 12.5px `#B5B0A2`; barra de cinco
segmentos de 4px (gap 3px, raio 2px) — etapas passadas/atual em `on-dark`, futuras em
`on-dark-border`; botão primário de largura flexível ("Enviar para decisão" em `green` quando
tudo preenchido, "Enviar mesmo com lacunas" em `#6E6A5E` quando não) + botão **Descartar** com
contorno `on-dark-border`; nota 12px `#9C978A` explicando a consequência: "4 campo(s) em
branco. Dá para avançar, mas fica registrado quem decidiu sem o dado."

**Checklist de campo** (`surface`): `CHECKLIST DE CAMPO` + progresso `4/6`; seis itens como
botões de largura total, hover `surface-2`, com caixa de 15px (raio 3px, borda 1.5px; marcada =
fundo `green` + `✓` branco 10px) e rótulo 13px que ganha `line-through` e cor `text-soft`
quando marcado. Itens: Matrícula do imóvel obtida no CRI · Visita ou foto recente do imóvel ·
IPTU consultado na prefeitura · Taxa de condomínio confirmada · Edital lido por inteiro ·
3 anúncios comparáveis salvos.

**Histórico do registro** (`surface`): lista de eventos com avatar circular de 24px (iniciais
mono 9.5px; `green-bg`/`green` para o usuário, `divider-dash`/`text-muted` para eventos de
sistema), texto 12.5px e timestamp mono 10.5px. Registra mudança de valor com o antes e o
depois: "Ocupação alterada de \"Não verificado\" para \"Ocupado — antigo mutuário\"."

---

## Tela 3 — Funil de aprovação

**Objetivo:** ver onde cada imóvel travou e quanto do trabalho manual está pendente.

Cabeçalho: sobre-título `FUNIL DE APROVAÇÃO · SETEMBRO`, H1 "Da fila de triagem até o lance"; à
direita duas métricas alinhadas à direita — **Base → aprovados 1,4%** e **Tempo médio de
pesquisa 9 dias** (rótulo mono 9.5px, valor 22px/600).

Cinco colunas em `grid repeat(5, minmax(0,1fr))`, gap 14px, `min-height: 430px`, fundo `col-bg`,
borda `border`, raio 4px, padding 12px:

| Coluna | Contagem | Nota | Barra |
|---|---|---|---|
| Não avaliados | 935 | "Avaliação ainda não iniciada" | 100%, `#9C978A` |
| Pesquisa de campo | 46 | "Alguém está preenchendo à mão" | 58%, `#7C7768` |
| Análise financeira | 19 | "Conta fechada com os dados manuais" | 40%, `amber` |
| Decisão | 7 | "Aguardando aval de investimento" | 26%, `red` |
| Aprovado p/ lance | 11 | "Teto de lance definido" | 16%, `green` |

Cabeçalho da coluna: nome 14px/600 + contagem mono 11px `label`; nota 11.5px `label`; barra de
3px em `track` com preenchimento na cor da coluna.

Card (fundo `surface`, borda `border`, **borda esquerda de 3px** na cor do estado, raio 3px,
padding `11px 12px`, hover fundo branco + borda `border-3`, clique abre a ficha):

- Endereço 13px, `line-height 1.35`
- Cidade em mono 10.5px `label`
- Linha `space-between`: valor mono 12px/600 e desconto mono 11px/600 (verde se ≥ 45%)
- Rodapé separado por `1px solid divider`: os cinco quadrados de procedência à esquerda e, à
  direita, uma pílula de estado em mono 10px — "Sem pesquisa" (neutra), "Visitado" / "Falta
  IPTU" / "Margem 34%" (âmbar), "Margem 16%" / "Pauta 03/09" (vermelha), "Teto R$ 214 mil" /
  "Lance 05/09" (verde)

Abaixo do quadro, três cartões de leitura em `grid repeat(3,1fr)`, cada um com tag mono 10px
uppercase colorida, título 14.5px e nota 12.5px `text-soft`: **Trabalho manual** (âmbar) ·
**Ponto cego** (vermelho) · **Próxima automação** (verde). São observações editoriais sobre o
estado da operação, não widgets de dados.

---

## Interações e estados

- **Filtros** aplicam-se imediatamente, em conjunto (AND), sem botão de aplicar. `Limpar
  filtros` volta tudo ao padrão (`MG`, todas as cidades, faixa cheia, desconto 0).
- **Clique na linha da tabela ou no card do funil** abre a ficha do imóvel. `Corta` e
  `Descartar` param a propagação.
- **Cada tecla em um campo de campo** recalcula a conta inteira, o contador de preenchimento, o
  rótulo/cor do botão de avançar e sua nota. Não existe botão de salvar na ficha; assuma
  autosave com debounce (~500ms) e registro no histórico.
- **Origem do dado muda com o input:** digitar torna o campo *manual*; apagar volta para
  *em branco*; aceitar a sugestão torna *automação*.
- **Detalhe da conta** é um toggle local, aberto por padrão.
- **Checklist** é toggle por item, com progresso `n/6`.
- **Hover** existe em toda linha e todo botão (ver cores acima). **Foco** é sempre o outline
  verde de 2px para dentro.
- **Sem carregamento assíncrono no protótipo.** No app real, prever: skeleton na tabela,
  estado de erro no painel de filtros, e um indicador discreto de "salvo" na ficha.
- **Responsivo:** não desenhado. O protótipo é dimensionado para 1440×980 — largura de trabalho
  em desktop. As grades usam `minmax(0,1fr)` e `auto-fit`, então reduzem sem estourar, mas as
  quebras para tablet/mobile precisam de decisão de produto.

## Estado da interface

```
tela            'triagem' | 'ficha' | 'funil'
contaAberta     boolean (padrão true)
busca           { uf, cidade, bairro, precoMin, precoMax, tipos[], financiamento, fgts,
                  descontoMin, semDados }
campos          por chave: { valor: string, origem: 'base'|'manual'|'auto'|'vazio',
                             sugestao?: string }
nota            string (anotações da visita)
check           { matricula, visita, iptu, condominio, edital, comparaveis } : boolean
```

Parâmetros do cenário, hoje expostos como ajustes do protótipo e que no app devem ser
configuração do usuário (com padrão global): **prazo de carregamento** (3–36 meses, padrão 12)
e **comissão do corretor** (0–8%, passo 0,5, padrão 6%). Há também um modo denso da tabela
(padding de linha 13px → 8px).

## Regras de negócio que a interface reflete

- **Piso de margem: 20%.** Abaixo disso a regra é não participar, independente de qualquer
  outro fator.
- **Prazo padrão de carregamento: 12 meses** entre arremate e revenda.
- Dívidas anteriores (IPTU, condomínio, foro/laudêmio) **só entram na conta se o edital as
  passar ao arrematante** — no leilão extrajudicial não há a proteção do Tema 1134 do STJ, que
  vale só para leilão judicial.
- **Campo em branco não é zero.** A interface mostra "em branco", avisa que a conta assume
  zero, e registra quem avançou sem o dado.
- Risco jurídico é corte binário hoje, mas os requisitos pedem **dois sub-scores**: risco de
  nulidade/atraso (aceitável, custa tempo) vs. risco de perda do direito sobre o imóvel
  (usucapião, ocupação de longa data — dealbreaker). **Não implementado na interface ainda.**

## Fórmulas da conta

Ver `BACKEND.md` para as tabelas completas (emolumentos por faixa, alíquotas de ITBI) e a
implementação de referência. Resumo:

```
comissao_leiloeiro = arremate × pct_leiloeiro          (padrão 5%, palpite até vir do edital)
itbi               = arremate × aliquota_municipio     (padrão 3%, palpite se não cadastrada)
registro           = faixa(arremate) na Tabela 4-2026 TJMG, item 5-e
aquisicao          = arremate + comissao_leiloeiro + itbi + registro
dividas            = iptu_atraso + condominio_atraso          (se do arrematante)
posse              = reforma + desocupacao
carregamento       = (iptu_mensal + condominio_mensal) × prazo_meses
investimento       = aquisicao + dividas + posse + carregamento
comissao_corretor  = revenda × pct_corretor            (padrão 6%)
base_ir            = aquisicao + reforma
ganho              = max(0, revenda − comissao_corretor − base_ir)
ir                 = ganho × 0,15
lucro              = revenda − comissao_corretor − ir − investimento
margem             = lucro ÷ investimento              → compara com o piso de 20%
margem_revenda     = lucro ÷ revenda                   (informativa)
```

## Assets

Nenhuma imagem ou ícone. Os únicos glifos são `←`, `↗`, `▾`, `▴`, `✓`, `·`, `→` e `—`, todos
tipográficos. Fontes: Source Serif 4 e IBM Plex Mono, via Google Fonts. Sem emoji.

## Escopo ainda não desenhado

Nesta ordem de prioridade, conforme os requisitos:

1. **Tela de importações** — status e volume de cada carga (Caixa via planilha, Zukerman via
   scraping). É o único lugar onde contagem de importação deve aparecer.
2. **Campos do edital na ficha** — responsabilidade por dívida anterior, imóvel foreiro
   (foro/laudêmio), vaga de garagem com matrícula própria, baixa de ônus.
3. **Dois níveis de risco jurídico** no funil e no score.
4. **Coleta manual guiada** como quarto tipo de dado, com o tutorial passo a passo de IPTU e
   condomínio.
5. **Cenário financiado** ao lado do cenário à vista na conta.
6. **Fluxo de matrícula em dois passos** — matrícula do edital → matrícula de confirmação
   emitida perto da data do leilão (RI Digital), com diff entre as duas.

## Arquivos deste pacote

| Arquivo | O que é |
|---|---|
| `README.md` | este documento — especificação da interface |
| `BACKEND.md` | modelo de dados, API, motor de cálculo, importador, regras |
| `Alvo Leiloes v4.dc.html` | protótipo atual, referência de verdade para o visual |
| `Alvo Leiloes v3.dc.html` | versão anterior (conta simplificada), para histórico |
| `support.js` | runtime do protótipo — presente só para os `.dc.html` abrirem; **não é referência de arquitetura** |
| `requisitos/processo-alvo-leiloes.md` | processo ponta a ponta, fonte das regras de negócio |
| `requisitos/roadmap-mvps.md` | fatiamento em MVPs |

Abra `Alvo Leiloes v4.dc.html` com o `support.js` na mesma pasta. A estrutura e todos os valores
também estão legíveis no próprio arquivo como texto.
