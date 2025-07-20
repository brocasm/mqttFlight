import network
import time
import machine
import ubinascii
from umqtt.robust import MQTTClient
import uhashlib
import urequests
import config
import os
import uasyncio as asyncio
from include import log, generate_module_id, keep_ampy_alive
from core.connection_wifi import WifiConnection
from core.mqtt import MQTTHandler

VERSION = "v0.15"
LOG_SCRIPT_NAME = "boot.py"

wifi = None

module_id = generate_module_id()

async def connect_wifi():
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


def compare_hashes(filepath, client):
    local_hash = calculate_file_hash(filepath)
    local_hash_hex = ubinascii.hexlify(local_hash).decode()    
    
    remote_hash_hex = mqtt_handler.get_value_retained(f"system/hash/{filepath}", None)    
    return local_hash_hex == remote_hash_hex

def download_file(url, filepath, chunk_size=1024):
    try:
        response = urequests.get(url)
        if response.status_code == 200:
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
                buffer = f_src.read(512)
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
            pass
            

async def main():
    global mqtt_handler

    await connect_wifi()

    mqtt_handler = CustomMQTTHandler()
    mqtt_handler.LOG_SCRIPT_NAME = LOG_SCRIPT_NAME
    await mqtt_handler.connect_mqtt()    

    topics = [f"system/countboot/{module_id}"]
    #await mqtt_handler.subscribe(topics)

    boot_counter = int(mqtt_handler.get_value_retained(f"system/countboot/{module_id}",0))
    boot_counter += 1
    mqtt_handler.client.publish(f"system/countboot/{module_id}", str(boot_counter), retain=True)
    mqtt_handler.client.publish(f"system/version/boot/{module_id}", VERSION)

    last_print_time = time.time()

    mqtt_task = asyncio.create_task(mqtt_handler.mqtt_loop())
    keep_ampy_alive_task = asyncio.create_task(keep_ampy_alive())

    files_to_check = ['main.py', 'boot.py', 'config.py', 'include.py', 'core/connection_wifi.py', 'core/mqtt.py']
    request_reboot = False
    for filepath in files_to_check:
        if not compare_hashes(filepath, mqtt_handler.client):
            request_reboot = True
            mqtt_handler.log("WARNING", f"Hash mismatch for {filepath}. Downloading new {filepath}...")                    
            backup_file(filepath)
            file_url = f"http://{config.SERVER_ADDRESS}:8000/{filepath}"
            download_file(file_url, filepath)
            mqtt_handler.log("WARNING", f"{filepath} updated successfully.")
        else:
            mqtt_handler.log("INFO", f"Hash for {filepath} is identical, no update needed.")
    if request_reboot:
        mqtt_handler.log("WARNING", "Rebooting...")
        time.sleep(2)
        machine.reset()
    
    try:
        mqtt_handler.log("WARNING", "Launching main.py")
        import main
    except Exception as e:
        mqtt_handler.log("ERROR", f'Failed to import main.py: {e}')

if __name__ == "__main__":
    asyncio.run(main())