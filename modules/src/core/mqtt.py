import machine
import time
from umqtt.robust import MQTTClient
import uasyncio as asyncio
import config
from include import log, generate_module_id



class MQTTHandler:
    def __init__(self):
        self.module_id = generate_module_id()
        self.client = None
        self.led = machine.Pin(2, machine.Pin.OUT)  # Adjust the pin number as needed
        self.LOG_SCRIPT_NAME = "core-mqtt.py"
        self.received_messages = 0

    async def blink_led(self):
        for _ in range(3):
            self.led.on()
            await asyncio.sleep(0.1)
            self.led.off()
            await asyncio.sleep(0.1)

    def mqtt_callback(self, topic, msg):
        print(f"Received message: {msg} on topic: {topic}")
        if config.DEV_MODE:            
            self.received_messages +=  1
            print(f"Total messages received: {self.received_messages}")
            self.client.publish(f"system/received_messages/{self.module_id}",str(self.received_messages))
              
    def get_value_retained(self, topic, default=None):

        client = MQTTClient(self.module_id+"-TEMP", config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_USER, config.MQTT_PASSWORD)
        client.set_callback(self.mqtt_callback)
        client.connect(clean_session=False)    

        def on_message(topic, msg):
            nonlocal ret
            try:
                ret = msg.decode()
            except ValueError:
                ret = default

        ret = None
        client.set_callback(on_message)
        client.subscribe(topic)

        start_time = time.time()
        while time.time() - start_time < 5:
            client.check_msg()
            if ret != None:
                break
        
        client.disconnect()
        if ret is None:
            ret = default
        return ret   
        
    def log(self, level, message):
        log(client=self.client, level=level, message=message, module_id=self.module_id, filepath=self.LOG_SCRIPT_NAME)

    async def subscribe(self, topics):                      
        for topic in topics:
            self.client.subscribe(topic)
            self.log("DEBUG", f"Subscribed to topic {topic}")
            self.client.check_msg()            

    async def connect_mqtt(self):
        self.log("INFO", "Attempting to connect to MQTT broker...")
        try:
            self.client = MQTTClient(config.MODULE_PREFIX+self.module_id, config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_USER, config.MQTT_PASSWORD)
            self.client.set_callback(self.mqtt_callback)
            self.client.connect(clean_session=False)
            self.log("WARNING", "Successfully connected to MQTT broker.")
        except OSError as e:
            self.log("ERROR", f"Failed to connect to MQTT broker: {e}")
            raise

    async def mqtt_loop(self):
        while True:
            try:
                self.client.check_msg()
            except Exception as e:
                self.log("ERROR", f"Connection lost: {e}. Attempting to reconnect...")
                await self.reconnect_mqtt()
            await asyncio.sleep_ms(100)

    async def reconnect_mqtt(self):
        backoff_time = 1
        while True:
            try:
                self.log("WARNING", f"Reconnecting to MQTT broker in {backoff_time} seconds...")
                await asyncio.sleep(backoff_time)
                self.client.connect(clean_session=False)
                self.log("WARNING", "Reconnected to MQTT broker.")
                break
            except Exception as e:
                self.log("ERROR", f"Reconnection failed: {e}. Retrying in {backoff_time * 2} seconds...")
                backoff_time = min(backoff_time * 2, 60)  # Exponential backoff with a max wait time of 60 seconds

    