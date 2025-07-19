import network
import time
import machine
import config
from include import generate_module_id
import uasyncio as asyncio
from core.connection_wifi import WifiConnection
from core.mqtt import MQTTHandler  # Import MQTTHandler

module_id = generate_module_id()

wifi = None
mqtt_handler = None

# Connect to Wi-Fi
async def connect_wifi():
    global wifi
    wifi = WifiConnection()
    await wifi.connect()

# Main function
async def main():
    global mqtt_handler

    await connect_wifi()

    mqtt_handler = MQTTHandler()
    await mqtt_handler.connect_mqtt()

    last_print_time = time.time()

    # Create a task for the MQTT loop
    mqtt_task = asyncio.create_task(mqtt_handler.mqtt_loop())

    while True:
        await asyncio.sleep(0.1)
        current_time = time.time()
        if current_time - last_print_time >= 5:
            print("keep picocom alive")
            last_print_time = current_time

if __name__ == "__main__":
    asyncio.run(main())