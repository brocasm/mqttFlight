#!/bin/sh

# Active l'environnement virtuel
source /root/venv/bin/activate

# Liste des fichiers à transférer (sans le chemin)
files="boot.py config.py main.py include.py"

# Chemin source des fichiers
source_path="/root/mqttFlight/modules/src"

# Transfère chaque fichier sur l'ESP8266
for file in $files; do
    source_file="$source_path/$file"
    echo "Transfert de $source_file sur l'ESP8266..."
    ampy --port /dev/ttyUSB0 put $source_file

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