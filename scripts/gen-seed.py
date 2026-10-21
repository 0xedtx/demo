#!/usr/bin/env python3
"""Gera dados realistas (sintéticos) de pedidos de compra do squad Atlas.

Saídas:
  data/app/seed/pedidos_compra.csv   -> usado pelo serviço de dados quando não há banco
  db/seed.sql                        -> para carregar no Postgres externo

Determinístico: rodar de novo gera exatamente os mesmos dados.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
HOJE = date(2026, 10, 21)
rng = random.Random(2026)

CATALOGO = {
    "TI e Equipamentos": [("Notebook 14 polegadas", 4200, 6800), ("Monitor 24 polegadas", 780, 1200), ("Switch 24 portas", 1900, 3400), ("Nobreak 1500VA", 1100, 1900)],
    "Material de Escritório": [("Resma de papel A4 (caixa com 10)", 240, 310), ("Toner para impressora", 320, 640), ("Kit canetas e post-it", 60, 140)],
    "Mobiliário": [("Cadeira ergonômica", 780, 1450), ("Mesa de reunião", 1800, 3900), ("Armário de aço", 690, 1250)],
    "Limpeza e Copa": [("Café em grão 1kg", 58, 92), ("Kit de limpeza mensal", 210, 420), ("Água mineral 20L (lote com 10)", 120, 180)],
    "Manutenção": [("Manutenção de ar-condicionado", 350, 900), ("Revisão elétrica", 600, 1800)],
    "Marketing": [("Brindes personalizados (lote de 100)", 900, 2400), ("Banner e impressos", 300, 950)],
}
PESOS = [22, 22, 10, 18, 14, 14]
QTD = {
    "TI e Equipamentos": (1, 12), "Material de Escritório": (2, 30), "Mobiliário": (1, 10),
    "Limpeza e Copa": (1, 8), "Manutenção": (1, 3), "Marketing": (1, 2),
}
FORNECEDORES = {
    "TI e Equipamentos": ["Tecnoforte Distribuidora", "Nordeste Informática", "ByteSul Atacado"],
    "Material de Escritório": ["Papelaria Central Ceará", "Escritório Fácil", "Grafite & Cia"],
    "Mobiliário": ["Móveis Jaguaribe", "Ergo Office Brasil"],
    "Limpeza e Copa": ["Limpa Mais Suprimentos", "Casa do Café Fortaleza"],
    "Manutenção": ["Clima Frio Serviços", "Eletro Norte Manutenções"],
    "Marketing": ["Gráfica Ponto Certo", "Brindes Litoral"],
}
SETORES = ["Financeiro", "Operações", "TI", "RH", "Comercial", "Diretoria"]
SOLICITANTES = ["Ana Beatriz", "Carlos Eduardo", "Marina Lopes", "Rafael Pontes", "Juliana Costa", "Thiago Nogueira", "Camila Freitas", "Lucas Almeida"]

N = 180
inicio, fim = date(2025, 11, 1), date(2026, 10, 15)

linhas = []
for _ in range(N):
    cat = rng.choices(list(CATALOGO), weights=PESOS)[0]
    desc, pmin, pmax = rng.choice(CATALOGO[cat])
    qtd = rng.randint(*QTD[cat])
    preco = round(rng.uniform(pmin, pmax), 2)
    criado = inicio + timedelta(days=rng.randint(0, (fim - inicio).days))
    previsao = criado + timedelta(days=rng.randint(5, 30))
    entregue = None
    r = rng.random()
    if r < 0.06:
        status = "cancelado"
    elif previsao < HOJE:
        if rng.random() < 0.86:
            status = "entregue"
            entregue = min(HOJE, max(criado + timedelta(days=2), previsao + timedelta(days=rng.randint(-3, 7))))
        else:
            status = "atrasado"
    else:
        status = rng.choice(["aprovado", "pendente"])
    linhas.append({
        "fornecedor": rng.choice(FORNECEDORES[cat]), "categoria": cat, "descricao": desc,
        "quantidade": qtd, "valor_unitario": preco, "valor_total": round(qtd * preco, 2),
        "status": status, "solicitante": rng.choice(SOLICITANTES), "setor": rng.choice(SETORES),
        "criado_em": criado, "previsao_entrega": previsao, "entregue_em": entregue,
    })

linhas.sort(key=lambda x: x["criado_em"])
seq_ano = {}
for i, l in enumerate(linhas, start=1):
    ano = l["criado_em"].year
    seq_ano[ano] = seq_ano.get(ano, 0) + 1
    l["id"] = i
    l["numero"] = f"OC-{ano}-{seq_ano[ano]:04d}"

COLUNAS = ["id", "numero", "fornecedor", "categoria", "descricao", "quantidade", "valor_unitario",
           "valor_total", "status", "solicitante", "setor", "criado_em", "previsao_entrega", "entregue_em"]

csv_path = RAIZ / "data" / "app" / "seed" / "pedidos_compra.csv"
csv_path.parent.mkdir(parents=True, exist_ok=True)
with csv_path.open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(COLUNAS)
    for l in linhas:
        w.writerow([("" if l[c] is None else l[c]) for c in COLUNAS])


def sql(v):
    if v is None:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


cols_sql = [c for c in COLUNAS if c != "id"]
valores = ",\n".join("  (" + ", ".join(sql(l[c]) for c in cols_sql) + ")" for l in linhas)
(RAIZ / "db" / "seed.sql").write_text(
    "-- Gerado por scripts/gen-seed.py (dados sintéticos e realistas). Não edite à mão.\n"
    f"INSERT INTO pedidos_compra ({', '.join(cols_sql)}) VALUES\n{valores};\n",
    encoding="utf-8",
)
print(f"{len(linhas)} pedidos gerados")
