import mysql.connector
import requests
import time
import urllib3
import json

# Warnung unterdrücken (nur für Testzwecke!)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Lade Konfiguration
try:
    with open('config/config.json', 'r', encoding='utf-8') as f:
        config = json.load(f)
except FileNotFoundError:
    print("Fehler: config.json nicht gefunden!")
    exit()
except json.JSONDecodeError:
    print("Fehler: config.json ist keine gültige JSON-Datei!")
    exit()

# --- KONFIGURATION ---
DB_CONFIG = config['db_config']
UNIFI_IP = config['UNIFI_IP']
UNIFI_API_TOKEN = config['UNIFI_API_TOKEN']
VISIT_REASON = "VF-Tool"

# --- SKRIPT ---
db = None # Vorinitialisieren für den finally-Block
try:
    # NEU: explizite Angabe des Charsets, um Encoding-Probleme (z.B. bei 'ö') zu vermeiden
    db = mysql.connector.connect(
        user=DB_CONFIG['user'], 
        password=DB_CONFIG['password'], 
        host=DB_CONFIG['host'],
        database=DB_CONFIG['database'],
        charset='utf8mb4' 
    )
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
    print("Rufe Door Groups ab...")
    response = requests.get(
        f"{UNIFI_IP}/api/v1/developer/door_groups/topology",
        headers=headers,
        verify=False
    )
    response.raise_for_status() # Löst einen Fehler aus, wenn der HTTP-Status nicht 2xx ist
    door_groups = response.json()["data"]
    resources = [{"id": dg["id"], "type": "door_group"} for dg in door_groups]
    print(f"{len(door_groups)} Door Groups gefunden.")

    # Zugang für eine Woche
    start_time = int(time.time())
    end_time = start_time + 7 * 24 * 60 * 60

    # --- Vorher alle Visitors mit Besuchsgrund "VF-Tool" löschen ---
    print("\nLösche alte Visitors mit Grund 'VF-Tool'...")
    response = requests.get(
        f"{UNIFI_IP}/api/v1/developer/visitors",
        headers=headers,
        verify=False
    )
    response.raise_for_status()
    visitors = response.json().get("data", [])

    deleted_count = 0
    for visitor in visitors:
        if visitor.get("visit_reason") == VISIT_REASON:
            visitor_id = visitor["id"]
            delete_url = f"{UNIFI_IP}/api/v1/developer/visitors/{visitor_id}?is_force=true"
            # print(f"Lösche Visitor ID: {visitor_id}") # Optional: für Debugging
            response = requests.delete(delete_url, headers=headers, verify=False)
            if response.status_code == 200 and response.json().get('code') == 'SUCCESS':
                deleted_count += 1
            else:
                print(f"WARNUNG: Konnte Visitor {visitor_id} nicht löschen. Status: {response.status_code}, Antwort: {response.text}")
    print(f"{deleted_count} alte Visitors gelöscht.")

    # --- Neue Visitors anlegen ---
    print("\nLege neue Visitors an...")
    for firstname, lastname, carlicenseplate in besucher:
        
        # NEU: Datenbereinigung und Validierung
        # Entfernt führende/nachfolgende Leerzeichen, die Probleme verursachen können
        clean_firstname = firstname.strip() if firstname else "Unbekannt"
        clean_lastname = lastname.strip() if lastname else "Unbekannt"
        
        license_plates_list = []
        # Stellt sicher, dass das Kennzeichen nicht leer oder None ist, bevor es hinzugefügt wird
        if carlicenseplate and carlicenseplate.strip():
            license_plates_list.append(carlicenseplate.strip())

        data = {
            "first_name": clean_firstname,
            "last_name": clean_lastname,
            "remarks": f"Kennzeichen: {carlicenseplate.strip() if carlicenseplate else 'Keins'}",
            "mobile_phone": "",
            "email": "",
            "visitor_company": "",
            "start_time": start_time,
            "end_time": end_time,
            "visit_reason": VISIT_REASON,
            "resources": resources,
            # NEU: Nur hinzufügen, wenn Kennzeichen vorhanden
            "license_plates": license_plates_list 
        }

        print(f"--- Verarbeite: {clean_firstname} {clean_lastname} ---")
        try:
            response = requests.post(
                f"{UNIFI_IP}/api/v1/developer/visitors",
                headers=headers,
                json=data,
                verify=False,
                timeout=10 # NEU: Timeout hinzugefügt
            )
            
            # NEU: Detaillierte Fehlerprüfung
            response_data = response.json()
            if response.status_code == 200 and response_data.get('code') == 'SUCCESS':
                print(f"ERFOLG: Visitor '{clean_firstname} {clean_lastname}' erfolgreich angelegt.")
            else:
                print(f"FEHLER bei '{clean_firstname} {clean_lastname}'!")
                print(f"  -> Status Code: {response.status_code}")
                print(f"  -> API Antwort: {response_data}")
                print("  -> Gesendete Daten:")
                # Gibt die gesendeten Daten schön formatiert aus, damit du sie überprüfen kannst
                print(json.dumps(data, indent=4, ensure_ascii=False))
                print("-" * 20)

        except requests.exceptions.RequestException as e:
            print(f"FEHLER bei der API-Anfrage für '{clean_firstname} {clean_lastname}': {e}")

finally:
    # NEU: Sicherstellen, dass die Datenbankverbindung immer geschlossen wird
    if db and db.is_connected():
        cursor.close()
        db.close()
        print("\nDatenbankverbindung geschlossen.")

