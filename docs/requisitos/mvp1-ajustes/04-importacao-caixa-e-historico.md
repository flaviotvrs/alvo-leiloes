# 4. Tela de importação da planilha da Caixa + histórico

> **Correção (depois do item 5 ter sido definido):** este arquivo foi escrito antes de existir
> o item [`05-dados-globais-vs-dados-do-usuario.md`](05-dados-globais-vs-dados-do-usuario.md).
> Import é dado global — isso não muda nada da mecânica de upsert/inativação/reativação
> descrita abaixo — mas o rastro de auditoria proposto originalmente (reaproveitar
> `EventoAvaliacao`) deixou de fazer sentido, já que essa tabela passa a ser por usuário. A
> seção "`upsert.py`" abaixo já está corrigida inline para usar um novo modelo `EventoLote`,
> em escopo de lote; o resto do arquivo continua válido como escrito. Implementar o item 5
> antes deste.

## O que já existe (não precisa ser construído do zero)

- `POST /importacoes` (`backend/app/api/v1/importacoes.py:32-52`) já recebe um upload, chama
  o importador e devolve o resultado.
- `GET /importacoes` (linha 55-60) já lista o histórico, mais recente primeiro.
- `Importacao` (`backend/app/models/importacao.py`) já guarda `arquivo_nome`, `arquivo_hash`,
  `linhas_lidas`, `criados`, `atualizados`, `inalterados`, `erros` (lista JSON), `status`,
  datas.
- `aplicar_importacao` (`backend/app/importers/upsert.py`) já faz upsert por
  `(fonte, codigo_externo)`, já **nunca** escreve em `campo_avaliacao` (dado manual do usuário
  sempre vence — comentário na linha 32-34), já marca `ativo=False` quando um lote some da
  planilha (linhas 89-91), e já reativa (`lote_existente.ativo = True`, linha 79) quando um
  lote volta a aparecer.
- Dedup: reimportar o mesmo arquivo (mesmo hash) é barato e não reprocessa nada
  (linhas 42-49).

Ou seja, boa parte da mecânica de upsert/inativação/reativação pedida já está correta em
espírito. O que falta é: (a) a tela em si (não existe rota nem página no frontend), (b) alguns
campos/eventos de auditoria que o requisito pede e o código ainda não grava, e (c) — mais
importante — **o parser não funciona contra o arquivo real da Caixa**, confirmado rodando o
código atual contra a amostra fornecida (`docs/requisitos/Planilha_Caixa_Sample.csv`).

## Formato real do arquivo (confirmado contra a amostra)

Testado diretamente: `docs/requisitos/Planilha_Caixa_Sample.csv`, 1030 linhas, 1027 imóveis.

- **Não é XLSX.** É um CSV: texto delimitado por `;`, **codificado em ISO-8859-1 (Latin-1)**,
  não UTF-8. O endpoint atual só aceita `.xlsx`/`.xls` e usa `openpyxl`
  (`backend/app/api/v1/importacoes.py:38`, `backend/app/importers/caixa.py` inteiro) — isso
  precisa mudar para parsing de texto/CSV.
- Estrutura de linhas (1-indexado):
  1. Linha em branco.
  2. Linha de metadado:
     `" Lista de Imóveis da Caixa;;Data de geração:;14/08/2026;;;;;;;"` — o rótulo
     `"Data de geração:"` aparece como um campo, e o campo seguinte é a data, formato
     `DD/MM/AAAA`. Mais robusto localizar pelo rótulo do que fixar índice de coluna.
  3. Cabeçalho (12 colunas): `N° do imóvel;UF;Cidade;Bairro;Endereço;Preço;Valor de
     avaliação;Desconto;Financiamento;Descrição;Modalidade de venda;Link de acesso`
  4. Linha em branco.
  5. em diante: dados, sempre 12 campos por linha (verificado nas 1027 linhas da amostra —
     nenhuma exceção).
- **Todo campo tem espaços em volta** (ex.: `" 8555507642727 "`, `"MG "`,
  `"AGUAS FORMOSAS "`) — precisa de `.strip()` em cada valor lido, não só nos que já são
  tratados hoje.
