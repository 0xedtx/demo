#!/usr/bin/env bash
# Roda DENTRO do container da squad, como o usuário da squad, chamado pelo GitHub Actions
# logo depois de os arquivos serem extraídos. Faz o que não dá para fazer no CI:
# instalar dependências de produção, (re)instalar as units do systemd e o site do nginx,
# reiniciar os serviços e conferir se subiram. Pode rodar quantas vezes quiser.
set -euo pipefail

DIR="$(cd "$(dirname "$0")/.." && pwd)"
APP_USER="$(id -un)"
DOMINIO="demo.amontadavalley.com.br"
SITE_NOME="atlas-app"
cd "$DIR"

echo "==> api: dependências de produção"
(cd api && npm ci --omit=dev --no-audit --no-fund)

echo "==> data: virtualenv e dependências (sem sudo, sem --break-system-packages)"
[ -d data/.venv ] || python3 -m venv data/.venv
data/.venv/bin/python -m pip install --quiet -r data/requirements.txt

[ -f .env ] || echo "AVISO: não existe $DIR/.env; o serviço de dados vai usar o CSV de exemplo"

echo "==> systemd: instalando as units"
for s in web api data; do
  sed -e "s#__APP_DIR__#$DIR#g" -e "s#__APP_USER__#$APP_USER#g" "deploy/systemd/atlas-$s.service.template" \
    | sudo tee "/etc/systemd/system/atlas-$s.service" >/dev/null
done
sudo systemctl daemon-reload
sudo systemctl enable atlas-data atlas-api atlas-web >/dev/null 2>&1
sudo systemctl restart atlas-data atlas-api atlas-web

echo "==> nginx: site $SITE_NOME"
SITE="/etc/nginx/sites-available/$SITE_NOME"
LINK="/etc/nginx/sites-enabled/$SITE_NOME"
if ! sudo cmp -s deploy/nginx/atlas-app.conf "$SITE" || [ ! -L "$LINK" ]; then
  BAK="/etc/nginx/valley-backups/$(date +%Y%m%d%H%M%S)"
  sudo mkdir -p "$BAK"
  MOVIDOS=()
  # tira de sites-enabled os sites antigos DESTE domínio (guarda a cópia de segurança fora de sites-enabled)
  for f in $(sudo grep -l "server_name[[:space:]].*$DOMINIO" /etc/nginx/sites-enabled/* 2>/dev/null || true); do
    [ "$(basename "$f")" = "$SITE_NOME" ] && continue
    sudo cp -L "$f" "$BAK/$(basename "$f").conteudo"
    sudo mv "$f" "$BAK/$(basename "$f")"
    MOVIDOS+=("$(basename "$f")")
  done
  sudo install -o root -g root -m 0644 deploy/nginx/atlas-app.conf "$SITE"
  sudo ln -sfn "$SITE" "$LINK"
  if sudo nginx -t; then
    sudo systemctl reload nginx
    echo "nginx recarregado (backup do site anterior em $BAK)"
  else
    echo "ERRO: nginx -t falhou; voltando ao site anterior" >&2
    sudo rm -f "$LINK"
    for n in "${MOVIDOS[@]}"; do sudo mv "$BAK/$n" "/etc/nginx/sites-enabled/$n"; done
    sudo nginx -t && sudo systemctl reload nginx
    exit 1
  fi
else
  echo "site do nginx já está atualizado"
fi

echo "==> conferindo se subiu"
for i in 1 2 3 4 5 6; do
  if curl -fsS http://127.0.0.1:3001/api/health >/dev/null; then break; fi
  echo "aguardando a api... ($i)"; sleep 3
done
echo -n "api direta:      "; curl -fsS http://127.0.0.1:3001/api/health; echo
echo -n "via nginx local: "; curl -fsS -H "Host: $DOMINIO" http://127.0.0.1/api/health; echo
sudo systemctl is-active atlas-data atlas-api atlas-web
