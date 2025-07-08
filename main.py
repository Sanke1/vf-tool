#!/usr/bin/env python3
"""module_check_and_schedule.py

Prüft, ob die benötigten Module vorhanden sind, führt anschließend die beiden
Skripte »vf_extract_toDB.py« und »unifiaccess_db_sync.py« aus und wiederholt
diesen Durchlauf alle 24 Stunden.

Beenden jederzeit mit Ctrl‑C.
"""

import subprocess
import time
import datetime
import importlib
import sys
import traceback

# 1) Modul‑Check -------------------------------------------------------------
modules = [
    "json",
    "mysql.connector",
    "requests",
    "time",
    "datetime",
    "urllib3",
]

print("\n➡️  Überprüfe benötigte Python‑Module …\n")
for module in modules:
    try:
        importlib.import_module(module)
        print(f"✅ Modul '{module}' ist installiert.")
    except ImportError:
        print(f"❌ Modul '{module}' ist NICHT installiert. Bitte nachinstallieren!")
    except Exception as e:
        print(f"⚠️  Fehler beim Prüfen von '{module}': {e}")

# 2) Hilfsfunktion zum Ausführen der Skripte ---------------------------------

def run_scripts():
    """Startet erst vf_extract_toDB.py, danach unifiaccess_db_sync.py.
    Gibt True zurück, wenn beide Skripte erfolgreich durchgelaufen sind, sonst False."""
    success = True

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] Starte 'vf_extract_toDB.py' …")
    try:
        res1 = subprocess.run([sys.executable, "vf_extract_toDB.py"], capture_output=True, text=True, timeout=1800)
        print(res1.stdout)
        if res1.stderr:
            print(res1.stderr, file=sys.stderr)
        if res1.returncode != 0:
            print(f"❌ 'vf_extract_toDB.py' Fehlercode: {res1.returncode}")
            success = False
    except Exception as e:
        print(f"❌ Ausnahme beim Ausführen von 'vf_extract_toDB.py': {e}")
        traceback.print_exc()
        success = False

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Starte 'unifiaccess_db_sync.py' …")
    try:
        res2 = subprocess.run([sys.executable, "unifiaccess_db_sync.py"], capture_output=True, text=True, timeout=1800)
        print(res2.stdout)
        if res2.stderr:
            print(res2.stderr, file=sys.stderr)
        if res2.returncode != 0:
            print(f"❌ 'unifiaccess_db_sync.py' Fehlercode: {res2.returncode}")
            success = False
    except Exception as e:
        print(f"❌ Ausnahme beim Ausführen von 'unifiaccess_db_sync.py': {e}")
        traceback.print_exc()
        success = False

    return success

# 3) Endlosschleife mit 24‑Stunden‑Pause und Failsafe ------------------------

def main():
    try:
        while True:
            success = run_scripts()
            if not success:
                print("\n⚠️ Fehler beim Ausführen der Skripte. Versuche es in 24 Stunden erneut.")
            else:
                print("\n✅ Beide Skripte wurden erfolgreich ausgeführt.")
            print("\n⏳ Warte 24 h bis zum nächsten Durchlauf …\n")
            time.sleep(24 * 60 * 60)  # 24 Stunden in Sekunden
    except KeyboardInterrupt:
        print("\nAbbruch durch Benutzer – Programm beendet.")

if __name__ == "__main__":
    main()
