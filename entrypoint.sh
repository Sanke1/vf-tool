#!/bin/sh
set -e

cd "$(dirname "$0")"
ls -l
pwd

envsubst < config.json.template > config.json

until nc -z $DB_HOST $DB_PORT; do
  echo "Waiting for MariaDB..."
  sleep 2
done

exec python main.py
