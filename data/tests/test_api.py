from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok-atualizado"


def test_resumo_tem_numeros_coerentes():
    r = client.get("/insights/resumo").json()
    assert r["total_pedidos"] > 100
    assert r["valor_total"] > 0
    assert sum(r["por_status"].values()) == r["total_pedidos"]


def test_categorias_vem_ordenadas_do_maior_para_o_menor():
    valores = [c["valor_total"] for c in client.get("/insights/categorias").json()]
    assert valores == sorted(valores, reverse=True)


def test_pedidos_filtra_por_status_e_pagina():
    r = client.get("/pedidos", params={"status": "atrasado", "limit": 3}).json()
    assert len(r["itens"]) <= 3
    assert r["total"] >= len(r["itens"])
    assert all(p["status"] == "atrasado" for p in r["itens"])
