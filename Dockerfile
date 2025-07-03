FROM alpine:latest

# ─────────────────────── System vorbereiten ───────────────────────
RUN apk add --no-cache python3 py3-pip git && \
    ln -sf python3 /usr/bin/python

# Arbeitsverzeichnis
WORKDIR /app

# ─────────────────────── Quellcode klonen ─────────────────────────
RUN git clone https://github.com/Sanke1/vf-tool .

# ─────────────────────── Config‑Verzeichnis ───────────────────────
#  Ordner /config anlegen und Beispiel‑Config hinein kopieren
RUN mkdir -p /config && \
    cp /app/config.example.json /config/config.example.json

# (Optional) Symlink, falls die App /app/config.json erwartet
RUN ln -s /config/config.json /app/config.json || true

# ─────────────────────── Python‑Env + Abhängigkeiten ──────────────
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install mysql-connector-python requests urllib3

# ─────────────────────── Entrypoint kopieren ──────────────────────
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
