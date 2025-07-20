import network
import time
import machine
import ubinascii
from umqtt.robust import MQTTClient
import uhashlib
import urequests
import config
import os
from include import log, generate_module_id
from core.connection_wifi import WifiConnection
from core.mqtt import MQTTHandler

BOOT_VERSION = "v0.14"
LOG_SCRIPT_NAME = "boot.py"

wifi = None

module_id = generate_module_id()

def get_mqtt_client_id():
    mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    return config.MODULE_PREFIX + mac.replace(":", "")[-6:]

def connect_wifi():
    global wifi
    wifi = WifiConnection()
    await wifi.connect()




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


class CustomMQTTHandler(MQTTHandler):
    def mqtt_callback(self, topic, msg):
        super().mqtt_callback(topic, msg)

        topic = topic.decode('utf-8')
        msg = msg.decode('utf-8')

        if topic == f"system/countboot/{module_id}":
            try:
                boot_counter = int(msg.decode())
            except ValueError:
                boot_counter = 0            
            boot_counter += 1
            client.publish(f"system/countboot/{module_id}", str(boot_counter), retain=True)
            client.publish(f"system/version/boot/{module_id}", BOOT_VERSION)  
           

# Main function
async def main():
    global mqtt_handler

    await connect_wifi()

    mqtt_handler = CustomMQTTHandler()
    mqtt_handler.LOG_SCRIPT_NAME = LOG_SCRIPT_NAME
    await mqtt_handler.connect_mqtt()    

    topics = [f"system/countboot/{module_id}"]
    await mqtt_handler.subscribe(topics)

    last_print_time = time.time()

    # Create a task for the MQTT loop
    mqtt_task = asyncio.create_task(mqtt_handler.mqtt_loop())
    keep_ampy_alive_task = asyncio.create_task(keep_ampy_alive())

    files_to_check = ['main.py', 'boot.py', 'config.py', 'include.py', 'core/connection_wifi.py', 'core/mqtt.py']
    request_reboot = False
    for filepath in files_to_check:
        

        if not compare_hashes(filepath, client):
            request_reboot = True
            log(level="WARNING", message=f"Hash mismatch for {filepath}. Downloading new {filepath}...", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)            
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
        log(level="WARNING", message="Launching main.py", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)
        import main
    except Exception as e:
        log(level="ERROR", message=f'Failed to import main.py: {e}', filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)

    

if __name__ == "__main__":
    asyncio.run(main())