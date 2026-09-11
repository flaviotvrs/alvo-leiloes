# Backend: Alvo Leilões — MVP 1

Complemento do `README.md` (interface). Escopo aqui: modelo de dados, importador, motor de
cálculo determinístico, API que a interface consome, e o que precisa ficar pronto agora para
não travar os MVPs seguintes.

## Escopo do MVP 1

Dentro: ingestão de imóveis (planilha da Caixa; scraping Zukerman como segundo conector),
armazenamento com procedência por campo, motor de cálculo de viabilidade com as tabelas de
emolumentos de MG e ITBI, coleta manual guiada para os inputs sem automação viável, funil de
etapas e trilha de auditoria.

Fora, propositalmente: matrícula, processos judiciais, checklist jurídico, score consolidado,
checklist do dia do leilão, pós-arremate. Não construa abstração de agentes agora — mas deixe
os ganchos apontados na seção "Preparar para os MVPs 2–4".

## Princípios de arquitetura

1. **`imovel_id` estável desde já.** Chave interna própria (UUID), nunca o número do leiloeiro.
   Reimportar a mesma planilha atualiza o registro existente; não cria outro. Os MVPs seguintes
   vão pendurar extrações de agentes nesse mesmo id.
2. **Procedência por campo, não por registro.** Cada valor guarda origem, quem preencheu,
   quando, e a fonte declarada. É o que a interface pinta de cinza/verde/âmbar/tracejado.
3. **O cálculo é determinístico e reprodutível.** Nenhum LLM na conta. Toda execução guarda os
   parâmetros e as versões de tabela usadas, para que uma conta antiga possa ser reexplicada.
4. **Palpite é um dado de primeira classe.** O motor devolve, por linha, se o valor foi
   confirmado ou assumido, e qual campo o usuário deve preencher para confirmar.
5. **Ausente ≠ zero.** `null` é ausência. A conta trata `null` como zero para poder fechar, mas
   marca a linha como incompleta e propaga isso até o veredito.

## Modelo de dados

Postgres como referência. Nomes em snake_case.

### `imovel`

Identidade e fatos estruturais do imóvel, independentes de leilão.

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | uuid PK | o `imovel_id` estável |
| `uf` | char(2) | |
| `cidade` | text | normalizada (sem acento variável, casing consistente) |
| `bairro` | text | |
| `endereco` | text | como veio da fonte |
| `tipo` | enum | `casa` `apartamento` `terreno` `loja` `outro` |
| `area_total_m2` | numeric | |
| `area_privativa_m2` | numeric | |
| `area_terreno_m2` | numeric | |
| `quartos` | int | |
| `descricao_oficial` | text | texto da fonte, preservado |
| `inscricao_municipal` | text nullable | número de inscrição para consulta de IPTU — **[TBD nos requisitos]** de onde vem (edital, matrícula ou consulta na prefeitura) |
| `criado_em` / `atualizado_em` | timestamptz | |

### `lote_leilao`

Um imóvel pode voltar a leilão. A oferta é que tem preço e datas.

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | uuid PK | |
| `imovel_id` | uuid FK | |
| `fonte` | enum | `caixa` `zukerman` |
| `codigo_externo` | text | nº do imóvel no leiloeiro; único por fonte |
| `modalidade` | text | "Venda Direta Online", "Licitação Aberta", "Leilão SFI" |
| `preco_venda` | numeric | valor mínimo / de arremate pretendido |
| `valor_avaliacao` | numeric | |
| `desconto_pct` | numeric | como publicado pela fonte; não recalcular |
| `aceita_financiamento` | boolean | |
| `aceita_fgts` | boolean nullable | **não vem na planilha da Caixa** — nasce nulo, é dado manual |
| `praca_1_valor` / `praca_1_data` | numeric / date | |
| `praca_2_valor` / `praca_2_data` | numeric / date | |
| `url_fonte` | text | link para a página do imóvel |
| `importacao_id` | uuid FK | carga que trouxe ou atualizou este lote |
| `ativo` | boolean | falso quando desaparece da planilha seguinte |

Constraint: `unique (fonte, codigo_externo)`.

### `avaliacao`

