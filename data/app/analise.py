"""A parte de 'análise de dados': funções puras que recebem um DataFrame e devolvem números."""
import pandas as pd


def _validos(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["status"] != "cancelado"]


def resumo(df: pd.DataFrame) -> dict:
    v = _validos(df)
    entregues = df[df["entregue_em"].notna()]
    prazo = (entregues["entregue_em"] - entregues["criado_em"]).dt.days.mean() if len(entregues) else None
    return {
        "total_pedidos": int(len(df)),
        "valor_total": round(float(v["valor_total"].sum()), 2),
        "ticket_medio": round(float(v["valor_total"].mean()), 2) if len(v) else 0.0,
        "atrasados": int((df["status"] == "atrasado").sum()),
        "prazo_medio_entrega_dias": None if prazo is None or pd.isna(prazo) else round(float(prazo), 1),
        "por_status": {k: int(n) for k, n in df["status"].value_counts().items()},
    }


def _agrupar(df: pd.DataFrame, coluna: str, nome: str) -> list[dict]:
    g = (
        _validos(df)
        .groupby(coluna)
        .agg(pedidos=("id", "count"), valor_total=("valor_total", "sum"))
        .reset_index()
        .sort_values("valor_total", ascending=False)
    )
    return [
        {nome: r[coluna], "pedidos": int(r["pedidos"]), "valor_total": round(float(r["valor_total"]), 2)}
        for _, r in g.iterrows()
    ]


def categorias(df: pd.DataFrame) -> list[dict]:
    return _agrupar(df, "categoria", "categoria")


def fornecedores(df: pd.DataFrame, top: int = 5) -> list[dict]:
    return _agrupar(df, "fornecedor", "fornecedor")[:top]


def mensal(df: pd.DataFrame) -> list[dict]:
    v = _validos(df).copy()
    v["mes"] = v["criado_em"].dt.strftime("%Y-%m")
    g = v.groupby("mes").agg(pedidos=("id", "count"), valor_total=("valor_total", "sum")).reset_index().sort_values("mes")
    return [
        {"mes": r["mes"], "pedidos": int(r["pedidos"]), "valor_total": round(float(r["valor_total"]), 2)}
        for _, r in g.iterrows()
    ]
