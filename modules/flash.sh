#!/bin/sh

# Vérifie si le fichier binaire existe
if [ ! -f "ESP8266/ESP8266.bin" ]; then
    echo "Erreur : le fichier ESP8266.bin n'existe pas dans le répertoire courant."
    exit 1
fi

# Active l'environnement virtuel
source /root/venv/bin/activate

# Efface la mémoire flash de l'ESP8266
echo "Effacement de la mémoire flash..."
esptool --port /dev/ttyUSB0 erase_flash

# Écrit le fichier binaire sur l'ESP8266
echo "Écriture du fichier binaire sur l'ESP8266..."
esptool --port /dev/ttyUSB0 --baud 460800 write_flash --flash-size=detect 0 ESP8266/ESP8266.bin

# Vérifie si l'écriture a réussi
if [ $? -eq 0 ]; then
    echo "Flashing terminé avec succès."
else
    echo "Erreur lors du flashing."
    deactivate
    exit 1
fi

# Désactive l'environnement virtuel
deactivate

# Appelle le script de transfert
./transfer.sh