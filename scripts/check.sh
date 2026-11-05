#!/usr/bin/env bash
# Vérifications avant déploiement : HTML valide + fichiers locaux référencés présents.
set -euo pipefail
cd "$(dirname "$0")/.."
test -f index.html || { echo "index.html manquant"; exit 1; }
npx --yes html-validate@8.24.1 index.html
missing=0
for f in $(grep -oE '(src|href)="[^"#:]+"' index.html | sed -E 's/.*="([^"]+)"/\1/' | sort -u); do
  [ -e "$f" ] || { echo "Fichier référencé introuvable : $f"; missing=1; }
done
[ "$missing" -eq 0 ] && echo "OK : toutes les vérifications passent."
exit "$missing"
