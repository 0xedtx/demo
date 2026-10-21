"""Serviço de dados do squad Atlas (FastAPI).

Importante: este serviço NÃO é público. Ele escuta só em 127.0.0.1:8000 e quem conversa
com ele é a API (Nest), de dentro do mesmo servidor. Veja docs/COMO-FUNCIONA.md.
"""
from fastapi import FastAPI, Query

from . import analise, repo

app = FastAPI(title="Atlas · dados", version="1.0.0")


@app.get("/health")
def health():
    return {"status": "ok", "fonte": repo.fonte()}


@app.get("/pedidos")
def pedidos(
    status: str | None = None,
    categoria: str | None = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    df = repo.carregar()
    if status:
        df = df[df["status"] == status]
    if categoria:
        df = df[df["categoria"] == categoria]
    df = df.sort_values(["criado_em", "id"], ascending=False)
    return {"total": int(len(df)), "itens": repo.serializar(df.iloc[offset : offset + limit])}


@app.get("/insights/resumo")
def insights_resumo():
    return analise.resumo(repo.carregar())


@app.get("/insights/categorias")
def insights_categorias():
    return analise.categorias(repo.carregar())


@app.get("/insights/fornecedores")
def insights_fornecedores(top: int = Query(5, ge=1, le=20)):
    return analise.fornecedores(repo.carregar(), top)


@app.get("/insights/mensal")
def insights_mensal():
    return analise.mensal(repo.carregar())
