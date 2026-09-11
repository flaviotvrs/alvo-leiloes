# 3. Lance máximo sugerido, por margem de lucro desejada (global ou por imóvel)

> **Nota (depois do item 5 ter sido definido):** este item não precisa de nenhuma mudança por
> causa do item [`05-dados-globais-vs-dados-do-usuario.md`](05-dados-globais-vs-dados-do-usuario.md).
> `margem_desejada_pct` e `teto_lance` já são campos de `Avaliacao` — ao `Avaliacao` virar por
> (lote, usuário), os dois já nascem por usuário automaticamente, de graça. Só vale implementar
> este item depois do item 5, para não escrever a migration de `Avaliacao` duas vezes.

## Problema

O motor de cálculo (`backend/app/services/calculo.py`) hoje só anda em uma direção: recebe um
`arremate` fixo (o preço mínimo do lote, `snapshot.arremate = lote.preco_venda` em
`backend/app/services/snapshot.py:63`) e devolve lucro/margem para *esse* valor. Já existe:

- Um piso de margem **global**, por usuário: `ParametroUsuario.piso_margem_pct`
  (`backend/app/models/parametro.py:20`, default 20%), usado só para decidir o rótulo
  `aprovado`/`reprovado` (`backend/app/services/calculo.py:240-242`).
- Um campo de teto de lance **manual**: `Avaliacao.teto_lance`
  (`backend/app/models/avaliacao.py:34`), preenchido à mão na Ficha, sem nenhum cálculo por
  trás — é só um número que o usuário digita.

Não existe hoje nenhum caminho que, dado "eu quero pelo menos X% de lucro neste imóvel",
devolva "então o lance máximo é R$ Y" — nem globalmente, nem por imóvel.

## Comportamento esperado

1. Para qualquer imóvel com valor de mercado já preenchido, a Ficha mostra um **lance máximo
   sugerido**: o maior valor de arremate para o qual `margem_investimento_pct` ainda é ≥ à
   margem de lucro desejada.
2. Por padrão, a margem desejada é o piso global (`piso_margem_pct`, hoje 20%).
3. O usuário pode sobrescrever a margem desejada **para aquele imóvel específico** (ex.: 5%
   porque o risco é menor, 0% porque é para morar, 100%+ porque o risco é alto) — isso muda o
   lance máximo sugerido só daquele imóvel, sem afetar o piso global nem outros imóveis.

## Decisões confirmadas com o usuário

- A margem ajustada por imóvel **também muda o veredito** aprovado/reprovado daquele imóvel
  (não fica restrito a mudar só o número do lance máximo) — ou seja, para aquele imóvel, a
  margem por imóvel *é* o novo piso, substituindo o global.
- O lance máximo calculado aparece como **sugestão ao lado** do `teto_lance` manual existente
  — não o substitui. O usuário continua podendo confirmar ou sobrescrever o valor final à mão,
  no mesmo espírito de outras sugestões automáticas do sistema (ex.: `sugestao_valor` em
  `CampoAvaliacao`, `backend/app/models/campo_avaliacao.py:47-48`).

## Design proposto

### Por que dá para calcular por busca binária (e não precisa de fórmula fechada)

`calcular()` já é uma função pura `Snapshot -> Resultado` (`backend/app/services/calculo.py`).
Fixando tudo no snapshot exceto `arremate`, dá para provar que `margem_investimento_pct` é
**monotonicamente decrescente** conforme `arremate` sobe:

- `investimento` cresce com `arremate` (comissão do leiloeiro, ITBI e registro em cartório são
  todos função crescente do arremate — `comissao_leiloeiro`/`itbi` proporcionais,
  `registro` uma função em degraus via `buscar_faixa`, mas nunca decrescente).
- `lucro` cai com `arremate`: o custo de aquisição sobe mais rápido do que o IR economiza (o
  IR cai porque `ganho_capital = revenda - comissao_corretor - (aquisicao + reforma)` diminui
  quando `aquisicao` sobe, mas a alíquota de IR — 15% no parâmetro padrão — é bem menor que
  100%, então o efeito líquido em `lucro` é sempre negativo).
- Logo `margem_investimento_pct = lucro / investimento` cai estritamente conforme `arremate`
  sobe (numerador encolhe, denominador cresce).
- Um limite superior seguro para a busca é o próprio `valor_mercado` (revenda): se
  `arremate >= revenda`, `investimento` (que inclui o arremate mais custos) já supera a
  revenda, então `lucro` já é negativo — não faz sentido buscar acima disso.

Isso permite uma busca binária inteira simples (sem cálculo simbólico, sem depender de
`registro` ser uma função contínua) — poucas dezenas de iterações, cada uma reaproveitando
`calcular()` como caixa-preta.

### Backend

1. **Novo campo em `backend/app/models/avaliacao.py`**:
   ```python
   margem_desejada_pct: Mapped[float | None] = mapped_column(Numeric(5, 2))
   ```
   `None` = "usa o piso global do usuário". Requer migration Alembic.

2. **`backend/app/schemas/api.py`**:
   - `AvaliacaoDTO` (linha 94) ganha `margem_desejada_pct: Decimal | None`.
   - `PatchAvaliacaoRequest` (linha 118) ganha `margem_desejada_pct: Decimal | None = None`,
     no mesmo padrão de `teto_lance` já existente ali.
   - `FichaResponse` (linha 105) ganha `lance_maximo_sugerido: Decimal | None`.

3. **`backend/app/api/v1/avaliacoes.py` — `atualizar_avaliacao` (linha ~134)**: aplicar
   `body.margem_desejada_pct` em `avaliacao.margem_desejada_pct` quando presente, igual já
   feito para `teto_lance`.

