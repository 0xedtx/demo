"""De onde vêm os dados: Postgres externo (se DATABASE_URL existir) ou o CSV de exemplo."""
import os
from pathlib import Path

import pandas as pd

SEED = Path(__file__).parent / "seed" / "pedidos_compra.csv"
DATAS = ["criado_em", "previsao_entrega", "entregue_em"]

_engine = None


def fonte() -> str:
    return "postgres" if os.getenv("DATABASE_URL") else "csv"


def _engine_pg():
    global _engine
    if _engine is None:
        from sqlalchemy import create_engine

        _engine = create_engine(os.environ["DATABASE_URL"], pool_pre_ping=True)
    return _engine


def carregar() -> pd.DataFrame:
    if fonte() == "postgres":
        df = pd.read_sql("SELECT * FROM pedidos_compra", _engine_pg(), parse_dates=DATAS)
    else:
        df = pd.read_csv(SEED, parse_dates=DATAS)
    for c in ("valor_unitario", "valor_total"):
        df[c] = df[c].astype(float)
    df["quantidade"] = df["quantidade"].astype(int)
    return df


def serializar(df: pd.DataFrame) -> list[dict]:
    """DataFrame -> lista de dicts que o JSON entende (datas em texto, NaT em null)."""
    out = df.copy()
    for c in DATAS:
        out[c] = out[c].dt.strftime("%Y-%m-%d")
    out = out.astype(object).where(pd.notna(out), None)
    return out.to_dict(orient="records")
