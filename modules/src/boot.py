import network
import time
import machine
import ubinascii
from umqtt.simple import MQTTClient
import uhashlib
import urequests
import config
import os
from include import log

BOOT_VERSION = "v0.12"
LOG_SCRIPT_NAME = "boot.py"

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

def generate_module_id():
    mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    module_id = "modules-" + mac.replace(":", "")[-6:]
    return module_id

def get_boot_counter(client, topic):
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
        client.check_msg()
        if counter != 0:
            break

    return counter

def connect_mqtt(module_id):
    client_id = get_mqtt_client_id()
    client = MQTTClient(client_id, config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_USER, config.MQTT_PASSWORD)
    client.connect()
    log(level="INFO", message='Connected to MQTT Broker', filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)

    topic = "cockpit/" + module_id + "/countboot"
    boot_counter = get_boot_counter(client, topic)
    boot_counter += 1
    client.publish(topic, str(boot_counter), retain=True)
    client.publish("cockpit/" + module_id + "/version/boot", BOOT_VERSION)    

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

def compare_hashes(filepath, client):
    local_hash = calculate_file_hash(filepath)
    local_hash_hex = ubinascii.hexlify(local_hash).decode()
    remote_hash_topic = f"system/hash/{filepath}"
    remote_hash = get_remote_hash(client, remote_hash_topic)
    remote_hash_hex = remote_hash.decode() if remote_hash else None
    return local_hash_hex == remote_hash_hex

def download_file(url,filepath, chunk_size=1024):
    try:
        response = urequests.get(url)
        if response.status_code == 200:
            # Ouvrir un fichier local pour écrire les données téléchargées
            with open(filepath, 'wb') as f:
                while True:
                    chunk = response.raw.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
            return filepath
        else:
            raise Exception(f"Failed to download file: {response.status_code}")
    except Exception as e:
        raise Exception(f"An error occurred: {str(e)}")

def backup_file(filepath):
    with open(filepath, 'rb') as f_src:
        with open(filepath + '_backup', 'wb') as f_dst:
            while True:
                buffer = f_src.read(512)  # Lire en blocs de 512 octets
                if not buffer:
                    break
                f_dst.write(buffer)

def restore_file(filepath):
    with open(filepath + '_backup', 'rb') as f:
        content = f.read()
    with open(filepath, 'wb') as f:
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
        log(level="WARNING", message="Fallback triggered. Restoring main.py from backup...", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)
        restore_file('main.py')
        client.publish(fallback_topic, 'done', retain=True)
        log(level="WARNING", message="Fallback completed.", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)

    files_to_check = ['main.py', 'boot.py', 'config.py', 'include.py']
    request_reboot = False
    for filepath in files_to_check:
        

        if not compare_hashes(filepath, client):
            request_reboot = True
            log(level="WARNING", message=f"Hash mismatch for {filepath}. Downloading new {filepath}...", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)
            log(level="DEBUG", message=f"{local_hash_hex} != {remote_hash_hex}", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)
            backup_file(filepath)
            file_url = f"http://{config.SERVER_ADDRESS}:8000/{filepath}"
            download_file(file_url,filepath)            
            log(level="WARNING", message=f"{filepath} updated successfully.", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)
        else:
            log(level="INFO", message=f"Hash for {filepath} is identical, no update needed.", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)
    if request_reboot:
        log(level="WARNING", message="Rebooting...", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)
        time.sleep(2)
        machine.reset()
    
    try:
        log(level="DEBUG", message="Launching main.py", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)
        import main
    except Exception as e:
        log(level="ERROR", message=f'Failed to import main.py: {e}', filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)

if __name__ == "__main__":
    main()