- **Preço e Valor de avaliação**: formato BR completo — `"25.560,07"` (ponto = milhar, vírgula
  = decimal). O parser atual (`_parse_decimal` em `caixa.py:65-69`) já trata esse formato
  corretamente.
- **Desconto**: formato diferente dos dois campos acima — `"41.91"`, `"68.98"`, `"0.00"` (ponto
  como separador decimal, sem separador de milhar, sem símbolo `%`). O parser atual
  (`_parse_percentual`, linhas 58-63) já lida bem com esse caso por acidente (só mexe em `,` se
  houver, e como não há vírgula aqui o valor passa direto) — **confirmado sem bug**, só deixando
  registrado por que funciona.
- **Financiamento**: string literal `"Sim"` ou `"Não"` — **não** é um booleano nativo de
  planilha. O parser atual faz `bool(campo("aceita_financiamento"))`
  (`caixa.py:127`), que para uma string não vazia como `"Não"` sempre dá `True` — **bug
  confirmado**: hoje, se essa coluna existisse com o nome certo, todo imóvel importado
  entraria como "aceita financiamento", inclusive os que dizem "Não".

## Bugs confirmados rodando o código atual contra a amostra real

Testes feitos diretamente contra `backend/app/importers/parsing.py` e o dicionário `COLUNAS`
de `backend/app/importers/caixa.py` usando cabeçalhos e descrições reais da amostra:

1. **Mapeamento de coluna "Valor de avaliação" ausente.** O cabeçalho real normaliza
   (`normalizar_texto`) para `"valor de avaliacao"`, mas `COLUNAS` só tem a chave `"avaliacao"`
   (`caixa.py`, dicionário `COLUNAS`). Resultado: a coluna nunca é encontrada,
   `lote.valor_avaliacao` fica sempre `None` para toda importação real.

2. **Mapeamento de coluna "Financiamento" errado.** O cabeçalho real normaliza para
   `"financiamento"`, mas `COLUNAS` só tem a chave `"aceita financiamento"`. Resultado: a
   coluna nunca é encontrada — **e** mesmo que fosse corrigida, o valor de texto `"Sim"/"Não"`
   precisa de um parser dedicado (ver acima), não `bool(...)` direto.

3. **Extração de área (total/privativa/terreno) sempre retorna `None` com descrição real.**
   As regexes em `backend/app/importers/parsing.py:14-16` esperam o número **depois** da frase
   e seguido de `m` (padrão "área privativa de 42 m²"). O texto real da Caixa é o oposto — o
   número vem **antes** da frase, sem unidade: `"37.21 de área total, 37.21 de área privativa,
   74.97 de área do terreno"`. Testado diretamente: as três funções (`extrair_area_total`,
   `extrair_area_privativa`, `extrair_area_terreno`) devolvem `None` para toda descrição real
   da amostra. Padrão corrigido e testado contra 4 descrições reais da amostra (todas
   passaram):
   ```python
   _RE_AREA_TOTAL = re.compile(r"(\d+(?:[.,]\d+)?)\s*de\s+[aá]rea\s+total", re.IGNORECASE)
   _RE_AREA_PRIVATIVA = re.compile(r"(\d+(?:[.,]\d+)?)\s*de\s+[aá]rea\s+privativa", re.IGNORECASE)
   _RE_AREA_TERRENO = re.compile(r"(\d+(?:[.,]\d+)?)\s*de\s+[aá]rea\s+d[eo]\s+terreno", re.IGNORECASE)
   ```

4. **Extração de quartos sempre retorna `None` com descrição real.** A regex em
   `parsing.py:17` procura `"quarto"`/`"dormitório"`; o texto real usa a abreviação
   `"qto(s)"` (ex.: `"2 qto(s), WC, 1 sala(s), cozinha"`). Testado e confirmado `None` sempre.
   Padrão corrigido e testado:
   ```python
   _RE_QUARTOS = re.compile(r"(\d+)\s*qto", re.IGNORECASE)
   ```

5. **`inferir_tipo` já funciona corretamente** com a descrição real (testado: `"Casa, 37.21 de
   área total..."` → `TipoImovel.CASA`) — nenhuma mudança necessária ali.

