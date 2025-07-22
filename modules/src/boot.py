import time
import json
import network
import machine
import os
import uasyncio as asyncio

from core.connection_wifi import WifiConnection

CONFIG_FILE = 'config.json'

wifi = None

async def connect_wifi():
    global wifi
    wifi = WifiConnection()
    await wifi.connect()


def load_config():
    try:
        with open(CONFIG_FILE) as f:
            return json.load(f)
    except:
        return {}

def run_script(filename):
    try:
        print(f"[boot] Tentative de lancement : {filename}")
        with open(filename) as f:
            code = f.read()
            exec(code, {'__name__': '__main__'})
        return True
    except Exception as e:
        print(f"[boot] Échec de {filename} :", e)
        return False
def perform_update():
    try:
        import update
        print("[boot] Vérification des mises à jour...")
        asyncio.run(update.check_and_update_files())
    except Exception as e:
        print("[boot] Erreur dans update.py :", e)
def main():
    print("[boot] --- Démarrage du module ---")
    connect_wifi()

    perform_update()

    cfg = load_config()
    main_valid = cfg.get("main_valid", False)

    if main_valid and 'main.py' in os.listdir():
        if run_script("main.py"):
            return

    print("[boot] main.py non valide ou erreur → tentative main_backup.py")
    if 'main_backup.py' in os.listdir():
        if run_script("main_backup.py"):
            return

    print("[boot] Échec de main_backup.py → passage en mode fallback")
    run_script("fallback.py")

main()
