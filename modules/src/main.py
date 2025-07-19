import machine
import time

# Configure la broche D4 (GPIO2) comme sortie
led = machine.Pin(2, machine.Pin.OUT)

def blink_morse_code():
    morse_code = ".--....--."
    for symbol in morse_code:
        if symbol == ".":
            led.on()  # Allume la LED
            time.sleep(0.1)  # Attend 0.5 seconde
        elif symbol == "-":
            led.on()  # Allume la LED
            time.sleep(1)  # Attend 1 seconde
        led.off()  # Éteint la LED
        time.sleep(0.5)  # Attend 0.5 seconde entre chaque symbole

while True:
    blink_morse_code()