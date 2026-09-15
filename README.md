# Alvo Leilões

Ferramenta interna para garimpo de imóveis em leilão extrajudicial (Lei 9.514/97). Importa
uma base de imóveis (hoje a planilha da Caixa), permite filtrar o que vale a pena olhar numa
tela de **Triagem**, coletar os dados de campo (visita, prefeitura, administradora,
comparáveis) numa **Ficha do imóvel**, e calcula automaticamente a viabilidade financeira do
negócio, movendo cada imóvel por um **Funil de aprovação** de 5 etapas.

Duas regras atravessam o produto inteiro: **a procedência de todo dado é visível** (base
importada, digitado à mão, ou automação futura) e **palpite nunca se disfarça de fato**
— quando o sistema assume um valor (ex. alíquota de ITBI não cadastrada), a interface deixa
isso explícito e aponta o que confirmar.

> Este é o **MVP 1**: pipeline financeiro determinístico. Sem LLM na conta — o motor de
> cálculo é uma função pura e auditável. Os MVPs seguintes (agente de valor de mercado,
> agente de matrícula, agente juiz) estão descritos em `docs/requisitos/roadmap-mvps.md`.

## Documentação

A especificação completa do produto está em `docs/`:

| Arquivo | Conteúdo |
|---|---|
| `docs/README.md` | especificação da interface (design tokens, telas, interações) |
| `docs/BACKEND.md` | modelo de dados, motor de cálculo, API — fonte de verdade técnica |
| `docs/requisitos/processo-alvo-leiloes.md` | processo de negócio ponta a ponta |
| `docs/requisitos/roadmap-mvps.md` | fatiamento em MVPs |
| `docs/Alvo Leiloes v4.dc.html` | protótipo visual de alta fidelidade (abra no navegador) |

Este README trata só de **rodar e desenvolver** o que já está implementado.

## Stack

