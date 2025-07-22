import os
import hashlib
from config import MQTT_BROKER, MQTT_PORT, MQTT_USER, MQTT_PASSWORD
import time
import paho.mqtt.client as mqtt

def calculate_sha256(file_path):
    """Calculate the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def publish_sha256_of_files(directory):
    """Publish the SHA-256 hash of each file in the given directory to an MQTT topic."""
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.connect(MQTT_BROKER, MQTT_PORT)
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            file_hash = calculate_sha256(file_path)
            topic = f"system/hash/{file_path.replace('./src','')}"
            client.publish(topic, file_hash, retain=True)
            print(f"Published hash for {file_path}: {file_hash}")
            time.sleep(1)
    client.disconnect()

# Specify the directory you want to scan
directory_to_scan = "./src"
publish_sha256_of_files(directory_to_scan)