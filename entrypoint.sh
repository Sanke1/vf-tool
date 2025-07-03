#!/bin/sh
set -e

# ─────────────────────── Config prüfen ────────────────────────────
# Wenn KEINE /config/config.json vorhanden ist → Vorlage kopieren
if [ ! -f /config/config.json ]; then
  echo "[INFO] /config/config.json nicht gefunden – erstelle aus config.example.json"
  cp /config/config.example.json /config/config.json
fi

# (Optional) Symlink jeweils aktualisieren
ln -sf /config/config.json /app/config.json

# ─────────────────────── Anwendung starten ────────────────────────
exec /app/venv/bin/python3 your_script.py  "$@"


exec /app/venv/bin/python main.py
