import mysql.connector
import requests
import time
import urllib3
import json

# Warnung unterdrücken (nur für Testzwecke!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Lade Konfiguration
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# --- KONFIGURATION ---
DB_CONFIG = config['db_config']
UNIFI_IP = config['UNIFI_IP']
UNIFI_API_TOKEN = config['UNIFI_API_TOKEN']
VISIT_REASON = "VF-Tool"  # Wird jetzt korrekt verwendet

# --- SKRIPT ---
# Verbindung zur MariaDB
db = mysql.connector.connect(user=DB_CONFIG['user'], password=DB_CONFIG['password'], host=DB_CONFIG['host'],database=DB_CONFIG['database'])
cursor = db.cursor()

# Daten auslesen
cursor.execute("SELECT firstname, lastname, carlicenseplate FROM vf_export_user")
besucher = cursor.fetchall()

# UniFi Access API Konfiguration
headers = {
    "Authorization": f"Bearer {UNIFI_API_TOKEN}",
    "accept": "application/json",
    "content-type": "application/json"
}

# Alle Door Groups abrufen
response = requests.get(
    f"{UNIFI_IP}/api/v1/developer/door_groups/",
    headers=headers,
    verify=False
)
door_groups = response.json()["data"]
resources = [{"id": dg["id"], "type": "door_group"} for dg in door_groups]

# Zugang für eine Woche
start_time = int(time.time())
end_time = start_time + 7 * 24 * 60 * 60

# --- Vorher alle Visitors mit Besuchsgrund "VF-Tool" löschen ---
response = requests.get(
    f"{UNIFI_IP}/api/v1/developer/visitors",
    headers=headers,
    verify=False
)
visitors = response.json().get("data", [])

# Alle Visitors mit visit_reason = "VF-Tool" löschen
for visitor in visitors:
    if visitor.get("visit_reason") == VISIT_REASON:  # Jetzt ist VISIT_REASON definiert!
        visitor_id = visitor["id"]
        # Füge is_force=true hinzu für physisches Löschen
        response = requests.delete(
            f"{UNIFI_IP}/api/v1/developer/visitors/{visitor_id}?is_force=true",
            headers=headers,
            verify=False
        )
        print(f"Visitor gelöscht: ID {visitor_id}, Antwort: {response.json()}")

# --- Neue Visitors anlegen ---
for firstname, lastname, carlicenseplate in besucher:
    data = {
        "first_name": firstname,
        "last_name": lastname,
        "remarks": f"Kennzeichen: {carlicenseplate}",
        "mobile_phone": "",
        "email": "",
        "visitor_company": "",
        "start_time": start_time,
        "end_time": end_time,
        "visit_reason": VISIT_REASON,
        "resources": resources,
        "license_plates": [carlicenseplate]
    }
    response = requests.post(
        f"{UNIFI_IP}/api/v1/developer/visitors",
        headers=headers,
        json=data,
        verify=False
    )
    print(f"Visitor angelegt: {firstname} {lastname}, Antwort: {response.json()}")
