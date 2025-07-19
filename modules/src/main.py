import network
import time
import machine
from umqtt.simple import MQTTClient
import config
from include import log, generate_module_id
import uasyncio as asyncio

module_id = generate_module_id()
print(module_id)

# Define the LED pin
led = machine.Pin(2, machine.Pin.OUT)  # Adjust the pin number as needed

# Async function to blink the LED rapidly 3 times
async def blink_led():
    for _ in range(3):
        led.on()
        await asyncio.sleep(0.1)
        led.off()
        await asyncio.sleep(0.1)

# Connect to Wi-Fi
async def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    while not wlan.isconnected():
        await asyncio.sleep(1)
    print("Connected to Wi-Fi")

# MQTT callback function
def mqtt_callback(topic, msg):
    global module_id
    topic = topic.decode('utf-8')
    msg = msg.decode('utf-8')
    print(f"Received message: {msg} on topic: {topic}")

    if topic == 'cockpit/default/altitude':
        print(f"Altitude: {msg}")
        asyncio.create_task(blink_led())  # Blink the LED when a message is received on the altitude topic
    elif topic == f'cockpit/{module_id}/reboot' and msg == 'True':
        print("Reboot command received")
        client.publish(f'cockpit/{module_id}/reboot', 'done')
        time.sleep(1)
        machine.reset()

# Connect to MQTT broker
async def connect_mqtt():
    global module_id
    global client
    client = MQTTClient(config.MODULE_PREFIX, config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_USER, config.MQTT_PASSWORD)
    client.set_callback(mqtt_callback)
    client.connect()
    topics = ['cockpit/default/altitude', f'cockpit/{module_id}/reboot']
    print(topics)
    for topic in topics:
        print(f"Listening to topic {topic}")
        client.subscribe(topic)

    print("Connected to MQTT broker")

# Main function
async def main():
    await connect_wifi()
    await connect_mqtt()

    last_print_time = time.time()
    while True:
        client.check_msg()
        await asyncio.sleep(0.1)
        current_time = time.time()
        if current_time - last_print_time >= 5:
            print("keep picocom alive")
            last_print_time = current_time

if __name__ == "__main__":
    asyncio.run(main())