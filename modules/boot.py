import network
import time
import machine
import ubinascii
from umqtt.simple import MQTTClient
import config

def connect_wifi():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('Connecting to Wi-Fi...')
        sta_if.active(True)
        sta_if.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        while not sta_if.isconnected():
            time.sleep(0.5)
    print('Network config:', sta_if.ifconfig())

def generate_module_id():
    # Obtenir l'adresse MAC et générer un ID de module
    mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
    module_id = "modules-" + mac.replace(":", "")[-6:]  # Prendre les 6 derniers caractères de l'adresse MAC
    return module_id

def connect_mqtt(module_id):
    client_id = config.get_mqtt_client_id()
    client = MQTTClient(client_id, config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_USER, config.MQTT_PASSWORD)
    client.connect()
    print('Connected to MQTT Broker')

    # Envoyer un message MQTT pour indiquer le dernier démarrage
    timestamp = time.time()
    # Convertir le timestamp en une date et heure lisibles si possible, sinon utiliser le timestamp
    try:
        import utime
        local_time = utime.localtime(timestamp)
        date_time = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            local_time[0], local_time[1], local_time[2],
            local_time[3], local_time[4], local_time[5]
        )
        message = date_time
    except:
        message = str(timestamp)

    topic = "cockpit/" + module_id + "/lastboot"
    client.publish(topic, message)
    print('Published last boot message to topic:', topic)

    return client

def main():
    connect_wifi()
    module_id = generate_module_id()
    client = connect_mqtt(module_id)

    # Lancer le script main.py
    try:
        import main
    except Exception as e:
        print('Failed to import main.py:', e)

if __name__ == "__main__":
    main()
