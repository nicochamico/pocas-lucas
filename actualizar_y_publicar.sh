#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 actualizar_ofertas.py
netlify deploy --prod --dir=.
