#!/usr/bin/env bash
# Cria o repositório de outra squad a partir deste modelo (Atlas), trocando usuário, domínio e nomes.
# Uso: ./scripts/new-squad.sh <usuario-da-squad> "<Nome>"
#   <usuario-da-squad> é o usuário/container da squad no servidor: comprasabertas, atlas ou monitorame.
# As portas (3000, 3001, 8000) não mudam: cada squad tem o próprio container.
set -euo pipefail

if [ $# -ne 2 ]; then
  echo "uso: $0 <usuario-da-squad> \"<Nome>\""
  echo "ex.: $0 comprasabertas \"Compras Abertas\""
  exit 1
fi
slug="$1"; nome="$2"
case "$slug" in
  *[!a-z0-9]*|"") echo "o usuário da squad deve ter só letras minúsculas e números"; exit 1;;
esac

origem="$(cd "$(dirname "$0")/.." && pwd)"
destino="$origem/../$slug"
[ -e "$destino" ] && { echo "já existe $destino"; exit 1; }

mkdir -p "$destino"
(cd "$origem" && tar --exclude=node_modules --exclude=.next --exclude=dist --exclude=.venv \
  --exclude=__pycache__ --exclude=.pytest_cache --exclude=.git -cf - .) | (cd "$destino" && tar -xf -)

# troca de nomes em todos os arquivos de texto (sem mexer em lockfiles nem nos dados)
grep -rIl --exclude=package-lock.json --exclude=pedidos_compra.csv --exclude=seed.sql . "$destino" | while read -r f; do
  perl -pi -e "s/atlas/$slug/g; s/Atlas/$nome/g" "$f"
done
# lockfiles: só o nome do pacote
for lock in "$destino/web/package-lock.json" "$destino/api/package-lock.json"; do
  [ -f "$lock" ] && perl -pi -e "s/\"name\": \"atlas-/\"name\": \"$slug-/g" "$lock"
done
# arquivos cujo nome carrega o da squad
for f in "$destino"/deploy/systemd/atlas-*.template "$destino"/deploy/nginx/atlas-app.conf; do
  [ -e "$f" ] && mv "$f" "$(dirname "$f")/$(basename "$f" | sed "s/atlas/$slug/")"
done

echo "pronto: $destino"
echo "próximos passos: git init, criar o repositório no GitHub e configurar o environment production (docs/CONFIGURACAO.md)"
