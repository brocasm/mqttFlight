import network
import time
import machine
import config
from include import generate_module_id, keep_ampy_alive
import uasyncio as asyncio
from core.connection_wifi import WifiConnection
from core.mqtt import MQTTHandler

LOG_SCRIPT_NAME = "main.py"
VERSION = "v0.1"

module_id = generate_module_id()

wifi = None
mqtt_handler = None

class CustomMQTTHandler(MQTTHandler):
    def mqtt_callback(self, topic, msg):
        super().mqtt_callback(topic, msg)

        topic = topic.decode('utf-8')
        msg = msg.decode('utf-8')
        if topic == 'cockpit/default/altitude':
            print(f"Altitude reçu: {msg}")
            asyncio.create_task(self.blink_led())  # Blink the LED when a message is received on the altitude topic
        elif topic == f'cockpit/{self.module_id}/reboot' and msg == 'True':
            print("Reboot command received")
            self.client.publish(f'cockpit/{self.module_id}/reboot', 'done')
            time.sleep(1)
            machine.reset()

# Connect to Wi-Fi
async def connect_wifi():
    global wifi
    wifi = WifiConnection()
    await wifi.connect()


# Main function
async def main():
    global mqtt_handler

    await connect_wifi()

    mqtt_handler = CustomMQTTHandler()
    mqtt_handler.LOG_SCRIPT_NAME = LOG_SCRIPT_NAME
    await mqtt_handler.connect_mqtt()

    mqtt_handler.client.publish(f"system/version/main/{module_id}", VERSION)

    topics = ['cockpit/default/altitude', f'cockpit/{module_id}/reboot']
    await mqtt_handler.subscribe(topics)

    last_print_time = time.time()

    # Create a task for the MQTT loop
    mqtt_task = asyncio.create_task(mqtt_handler.mqtt_loop())
    keep_ampy_alive_task = asyncio.create_task(keep_ampy_alive())

    while True:
        await asyncio.sleep(0.1)
        pass

if __name__ == "__main__":
    asyncio.run(main())