6. **`0.00` nas três áreas provavelmente significa "não se aplica", não "zero literal".**
   Ex.: um Terreno vem com `"0.00 de área total, 0.00 de área privativa, 1000.00 de área do
   terreno"` — a Caixa sempre preenche os três campos, mesmo quando a dimensão não faz sentido
   para aquele tipo de imóvel. Recomendado: nas funções de extração de área, tratar valor
   extraído igual a `0` como `None` (não informado), em vez de gravar `0.00 m²` como se fosse
   um dado real — isso evita poluir `Imovel.area_total_m2` etc. com zeros sem sentido.

## Mudanças necessárias

### Backend — parser (`backend/app/importers/`)

1. **`caixa.py`**: substituir a leitura via `openpyxl` por leitura de texto:
   - Decodificar o arquivo como `ISO-8859-1`.
   - Fazer split por linha e por `;`, com `.strip()` em cada campo.
   - Localizar a linha de metadado pelo rótulo `"Data de geração:"` (não por índice fixo de
     linha, para tolerar uma linha em branco a mais/a menos) e extrair a data (`DD/MM/AAAA`).
   - Localizar a linha de cabeçalho como a primeira linha não vazia que contenha os nomes de
     coluna esperados (ou, mais simples: a linha seguinte à de metadado, pulando linhas em
     branco) e montar `indice_por_campo` a partir dela, do mesmo jeito que já é feito hoje
     (reaproveitar `normalizar_texto`).
   - Corrigir `COLUNAS`: adicionar `"valor de avaliacao": "valor_avaliacao"` e trocar/adicionar
     `"financiamento": "aceita_financiamento"`.
   - Nova função `_parse_bool_sim_nao(valor: str) -> bool` (`"sim"` case-insensitive → `True`,
     qualquer outra coisa → `False`) para a coluna Financiamento.
   - `extrair_lotes_caixa` passa a devolver também a data de geração do arquivo (ex.: retornar
     uma tupla `(lotes, gerado_em)` ou um objeto pequeno, para `importar_caixa` repassar adiante
     até `Importacao.arquivo_gerado_em`).
   - Manter `hash_arquivo` como está (hash em bytes crus, independe de encoding).

2. **`parsing.py`**: corrigir as quatro regexes (área total/privativa/terreno, quartos)
   conforme os padrões testados acima; tratar `0` como `None` nas três funções de área.

