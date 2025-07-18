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
    client.check_msg()  # Vérifier les messages MQTT    
    return counter

def connect_mqtt(module_id):
    client_id = config.get_mqtt_client_id()
    client = MQTTClient(client_id, config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_USER, config.MQTT_PASSWORD)
    client.connect()
    print('Connected to MQTT Broker')

    topic = "cockpit/" + module_id + "/lastboot"

    # Récupérer le compteur actuel
    boot_counter = get_boot_counter(client, topic)

    # Incrémenter le compteur
    boot_counter += 1

    # Publier le nouveau compteur
    client.publish(topic, str(boot_counter))
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