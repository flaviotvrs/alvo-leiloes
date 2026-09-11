# 5. Separar dados globais do sistema de dados por usuário

> Item acrescentado depois dos itens 1-4, numa mensagem de acompanhamento — mas é o mais
> **fundamental** dos cinco: os itens 2, 3 e 4 mexem todos em `Avaliacao` (etapa do funil,
> margem desejada, teto de lance) e no rastro de auditoria da importação, e a modelagem certa
> desses dois pontos depende diretamente da separação descrita aqui. **Ver "Ordem sugerida de
> implementação" no final deste arquivo** — isso afeta a ordem em que os outros itens devem
> ser feitos, e corrige duas decisões de design tomadas nos itens 2 e 4 antes deste item
> existir (ver as notas de "Correção" no topo de cada um).

## O princípio

- **Dado global/do sistema**: tudo que descreve o imóvel e a oferta de leilão em si —
  endereço, área, tipo, preço, desconto, condições de pagamento, e (futuramente) cadastro
  manual por um administrador ou imóveis de outros leiloeiros. É **o mesmo para todo mundo**
  que olhar aquele imóvel.
- **Dado por usuário**: tudo que é fruto da análise de uma pessoa — valor de mercado que ela
  estimou, dívidas de IPTU/condomínio que ela apurou, ocupação que ela verificou, anotações,
  teto de lance, margem de lucro desejada, e **em qual etapa do funil aquele imóvel está**
  (isso inclui já ter sido selecionado para o funil ou descartado). Dois usuários olhando o
  mesmo imóvel podem ter conclusões completamente diferentes — inclusive um pode ter
  descartado e o outro ter aprovado para lance.

## Problema no modelo atual

