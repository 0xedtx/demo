# Atlas · repositório demo

Repositório demo do laboratório de DevOps do **Amontada Valley**. É um painel de pedidos de compra: uma tela, uma API e um serviço de análise de dados, publicados no container da squad por um workflow do GitHub Actions.

Site de exemplo: `atlas.amontadavalley.com.br`

| Pasta | O que é | Tecnologia |
|---|---|---|
| `web/` | tela (painel de compras) | Next + React |
| `api/` | API pública sob `/api` | Nest |
| `data/` | análise de dados, só acessível por `localhost` | FastAPI + pandas |
| `db/` | tabela e dados de exemplo do Postgres | SQL |
| `deploy/` | units do systemd, site do nginx e script de deploy | configuração |
| `.github/workflows/` | CI (nos PRs) e Deploy (na main) | GitHub Actions |
| `docs/` | como tudo conversa, configuração, roteiro do lab | Markdown |

## Comece por aqui

1. [docs/COMO-FUNCIONA.md](docs/COMO-FUNCIONA.md): do navegador até o banco, passo a passo.
2. [docs/ROTEIRO-LAB.md](docs/ROTEIRO-LAB.md): o que fazer no laboratório (PR, review, deploy).
3. [docs/CONFIGURACAO.md](docs/CONFIGURACAO.md): environments, secrets, container e banco (para quem prepara o ambiente).

## Rodar local, resumido

```bash
(cd data && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt && .venv/bin/uvicorn app.main:app --port 8000 --reload) &
(cd api  && npm install && npm run dev) &
(cd web  && npm install && npm run dev)
```

Abra `http://localhost:3000`. Portas: web 3000, api 3001, dados 8000.

## Criar o repositório de outra squad

```bash
./scripts/new-squad.sh <usuario-da-squad> "<Nome>"
# exemplos:
#   ./scripts/new-squad.sh comprasabertas "Compras Abertas"
#   ./scripts/new-squad.sh monitorame "Monitorame"
```

Gera uma cópia em `../<usuario-da-squad>` com usuário, domínio, nomes dos serviços e do nginx trocados. As portas ficam as mesmas, porque cada squad tem o próprio container. O usuário precisa ser o da squad no servidor (`comprasabertas`, `atlas` ou `monitorame`). Os dados de exemplo continuam sendo de compras; troque pelo domínio da squad.

## Dados de exemplo

`scripts/gen-seed.py` gera 180 pedidos de compra sintéticos (sempre os mesmos). Eles ficam em `data/app/seed/pedidos_compra.csv` (usado sem banco) e `db/seed.sql` (para o Postgres).
