modules = [
    "json",
    "mysql.connector",
    "requests",
    "time",
    "datetime",
    "urllib3"
]

for module in modules:
    try:
        __import__(module)
        print(f"✅ Modul '{module}' ist installiert.")
    except ImportError:
        print(f"❌ Modul '{module}' ist NICHT installiert.")
    except Exception as e:
        print(f"⚠️ Fehler beim Prüfen von '{module}': {e}")