O trabalho do usuário sobre um lote. É o agregado que a ficha edita.

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | uuid PK | |
| `lote_id` | uuid FK | |
| `etapa` | enum | `nao_avaliado` `pesquisa_campo` `analise_financeira` `decisao` `aprovado_lance` `descartado` |
| `responsavel_id` | uuid FK | |
| `etapa_desde` | timestamptz | alimenta "há 2 dias nesta etapa" e o tempo médio |
| `motivo_descarte` | text nullable | |
| `teto_lance` | numeric nullable | preenchido na etapa de aprovação |
| `anotacoes` | text | anotações da visita |
| `checklist` | jsonb | `{ matricula: bool, visita: bool, iptu: bool, condominio: bool, edital: bool, comparaveis: bool }` |

Regra: criar a `avaliacao` no momento da importação, em `nao_avaliado`. A contagem de
"Não avaliados" da interface é `count(etapa = 'nao_avaliado')` — nunca uma contagem de
importação.

### `campo_avaliacao`

Uma linha por campo preenchido à mão. É o coração da procedência.

| Coluna | Tipo | Nota |
|---|---|---|
| `id` | uuid PK | |
| `avaliacao_id` | uuid FK | |
| `chave` | text | ver catálogo abaixo |
| `valor_numerico` | numeric nullable | |
| `valor_texto` | text nullable | para enums (ocupação, FGTS) |
| `origem` | enum | `base` `manual` `coleta_guiada` `automacao` |
| `fonte_declarada` | text nullable | "site da prefeitura, protocolo 4471", "3 anúncios na mesma rua", "administradora Lopes" |
| `preenchido_por` | uuid FK nullable | |
| `preenchido_em` | timestamptz | |
| `sugestao_valor` | numeric nullable | valor proposto por automação, ainda não aceito |
| `sugestao_origem` | text nullable | qual agente sugeriu |

Constraint: `unique (avaliacao_id, chave)`.

**Catálogo de chaves** (as onze da ficha):

| Chave | Tipo | Origem esperada no MVP 1 | Entra na conta como |
|---|---|---|---|
| `aceita_fgts` | enum | manual | não entra (filtro de triagem) |
| `valor_mercado` | numeric | manual → automação no MVP 2 | valor de revenda |
| `itbi_aliquota_pct` | numeric | manual | sobrescreve a tabela de ITBI |
| `comissao_leiloeiro_pct` | numeric | manual (do edital) | percentual da comissão |
| `iptu_atraso` | numeric | coleta guiada | dívida assumida |
| `condominio_atraso` | numeric | manual (administradora) | dívida assumida |
| `iptu_mensal` | numeric | coleta guiada | carregamento |
| `condominio_mensal` | numeric | manual (administradora) | carregamento |
| `ocupacao` | enum | manual | não entra (contexto de risco) |
| `reforma` | numeric | manual | recuperação + base do IR |
| `desocupacao` | numeric | manual | recuperação |

Enums: `ocupacao` ∈ {`nao_verificado`, `desocupado`, `ocupado_mutuario`, `ocupado_terceiros`,
`locado_com_contrato`}. `aceita_fgts` ∈ {`nao_verificado`, `aceita`, `nao_aceita`}.

Campos já previstos nos requisitos e **fora do MVP 1** (não crie colunas agora, mas conheça o
destino): responsabilidade por dívida anterior (do edital), imóvel foreiro + foro/laudêmio,
vaga de garagem com matrícula própria, responsável pela baixa de ônus.

### `evento_avaliacao`

Trilha de auditoria. Alimenta o "Histórico do registro" da ficha.

`id`, `avaliacao_id`, `tipo` (`importacao` `campo_alterado` `etapa_alterada` `calculo`
`descarte` `sugestao_aceita`), `ator_id` nullable (nulo = sistema), `payload` jsonb com
`{ chave, de, para }`, `criado_em`.

Regra que a interface expõe: mudança de valor guarda **antes e depois**
("Ocupação alterada de 'Não verificado' para 'Ocupado — antigo mutuário'"). E avançar etapa com
campo em branco grava explicitamente quem decidiu sem o dado.

### `importacao`

`id`, `fonte`, `arquivo_nome`, `arquivo_hash`, `linhas_lidas`, `criados`, `atualizados`,
`inalterados`, `erros` jsonb, `iniciada_em`, `concluida_em`, `status`
(`processando` `concluida` `falhou`), `executada_por`.

É a tabela que sustenta a futura tela de Importações — o único lugar do produto onde volume e
status de importação aparecem.

### Tabelas de referência

