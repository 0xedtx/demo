# Configuração: environments, secrets e container

O código já vem com os workflows prontos. Falta ligar o repositório ao container da squad, e isso é feito em três lugares: no GitHub, no container e no banco. A infraestrutura em si (container, túnel do Cloudflare, nginx base, Node, Python) já está pronta.

## 1. No GitHub (Settings do repositório)

**Environment**: Settings → Environments → New environment → `production`.
Se quiser um freio de segurança, marque *Required reviewers*: o deploy fica esperando alguém aprovar.

**Variables** do environment `production` (valores que podem aparecer):

| Nome | Valor para o Atlas |
|---|---|
| `SSH_HOST` | `ssh-atlas.amontadavalley.com.br` |
| `SSH_USER` | `atlas` |
| `DEPLOY_PATH` | `/home/atlas/apps/demo` (opcional; esse já é o padrão) |
| `SITE_URL` | `https://atlas.amontadavalley.com.br` (usado no teste de fumaça; vazio pula o teste) |

**Secrets** do environment `production` (valores sensíveis):

| Nome | O que é |
|---|---|
| `SSH_PRIVATE_KEY` | conteúdo da chave **privada** usada só pelo deploy |
| `SSH_KNOWN_HOSTS` | conteúdo do arquivo `known_hosts` do pacote de acesso da squad (prova que estamos falando com o servidor certo) |

**Qual chave usar?** O pacote de acesso da squad traz uma PEM compartilhada que administra o container inteiro. Funciona, mas é melhor o GitHub ter uma chave própria, que dá para revogar sem mexer na da equipe:

```bash
# na sua máquina, com o acesso da squad já configurado (ssh atlas funcionando)
ssh-keygen -t ed25519 -C "github-actions-atlas" -f ./deploy_atlas -N ""
ssh-copy-id -i ./deploy_atlas.pub atlas        # acrescenta a chave pública no container
# conteúdo de ./deploy_atlas        -> secret SSH_PRIVATE_KEY
# conteúdo de ~/.ssh/valley-atlas/known_hosts -> secret SSH_KNOWN_HOSTS
rm ./deploy_atlas ./deploy_atlas.pub           # a privada passa a morar só no GitHub
```

Não use `StrictHostKeyChecking no` para "resolver" erros de conexão: o `known_hosts` existe justamente para isso.

**Proteção da main** (Settings → Branches → Add rule para `main`):
- Require a pull request before merging, com 1 aprovação.
- Require status checks to pass: `web (Next)`, `api (Nest)`, `data (FastAPI)`.

Assim ninguém dá push direto na main e nada entra sem passar no CI e sem review.

## 2. No container

Quase nada: o primeiro deploy faz o resto. Só falta, se for ligar o banco, criar o arquivo de ambiente (ele fica só no container, nunca no git):

```bash
ssh atlas
mkdir -p ~/apps/demo
nano ~/apps/demo/.env
```

```
DATABASE_URL=postgresql+psycopg2://USUARIO:SENHA@HOST-DO-BANCO:5432/NOME_DO_BANCO?sslmode=require
```

Sem esse arquivo o serviço de dados usa o CSV de exemplo, o que é ótimo para testar o fluxo antes de ligar o banco. Depois de criar ou mudar o `.env`: `sudo systemctl restart atlas-data`.

**O que o primeiro deploy mexe no container** (tudo pelo `deploy/remote-deploy.sh`, sempre como o usuário da squad, com `sudo` só onde precisa):

1. Instala as dependências (`npm ci` para a API, `venv` + `pip` para os dados), sem `sudo` e sem tocar no Python do sistema.
2. Instala três units do systemd (`atlas-web`, `atlas-api`, `atlas-data`), habilita no boot e reinicia.
3. Troca o site do nginx deste domínio pelo `deploy/nginx/atlas-app.conf`. O site anterior (a página de boas-vindas) é movido para `/etc/nginx/valley-backups/<data-hora>/`. Se o `nginx -t` falhar, o site anterior volta sozinho. O `include` das páginas de erro do Valley é mantido.

Para reverter na mão: remova o link `/etc/nginx/sites-enabled/atlas-app`, devolva o arquivo do backup para `sites-enabled`, rode `sudo nginx -t` e só então `sudo systemctl reload nginx`.

## 3. No banco (Postgres externo)

```bash
psql "$DATABASE_URL" -f db/schema.sql   # cria a tabela pedidos_compra
psql "$DATABASE_URL" -f db/seed.sql     # carrega 180 pedidos de exemplo
```

(Para o `psql`, use a URL sem o `+psycopg2`: `postgresql://USUARIO:SENHA@HOST:5432/NOME`.)

Os dados são sintéticos, gerados por `scripts/gen-seed.py` com nomes de fornecedores inventados, mas com volume, valores, prazos e atrasos parecidos com os de uma operação de compras de verdade. Para usar dados reais, é só apontar `DATABASE_URL` para uma tabela com as mesmas colunas de `db/schema.sql`.

## Conferindo se ficou tudo ligado

1. Faça uma mudança pequena, abra um PR e veja o CI rodar.
2. Faça o merge e acompanhe a aba **Actions**.
3. Abra `https://atlas.amontadavalley.com.br`: os três selos no topo (web, api, dados) devem estar verdes.
