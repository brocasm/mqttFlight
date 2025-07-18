#!/bin/bash

# Active l'environnement virtuel
source /root/venv/bin/activate

# Transfère le fichier main.py sur l'ESP8266
echo "Transfert de main.py sur l'ESP8266..."
ampy --port /dev/ttyUSB0 put main.py

# Vérifie si le transfert a réussi
if [ $? -eq 0 ]; then
    echo "Transfert de main.py terminé avec succès."
else
    echo "Erreur lors du transfert de main.py."
    deactivate
    exit 1
fi

# Désactive l'environnement virtuel
deactivate