`itbi_municipio`: `uf`, `cidade`, `aliquota_pct`, `fonte` (`legislacao` `agregador`),
`confianca` (`confirmada` `a_confirmar` `desconhecida`), `observacao`, `atualizado_em`.

`emolumento_faixa`: `tabela` (`tjmg_4_2026`), `item` (`5e`), `limite_superior`, `valor`,
`vigencia_inicio`, `vigencia_fim`. Versionada — uma conta antiga deve poder ser reexplicada com
a tabela vigente na data.

`parametro_usuario`: `usuario_id`, `prazo_carregamento_meses` (padrão 12),
`comissao_corretor_pct` (padrão 6), `piso_margem_pct` (padrão 20), `ir_aliquota_pct` (padrão 15),
`itbi_aliquota_padrao_pct` (padrão 3), `comissao_leiloeiro_padrao_pct` (padrão 5).

Os quatro últimos são os **valores de palpite**. Ficarem em tabela, e não no código, é o que
permite a interface dizer "usando palpite de 3%" com um número que o usuário pode mudar.

## Dados de referência a carregar

### Alíquotas de ITBI (levantamento inicial)

| Município | Alíquota | Confiança |
|---|---|---|
| Belo Horizonte | 3% | confirmada em legislação municipal (há isenção para imóvel de baixo valor e faixa reduzida de 1,5% no 1º imóvel — **não modelado no MVP 1**) |
| Contagem | 3% | agregador, a confirmar |
| Betim | 3% | agregador, a confirmar |
| Sete Lagoas | 2,5% | agregador, a confirmar |
| Juatuba, Mateus Leme, Igarapé, Lagoa Santa, Florestal, Itaúna | desconhecida | checar na prefeitura |

Município sem alíquota cadastrada usa `itbi_aliquota_padrao_pct` (3%) e a linha da conta volta
marcada como palpite. O caminho de correção é o usuário digitar a alíquota no campo
`itbi_aliquota_pct` da ficha — o que vale só para aquela avaliação. Ofereça, no admin,
"promover este valor para a tabela do município".

### Emolumentos — Tabela 4-2026 TJMG, item 5-e

Escritura pública / instrumento particular / título judicial com conteúdo financeiro. Valor
final ao usuário, já com ISSQN. Usada para o custo de registro.

| Limite superior (R$) | Valor (R$) |
|---|---|
| 1.400,00 | 227,95 |
| 2.720,00 | 371,84 |
| 5.440,00 | 538,85 |
| 7.000,00 | 745,98 |
| 14.000,00 | 994,78 |
| 28.000,00 | 1.285,21 |
| 42.000,00 | 1.597,11 |
| 56.000,00 | 1.989,94 |
| 70.000,00 | 2.404,60 |
| 105.000,00 | 3.026,34 |
| 140.000,00 | 3.839,67 |
| 175.000,00 | 4.106,03 |
| 210.000,00 | 4.372,88 |
| 280.000,00 | 4.914,86 |
| 350.000,00 | 5.050,25 |
| 420.000,00 | 5.186,26 |
| 560.000,00 | 5.677,78 |
| 700.000,00 | 5.989,84 |
| 840.000,00 | 6.302,53 |
| 1.120.000,00 | 7.046,73 |
| 1.400.000,00 | 7.632,83 |
| 1.680.000,00 | 8.219,92 |
| 3.200.000,00 | 8.808,22 |
| 3.700.000,00 | 13.034,69 |
| acima de 3.700.000,00 | 13.034,69 + faixas adicionais de R$ 500.000 (Nota XVII, regra progressiva) |

Duas ressalvas dos requisitos, ambas para expor na interface e não esconder no código:

- **Acima de R$ 3.700.000** a tabela é progressiva por faixas adicionais de R$ 500.000. Trate
  como caso especial: calcule pelo teto conhecido e marque a linha como **estimativa**. Os
  imóveis de interesse são de faixa popular.
- **A base de cálculo oficial é o valor da avaliação da repartição fazendária**, não o valor de
  arremate (Nota VII da tabela). O MVP usa o arremate como proxy — mais fácil de obter — e a
  linha deve dizer isso.

## Motor de cálculo

Função pura, sem I/O. Recebe um snapshot; devolve o resultado e a explicação linha a linha. A
interface não recalcula nada por conta própria: ela renderiza o que este motor devolve.

### Entrada

