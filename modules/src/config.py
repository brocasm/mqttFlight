import network
import ubinascii

def get_mac_suffix():
    mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    return mac.replace(":", "")[-6:]  # Prendre les 6 derniers caractères de l'adresse MAC

# Configuration Wi-Fi
WIFI_SSID = "mqttFlight-rpi-f3:16"
WIFI_PASSWORD = "mqttFlight-rpi"

# Configuration MQTT
MQTT_BROKER = "192.168.42.1"
MQTT_PORT = 1883
MQTT_USER = "mqtt_admin"
MQTT_PASSWORD = "monmotdepasse"

def get_mqtt_client_id():
    return "esp-module-" + get_mac_suffix()