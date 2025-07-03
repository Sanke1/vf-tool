FROM alpine:latest

# Installiere Python und pip
RUN apk add --no-cache python3 py3-pip git && \
    ln -sf python3 /usr/bin/python

# Arbeitsverzeichnis erstellen
WORKDIR /app

# Klone das GitHub-Repository (ersetze URL ggf. durch dein Repo)
RUN git clone https://$GIT_TOKEN@github.com/Sanke1/vf-tool . 

# Installiere Python-Abhängigkeiten, falls requirements.txt vorhanden
# RUN pip install -r requirements.txt

# Standardmäßig wird das Python-Skript gestartet (ersetze main.py durch deinen Einstiegspunkt)
CMD ["python", "main.py"]
