# Ajustes para concluir o MVP 1 — visão geral

> Reestruturação de `docs/requisitos/mvp1-ajustes.md` (notas originais do usuário) em specs
> acionáveis, uma por item, para implementação futura. Cada arquivo desta pasta cobre um dos
> itens, com: problema atual (com referência a arquivo/linha do código hoje), comportamento
> esperado, decisões já confirmadas com o usuário, mudanças necessárias por arquivo, e
> critérios de aceite. Complementa `docs/requisitos/processo-alvo-leiloes.md` (modelo do
> processo) e `docs/requisitos/roadmap-mvps.md` (escopo do MVP 1).
>
> O item 5 (dados globais vs. por usuário) foi acrescentado numa mensagem de acompanhamento,
> depois dos itens 1-4 já estarem escritos — é o mais estrutural dos cinco, e corrigiu uma
> suposição de modelagem nos itens 2 e 4 (ver notas de "Correção" no topo desses dois
> arquivos). Ver "Ordem sugerida de implementação" abaixo.

## Itens

1. [`01-filtro-persistente-na-navegacao.md`](01-filtro-persistente-na-navegacao.md) — filtro da Triagem some ao abrir a Ficha e voltar.
2. [`02-triagem-seleciona-funil.md`](02-triagem-seleciona-funil.md) — funil lista todo mundo na base; Triagem deve ser o portão de entrada.
3. [`03-lance-maximo-sugerido.md`](03-lance-maximo-sugerido.md) — calculadora deve indicar o lance máximo por margem de lucro desejada (global ou por imóvel).
4. [`04-importacao-caixa-e-historico.md`](04-importacao-caixa-e-historico.md) — tela de importação da planilha da Caixa + histórico; upsert/inativação/reativação com auditoria.
5. [`05-dados-globais-vs-dados-do-usuario.md`](05-dados-globais-vs-dados-do-usuario.md) — dado do imóvel/importação é global (todo mundo vê igual); análise (etapa do funil, valor de mercado, teto de lance etc.) é por usuário. **Item mais estrutural dos cinco — ler antes de implementar os itens 2 e 4.**

## Ordem sugerida de implementação

O item 5 foi adicionado depois dos itens 1-4 já estarem escritos, e corrige uma suposição de
modelagem que os itens 2 e 4 fizeram antes dele existir (cada um tem uma nota de "Correção" no
topo do arquivo, explicando exatamente o quê). Ordem recomendada:

1. **Item 5** — corrige o modelo de `Avaliacao` para ser por (lote, usuário) antes de mais
   nada mexer nela.
2. **Item 2** — nova etapa `TRIAGEM`, já em cima do modelo corrigido.
3. **Item 4** — importador + tela de importações; o rastro de auditoria usa o novo modelo de
   evento em escopo de lote (`EventoLote`) que o item 5 tornou necessário.
4. **Item 3** — não precisa de trabalho extra depois do item 5 (`margem_desejada_pct` e
   `teto_lance` já nascem por usuário de graça).
5. **Item 1** — independente dos demais, pode entrar em qualquer ponto da sequência.

## Como este documento foi montado

Antes de escrever qualquer spec, o código atual foi lido (não só as notas do usuário) para
ancorar cada item em comportamento real:

- Modelos: `backend/app/models/{imovel,avaliacao,lote_leilao,importacao,campo_avaliacao,evento_avaliacao,enums,parametro}.py`
- Serviços: `backend/app/services/{calculo,snapshot,emolumentos}.py`
- Importador: `backend/app/importers/{caixa,upsert,parsing}.py`
- API: `backend/app/api/v1/{imoveis,avaliacoes,funil,importacoes}.py`
- Frontend: `frontend/src/pages/{Triagem,Funil,Ficha}.tsx`, `frontend/src/components/FiltroPainel.tsx`, `frontend/src/App.tsx`, `frontend/src/components/NavBar.tsx`

Isso revelou que dois dos quatro itens (2 e 4) já têm boa parte da infraestrutura de suporte
pronta no backend (endpoint de importação, endpoint genérico de troca de etapa, filtro por
etapa em `/imoveis`) — o trabalho real é fechar lacunas específicas, não construir do zero.
Também revelou **bugs concretos** no parser da planilha da Caixa, confirmados rodando o
parser atual contra uma amostra real do arquivo (`docs/requisitos/Planilha_Caixa_Sample.csv`)
— detalhados no item 4.

## Decisões já confirmadas com o usuário (não reabrir)

- **Item 2:** a seleção para o funil vira uma nova etapa do pipeline ("Em triagem"), anterior
  a "Não avaliado" — não um flag booleano separado.
- **Item 3:** a margem de lucro ajustada por imóvel também muda o veredito
  aprovado/reprovado daquele imóvel (não só o número do lance máximo).
- **Item 3:** o lance máximo calculado aparece como **sugestão ao lado** do campo manual
  `teto_lance` já existente — não o substitui.
- **Item 4:** o usuário forneceu um arquivo real de amostra da planilha da Caixa
  (`docs/requisitos/Planilha_Caixa_Sample.csv`) — o formato real (CSV, não XLSX) já foi
  validado contra o parser atual.
- **Item 5:** o escopo agora é só corrigir o *modelo de dados* (`Avaliacao` por usuário, não
  mais por lote) — autenticação real com múltiplas contas de fato logando continua fora do
  MVP1, como já era antes.
- **Item 5:** a avaliação de um usuário para um imóvel nasce sob demanda, no primeiro acesso
  dele (Triagem ou Ficha) — não mais no momento da importação, e sem passo de provisionamento
  separado por usuário.