```ts
type Snapshot = {
  arremate: number;
  cidade: string; uf: string;
  campos: Record<string, { valor: number | null; origem: Origem }>;
  parametros: {
    prazoCarregamentoMeses: number;      // 12
    comissaoCorretorPct: number;         // 6
    pisoMargemPct: number;               // 20
    irAliquotaPct: number;               // 15
    itbiAliquotaPadraoPct: number;       // 3
    comissaoLeiloeiroPadraoPct: number;  // 5
  };
  tabelas: { itbi: ItbiTabela; emolumentos: EmolumentoTabela };
  dividasSaoDoArrematante: boolean;      // do edital; default true (conservador)
};
```

### Saída

```ts
type Linha = {
  chave: string; grupo: Grupo; rotulo: string;
  valor: number | null;                  // null = campo em branco
  assumido: boolean;                     // true = palpite
  fonte: string;                         // texto exibido no hint
  campoParaConfirmar?: string;           // qual campo o usuário deve preencher
};

type Resultado = {
  grupos: { grupo: Grupo; subtotal: number; linhas: Linha[] }[];
  aquisicao: number; dividas: number; posse: number; carregamento: number;
  investimento: number;
  comissaoCorretor: number; ganhoCapital: number; ir: number;
  lucro: number | null;
  margemInvestimentoPct: number | null;
  margemRevendaPct: number | null;
  veredito: 'aprovado' | 'reprovado' | 'incompleto';
  camposEmBranco: string[];
  premissas: string[];                   // toda linha assumida, em texto
  versaoTabelaEmolumentos: string;
  calculadoEm: string;
};
```

`veredito` é `incompleto` enquanto `valor_mercado` for nulo — sem revenda estimada não existe
margem. Com margem calculada: `aprovado` se `margemInvestimentoPct >= pisoMargemPct`, senão
`reprovado`. O veredito financeiro **não** é a decisão final: no MVP 4 ele é uma das entradas do
agente juiz.

### Fórmulas

```
pctLeiloeiro  = campos.comissao_leiloeiro_pct ?? param.comissaoLeiloeiroPadraoPct
                (assumido quando vem do padrão)
pctItbi       = campos.itbi_aliquota_pct
                ?? tabelaItbi[uf][cidade]?.aliquota
                ?? param.itbiAliquotaPadraoPct
                (assumido só no último caso)

comissaoLeiloeiro = round(arremate × pctLeiloeiro / 100)
itbi              = round(arremate × pctItbi / 100)
registro          = faixaEmolumento(arremate)
aquisicao         = arremate + comissaoLeiloeiro + itbi + registro

dividas      = dividasSaoDoArrematante ? (iptu_atraso ?? 0) + (condominio_atraso ?? 0) : 0
posse        = (reforma ?? 0) + (desocupacao ?? 0)
carregamento = ((iptu_mensal ?? 0) + (condominio_mensal ?? 0)) × prazoCarregamentoMeses
investimento = aquisicao + dividas + posse + carregamento

revenda           = valor_mercado
comissaoCorretor  = round(revenda × comissaoCorretorPct / 100)
baseIR            = aquisicao + (reforma ?? 0)
ganhoCapital      = max(0, revenda − comissaoCorretor − baseIR)
ir                = round(ganhoCapital × irAliquotaPct / 100)

lucro                 = revenda − comissaoCorretor − ir − investimento
margemInvestimentoPct = lucro / investimento × 100
margemRevendaPct      = lucro / revenda × 100
```

Notas de implementação:

- **Não use ponto flutuante para dinheiro.** Inteiro em centavos ou decimal exato. Arredonde só
  na fronteira de cada linha, com `ROUND_HALF_UP`, e devolva inteiros em reais para exibição.
- **IR:** o MVP aplica 15% fixo. A faixa real é 15% a 22,5% conforme o ganho, e há discussão de
  base de cálculo (custo de aquisição admissível) que os requisitos deixam como TBD. Deixe a
  alíquota em parâmetro e a fórmula isolada em uma função própria; quando as faixas entrarem, só
  ela muda.
- **Base do IR** exclui carregamento, desocupação e dívidas anteriores — inclui aquisição e
  reforma. Se essa premissa mudar após consulta contábil, é um ponto único no código.
- Grave um `resultado_calculo` por execução relevante (entrada da avaliação em análise
  financeira, mudança de etapa, fechamento de decisão), com snapshot de entrada e versões de
  tabela. Não precisa persistir cada tecla — recalcule sob demanda para a ficha.