3. **`upsert.py`**:
   - `Importacao` ganha (ver seção de modelo abaixo) `inativados` e `reativados` — contar
     cada um no loop de inativação (linhas 89-91) e detectar reativação (capturar
     `estava_inativo = not lote_existente.ativo` **antes** de setar
     `lote_existente.ativo = True`, linha 79).
   - Registrar um evento (não só atualizar o `LoteLeilao`) nos quatro casos hoje silenciosos ou
     parcialmente silenciosos: criação, atualização de campos, inativação, reativação.

     > **Correção (depois do item 5 ter sido definido):** a primeira versão deste documento
     > propunha reaproveitar `EventoAvaliacao` para isso (é o que o evento de criação já faz
     > hoje, em `upsert.py:151-157`). Isso deixou de fazer sentido: pelo item 5
     > (`05-dados-globais-vs-dados-do-usuario.md`), `Avaliacao`/`EventoAvaliacao` passam a ser
     > **por usuário**, e o próprio item 5 remove a criação de `Avaliacao` do importador (a
     > importação não sabe mais para qual usuário gravar esse evento — nem deveria, já que
     > "o lote mudou de preço" é dado global, igual para todo mundo). Esses quatro eventos
     > precisam de uma trilha própria, em escopo de `LoteLeilao`, não de `Avaliacao`.

     **Novo modelo**, `backend/app/models/evento_lote.py`, espelhando `EventoAvaliacao`:
     ```python
     class EventoLote(UUIDPk, Base):
         __tablename__ = "evento_lote"

         lote_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lote_leilao.id"), index=True)
         tipo: Mapped[TipoEvento] = mapped_column(str_enum(TipoEvento, "tipo_evento"))
         importacao_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("importacao.id"))
         ator_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("usuario.id"))
         payload: Mapped[dict] = mapped_column(JSONB, default=dict)
         criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
     ```
     Reaproveita o enum `TipoEvento` já existente (`backend/app/models/enums.py`) —
     `TipoEvento.IMPORTACAO` com um campo `"acao"` no payload distinguindo
     `criado`/`atualizado`/`inativado`/`reativado`, em vez de criar variantes novas de enum:
     - **Criação** (`_criar_lote`, hoje grava em `EventoAvaliacao`): passa a gravar em
       `EventoLote`, `payload={"acao": "criado", "fonte": ..., "codigo_externo": ...}`.
     - **Atualização de campos** (`_atualizar_lote` retorna `mudou=True`, linha 82-83):
       `payload={"acao": "atualizado", "mudancas": {"preco_venda": {"de": ..., "para": ...}, ...}}`
       (mesmo espírito do payload `{chave, de, para}` já usado em
       `backend/app/api/v1/avaliacoes.py:87-93`, só que para vários campos de uma vez).
     - **Inativação**: `payload={"acao": "inativado", "importacao_id": ...}`.
     - **Reativação**: `payload={"acao": "reativado", "importacao_id": ...}`.

     Requer migration Alembic (nova tabela). `ator_id` fica `None` para importações
     automáticas (não há um usuário "agindo") — quando existir cadastro manual de imóvel por
     um administrador (fora de escopo deste item, citado no requisito original como algo
     futuro), esses eventos aí sim teriam `ator_id` preenchido.

     Isso é o que alimenta o "histórico do imóvel" pedido no requisito, na metade que é dado
     global (a outra metade, o que o próprio usuário fez com a análise dele, continua vindo de
     `EventoAvaliacao`, sem mudança). Ver "Frontend — nova tela" e a nota sobre a Ficha
     precisar mesclar as duas trilhas.

### Backend — modelo (`backend/app/models/importacao.py`)

Novos campos:
```python
arquivo_gerado_em: Mapped[date | None] = mapped_column(Date)
inativados: Mapped[int] = mapped_column(Integer, default=0)
reativados: Mapped[int] = mapped_column(Integer, default=0)
```
Requer migration Alembic.

### Backend — API

1. **`backend/app/api/v1/importacoes.py`**:
   - `disparar_importacao`: trocar a checagem de extensão de `.xlsx`/`.xls` para `.csv`
     (a planilha real da Caixa é CSV — ver seção de formato acima). Remover a dependência de
     `openpyxl` deste fluxo se nada mais do backend precisar dela.
   - `_to_dto`: incluir `arquivo_gerado_em`, `inativados`, `reativados`.
2. **`backend/app/schemas/api.py` — `ImportacaoDTO`** (linha 165): adicionar os três campos
   novos.
3. **Novo endpoint** para expor `EventoLote`, ex. em `backend/app/api/v1/imoveis.py` (mesmo
   router de `GET /imoveis/{lote_id}`, já que é o mesmo recurso):
   `GET /imoveis/{lote_id}/eventos` → `list[EventoDTO]` (reaproveitar o schema `EventoDTO` já
   existente, `backend/app/schemas/api.py:133-138` — o formato é o mesmo, só a tabela de
   origem muda). Não precisa checar posse de usuário (é dado global, qualquer usuário
   autenticado pode ver o histórico de mudanças de um imóvel).

### Frontend — nova tela

Não existe hoje rota nem página para importação (`frontend/src/App.tsx` só tem `/triagem`,
`/funil`, `/imoveis/:loteId`; `frontend/src/components/NavBar.tsx` só tem esses dois links de
navegação).

