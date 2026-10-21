-- Banco do squad Atlas (Postgres). Aplique uma vez, depois carregue db/seed.sql.
--   psql "$DATABASE_URL" -f db/schema.sql
--   psql "$DATABASE_URL" -f db/seed.sql
CREATE TABLE IF NOT EXISTS pedidos_compra (
  id               SERIAL PRIMARY KEY,
  numero           TEXT NOT NULL UNIQUE,
  fornecedor       TEXT NOT NULL,
  categoria        TEXT NOT NULL,
  descricao        TEXT NOT NULL,
  quantidade       INTEGER NOT NULL CHECK (quantidade > 0),
  valor_unitario   NUMERIC(12,2) NOT NULL,
  valor_total      NUMERIC(14,2) NOT NULL,
  status           TEXT NOT NULL CHECK (status IN ('pendente','aprovado','entregue','atrasado','cancelado')),
  solicitante      TEXT NOT NULL,
  setor            TEXT NOT NULL,
  criado_em        DATE NOT NULL,
  previsao_entrega DATE NOT NULL,
  entregue_em      DATE
);
CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos_compra (status);
CREATE INDEX IF NOT EXISTS idx_pedidos_criado_em ON pedidos_compra (criado_em);