## Importador

Um conector por fonte, sem tentar reaproveitar parsing entre elas: os requisitos são explícitos
em que Zukerman não reaproveita a planilha da Caixa.

**Caixa (planilha).** Upload manual ou coleta agendada. Passos: hash do arquivo (dedup de carga
idêntica); parse com mapeamento declarativo coluna → campo; normalização de cidade/bairro/tipo e
parse da descrição para área e quartos; upsert por `(fonte, codigo_externo)`; marcar `ativo =
false` nos lotes ausentes da carga nova; criar `avaliacao` em `nao_avaliado` para lote novo;
gravar `evento_avaliacao` tipo `importacao`; fechar `importacao` com contadores e erros por
linha.

Regras: importação **nunca** sobrescreve `campo_avaliacao` (dado do usuário ganha sempre);
divergência entre planilha e dado manual é sinalizada, não resolvida automaticamente;
`aceita_fgts` nasce nulo porque a planilha não traz esse campo.

**Zukerman (scraping).** Segundo conector, mesma superfície de saída (lista de lotes
normalizados) e mesmo destino. Isolar o HTML frágil em uma camada fina de extração, com
snapshot do HTML original guardado para depuração.

## Coleta manual guiada

Os requisitos separam isso como um tipo próprio de tarefa: nem coleta automática, nem decisão
humana. Vale para `iptu_atraso`, `iptu_mensal` (site da prefeitura, por número de inscrição) e
`condominio_atraso`, `condominio_mensal` (administradora ou síndico).

Backend: tabela `tutorial_coleta` com `cidade` (nullable = genérico), `chave_campo`, `passos`
jsonb (`[{ texto, url? }]`), `url_base`. Endpoint que devolve o tutorial da cidade do imóvel
mais o número de inscrição, se houver. Ao salvar, o campo é gravado com `origem =
'coleta_guiada'` e `fonte_declarada` obrigatória.

Como os requisitos observam, com ~10 municípios de interesse compensa cadastrar o tutorial (e
depois scrapers pontuais por município) em vez de construir um agente de navegação genérico.

## API

REST, JSON, autenticado. Prefixo `/api/v1`.

| Método | Rota | Uso |
|---|---|---|
| `GET` | `/imoveis` | tabela de triagem; filtros abaixo; paginação por cursor; `sort=desconto_desc` (padrão) |
| `GET` | `/imoveis/facetas` | cidades e tipos distintos + contagens, para popular os filtros |
| `GET` | `/imoveis/:loteId` | ficha completa: lote, imóvel, avaliação, campos com procedência, resultado do cálculo, checklist, histórico |
| `PATCH` | `/avaliacoes/:id/campos/:chave` | grava um campo (`valor`, `fonte_declarada`); devolve o resultado do cálculo recalculado |
| `POST` | `/avaliacoes/:id/campos/:chave/aceitar-sugestao` | aceita valor de automação; origem passa a `automacao` |
| `PATCH` | `/avaliacoes/:id` | anotações, checklist, teto de lance |
| `POST` | `/avaliacoes/:id/etapa` | move etapa (`{ etapa, motivo? }`); valida transição; grava evento com os campos em branco no momento |
| `POST` | `/avaliacoes/:id/descartar` | `{ motivo }` |
| `GET` | `/avaliacoes/:id/calculo` | recalcula sem persistir (usado no debounce da ficha) |
| `GET` | `/avaliacoes/:id/eventos` | histórico do registro |
| `GET` | `/funil` | colunas com contagem, cards por etapa, e as duas métricas do topo |
| `GET` | `/tutoriais/:chave?cidade=` | passos da coleta guiada |
| `POST` | `/importacoes` | dispara/registra carga (multipart para a planilha) |
| `GET` | `/importacoes` | histórico de cargas — base da futura tela de Importações |
| `GET` | `/parametros` / `PATCH` `/parametros` | prazo de carregamento, % corretor, piso de margem, valores de palpite |
| `GET` | `/referencias/itbi` / `PATCH` `/referencias/itbi/:id` | manutenção da tabela de alíquotas |

Filtros de `GET /imoveis`, espelhando o painel: `uf`, `cidade`, `bairro` (substring
case-insensitive), `preco_min`, `preco_max`, `tipo` (repetível), `financiamento`
(`indiferente|aceita|nao_aceita`), `fgts` (`indiferente|aceita|nao_aceita`), `desconto_min`,
`sem_dados_campo` (bool), `etapa` (repetível).

