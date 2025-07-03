#!/usr/bin/env python3
"""module_check_and_schedule.py

Prüft, ob die benötigten Module vorhanden sind, führt anschließend die beiden
Skripte »vf_extract_toDB.py« und »unifiaccess_db_sync.py« aus und wiederholt
diesen Durchlauf alle 24 Stunden.

Benutzung:
    $ python3 module_check_and_schedule.py

Beenden jederzeit mit Ctrl‑C.
"""

import subprocess
import time
import datetime
import importlib
import sys

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

def run_scripts() -> None:
    """Startet erst vf_extract_toDB.py, danach unifiaccess_db_sync.py."""

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n[{timestamp}] Starte 'vf_extract_toDB.py' …")
    res1 = subprocess.run([sys.executable, "vf_extract_toDB.py"], capture_output=True, text=True)
    print(res1.stdout)
    if res1.stderr:
        print(res1.stderr, file=sys.stderr)

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] Starte 'unifiaccess_db_sync.py' …")
    res2 = subprocess.run([sys.executable, "unifiaccess_db_sync.py"], capture_output=True, text=True)
    print(res2.stdout)
    if res2.stderr:
        print(res2.stderr, file=sys.stderr)

# 3) Endlosschleife mit 24‑Stunden‑Pause -------------------------------------

def main() -> None:
    try:
        while True:
            run_scripts()
            print("\n⏳ Warte 24 h bis zum nächsten Durchlauf …\n")
            time.sleep(24 * 60 * 60)  # 24 Stunden in Sekunden
    except KeyboardInterrupt:
        print("\nAbbruch durch Benutzer – Programm beendet.")


if __name__ == "__main__":
    main()
