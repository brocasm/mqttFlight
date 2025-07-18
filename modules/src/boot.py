import network
import time
import machine
import ubinascii
from umqtt.simple import MQTTClient
import uhashlib
import urequests
import config


import ubinascii

def get_mqtt_client_id():
    mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    return config.MODULE_PREFIX + mac.replace(":", "")[-6:]
def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    try:
        if not sta_if.isconnected():
            print('Connecting to Wi-Fi...')
            sta_if.active(True)
            sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
            while not sta_if.isconnected():
                time.sleep(0.5)
                if sta_if.status() == network.STAT_CONNECTING:
                    continue
                elif sta_if.status() == network.STAT_WRONG_PASSWORD:
                    raise Exception("Wi-Fi connection failed: Incorrect password")
                elif sta_if.status() == network.STAT_NO_AP_FOUND:
                    raise Exception("Wi-Fi connection failed: Access point not found")
                elif sta_if.status() == network.STAT_CONNECT_FAIL:
                    raise Exception("Wi-Fi connection failed: Connection failed")
                elif sta_if.status() == network.STAT_IDLE:
                    raise Exception("Wi-Fi connection failed: Interface is idle")
                else:
                    raise Exception("Wi-Fi connection failed: Unknown error")
        print('Network config:', sta_if.ifconfig())
    except Exception as e:
        print(f"Error: {e}")
        # Optionally, you can add logic here to attempt reconnection or take other actions

def generate_module_id():
    # Obtenir l'adresse MAC et générer un ID de module
    mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    module_id = "modules-" + mac.replace(":", "")[-6:]  # Prendre les 6 derniers caractères de l'adresse MAC
    return module_id

def get_boot_counter(client, topic):
    # Fonction pour récupérer le compteur actuel depuis le topic MQTT
    def on_message(topic, msg):
        nonlocal counter
        try:
            counter = int(msg.decode())
        except ValueError:
            counter = 0

    counter = 0
    client.set_callback(on_message)
    client.subscribe(topic)

    start_time = time.time()
    while time.time() - start_time < 5:
        client.check_msg()  # Vérifier les messages MQTT
        if counter != 0:
            break

    return counter

def connect_mqtt(module_id):
    client_id = get_mqtt_client_id()
    client = MQTTClient(client_id, config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_USER, config.MQTT_PASSWORD)
    client.connect()
    print('Connected to MQTT Broker')

    topic = "cockpit/" + module_id + "/countboot"

    # Récupérer le compteur actuel
    boot_counter = get_boot_counter(client, topic)

    # Incrémenter le compteur
    boot_counter += 1

    # Publier le nouveau compteur
    client.publish(topic, str(boot_counter), retain=True)
    print('Published last boot message to topic:', topic)

    return client

def calculate_file_hash(filepath):
    with open(filepath, 'rb') as f:
        hasher = uhashlib.sha256()
        buf = f.read(128)
        while buf:
            hasher.update(buf)
            buf = f.read(128)
    return hasher.digest()

def get_remote_hash(client, topic):
    def on_message(topic, msg):
        nonlocal remote_hash
        remote_hash = msg

    remote_hash = None
    client.set_callback(on_message)
    client.subscribe(topic)

    start_time = time.time()
    while time.time() - start_time < 5:
        client.check_msg()
        if remote_hash is not None:
            break

    return remote_hash

def download_file(url):
    response = urequests.get(url)
    if response.status_code == 200:
        return response.content
    else:
        raise Exception(f"Failed to download file: {response.status_code}")

def update_main_file(content):
    with open('main.py', 'wb') as f:
        f.write(content)

def backup_main_file():
    with open('main.py', 'rb') as f:
        content = f.read()
    with open('main_backup.py', 'wb') as f:
        f.write(content)

def restore_main_file():
    with open('main_backup.py', 'rb') as f:
        content = f.read()
    with open('main.py', 'wb') as f:
        f.write(content)

def check_fallback(client, topic):
    def on_message(topic, msg):
        nonlocal fallback
        fallback = msg.decode() == 'True'

    fallback = False
    client.set_callback(on_message)
    client.subscribe(topic)

    start_time = time.time()
    while time.time() - start_time < 5:
        client.check_msg()
        if fallback:
            break

    return fallback

def main():
    connect_wifi()
    module_id = generate_module_id()
    client = connect_mqtt(module_id)

    fallback_topic = f"cockpit/{module_id}/fallback"
    if check_fallback(client, fallback_topic):
        print("Fallback triggered. Restoring main.py from backup...")
        restore_main_file()
        client.publish(fallback_topic, 'done', retain=True)
        print("Fallback completed.")

    local_hash = calculate_file_hash('main.py')
    remote_hash_topic = f"system/hash/main.py"
    remote_hash = get_remote_hash(client, remote_hash_topic)

    if local_hash != remote_hash:
        print("Hash mismatch. Downloading new main.py...")
        backup_main_file()
        main_file_url = f"http://{config.SERVER_ADDRESS}:8000/main.py"
        new_main_content = download_file(main_file_url)
        update_main_file(new_main_content)
        print("main.py updated successfully.")

    # Lancer le script main.py
    try:
        import main
    except Exception as e:
        print('Failed to import main.py:', e)

if __name__ == "__main__":
    main()