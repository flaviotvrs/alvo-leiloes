from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import avaliacoes, funil, imoveis, importacoes, parametros, referencias
from app.config import settings

app = FastAPI(title="Alvo Leilões API")

# Localhost (dev) sempre liberado via regex; origens de produção vêm de ALLOWED_ORIGINS.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(imoveis.router, prefix="/api/v1")
app.include_router(avaliacoes.router, prefix="/api/v1")
app.include_router(funil.router, prefix="/api/v1")
app.include_router(importacoes.router, prefix="/api/v1")
app.include_router(parametros.router, prefix="/api/v1")
app.include_router(referencias.router, prefix="/api/v1")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
