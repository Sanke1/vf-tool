import mysql.connector
import requests
import time
import urllib3

# Warnung unterdrücken (nur für Testzwecke!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURATION ---
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "38YR44n8"
DB_NAME = "vf-toolbox"
API_HOST = "https://10.0.0.1:12445"
API_TOKEN = "W104t1Udw42LeWID9op0K_zTlUwiwfAn"
VISIT_REASON = "VF-Tool"  # Wird jetzt korrekt verwendet

# --- SKRIPT ---
# Verbindung zur MariaDB
db = mysql.connector.connect(
    host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME
)
cursor = db.cursor()

# Daten auslesen
cursor.execute("SELECT firstname, lastname, carlicenseplate FROM vf_export_user")
besucher = cursor.fetchall()

# UniFi Access API Konfiguration
headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "accept": "application/json",
    "content-type": "application/json"
}

# Alle Door Groups abrufen
response = requests.get(
    f"{API_HOST}/api/v1/developer/door_groups",
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
    f"{API_HOST}/api/v1/developer/visitors",
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
            f"{API_HOST}/api/v1/developer/visitors/{visitor_id}?is_force=true",
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
        "license_plates": [carlicenseplate]  # Experimentell, laut Forenpost
    }
    response = requests.post(
        f"{API_HOST}/api/v1/developer/visitors",
        headers=headers,
        json=data,
        verify=False
    )
    print(f"Visitor angelegt: {firstname} {lastname}, Antwort: {response.json()}")
