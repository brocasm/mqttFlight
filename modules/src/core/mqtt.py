import machine
import time
from umqtt.simple import MQTTClient
import uasyncio as asyncio
import config
from include import log, generate_module_id

class MQTTHandler:
    def __init__(self):
        self.module_id = generate_module_id()
        self.client = None
        self.led = machine.Pin(2, machine.Pin.OUT)  # Adjust the pin number as needed

    async def blink_led(self):
        for _ in range(3):
            self.led.on()
            await asyncio.sleep(0.1)
            self.led.off()
            await asyncio.sleep(0.1)

    def mqtt_callback(self, topic, msg):
        print(f"Received message: {msg} on topic: {topic}")
              

        
    def log(self, level, message):
        log(client=self.client, level=level, message=message, module_id=self.module_id)

    async def subscribe(self, topics):                      
        for topic in topics:
            self.client.subscribe(topic)
            self.log("DEBUG", f"Subscribed to topic {topic}")            

    async def connect_mqtt(self):
        self.client = MQTTClient(config.MODULE_PREFIX, config.MQTT_BROKER, config.MQTT_PORT, config.MQTT_USER, config.MQTT_PASSWORD)
        self.client.set_callback(self.mqtt_callback)
        self.client.connect(clean_session=False)
        print("Connected to MQTTHandler")        
        
    
    async def mqtt_loop(self):
        while True:
            try:
                self.client.check_msg()
            except Exception as e:
                print("Perte de connexion détectée, reconnexion en cours...")
                while True:
                    try:
                        self.client.connect(clean_session=False)                        
                        print("Reconnecté au broker MQTT")
                        break
                    except Exception as e:
                        print("Nouvel échec de connexion, retry dans 5 secondes")
                        await asyncio.sleep(5)
            await asyncio.sleep_ms(100)    

    