`Avaliacao` (`backend/app/models/avaliacao.py`) hoje é **uma linha por lote de leilão**, ponto
— não uma linha por (lote, usuário). Toda a análise (etapa, checklist, `teto_lance`,
anotações) e, por extensão, tudo que pendura nela (`CampoAvaliacao`, `EventoAvaliacao`) é hoje
efetivamente **global**: se dois usuários existissem, os dois estariam literalmente editando a
mesma linha, vendo a mesma etapa, sobrescrevendo os campos um do outro. O sistema documenta
isso como uma limitação conhecida e deliberada do MVP1
(`backend/app/api/deps.py:22-25`: "Autenticação mínima do MVP1... não é multiusuário, fora de
escopo") — mas o *modelo de dados* em si não distingue as duas naturezas de dado, o que deixa
uma dívida técnica que fica bem mais cara de pagar depois que a base de imóveis já estiver
grande.

`Imovel`, `LoteLeilao` e `Importacao` já estão corretamente modelados como globais — nenhuma
mudança neles é necessária. `ParametroUsuario` já está corretamente modelado como por usuário
(tem `usuario_id`, `unique=True`) — também sem mudança.

## Decisões confirmadas com o usuário

- **Escopo agora**: só corrigir o *modelo de dados* para nascer pronto para múltiplos
  usuários — `Avaliacao` passa a ser por (lote, usuário). Autenticação real (login, múltiplas
  contas de fato logando e usando o sistema) continua fora do MVP1, exatamente como está hoje
  (token fixo, um usuário seed) — isso é trabalho futuro, não deste item.
- **Como a avaliação de um usuário nasce**: sob demanda, no primeiro acesso daquele usuário
  àquele imóvel (na Triagem ou na Ficha) — não mais no momento da importação, e não como um
  passo de provisionamento separado por usuário.

## Design proposto

### `backend/app/models/avaliacao.py`

```python
usuario_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("usuario.id"), index=True)
```
com
```python
__table_args__ = (UniqueConstraint("lote_id", "usuario_id", name="uq_avaliacao_lote_usuario"),)
```

**Remover `responsavel_id`.** Hoje é um campo nullable, nunca de fato atribuído por nenhuma
ação do usuário (só setado à mão nos seeds — `backend/app/seeds/seed.py:70,83,89,102,117`) e
usado em exatamente um lugar de lógica real: `snapshot.py:34`, para descobrir de quem são os
`ParametroUsuario` a aplicar no cálculo. Com `usuario_id` passando a existir como o dono de
fato da avaliação, `responsavel_id` vira um segundo campo "de quem é isso" redundante e mais
confuso que o primeiro — remover em vez de manter os dois. Se no futuro fizer sentido um
conceito de "responsável designado" diferente do "dono" (ex. equipe compartilhando uma conta),
isso é uma feature nova a desenhar quando existir, não algo para manter como campo morto hoje.

### Migration (Alembic)

1. Adicionar `usuario_id` como nullable.
2. Backfill: `UPDATE avaliacao SET usuario_id = (SELECT id FROM usuario ORDER BY criado_em LIMIT 1) WHERE usuario_id IS NULL`
   — atribui todas as avaliações hoje existentes ao único usuário seed, preservando o
   histórico atual sem perda de dado.
3. Alterar `usuario_id` para `NOT NULL`.
4. Adicionar a `UniqueConstraint("lote_id", "usuario_id")`.
5. Remover a coluna `responsavel_id` (e sua FK).

### Criação sob demanda (substitui a criação no import)

Novo helper, ex. `backend/app/services/avaliacoes.py`:

```python
def obter_ou_criar_avaliacao(db: Session, lote_id: UUID, usuario_id: UUID) -> Avaliacao:
    avaliacao = db.query(Avaliacao).filter_by(lote_id=lote_id, usuario_id=usuario_id).one_or_none()
    if avaliacao is None:
        avaliacao = Avaliacao(lote_id=lote_id, usuario_id=usuario_id, etapa=Etapa.TRIAGEM)
        db.add(avaliacao)
        db.flush()
    return avaliacao


def obter_ou_criar_avaliacoes(db: Session, lote_ids: list[UUID], usuario_id: UUID) -> dict[UUID, Avaliacao]:
    """Versão em lote, para paginação — só cria as que realmente faltam na página atual."""
    existentes = (
        db.query(Avaliacao)
        .filter(Avaliacao.usuario_id == usuario_id, Avaliacao.lote_id.in_(lote_ids))
        .all()
    )
    por_lote = {a.lote_id: a for a in existentes}
    faltando = [lid for lid in lote_ids if lid not in por_lote]
    for lid in faltando:
        nova = Avaliacao(lote_id=lid, usuario_id=usuario_id, etapa=Etapa.TRIAGEM)
        db.add(nova)
        por_lote[lid] = nova
    if faltando:
        db.flush()
    return por_lote
```

`Etapa.TRIAGEM` aqui é a etapa inicial definida no item 2 — este item e o item 2 são a mesma
mudança de "onde nasce a etapa inicial", só que agora sabemos que o lugar certo é aqui, não no
importador (ver nota de correção em `02-triagem-seleciona-funil.md`).

### `backend/app/importers/upsert.py`

`_criar_lote` **para de criar `Avaliacao`**. O importador passa a mexer só em dado global
(`Imovel`, `LoteLeilao`) — ver correção detalhada em `04-importacao-caixa-e-historico.md`
(o rastro de auditoria da importação também precisa sair de `EventoAvaliacao`, que agora é por
usuário, para um novo evento em escopo de lote).

### `backend/app/api/v1/imoveis.py`

**`GET /imoveis/{lote_id}` (Ficha)**: em vez de `db.query(Avaliacao).filter_by(lote_id=lote.id).one()`,
usar `obter_ou_criar_avaliacao(db, lote.id, usuario.id)` — este é o "primeiro acesso" que cria
a avaliação daquele usuário para aquele imóvel.

**`GET /imoveis` (Triagem/listagem)**: o join com `Avaliacao` precisa virar `outerjoin`,
filtrado pelo usuário atual — porque a maioria dos lotes ainda não vai ter avaliação nenhuma
para a maioria dos usuários:

```python
query = (
    db.query(LoteLeilao, Imovel, Avaliacao)
    .join(Imovel, LoteLeilao.imovel_id == Imovel.id)
    .outerjoin(
        Avaliacao,
        (Avaliacao.lote_id == LoteLeilao.id) & (Avaliacao.usuario_id == usuario.id),
    )
    .filter(LoteLeilao.ativo.is_(True))
)
```
O filtro por `etapa` (usado pelo item 2 para a Triagem listar só `etapa=triagem`) precisa
tratar "sem linha de avaliação ainda" como equivalente a `TRIAGEM`:
```python
if etapa:
    condicoes = [Avaliacao.etapa.in_(etapa)]
    if Etapa.TRIAGEM in etapa:
        condicoes.append(Avaliacao.id.is_(None))
    query = query.filter(or_(*condicoes))
```
O filtro `sem_dados_campo` (subquery `exists()` sobre `CampoAvaliacao.avaliacao_id`) já
funciona corretamente sem mudança: quando `Avaliacao.id` é `NULL`, a subquery nunca encontra
campo nenhum, então `~tem_campo` já dá `True` — "sem dados de campo" continua correto para
lotes ainda sem avaliação.

**Depois de paginar** (só nas linhas da página atual, não no resultado inteiro filtrado — é
isso que mantém a operação barata mesmo com uma base grande), chamar
`obter_ou_criar_avaliacoes` para as linhas cuja `Avaliacao` veio `None` do outer join, e montar
o `ImovelListItem` de cada uma já com o `avaliacao_id`/`etapa` reais — o frontend precisa de um
`avaliacao_id` de verdade em toda linha para poder agir (Corta / Selecionar p/ funil) sem uma
chamada extra.

### `backend/app/api/v1/funil.py`

A query de `avaliacoes_ativas` (já ajustada no item 2 para excluir `Etapa.TRIAGEM`) precisa
também filtrar pelo usuário atual:
```python
avaliacoes_ativas = (
    db.query(Avaliacao, LoteLeilao, Imovel)
    .join(LoteLeilao, Avaliacao.lote_id == LoteLeilao.id)
    .join(Imovel, LoteLeilao.imovel_id == Imovel.id)
    .filter(LoteLeilao.ativo.is_(True))
    .filter(Avaliacao.usuario_id == usuario.id)
    .filter(Avaliacao.etapa != Etapa.TRIAGEM)
    .all()
)
```
Aqui o join com `Avaliacao` continua `inner` (não `outer`) de propósito: um lote sem avaliação
para este usuário significa "esse usuário nunca triou esse imóvel", que já deve estar fora do
funil — não precisa de tratamento especial, o inner join já resolve isso sozinho.

### `backend/app/api/v1/avaliacoes.py`

`_get_avaliacao_ou_404` precisa checar posse, não só existência — hoje qualquer token válido
pode ler/escrever qualquer `avaliacao_id` (inofensivo com um usuário só, mas errado assim que
existir um segundo):
```python
def _get_avaliacao_ou_404(db: Session, avaliacao_id: UUID, usuario: Usuario) -> Avaliacao:
    avaliacao = db.get(Avaliacao, avaliacao_id)
    if avaliacao is None or avaliacao.usuario_id != usuario.id:
        raise HTTPException(status_code=404, detail="Avaliação não encontrada")
    return avaliacao
```
(404 em vez de 403 propositalmente — não confirma para quem não é dono que o id existe.) Todos
os endpoints deste router que já recebem `usuario: Usuario = Depends(get_current_usuario)`
passam a repassar `usuario` para essa função.

### `backend/app/services/snapshot.py`

Trocar a busca de parâmetros de `avaliacao.responsavel_id` (removido) para `avaliacao.usuario_id`:
```python
parametros_db = db.query(ParametroUsuario).filter_by(usuario_id=avaliacao.usuario_id).one_or_none()
```
O fallback `.first()` quando não há `ParametroUsuario` para aquele usuário pode continuar por
enquanto (ainda não existe fluxo de "criar usuário novo provisiona parâmetros padrão" — isso é
trabalho de quando a autenticação real chegar).

### `backend/app/seeds/seed.py`

Como o importador não cria mais `Avaliacao`, o seed precisa criar explicitamente as avaliações
de exemplo para o usuário dev, com `usuario_id=usuario.id`, em vez de contar com uma linha já
criada por `importar_caixa` e só ajustar `responsavel_id` nela. `_avancar_funil_de_exemplo`
(linha 40 em diante) precisa trocar `avaliacao_de(lote)` (que hoje assume `.filter_by(lote_id=lote.id).one()`)
por algo equivalente a `obter_ou_criar_avaliacao(db, lote.id, usuario.id)`.

### `backend/app/schemas/api.py`

`AvaliacaoDTO` (linha 94-102): remover `responsavel_id`.

## Nota para o futuro (não é trabalho deste item)

`CampoAvaliacao.sugestao_valor`/`sugestao_origem` (`backend/app/models/campo_avaliacao.py:47-48`)
existe hoje como gancho para o MVP2 (agente de valor de mercado). Vale registrar desde já: uma
sugestão gerada por automação a partir de comparáveis de mercado é, pela mesma lógica deste
item, **dado global** (o mesmo comparável vale para qualquer usuário olhando aquele imóvel) —
não deveria, quando o MVP2 chegar, precisar ser recalculada/duplicada por usuário. Como
`CampoAvaliacao` é por avaliação (logo por usuário) depois desta mudança, isso é uma tensão a
resolver no desenho do MVP2 (ex.: sugestão computada e cacheada por imóvel, só o *valor aceito*
é que vira `CampoAvaliacao` por usuário) — não precisa ser resolvida agora, só não ignorar
quando chegar a hora.

## Critérios de aceite

- [ ] `Avaliacao` tem `usuario_id` obrigatório e `UniqueConstraint(lote_id, usuario_id)`.
- [ ] `responsavel_id` não existe mais em `Avaliacao` nem em `AvaliacaoDTO`.
- [ ] Importar uma planilha não cria nenhuma linha em `Avaliacao`.
- [ ] Abrir a Ficha de um imóvel nunca antes acessado por aquele usuário cria a avaliação dele
      na hora, em etapa `triagem`, sem afetar a avaliação de nenhum outro usuário para o mesmo
      imóvel.
- [ ] A tela de Triagem só cria avaliações para os imóveis que efetivamente aparecem na página
      carregada (não para o total filtrado inteiro) — validar que uma base grande não gera uma
      explosão de `INSERT`s ao carregar a tela.
- [ ] Tentar ler ou editar uma `avaliacao_id` que pertence a outro usuário devolve 404.
- [ ] O cálculo financeiro de um imóvel usa sempre os `ParametroUsuario` do dono da avaliação
      (`usuario_id`), não de um "responsável" solto.

## Ordem sugerida de implementação

Este item (5) deve ser feito **antes** dos itens 2 e 4, porque os dois fazem suposições sobre
onde/quando `Avaliacao` é criada que só fazem sentido depois desta mudança:

1. **Item 5** (este arquivo) — corrige o modelo de `Avaliacao` e onde ela nasce.
2. **Item 2** — a nova etapa `TRIAGEM` e a listagem filtrada da Triagem já partem do modelo
   corrigido (ver nota de correção no topo de `02-triagem-seleciona-funil.md`).
3. **Item 4** — o rastro de auditoria da importação (criado/atualizado/inativado/reativado)
   precisa de um novo lugar para viver, já que `EventoAvaliacao` deixou de ser um bom lugar
   para eventos de dado global (ver nota de correção no topo de
   `04-importacao-caixa-e-historico.md`).
4. **Item 3** — não precisa de nenhuma mudança adicional além do que já foi especificado:
   `margem_desejada_pct` e `teto_lance` já vivem em `Avaliacao`, então já nascem por usuário
   automaticamente depois deste item.
5. **Item 1** — independente, pode ser feito a qualquer momento.
