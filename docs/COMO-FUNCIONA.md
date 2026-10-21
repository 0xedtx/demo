# Como tudo conversa (sem mistério)

Esse é o roteiro do "de onde vem o que aparece na tela". Leia uma vez de ponta a ponta, depois use como consulta.

## Onde as coisas moram

O Amontada Valley tem um servidor (o notebook `valley`, com Ubuntu Server) que roda **um container por squad**. Cada container é um mini Ubuntu isolado, com usuário, pasta e rede próprios:

| Squad | Usuário no container | Site | SSH |
|---|---|---|---|
| Compras Abertas | `comprasabertas` | `comprasabertas.amontadavalley.com.br` | `ssh-comprasabertas.amontadavalley.com.br` |
| Atlas | `atlas` | `atlas.amontadavalley.com.br` | `ssh-atlas.amontadavalley.com.br` |
| Monitorame | `monitorame` | `monitorame.amontadavalley.com.br` | `ssh-monitorame.amontadavalley.com.br` |

Como cada squad tem o próprio container, o `localhost` de uma squad **não é** o `localhost` da outra. Por isso todas podem usar as mesmas portas sem brigar. Este repositório usa o Atlas como exemplo.

## O elenco dentro do container

| Quem | Tecnologia | Porta | Quem pode chamar |
|---|---|---|---|
| **nginx** | porteiro do container | `80` | o túnel do Cloudflare |
| **web** (a tela) | Next | `3000` | só o nginx |
| **api** (as regras) | Nest | `3001` | só o nginx |
| **dados** (as contas) | FastAPI + pandas | `8000` | só a api, por `localhost` |

E um quinto personagem que mora **fora** do container: o **banco de dados** (Postgres). Só o serviço de dados fala com ele.

## O caminho de uma requisição

Alguém abre `https://atlas.amontadavalley.com.br`:

```
 navegador
    │  1. "quem é atlas.amontadavalley.com.br?"
    ▼
 DNS / Cloudflare ── aponta para o Cloudflare, que cuida do HTTPS
    │
    │  2. túnel "valley_server": o servidor liga PARA o Cloudflare
    │     (nenhuma porta aberta no roteador, nenhum IP público exposto)
    ▼
 servidor valley ── cloudflared recebe o pedido
    │
    │  3. entrega no container do Atlas, porta 80
    ▼
 ┌──────────────── container "atlas" (Ubuntu 24.04) ─────────────────┐
 │                                                                   │
 │   nginx :80                                                       │
 │     ├─ caminho  /        ──►  Next   127.0.0.1:3000   (a tela)    │
 │     └─ caminho  /api/... ──►  Nest   127.0.0.1:3001   (a API)     │
 │                                  │                                │
 │                                  │  4. fetch por localhost        │
 │                                  ▼                                │
 │                             FastAPI  127.0.0.1:8000   (dados)     │
 │                                  │                                │
 └──────────────────────────────────┼────────────────────────────────┘
                                    │  5. DATABASE_URL (saída pela Internet)
                                    ▼
                          Postgres (banco externo)
```

Passo a passo:

1. **DNS** traduz o nome. O endereço aponta para o Cloudflare, não para a nossa casa.
2. **Túnel**: o servidor mantém uma conexão de saída com o Cloudflare. Os pedidos descem por ela. Por isso não precisamos abrir porta nem ter IP fixo.
3. **cloudflared** entrega o pedido no nginx do container da squad.
4. **nginx** olha o caminho. Se começa com `/api/`, manda para o Nest. Qualquer outra coisa vai para o Next. A regra está em `deploy/nginx/atlas-app.conf` e cabe numa tela.
5. **Nest** (a API) recebe `/api/dashboard`, não calcula nada sozinho e pergunta ao serviço de dados em `http://127.0.0.1:8000`. É `localhost`: a conversa nunca sai do container.
6. **FastAPI** carrega os pedidos (do banco, se existir `DATABASE_URL`; senão do CSV de exemplo), faz as contas com pandas e devolve números.
7. A resposta volta pelo mesmo caminho. O Next é só a casca: o navegador chama `/api/dashboard` e desenha o resultado.

