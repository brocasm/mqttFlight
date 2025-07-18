import machine
import time

# Configure la broche D4 (GPIO2) comme sortie
led = machine.Pin(2, machine.Pin.OUT)

while True:
    led.on()  # Allume la LED
    time.sleep(0.5)  # Attend 0.5 seconde
    led.off()  # Éteint la LED
    time.sleep(0.5)  # Attend 0.5 seconde
