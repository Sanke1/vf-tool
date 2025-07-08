FROM alpine:latest

RUN apk add --no-cache python3 py3-pip git bash gettext

WORKDIR /app

RUN git clone https://github.com/Sanke1/vf-tool .

# Virtuelle Umgebung anlegen und Pakete installieren
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir mysql-connector-python requests urllib3

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Starte das Skript immer mit der venv
ENV PATH="/app/venv/bin:$PATH"

ENTRYPOINT ["/app/entrypoint.sh"]
