import machine
import time
from umqtt.simple import MQTTClient
import config
from include import log

# Configure la broche D4 (GPIO2) comme sortie
led = machine.Pin(2, machine.Pin.OUT)

log(level="ERROR", message="Is running...", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)

client = MQTTClient(config.MODULE_PREFIX + module_id, config.MQTT_BROKER, user=config.MQTT_USER, password=config.MQTT_PASSWORD)
client.connect()

def on_message(topic, msg):
    if topic == b'cockpit/' + module_id + b'/reboot':
        if msg == b'True':
            client.publish(b'cockpit/' + module_id + b'/reboot', b'done')
            time.sleep(2)
            machine.reset()

client.set_callback(on_message)
client.subscribe(b'cockpit/' + module_id + b'/reboot')

def blink_morse_code():
    morse_code = ".--....--."
    for symbol in morse_code:
        if symbol == ".":
            led.on()  # Allume la LED
            time.sleep(0.5)  # Attend 0.5 seconde
        elif symbol == "-":
            led.on()  # Allume la LED
            time.sleep(1)  # Attend 1 seconde
        led.off()  # Éteint la LED
        time.sleep(0.5)  # Attend 0.5 seconde entre chaque symbole

while True:
    client.check_msg()
    blink_morse_code()