1. **Nova página** `frontend/src/pages/Importacoes.tsx`:
   - Formulário de upload (input de arquivo, aceitando `.csv`) + botão "Importar" → chama
     `POST /importacoes` (já existe, só muda o que o backend aceita).
   - Tabela de histórico abaixo, usando `GET /importacoes` (já existe), com as colunas pedidas
     pelo requisito:
     - Nome do arquivo (`arquivo_nome`)
     - Data de geração do arquivo (`arquivo_gerado_em`, novo campo)
     - Adicionados (`criados`)
     - Modificados (`atualizados`)
     - Inativados (`inativados`, novo campo)
     - Reativados (`reativados`, novo campo — bônus além do que foi pedido explicitamente,
       mas é exatamente o "voltou a ser incluído" do requisito, e é uma informação distinta de
       "modificados")
     - Status (`status`: sucesso/erro) — se `erros` (lista) não estiver vazia mesmo com
       `status=concluida` (o código atual permite conclusão parcial: erros por linha não
       abortam a carga, `upsert.py:88-89`), sinalizar isso visualmente (ex. badge "concluída
       com N erros"), não só olhar o campo `status`.
     - Detalhe do erro — ao clicar/expandir uma linha com erros, mostrar o conteúdo de
       `erros` (lista de `{codigo_externo, erro}`).
2. **Rota nova** em `frontend/src/App.tsx`: `<Route path="/importacoes" element={<Importacoes />} />`.
3. **Link de navegação novo** em `frontend/src/components/NavBar.tsx`, ao lado de "Triagem" e
   "Funil de aprovação".
4. **`frontend/src/api/types.ts`**: refletir os três campos novos de `ImportacaoDTO`.
5. **`frontend/src/pages/Ficha.tsx`** — a linha do tempo de histórico já existente
   (`useEventos`, linha 236, renderizada a partir da linha 542) hoje só busca
   `GET /avaliacoes/{id}/eventos`. Depois deste item, o histórico de um imóvel tem duas fontes
   (a trilha global de `EventoLote` — criado/atualizado/inativado/reativado pela importação —
   e a trilha por usuário de `EventoAvaliacao` — campo preenchido, etapa mudou, descarte). A
   Ficha precisa buscar as duas (`GET /imoveis/{lote_id}/eventos` além do que já busca),
   mesclar por `criado_em` e renderizar como uma linha do tempo só. `textoEvento`
   (`Ficha.tsx:565`) precisa dos casos novos (`acao: criado/atualizado/inativado/reativado`)
   além dos que já trata.

## Critérios de aceite

- [ ] Importar `docs/requisitos/Planilha_Caixa_Sample.csv` (ou um arquivo real equivalente)
      completa com sucesso, sem cair nos bugs listados acima — `valor_avaliacao`,
      `aceita_financiamento`, área (total/privativa/terreno) e quartos vêm preenchidos
      corretamente para os imóveis cuja descrição traz essa informação.
- [ ] A tela de Importações mostra o histórico com todas as colunas pedidas, incluindo data de
      geração do arquivo extraída corretamente da planilha.
- [ ] Reimportar o mesmo arquivo (mesmo conteúdo) não duplica nada e não reprocessa (dedup por
      hash já existente).
- [ ] Reimportar uma versão da planilha com um imóvel a menos marca esse imóvel como inativo
      na base, sem apagar nenhuma análise/campo preenchido manualmente, e registra um evento
      de inativação no histórico do imóvel.
- [ ] Reimportar depois com esse mesmo imóvel de volta reativa o imóvel (volta a `ativo=True`)
      preservando toda a análise manual anterior, e registra um evento de reativação.
- [ ] Reimportar uma versão com um imóvel que teve o preço alterado atualiza só os campos que
      mudaram, sem tocar em `campo_avaliacao` (dado manual do usuário), e registra um evento
      com o que mudou.
- [ ] Um arquivo com uma linha malformada não derruba a importação inteira — as linhas boas
      são processadas, e a linha com erro aparece detalhada no histórico.

## Decisões em aberto para quem for implementar

- O requisito original também fala em detectar "sucesso ou erro" no nível da importação como
  um todo. O modelo atual (`StatusImportacao`: `processando`/`concluida`/`falhou`) não
  distingue "concluída sem nenhum erro" de "concluída com alguns erros de linha" — a
  recomendação acima é resolver isso na UI (badge quando `erros` não está vazio), sem mexer no
  enum, mas dá pra reconsiderar se ficar confuso na prática.
- Zukerman (segunda fonte de leilão do MVP1, via scraping — ver `roadmap-mvps.md`) está fora
  do escopo deste item: este documento cobre só o importador de planilha da Caixa.
