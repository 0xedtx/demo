# Configuração: environments, secrets e container

O código já vem com os workflows prontos. Este checkout publica o produto Atlas no container de testes `demo`, em `demo.amontadavalley.com.br`. A ligação acontece no GitHub e no container; o banco externo é opcional. A infraestrutura em si (container, túnel do Cloudflare, nginx base, Node, Python) já está pronta. Os serviços da aplicação continuam se chamando `atlas-web`, `atlas-api` e `atlas-data`.

## 1. No GitHub (Settings do repositório)

**Environment**: Settings → Environments → New environment → `production`.
Se quiser um freio de segurança, marque *Required reviewers*: o deploy fica esperando alguém aprovar.

**Variables** do environment `production` (valores que podem aparecer):

| Nome | Valor para o ambiente demo |
|---|---|
| `SSH_HOST` | `ssh-demo.amontadavalley.com.br` |
| `SSH_USER` | `demo` |
| `DEPLOY_PATH` | `/home/demo/apps/atlas-demo` (defina explicitamente; sem a variable, o workflow usa `/home/demo/apps/demo`) |
| `SITE_URL` | `https://demo.amontadavalley.com.br` (usado no teste de fumaça; vazio pula o teste) |

**Secrets** do environment `production` (valores sensíveis):

| Nome | O que é |
|---|---|
| `SSH_PRIVATE_KEY` | conteúdo da chave **privada** usada só pelo deploy |
| `SSH_KNOWN_HOSTS` | conteúdo do arquivo `known_hosts` do pacote de acesso da squad (prova que estamos falando com o servidor certo) |

**Qual chave usar?** O pacote de acesso da squad traz uma PEM compartilhada que administra o container inteiro. Funciona, mas é melhor o GitHub ter uma chave própria, que dá para revogar sem mexer na da equipe:

```bash
# na sua máquina, com o acesso ao demo já configurado (ssh demo funcionando)
ssh-keygen -t ed25519 -C "github-actions-demo" -f ./deploy_demo -N ""
ssh-copy-id -i ./deploy_demo.pub demo        # acrescenta a chave pública no container
# conteúdo de ./deploy_demo        -> secret SSH_PRIVATE_KEY
# conteúdo de ~/.ssh/valley-demo/known_hosts -> secret SSH_KNOWN_HOSTS
rm ./deploy_demo ./deploy_demo.pub           # a privada passa a morar só no GitHub
```

Não use `StrictHostKeyChecking no` para "resolver" erros de conexão: o `known_hosts` existe justamente para isso.

**Proteção da main** (Settings → Branches → Add rule para `main`):
- Require a pull request before merging, com 1 aprovação.
- Require status checks to pass: `web (Next)`, `api (Nest)`, `data (FastAPI)`.

Assim ninguém dá push direto na main e nada entra sem passar no CI e sem review.

## 2. No container

Quase nada: o primeiro deploy faz o resto. Só falta, se for ligar o banco, criar o arquivo de ambiente (ele fica só no container, nunca no git):

```bash
ssh demo
mkdir -p ~/apps/atlas-demo
nano ~/apps/atlas-demo/.env
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
3. Abra `https://demo.amontadavalley.com.br`: os três selos no topo (web, api, dados) devem estar verdes.
