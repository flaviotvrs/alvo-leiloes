# 2. Triagem deve ser o portão de entrada do funil, não o funil listar tudo

> **Correção (depois do item 5 ter sido definido):** este arquivo foi escrito antes de existir
> o item [`05-dados-globais-vs-dados-do-usuario.md`](05-dados-globais-vs-dados-do-usuario.md),
> que corrige `Avaliacao` para ser por (lote, usuário) em vez de por lote. Isso muda **onde** a
> etapa inicial é atribuída: os passos 2 e 3 da seção "Backend" abaixo (mudar o default no
> import/`upsert.py`) estão **superados** — o importador deixa de criar `Avaliacao` (isso vira
> dado global, sem usuário para atribuir). A etapa inicial `TRIAGEM` passa a ser aplicada no
> momento de criação sob demanda descrito no item 5 (`obter_ou_criar_avaliacao`/
> `obter_ou_criar_avaliacoes`), não no importador. O resto deste arquivo (o novo valor de
> enum, `TRANSICOES_VALIDAS`, o filtro do Funil, a tela de Triagem) continua válido como
> escrito.

## Problema

Toda importação cria a `Avaliacao` de cada imóvel já na etapa `nao_avaliado`
(`backend/app/importers/upsert.py:143` — `Avaliacao(lote_id=lote_db.id, etapa=Etapa.NAO_AVALIADO)`),
e a coluna "Não avaliados" do Funil (`backend/app/api/v1/funil.py:22-23,48-59`) lista **todo**
imóvel ativo nessa etapa. Como praticamente nada muda de etapa sozinho, essa coluna hoje é, na
prática, "a base inteira" — se a importação trouxer todos os imóveis do Brasil disponíveis
para leilão, essa coluna cresce sem controle, o que é o problema de performance/usabilidade
relatado.

Além disso, `funil()` (linhas 48-54) busca **todas** as avaliações ativas sem filtrar por
etapa só para montar as colunas e calcular `base_para_aprovados_pct` — ou seja, o problema não
é só visual, é uma query que varre a base inteira a cada carregamento da tela.

## Comportamento esperado

- A Triagem (`frontend/src/pages/Triagem.tsx`) é a tela onde o usuário garimpa a base inteira
  (com os filtros de região, preço, tipo etc. já existentes) e decide, imóvel a imóvel, o que
  entra no funil de aprovação.
- O Funil só deve listar imóveis que o usuário **explicitamente selecionou** na Triagem. A
  coluna "Não avaliados" do funil passa a significar "selecionado, ainda sem pesquisa de
  campo" — não mais "toda a base importada".
- Imóveis recém-importados (ainda não vistos na Triagem) não aparecem em lugar nenhum do
  funil até serem selecionados ou descartados.

## Decisão confirmada com o usuário

Nova etapa do pipeline, anterior a `nao_avaliado`, em vez de um flag booleano separado — isso
reaproveita a máquina de etapas (`Etapa` / `TRANSICOES_VALIDAS`) que já existe no código, em
vez de criar um segundo mecanismo de estado paralelo.

## Design proposto

### Backend

1. **`backend/app/models/enums.py`** — adicionar `TRIAGEM = "triagem"` ao enum `Etapa`, como
   novo primeiro estágio (antes de `NAO_AVALIADO`):
   ```python
   class Etapa(str, Enum):
       TRIAGEM = "triagem"
       NAO_AVALIADO = "nao_avaliado"
       ...
   ```
   Requer migration Alembic para o tipo `etapa` no Postgres (`str_enum`, ver
   `backend/app/models/types.py`).

2. ~~`backend/app/importers/upsert.py:143` — todo imóvel novo nasce em `Etapa.TRIAGEM`~~ —
   **superado pelo item 5**: o importador para de criar `Avaliacao` por completo. `Etapa.TRIAGEM`
   continua sendo o valor certo, mas quem o atribui é `obter_ou_criar_avaliacao`/
   `obter_ou_criar_avaliacoes` (item 5), não o importador. O default do model `Avaliacao.etapa`
   em `backend/app/models/avaliacao.py:31` deve mudar de `Etapa.NAO_AVALIADO` para
   `Etapa.TRIAGEM` mesmo assim, já que é a etapa inicial real agora.

3. **`backend/app/api/v1/avaliacoes.py:26-33`** — `TRANSICOES_VALIDAS` ganha a nova etapa como
   origem:
   ```python
   TRANSICOES_VALIDAS: dict[Etapa, set[Etapa]] = {
       Etapa.TRIAGEM: {Etapa.NAO_AVALIADO, Etapa.DESCARTADO},
       Etapa.NAO_AVALIADO: {Etapa.PESQUISA_CAMPO, Etapa.DESCARTADO},
       ...  # resto inalterado
   }
   ```
   O endpoint genérico `POST /avaliacoes/{id}/etapa` (linhas 149-172) já valida contra esse
   dicionário e já registra `EventoAvaliacao` tipo `ETAPA_ALTERADA` — não precisa de nenhuma
   rota nova para "selecionar para o funil", só virar uma transição `triagem → nao_avaliado`
   através dele.

   O endpoint `POST /avaliacoes/{id}/descartar` (linha 175 em diante) **não** checa
   `TRANSICOES_VALIDAS` — seta `Etapa.DESCARTADO` incondicionalmente — então "Corta" na
   Triagem já funciona a partir de `TRIAGEM` sem nenhuma mudança.

