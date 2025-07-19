import network
import time
import machine
from umqtt.simple import MQTTClient
import config
from include import log, generate_module_id

module_id = generate_module_id()
print(module_id)

# Connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    while not wlan.isconnected():
        time.sleep(1)
    print("Connected to Wi-Fi")

# MQTT callback function
def mqtt_callback(topic, msg):
    global module_id
    topic = topic.decode('utf-8')
    msg = msg.decode('utf-8')
    print(f"Received message: {msg} on topic: {topic}")

    if topic == 'cockpit/default/altitude':
        print(f"Altitude: {msg}")
    elif topic == f'cockpit/{module_id}/reboot' and msg == 'True':
        print("Reboot command received")
        client.publish(f'cockpit/{module_id}/reboot', 'done')
        time.sleep(1)
        machine.reset()

# Connect to MQTT broker
def connect_mqtt():
    global module_id
    global client
    client = MQTTClient(config.MODULE_PREFIX, config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_USER, config.MQTT_PASSWORD)
    client.set_callback(mqtt_callback)
    client.connect()
    topics = ['cockpit/default/altitude',f'cockpit/{module_id}/reboot']
    print(topics)
    for topic in topics:
        print(f"ecoute du topic {topic}")
        client.subscribe(topic)

    
    print("Connected to MQTT broker 2")

# Main function
def main():
    connect_wifi()
    connect_mqtt()

    last_print_time = time.time()
    while True:
        client.check_msg()
        time.sleep(0.1)
        current_time = time.time()
        if current_time - last_print_time >= 5:
            print("keep picocom alive")
            last_print_time = current_time

if __name__ == "__main__":
    main()