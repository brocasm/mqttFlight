#!/bin/sh

# Active l'environnement virtuel
source /root/venv/bin/activate

# Liste des fichiers à transférer
files="src/boot.py src/config.py src/main.py src/include.py"

# Transfère chaque fichier sur l'ESP8266
for file in $files; do
    echo "Transfert de $file sur l'ESP8266..."
    ampy --port /dev/ttyUSB0 put $file

    # Vérifie si le transfert a réussi
    if [ $? -eq 0 ]; then
        echo "Transfert de $file terminé avec succès."
    else
        echo "Erreur lors du transfert de $file."
        deactivate
        exit 1
    fi
done

# Désactive l'environnement virtuel
deactivate