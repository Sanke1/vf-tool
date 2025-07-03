FROM alpine:latest

RUN apk add --no-cache python3 py3-pip git && \
    ln -sf python3 /usr/bin/python

WORKDIR /app

# Klone Repo
RUN git clone https://github.com/Sanke1/vf-tool .

# Erstelle virtuelles Environment + installiere Pakete
RUN python3 -m venv /app/venv && \
    /app/venv/bin/pip install --upgrade pip && \
    /app/venv/bin/pip install mysql-connector-python requests urllib3

# Verzeichnis als Volume kennzeichnen
CMD ["/app/venv/bin/python", "main.py"]