4. **`backend/app/api/v1/funil.py:48-54`** — a query de `avaliacoes_ativas` deve excluir
   `Etapa.TRIAGEM` explicitamente (não só deixar de aparecer nas colunas por não estar em
   `COLUNAS_FUNIL`), para resolver o problema de performance na raiz e para
   `base_para_aprovados_pct` não ficar diluído pelo volume de imóveis ainda não selecionados:
   ```python
   avaliacoes_ativas = (
       db.query(Avaliacao, LoteLeilao, Imovel)
       .join(LoteLeilao, Avaliacao.lote_id == LoteLeilao.id)
       .join(Imovel, LoteLeilao.imovel_id == Imovel.id)
       .filter(LoteLeilao.ativo.is_(True))
       .filter(Avaliacao.etapa != Etapa.TRIAGEM)
       .all()
   )
   ```
   `COLUNAS_FUNIL` em si não precisa mudar (continua começando em `Etapa.NAO_AVALIADO`).
   **Correção:** este filtro também precisa vir acompanhado de `.filter(Avaliacao.usuario_id
   == usuario.id)` — ver item 5, que já traz o trecho completo com as duas condições juntas.

5. ~~`backend/app/api/v1/imoveis.py` — nenhuma mudança necessária~~ — **superado pelo item 5**:
   o endpoint `GET /imoveis` já aceita `etapa: list[Etapa]` como filtro (linha 41 e 78-79) e já
   devolve `etapa` em cada `ImovelListItem`, mas o `join` com `Avaliacao` hoje é `inner` e sem
   filtro de usuário — precisa virar `outerjoin` filtrado pelo usuário atual, com a criação sob
   demanda das avaliações que faltarem na página retornada. Design completo em
   `05-dados-globais-vs-dados-do-usuario.md`. A Triagem só precisa passar `etapa=["triagem"]`
   por padrão (ver Frontend abaixo) — isso continua válido, só a query por trás mudou.

### Frontend

1. **`frontend/src/pages/Triagem.tsx`** — a listagem passa a sempre filtrar por
   `etapa: ["triagem"]` (fixo, não é um filtro que o usuário liga/desliga como
   `sem_dados_campo`) — mesclar isso ao objeto `filtros` enviado para `useImoveis`, mantendo
   os demais filtros (`uf`, `cidade`, `preco_min` etc.) vindos da querystring como hoje.

2. Novo botão de ação por linha, **"Selecionar p/ funil"**, ao lado de "Corta"
   (`frontend/src/pages/Triagem.tsx:230-248`) — chama
   `POST /avaliacoes/{avaliacao_id}/etapa` com `{ etapa: "nao_avaliado" }` e, no sucesso,
   invalida as queries de `imoveis`/`funil`/KPIs para a linha sumir da Triagem (já não bate
   mais o filtro `etapa=triagem`) e passar a aparecer no Funil.

   Alternativa mais enxuta, sem criar um terceiro botão: fazer o botão **"Preencher"**
   existente (que já leva para a Ficha) disparar essa mesma chamada de transição de etapa
   antes de navegar, já que abrir a Ficha para preencher dados É, na prática, selecionar o
   imóvel para o funil. Recomendado por manter a tela com 2 ações por linha (como é hoje) em
   vez de 3 — mas a decisão de UI final (botão dedicado vs. reaproveitar "Preencher") fica a
   critério de quem for implementar; o requisito de negócio é só que a transição
   `triagem → nao_avaliado` aconteça a partir de uma ação explícita na tela de Triagem.

3. **`frontend/src/api/hooks/useTriagemKpis.ts`** — o KPI "Não avaliados" (linha 20,
   `contagem("nao_avaliado", { etapa: "nao_avaliado" })`) hoje mede "quanto falta preencher"
   dentro da própria tela de Triagem. Depois da mudança, como a Triagem só lista itens em
   `etapa=triagem`, esse número deixa de descrever a tela onde está sendo mostrado — passa a
   contar quantos imóveis já foram selecionados para o funil (métrica ainda útil, só que
   merece um rótulo mais claro, ex. "Selecionados p/ funil"). Ajuste de rótulo, não de lógica
   — a chamada em si continua válida.

## Critérios de aceite

- [ ] Importar uma planilha nova: nenhum imóvel aparece no Funil até ser selecionado ou
      descartado na Triagem.
- [ ] Tela de Triagem lista apenas imóveis ainda não triados (`etapa=triagem`), com os filtros
      de região/preço/tipo continuando a funcionar sobre esse subconjunto.
- [ ] Selecionar um imóvel na Triagem → ele desaparece da lista de Triagem e passa a aparecer
      na coluna "Não avaliados" do Funil.
- [ ] "Corta" continua funcionando a partir da Triagem (transição `triagem → descartado`).
- [ ] A query do Funil não varre mais avaliações em `etapa=triagem` — conferir plano de
      execução / contagem de linhas antes/depois com uma base grande simulada.
- [ ] `base_para_aprovados_pct` no Funil passa a ser calculado só sobre imóveis que entraram
      no funil (excluindo o volume em triagem), não mais sobre a base bruta importada.

## Notas / decisões em aberto para quem for implementar

- Seleção em lote (marcar várias linhas da Triagem de uma vez e mandar todas para o funil) não
  está no escopo deste ajuste — cada imóvel é selecionado individualmente, como já é hoje para
  "Corta". Pode virar uma melhoria futura se o volume por sessão de triagem se mostrar alto
  demais para seleção um a um.
- Migration: `Avaliacao.etapa` já tem `index=True` (`backend/app/models/avaliacao.py:31`) —
  adicionar `TRIAGEM` ao enum do Postgres é uma migration de `ALTER TYPE ... ADD VALUE`
  (Alembic) — não precisa recriar a coluna.
