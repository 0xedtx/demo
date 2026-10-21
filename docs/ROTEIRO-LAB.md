# Roteiro do laboratório: PR, Review, Deploy

Objetivo: sair daqui tendo mudado alguma coisa na tela e visto ela entrar no ar sozinha.

## Antes de começar

- Você já configurou o acesso da sua squad (`cloudflared`, `~/.ssh/config`, a pasta com a chave) e `ssh atlas` entra no container. Troque `atlas` pelo nome da sua squad.
- O responsável já configurou o environment `production`, as variables e os secrets ([CONFIGURACAO.md](CONFIGURACAO.md)).
- Leia [COMO-FUNCIONA.md](COMO-FUNCIONA.md) uma vez. É o mapa do que vamos mexer.

## 1. Conhecer o container

```bash
ssh atlas
whoami                    # atlas
ls ~/apps                 # depois do primeiro deploy: demo
sudo systemctl status atlas-api --no-pager
```

## 2. Rodar tudo na sua máquina (3 terminais)

```bash
# terminal 1: dados (FastAPI)
cd data && python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# terminal 2: API (Nest)
cd api && npm install && npm run dev

# terminal 3: tela (Next)
cd web && npm install && npm run dev
```

Abra `http://localhost:3000`. Os três selos no topo devem estar verdes. Sem `DATABASE_URL` os dados vêm do CSV de exemplo.

## 3. Abrir um Pull Request

```bash
git switch -c minha-mudanca
# mude algo pequeno: o título em web/app/page.tsx, uma cor em web/app/globals.css
git add -A && git commit -m "feat: ajusta o título do painel"
git push -u origin minha-mudanca
```

No GitHub, abra o PR para a `main`. O **CI** começa sozinho: build, typecheck e testes dos três serviços.

## 4. Review

- Peça a alguém da squad para revisar.
- Quem revisa lê o diff, roda se precisar e deixa comentários. Aprovar é dizer "pode ir".
- Corrija o que pediram, faça novo push e o CI roda de novo.

## 5. Merge e deploy

Com o PR aprovado e o CI verde, clique em **Merge**. Abra a aba **Actions** e acompanhe o workflow **Deploy**: CI, build, entrada no container pelo túnel, instalação, reinício dos serviços, teste de fumaça.

## 6. Conferir no ar

Abra o domínio da squad e veja a sua mudança. Depois, de dentro do container:

```bash
ssh atlas
sudo journalctl -u atlas-web -n 20 --no-pager
curl 127.0.0.1:8000/health      # o serviço de dados, que só existe aqui dentro
```

Se algo falhou, a tabela "Quando algo dá errado" no final de [COMO-FUNCIONA.md](COMO-FUNCIONA.md) diz onde olhar.

## Desafios extras

- Quebre um teste de propósito e veja o PR ficar vermelho, bloqueado para merge.
- Pare o serviço de dados (`sudo systemctl stop atlas-data`) e veja o selo "dados" ficar vermelho na tela. Depois `sudo systemctl start atlas-data`.
- Adicione um endpoint novo no FastAPI, exponha pelo Nest e mostre na tela: passa pelas três camadas.
- Tente acessar o serviço de dados de fora (`curl https://atlas.amontadavalley.com.br/insights/resumo`) e explique por que não funciona.
