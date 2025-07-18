import machine
import time

# Configure la broche D4 (GPIO2) comme sortie
led = machine.Pin(2, machine.Pin.OUT)

while True:
    sequence = "--....--."
    # Boucle pour transformer la séquence
    for char in sequence:
        if char == '.':
            # Attendre 0.5 secondes
            time.sleep(0.5)
            print(".")
        elif char == '-':
            # Attendre 1 seconde
            time.sleep(1)
            print("-")
        else:
            print("Caractère non valide dans la séquence")

    # Indiquer la fin de la séquence
    print("Fin de la séquence")