Resposta de lista traz, por linha: identificação, preço, avaliação, desconto, modalidade,
financiamento, FGTS, e um resumo de preenchimento `{ preenchidos: 3, total: 5, faltando:
['condominio','reforma'] }` — é o que renderiza os cinco quadrados e a nota "falta condomínio e
reforma". O backend decide quais cinco campos contam; não deixe essa regra no cliente.

Cada valor de campo volta como `{ valor, origem, fonte_declarada, preenchido_por,
preenchido_em, sugestao }` — a interface depende disso para pintar a procedência.

Performance: a triagem roda sobre a base inteira com múltiplos filtros. Índices em
`(uf, cidade)`, `bairro` (trigram), `preco_venda`, `desconto_pct`, `avaliacao.etapa`, e um
índice parcial para `ativo = true`.

## Preparar para os MVPs 2–4

Sem construir nada disso agora:

- **MVP 2 (agente de valor de mercado):** o campo `valor_mercado` já tem `sugestao_valor` e
  `sugestao_origem`, e o endpoint de aceitar sugestão já existe. O agente vai escrever sugestão,
  nunca sobrescrever o valor do usuário — é a regra que a interface mostra hoje com o botão
  "Usar valor da automação".
- **MVP 3 (agente de matrícula):** as extrações documentais vão pendurar em `imovel_id`. Não
  modele campos de matrícula agora.
- **MVP 4 (agente juiz):** a saída do motor de cálculo é uma das entradas do juiz. Mantenha
  `Resultado` serializável, com `premissas` e `camposEmBranco` explícitos — o juiz precisa saber
  no que a conta se apoiou. O juiz começa como função determinística: margem ≥ 20% e ausência de
  dealbreaker jurídico (usucapião / ocupação de longa data); riscos de nulidade por vício formal
  são aceitáveis, custam tempo. Só vira LLM se a ponderação ficar complexa.

## Regras de negócio (referência rápida)

- Piso de margem **20%**. Abaixo, não participa, independente de qualquer outro fator.
- Prazo padrão de carregamento **12 meses**, parametrizável.
- Dívidas anteriores (IPTU, condomínio, foro/laudêmio) entram na conta **só se o edital as
  passar ao arrematante**. No leilão extrajudicial não existe a proteção do Tema 1134 do STJ,
  que vale só para leilão judicial. Enquanto o edital não for lido, assuma que são do
  arrematante (conservador) e marque como premissa.
- Escopo jurídico: alienação fiduciária, Lei 9.514/97. Desde a Lei 13.465/2017 não há purgação
  da mora após a consolidação da propriedade, apenas direito de preferência.
- Campo em branco não é zero: conta fecha, mas registra lacuna e quem avançou sem o dado.
- Dado do usuário sempre vence dado importado ou sugerido.

## Testes que valem a pena escrever primeiro

1. **Faixas de emolumento nas bordas:** 1.400,00 / 1.400,01 / 3.700.000,01 (caso progressivo).
2. **Precedência da alíquota de ITBI:** campo digitado > tabela do município > padrão de 3%, e o
   `assumido` correto em cada caso.
3. **Cenário completo com os números da ficha do protótipo:** arremate 49.647, ITBI a 3%,
   registro pela faixa de 56.000, IPTU em atraso 3.400, condomínio em atraso nulo, IPTU mensal
   285, condomínio mensal nulo, reforma 22.000, desocupação 15.000, revenda 190.000, corretor 6%,
   prazo 12 meses. Esperado: aquisição 55.608, dívidas 3.400, posse 37.000, carregamento 3.420,
   investimento 99.428, comissão do corretor 11.400, ganho 100.992, IR 15.149, lucro 64.023,
   margem sobre investimento ≈ 64,4%, margem sobre a revenda ≈ 33,7%, veredito `aprovado`.
   Fixe os parâmetros no teste — o número muda com o prazo de carregamento.
4. **Reimportação idempotente:** mesma planilha duas vezes não duplica lote nem apaga campo
   manual; lote ausente na carga nova vira `ativo = false`.
5. **Ausente ≠ zero:** condomínio nulo produz `veredito` com lacuna registrada e linha
   marcada, não `R$ 0` silencioso.
6. **Transição de etapa com lacuna** grava evento com a lista de campos em branco.