- **Backend:** Python (FastAPI) + SQLAlchemy 2.0 + Alembic, gerenciado com [`uv`](https://docs.astral.sh/uv/). Postgres 16.
- **Frontend:** React + TypeScript + Vite, Tailwind CSS, TanStack Query, React Router.
- **Dev local:** Postgres via Docker Compose; backend e frontend rodam nativamente no host (hot-reload em ambos).

## Setup

Pré-requisitos: Docker, [`uv`](https://docs.astral.sh/uv/), Node.js 20+.

```bash
# 1. variáveis de ambiente (um único .env na raiz, compartilhado por backend e frontend)
cp .env.example .env

# 2. banco de dados
docker compose up -d db

# 3. backend
cd backend
uv sync
uv run alembic upgrade head
uv run python -m app.seeds.seed      # dados de referência + 15 imóveis fictícios (ver nota abaixo)
uv run uvicorn app.main:app --reload --port 8000

# 4. frontend (outro terminal)
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- API: http://localhost:8000/api/v1 — Swagger em http://localhost:8000/docs
- Postgres: `localhost:5433` (não 5432 — porta padrão costuma estar ocupada; ver `.env`)

A API exige `Authorization: Bearer <token>`; o token de dev é `API_BEARER_TOKEN` no `.env`
(mesmo valor usado pelo frontend via `VITE_API_BEARER_TOKEN`). Autenticação é single-user no
MVP1 — não há tela de login.

### Dado de seed é fictício

`uv run python -m app.seeds.seed` roda o importador de verdade contra uma planilha **inventada**
(`backend/app/seeds/fixtures/sample_caixa.xlsx`, gerada por
`backend/app/seeds/fixtures/gerar_sample_caixa.py`), não a planilha real da Caixa. Serve só
para desenvolver e demonstrar a interface sem esperar a carga real. Quando a planilha real
estiver disponível, ela entra por `POST /api/v1/importacoes` (upload) e não conflita com o
seed — o importador nunca sobrescreve dado que o usuário já preencheu à mão.

Para zerar a base fictícia e recomeçar:

```bash
docker exec alvo-leiloes-db-1 psql -U alvo -d alvo_leiloes -c \
  "TRUNCATE imovel, lote_leilao, avaliacao, campo_avaliacao, evento_avaliacao, importacao RESTART IDENTITY CASCADE;"
```

## Testes

```bash
cd backend
uv run pytest                 # 10 unitários (motor de cálculo, sem banco) + 4 de integração (importador)
```

Os testes de integração rodam contra o Postgres de dev (uma transação por teste, com
rollback ao final) — **não usam um banco de teste isolado**. Se você tiver dados reais
gravados via API (não só o seed) na hora de rodar os testes, alguns podem colidir com esse
estado (ex. um `campo_avaliacao` já preenchido onde o teste espera ausência). Isso é uma
limitação conhecida do MVP1, não um bug — rode os testes num banco recém-seedado, ou zere a
base (comando acima) antes.

O motor de cálculo (`backend/app/services/calculo.py`) tem um golden test
(`tests/unit/test_calculo_golden.py`) que reproduz exatamente o cenário de exemplo do
`docs/BACKEND.md` — é o critério de aceite para qualquer mudança na fórmula.

## Estrutura

```
alvo-leiloes/
├── docker-compose.yml       # Postgres
├── .env                     # compartilhado por backend e frontend
├── docs/                    # especificação do produto (ver tabela acima)
├── backend/
│   └── app/
│       ├── models/          # SQLAlchemy — 1 arquivo por tabela
│       ├── schemas/         # Pydantic — contratos de API e do motor de cálculo
│       ├── services/        # calculo.py (motor puro), snapshot.py, numeros.py, ...
│       ├── importers/       # caixa.py (Zukerman: MVP1, ainda não implementado)
│       ├── api/v1/          # 1 router por recurso
│       └── seeds/           # seed.py + fixtures/ (dados fictícios de dev)
└── frontend/
    └── src/
        ├── pages/           # Triagem.tsx, Ficha.tsx, Funil.tsx
        ├── components/      # ProcedenciaChip, MoneyValue, LinhaConta, ...
        ├── api/              # client + tipos + hooks (TanStack Query)
        └── design-tokens/    # tokens transcritos de docs/README.md
```

## Deploy

Infra de baixo custo para uma ferramenta interna de baixo tráfego:

| Peça | Onde |
|---|---|
| Banco | [Neon](https://neon.tech) (Postgres serverless, free tier) |
| Backend | [Render](https://render.com) (Web Service Docker, free tier) |
| Frontend | [Cloudflare Pages](https://pages.cloudflare.com) (build estático do Vite, free) |

### Backend (Render)

1. No Neon, crie o projeto/branch e copie a **connection string com pooling** (host
   termina em `-pooler`), com `sslmode=require`.
2. No Render, "New +" → "Blueprint" apontando para este repo — ele lê o `render.yaml` da
   raiz e cria o serviço `alvo-leiloes-backend` (Docker, build a partir de `backend/`).
3. Preencha as env vars pedidas pelo blueprint (não têm valor padrão, por serem
   sensíveis/específicas do ambiente):
   - `DATABASE_URL` — a connection string pooled do Neon, no formato
     `postgresql+psycopg://usuario:senha@ep-xxx-pooler.regiao.neon.tech/alvo_leiloes?sslmode=require`
   - `API_BEARER_TOKEN` — um token novo, diferente do de dev
   - `ALLOWED_ORIGINS` — a URL do frontend em produção (ex.:
     `https://alvo-leiloes.pages.dev`); pode ter mais de uma, separadas por vírgula
4. O `preDeployCommand` do blueprint roda `alembic upgrade head` antes de cada deploy —
   não precisa aplicar migrations manualmente. Se o Render ignorar esse campo (varia por
   plano/versão), rode uma vez manualmente pelo Shell do serviço no dashboard.
5. Depois do primeiro deploy, rode o seed (opcional, só para demonstração) pelo Shell do
   serviço: `python -m app.seeds.seed`.

O plano free do Render hiberna o serviço após ~15min sem tráfego — a primeira requisição
depois disso demora ~30-50s (cold start). Para uma ferramenta interna de uso esporádico
costuma ser aceitável; se incomodar, o caminho de migração é para o Google Cloud Run
(free tier também, cold start bem mais rápido, mas exige conta GCP com billing).

### Frontend (Cloudflare Pages)

1. Cloudflare Pages → "Create a project" → conectar este repo.
2. Build settings:
   - Root directory: `frontend`
   - Build command: `npm run build`
   - Output directory: `dist`
3. Env vars do build (Settings → Environment variables):
   - `VITE_API_BASE_URL` — URL do backend no Render + `/api/v1` (ex.:
     `https://alvo-leiloes-backend.onrender.com/api/v1`)
   - `VITE_API_BEARER_TOKEN` — o mesmo valor de `API_BEARER_TOKEN` configurado no backend

Esses valores ficam embutidos no bundle JS gerado (Vite inlina env vars `VITE_*` em
build-time) — não são segredos protegidos no cliente, só evitam hardcode no código-fonte.

### Observação sobre autenticação

`API_BEARER_TOKEN` é único e estático (ver nota em `get_current_usuario`,
`backend/app/api/deps.py`) — suficiente para o MVP1 de single-user atrás de um link não
divulgado, mas visível a quem abrir o DevTools do frontend. Não é proteção real contra
acesso não autorizado; reavaliar se a ferramenta ganhar mais usuários ou dados sensíveis.

## Estado atual

**Implementado:** modelo de dados completo, motor de cálculo, importador da planilha Caixa,
API REST completa, as três telas do frontend.

**Fora de escopo por ora** (roadmap em `docs/requisitos/roadmap-mvps.md`): importador
Zukerman (scraping), coleta manual guiada (tutorial passo a passo de IPTU/condomínio),
agente de valor de mercado (MVP2), agente de matrícula (MVP3), agente juiz (MVP4).
