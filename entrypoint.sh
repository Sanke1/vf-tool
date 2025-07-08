#!/bin/sh
set -e

tail -f /dev/null

# config.json aus Template erzeugen
envsubst < config/config.json.template > config/config.json

# Warten bis Datenbank erreichbar ist (optional, für Robustheit)
until nc -z $DB_HOST $DB_PORT; do
  echo "Waiting for MariaDB..."
  sleep 2
done

# Python-App starten
exec python main.py
