# 1. Filtro da Triagem deve sobreviver a abrir a Ficha e voltar

## Problema

O filtro da tela de Triagem já vive na URL (`useSearchParams` em
`frontend/src/pages/Triagem.tsx:91-101`), o que é a abordagem certa — mas dois pontos da
navegação descartam essa querystring em vez de propagá-la:

- `frontend/src/pages/Ficha.tsx:285` — o link "Voltar" é um `<Link to="/triagem">` fixo, sem
  a querystring de filtros.
- `frontend/src/pages/Ficha.tsx:270` — depois de descartar um imóvel pela Ficha,
  `navigate("/triagem")` também não carrega a querystring.

Resultado: filtrar por região/preço/características na Triagem, abrir a ficha de um imóvel e
voltar (ou descartar e voltar) limpa o filtro e volta para a base inteira — exatamente o bug
relatado.

## Comportamento esperado

1. Usuário aplica filtros na Triagem (bairro, preço, tipo, desconto mínimo etc. — ver
   `frontend/src/components/FiltroPainel.tsx`).
2. Usuário clica em um imóvel (linha inteira ou botão "Preencher") e abre a Ficha.
3. Usuário clica em "Voltar" (ou descarta o imóvel) e retorna para `/triagem` — **com os
   mesmos filtros ainda aplicados**, exibindo a mesma lista de onde saiu.
4. Se o usuário chegar na Ficha por link direto (bookmark, URL colada, sem ter passado pela
   Triagem nesta navegação), "Voltar" cai na Triagem sem filtro nenhum — comportamento atual,
   sem mudança, já que não há filtro anterior para preservar.

## Design proposto

Não é necessário mexer no backend. A forma mais simples de carregar a proveniência do filtro
até a Ficha é via **state do React Router** (não expor a querystring da Triagem na própria URL
da Ficha, para não poluir `/imoveis/:loteId`):

1. Em `Triagem.tsx`, ao navegar para a Ficha (clique na linha e botão "Preencher"), passar o
   `search` atual como state:
   ```tsx
   navigate(`/imoveis/${item.lote_id}`, { state: { voltarPara: `/triagem${location.search}` } })
   ```
   (equivalente para o `<Link>`/`onClick` existente — usar `useLocation()` para pegar
   `location.search` atual da própria Triagem).
2. Em `Ficha.tsx`, ler esse state:
   ```tsx
   const location = useLocation();
   const voltarPara = (location.state as { voltarPara?: string } | null)?.voltarPara ?? "/triagem";
   ```
3. Trocar o `<Link to="/triagem">` (linha 285) por `<Link to={voltarPara}>`.
4. Trocar o `navigate("/triagem")` pós-descarte (linha 270) por `navigate(voltarPara)`.

Vale desenhar `voltarPara` como uma string de destino simples (não um objeto com label etc.)
porque hoje só há uma origem possível (Triagem). Os cards do Funil (`Funil.tsx:57`) também
navegam para a Ficha sem carregar state — não precisam mudar agora (o Funil não tem painel de
filtro hoje), mas o mesmo mecanismo serve se isso mudar depois: bastaria passar
`voltarPara: "/funil"` de lá também.

## Mudanças necessárias

- `frontend/src/pages/Triagem.tsx`: passar `state: { voltarPara: ... }` nos dois pontos de
  navegação para a Ficha (clique na linha, botão "Preencher").
- `frontend/src/pages/Ficha.tsx`: ler o state, usar como destino do link "Voltar" e do
  `navigate` pós-descarte, com fallback para `/triagem`.

Nenhuma mudança de backend, schema ou modelo é necessária para este item.

## Critérios de aceite

- [ ] Filtrar na Triagem (ex.: cidade + tipo + desconto mínimo) → abrir um imóvel → clicar em
      "Voltar" → mesma lista filtrada, não a base inteira.
- [ ] Mesmo fluxo, mas descartando o imóvel na Ficha em vez de clicar em "Voltar" → mesmo
      resultado.
- [ ] Acessar `/imoveis/:loteId` diretamente por URL (sem vir da Triagem) → "Voltar" leva para
      `/triagem` sem filtro (comportamento atual preservado).
