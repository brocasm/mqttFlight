import machine
import time

# Configure la broche D4 (GPIO2) comme sortie
led = machine.Pin(2, machine.Pin.OUT)


log(level="ERROR", message="Is running...", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)

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

def check_reboot(client, topic):
    def on_message(topic, msg):
        nonlocal reboot
        reboot = msg.decode() == 'True'

    reboot = False
    client.set_callback(on_message)
    client.subscribe(topic)

    start_time = time.time()
    while time.time() - start_time < 5:
        client.check_msg()
        if reboot:
            break

    return reboot
while True:
    blink_morse_code()

    reboot_topic = f"cockpit/{module_id}/reboot"
    if check_reboot(client, reboot_topic):
        log(level="WARNING", message="Reboot command received. Publishing 'done' and rebooting...", filepath=LOG_SCRIPT_NAME, client=client, module_id=module_id)
        client.publish(reboot_topic, 'done', retain=True)
        time.sleep(2)
        machine.reset()