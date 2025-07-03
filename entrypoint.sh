#!/bin/sh

# Prüfen, ob config.json im gemounteten /app/config fehlt
if [ ! -f /app/config/config.json ]; then
    cp /app/example.config.json /app/config/config.json
fi

exec /app/venv/bin/python main.py
