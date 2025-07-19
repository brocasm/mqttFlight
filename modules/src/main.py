import machine
import time
from umqtt.simple import MQTTClient
import config

from include import log, generate_module_id
LOG_SCRIPT_NAME = "main.py"

module_id = generate_module_id()

# Configure la broche D4 (GPIO2) comme sortie
led = machine.Pin(2, machine.Pin.OUT)

client = MQTTClient(config.MODULE_PREFIX + module_id, config.MQTT_BROKER, user=config.MQTT_USER, password=config.MQTT_PASSWORD)
client.connect()

log(level="ERROR", message="Is running...", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)

def on_message(topic, msg):
    topic_str = topic.decode('utf-8')
    msg_str = msg.decode('utf-8')
    if topic_str == 'cockpit/' + module_id + '/reboot':
        if msg_str == 'True':
            client.publish('cockpit/' + module_id + '/reboot', 'done')
            time.sleep(2)
            machine.reset()

client.set_callback(on_message)
client.subscribe('cockpit/' + module_id + '/reboot')

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
    #blink_morse_code()