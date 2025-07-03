#!/bin/sh
set -e

echo "🔍 Prüfe, ob config.json existiert …"
if [ ! -f "$LIVE_CFG" ]; then
  echo "📝 Konfiguration nicht gefunden – erstelle Standard-config.json"
  mkdir -p "$LIVE_CFG_DIR"
  cp "$DEFAULT_CFG" "$LIVE_CFG"
fi

echo "🚀 Starte Python-Anwendung"
exec "$@"
