#!/usr/bin/env bash
# Lance le site en local : http://localhost:${PORT:-8080}
cd "$(dirname "$0")/.."
python3 -m http.server "${PORT:-8080}"