4. **`backend/app/services/snapshot.py` — `montar_snapshot`**: resolver a margem efetiva ali,
   para que `calcular()` nem precise saber que a sobreposição por imóvel existe (mantém o
   motor puro/desacoplado do banco):
   ```python
   piso_margem_efetivo = (
       avaliacao.margem_desejada_pct
       if avaliacao.margem_desejada_pct is not None
       else parametros_db.piso_margem_pct
   )
   parametros = ParametrosSnapshot(
       ...,
       piso_margem_pct=piso_margem_efetivo,
   )
   ```
   Isso já resolve sozinho a decisão "a margem por imóvel também muda o veredito": o veredito
   em `calcular()` (linha 240-242) compara `margem_investimento_pct` contra
   `snapshot.parametros.piso_margem_pct`, que passa a ser o valor já resolvido por imóvel.

5. **Nova função em `backend/app/services/calculo.py`** (ou um novo módulo
   `backend/app/services/lance_maximo.py`, para não misturar a função pura original com a
   busca iterativa em cima dela — preferível):
   ```python
   def calcular_lance_maximo(snapshot: Snapshot) -> Decimal | None:
       """Maior arremate inteiro (em reais) para o qual margem_investimento_pct ainda atinge
       snapshot.parametros.piso_margem_pct. None se não houver valor de mercado (não dá pra
       calcular margem sem revenda)."""
       if snapshot.campos.get("valor_mercado") is None:
           return None
       revenda = snapshot.campos["valor_mercado"].valor
       alvo = snapshot.parametros.piso_margem_pct

       def margem_em(arremate: Decimal) -> Decimal | None:
           resultado = calcular(snapshot.model_copy(update={"arremate": arremate}))
           return resultado.margem_investimento_pct

       lo, hi = Decimal(0), revenda
       # nem arremate=0 atinge a margem desejada -> não há lance viável
       margem_no_zero = margem_em(lo)
       if margem_no_zero is None or margem_no_zero < alvo:
           return Decimal(0)
       while hi - lo > 1:
           mid = (lo + hi) // 2
           margem = margem_em(mid)
           if margem is not None and margem >= alvo:
               lo = mid
           else:
               hi = mid
       return lo
   ```
   (nomes/assinatura exatos a critério de quem implementar; o importante é o contrato: entrada
   `Snapshot`, saída o maior arremate inteiro que preserva a margem-alvo, `None` só quando não
   há valor de mercado, `Decimal(0)` como sinal explícito de "nenhum lance atinge a margem,
   nem de graça" — a Ficha deve tratar esse caso com uma mensagem própria, não mostrar "R$ 0"
   sem contexto.)

6. **`backend/app/api/v1/imoveis.py` — `ficha()` (linha ~145)**: depois de montar
   `resultado = calcular(montar_snapshot(db, avaliacao))`, calcular também
   `lance_maximo = calcular_lance_maximo(montar_snapshot(db, avaliacao))` e incluir em
   `FichaResponse`. (Dá pra montar o snapshot uma vez só e reusar, já que `montar_snapshot` não
   é barato — mas isso é detalhe de implementação.)

### Frontend

1. **`frontend/src/pages/Ficha.tsx`**:
   - Novo campo de input "Margem de lucro desejada para este imóvel" (%, opcional), com
     placeholder mostrando o piso global vigente quando vazio (ex.: "20% (padrão)"). Usa o
     mesmo mecanismo de patch já existente para `teto_lance`
     (`frontend/src/api/hooks/usePatchAvaliacao.ts`) — estender esse hook para aceitar
     `margem_desejada_pct` também.
   - Novo bloco read-only "Lance máximo sugerido: R$ X", próximo ao input manual de
     `teto_lance` (por volta da linha 420-430, onde já aparece `margem_investimento_pct`).
     Três estados a cobrir na UI:
     - valor calculado normalmente → mostrar o número, com uma ação "usar este valor" que
       copia para o campo manual `teto_lance`.
     - `null` (sem valor de mercado) → "Defina o valor de mercado para calcular o lance
       máximo."
     - `0` (nenhum lance atinge a margem) → mensagem explícita, ex. "Nenhum lance atinge a
       margem desejada de X% neste imóvel, nem arrematando de graça — os custos fixos já
       superam o retorno esperado."

2. **`frontend/src/api/types.ts`**: refletir os novos campos (`margem_desejada_pct` em
   `AvaliacaoDTO`, `lance_maximo_sugerido` em `FichaResponse`).

## Critérios de aceite

- [ ] Ficha de um imóvel com valor de mercado preenchido mostra um lance máximo sugerido
      coerente com o piso global (20% por padrão) — validar batendo à mão as contas de um
      cenário simples.
- [ ] Ajustar a margem desejada de um imóvel específico (ex. para 5%) muda o lance máximo
      sugerido **daquele imóvel** e o veredito aprovado/reprovado dele — sem afetar outros
      imóveis nem o parâmetro global do usuário.
- [ ] Zerar/limpar a margem por imóvel volta a usar o piso global.
- [ ] Imóvel sem valor de mercado preenchido: lance máximo aparece como indisponível, com
      mensagem clara, não um erro ou "R$ 0" sem explicação.
- [ ] Imóvel cujos custos fixos (dívidas em atraso, reforma, desocupação) já superam o valor
      de mercado: lance máximo mostra explicitamente "nenhum lance viável", não "R$ 0" como se
      fosse um valor calculado normal.
- [ ] O campo manual `teto_lance` continua funcionando exatamente como hoje (a sugestão não o
      substitui nem o sobrescreve automaticamente).
