import requests
import json
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime

# Lade Konfiguration
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

BASE_URL = config['base_url']
USERNAME = config['username']
PASSWORD = config['password']
APPKEY = config['appkey']
DB_CONFIG = config['db_config']
EXPORT_USERS = config['export_users']
EXPORT_FLIGHTS = config['export_flights']
EXPORT_RESERVATIONS = config['export_reservations']


# ----------------------------------------

def create_database_and_tables():
    conn = mysql.connector.connect(user=DB_CONFIG['user'], password=DB_CONFIG['password'], host=DB_CONFIG['host'])
    cursor = conn.cursor()

    try:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_CONFIG['database']}` DEFAULT CHARACTER SET 'utf8mb4'")
    except mysql.connector.Error as err:
        raise Exception(f"Fehler beim Erstellen der Datenbank: {err}")

    conn.database = DB_CONFIG['database']

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vf_export_user (
            uid INT PRIMARY KEY,
            firstname TEXT,
            lastname TEXT,
            carlicenseplate TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vf_export_flights_today (
            flid INT PRIMARY KEY,
            createtime DATETIME,
            modifytime DATETIME,
            callsign TEXT,
            pilotname TEXT,
            attendantname TEXT,
            dateofflight DATE,
            departuretime TIME,
            arrivaltime TIME,
            departurelocation TEXT,
            arrivallocation TEXT,
            flighttime INT,
            landingcount INT,
            comment TEXT
        )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS vf_export_reservations (
        prid INT PRIMARY KEY,
        datefrom DATETIME,
        dateto DATETIME,
        comment TEXT,
        freeseats INT,
        user TEXT,
        fi TEXT,
        type TEXT,
        ressource TEXT,
        daterange TEXT,
        duration TEXT
    )
''')


    conn.commit()
    cursor.close()
    conn.close()

def get_connection():
    return mysql.connector.connect(**DB_CONFIG)

def authenticate():
    token_response = requests.get(
        f"{BASE_URL}interface/rest/auth/accesstoken",
        headers={'Accept': 'application/json'}
    )
    token_response.raise_for_status()
    access_token = token_response.json()['accesstoken']

    login_data = {
        'accesstoken': access_token,
        'username': USERNAME,
        'password': PASSWORD,
        'appkey': APPKEY
    }

    headers = {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
    }

    login_response = requests.post(
        f"{BASE_URL}interface/rest/auth/signin",
        data=login_data,
        headers=headers
    )
    login_response.raise_for_status()
    
    return access_token

def logout(access_token):
    requests.post(
        f"{BASE_URL}interface/rest/auth/signout",
        data={'accesstoken': access_token},
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )

def get_user_list(access_token):
    response = requests.post(
        f"{BASE_URL}interface/rest/user/list",
        data={'accesstoken': access_token},
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    response.raise_for_status()
    users = response.json()
    if isinstance(users, dict):
        if 'httpstatuscode' in users:
            users.pop('httpstatuscode')
        users = list(users.values())
    return users


def get_flights_today(access_token):
    response = requests.post(
        f"{BASE_URL}interface/rest/flight/list/today",
        data={'accesstoken': access_token},
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    response.raise_for_status()
    data = response.json()
    
    # Filtere nur Einträge, die ein Dict (Flugdaten) sind:
    flights = [entry for entry in data.values() if isinstance(entry, dict) and "flid" in entry]
    return flights


import re

def clean_licenseplate(plate):
    # Entferne alle Sonderzeichen, Leerzeichen und Bindestriche; lasse nur Buchstaben und Zahlen
    return re.sub(r'[^a-zA-Z0-9]', '', str(plate))

def save_users_to_db(users):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vf_export_user")  # Alte Daten löschen
    saved = 0
    for user in users:
        if not isinstance(user, dict):
            continue
        uid = user.get('uid', '')
        try:
            uid_int = int(uid) if str(uid).isdigit() else None
        except:
            uid_int = None
        carlicenseplate = user.get('carlicenseplate', '')
        # Nur User mit Kennzeichen speichern
        if carlicenseplate:
            # Kennzeichen bereinigen
            clean_plate = clean_licenseplate(carlicenseplate)
            cursor.execute('''
                REPLACE INTO vf_export_user (uid, firstname, lastname, carlicenseplate)
                VALUES (%s, %s, %s, %s)
            ''', (
                uid_int,
                user.get('firstname', ''),
                user.get('lastname', ''),
                clean_plate
            ))
            saved += 1
    conn.commit()
    cursor.close()
    conn.close()
    return saved

def save_flights_to_db(flight_list):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vf_export_flights_today") #Alte Daten löschen
    saved = 0
    for flight in flight_list:
        if not str(flight.get("flid", "")).isdigit():
            continue  # Sicherheitscheck

        cursor.execute('''
            REPLACE INTO vf_export_flights_today (
                flid, createtime, modifytime, callsign, pilotname,
                attendantname, dateofflight, departuretime, arrivaltime,
                departurelocation, arrivallocation, flighttime,
                landingcount, comment
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            int(flight["flid"]),
            flight.get("createtime"),
            flight.get("modifytime"),
            flight.get("callsign"),
            flight.get("pilotname"),
            flight.get("attendantname"),
            flight.get("dateofflight"),
            flight.get("departuretime"),
            flight.get("arrivaltime"),
            flight.get("departurelocation"),
            flight.get("arrivallocation"),
            int(flight["flighttime"]) if flight.get("flighttime") else 0,
            int(flight["landingcount"]) if flight.get("landingcount") else 0,
            flight.get("comment", "")
        ))
        saved += 1
    conn.commit()
    cursor.close()
    conn.close()
    return saved

def get_reservations(access_token):
    response = requests.post(
        f"{BASE_URL}interface/rest/reservation/list/active",
        data={'accesstoken': access_token},
        headers={'Content-Type': 'application/x-www-form-urlencoded'}
    )
    response.raise_for_status()
    data = response.json()
    
    reservations = [entry for entry in data.values() 
                   if isinstance(entry, dict) and "prid" in entry]
    return reservations

def save_reservations_to_db(reservations):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM vf_export_reservations")
    saved = 0
    
    for res in reservations:
        cursor.execute('''
            REPLACE INTO vf_export_reservations (
                prid, datefrom, dateto, comment, freeseats,
                user, fi, type, ressource, daterange, duration
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            res["prid"],
            res.get("datefrom"),
            res.get("dateto"),
            res.get("comment", ""),
            int(res.get("freeseats", 0)),
            res.get("user", ""),
            res.get("fi", ""),
            res.get("type", ""),
            res.get("ressource", ""),
            res.get("daterange", ""),
            res.get("duration", "")
        ))
        saved += 1
    
    conn.commit()
    cursor.close()
    conn.close()
    return saved


def main():
    try:
        print("Initialisiere Datenbank...")
        create_database_and_tables()
        print("Authentifiziere bei Vereinsflieger...")
        access_token = authenticate()

        if EXPORT_USERS:
            print("Lade Benutzerliste...")
            users = get_user_list(access_token)
            print("API-Antwort:", users)  # <-- Diese Zeile neu einfügen!
            count = save_users_to_db(users)
            print(f"{count} Benutzer gespeichert.")

        if EXPORT_FLIGHTS:
            print("Lade heutige Flüge...")
            flights = get_flights_today(access_token)
            count = save_flights_to_db(flights)
            print(f"{count} Flüge gespeichert.")

        if EXPORT_RESERVATIONS:
            print("Lade aktive Reservierungen...")
            reservations = get_reservations(access_token)
            count = save_reservations_to_db(reservations)
            print(f"{count} Reservierungen gespeichert.")

        logout(access_token)
        print("Fertig.")

    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    main()