## Por que a parte de dados fica escondida?

Porque ela não precisa de ninguém de fora. Quem precisa dos números é a API.

- O FastAPI escuta em `127.0.0.1`, não em `0.0.0.0`: mesmo que alguém tente, a porta 8000 só aceita conversa de dentro do container.
- O nginx não tem nenhuma regra apontando para ela.
- O container é isolado dos outros: as squads não alcançam a rede umas das outras.

Dá para provar isso de dentro do container (`ssh atlas`):

```bash
curl http://127.0.0.1:8000/health                       # funciona: você está dentro
curl https://atlas.amontadavalley.com.br/api/health     # funciona: passa pelo porteiro
curl https://atlas.amontadavalley.com.br/docs           # não é do serviço de dados: cai na tela (Next)
```

## E o banco de dados?

O banco é **externo** (por exemplo um Postgres gerenciado na nuvem). Duas coisas importantes:

- O container sai para a Internet, mas **não** alcança redes privadas (`10.x`, `192.168.x`): isso é de propósito, para isolar as squads. Então o banco precisa ser acessível pela Internet, com senha e SSL (`?sslmode=require` na URL).
- A URL com a senha vive só no arquivo `.env` **dentro do container**. Nunca no git.

## Como o código chega no container

```
você ──► branch ──► Pull Request ──► review ──► merge na main
                         │                          │
                    CI roda (build,            Action de deploy:
                    typecheck, testes)         1. roda o CI de novo
                                               2. faz o build e empacota
                                               3. entra no container por SSH,
                                                  pelo túnel do Cloudflare
                                               4. extrai os arquivos em ~/apps/demo
                                               5. remote-deploy.sh: instala dependências,
                                                  atualiza as units do systemd e o nginx,
                                                  reinicia web, api e dados
                                               6. teste de fumaça em /api/health
```

O GitHub entra no container **por SSH**, com uma chave guardada nos Secrets do repositório, usando o mesmo `cloudflared` que você usa na sua máquina. Como criar e guardar essa chave está em [CONFIGURACAO.md](CONFIGURACAO.md).

Quem mantém os três programas de pé é o **systemd**, o gerenciador de serviços do Ubuntu: ele sobe tudo quando o container liga e levanta de novo se algum cair.

## Mini dicionário

- **Container**: um mini Ubuntu isolado dentro do servidor. Um por squad.
- **Túnel (Cloudflare Tunnel)**: conexão de saída do servidor para o Cloudflare. Os pedidos chegam por ela.
- **Proxy reverso**: o nginx recebendo pedidos e repassando para programas locais.
- **localhost / 127.0.0.1**: "este mesmo container". Quem fala por aqui não sai dele.
- **Porta**: o "ramal" da máquina. Um endereço, milhares de portas, cada programa atende uma.
- **systemd**: o cuidador que mantém os programas rodando e sobe de novo se caírem.
- **CI/CD**: CI é testar toda mudança automaticamente. CD é entregar sozinho depois que passou.
- **Secret**: valor sensível guardado no GitHub (chave, senha) que o workflow usa sem mostrar.

## Quando algo dá errado

Dentro do container (`ssh atlas`):

| Sintoma | Onde olhar |
|---|---|
| Tela abre, mas mostra "Não consegui falar com a API" | `sudo systemctl status atlas-api` e `sudo journalctl -u atlas-api -n 100 --no-pager` |
| API responde, mas o painel diz "dados fora do ar" | `sudo journalctl -u atlas-data -n 100 --no-pager` e `curl 127.0.0.1:8000/health` |
| 502 Bad Gateway | o nginx não alcançou a porta: o serviço correspondente caiu (`sudo systemctl status atlas-web`) |
| Deploy falhou no passo de SSH | secrets `SSH_PRIVATE_KEY` e `SSH_KNOWN_HOSTS`, variables `SSH_HOST` e `SSH_USER` |
| Deploy falhou no passo do nginx | o `remote-deploy.sh` já voltou o site anterior; veja o backup em `/etc/nginx/valley-backups/` |
