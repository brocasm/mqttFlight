#!/bin/ash
# Script pour configurer un point d'accès Wi-Fi, installer Python 3, Node.js, et un broker MQTT sur Alpine Linux
# Mettre à jour les paquets
echo "Mise à jour des paquets..."
apk update
# Installer les paquets nécessaires pour le point d'accès Wi-Fi
echo "Installation des paquets nécessaires pour le point d'accès Wi-Fi et serial..."
apk add hostapd dnsmasq mosquitto picocom


# Obtenir une fraction de l'adresse MAC pour le SSID
MAC_ADDRESS=$(cat /sys/class/net/wlan1/address)
SSID_SUFFIX=${MAC_ADDRESS: -5} # Prendre les 5 derniers caractères de l'adresse MAC
SSID="mqttFlight-rpi-$SSID_SUFFIX"
# Configurer l'interface réseau
echo "Configuration de l'interface réseau..."
cat configs/interfaces > /etc/network/interfaces

# Configurer hostapd pour le point d'accès Wi-Fi
echo "Configuration de hostapd..."
cat configs/hostapd.conf > /etc/hostapd/ 

# Configurer dnsmasq pour le DHCP
echo "Configuration de dnsmasq..."
cat configs/dnsmasq.conf > /etc/dnsmasq.conf

# Activer et redémarrer les services
echo "Activation et redémarrage des services..."
rc-update add hostapd
rc-update add dnsmasq
service hostapd restart
service dnsmasq restart

# Installer Python 3 et Node.js
echo "Installation de Python 3 et Node.js..."
apk add python3 nodejs py3-pip

# Installer les composant pip
echo "Installation des composants pip..."
python3 -v venv /root/venv
source /root/venv/bin/activate
pip install esptool adafruit-ampy

# Sauvegarder le fichier de configuration Mosquitto
echo "Sauvegarde du fichier de configuration Mosquitto..."
cp /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.bak
# Configurer Mosquitto MQTT Broker
echo "Configuration de Mosquitto MQTT Broker..."
cat configs/mosquitto.conf > /etc/mosquitto/mosquitto.conf 

# Créer un utilisateur MQTT
echo "Création d'un utilisateur MQTT..."
mosquitto_passwd -c -b /etc/mosquitto/pwfile mqtt_admin monmotdepasse

# Créer un fichier ACL de base
echo "Création d'un fichier ACL de base..."
cat configs/acl.conf > /etc/mosquitto/acl.conf 

# Définir les permissions appropriées pour le fichier de mots de passe et ACL
chown mosquitto:mosquitto /etc/mosquitto/pwfile
chmod 644 /etc/mosquitto/pwfile
chown mosquitto:mosquitto /etc/mosquitto/acl.conf
chmod 644 /etc/mosquitto/acl.conf

# Activer et redémarrer Mosquitto
rc-update add mosquitto
service mosquitto restart

# Résumé des configurations appliquées
echo "Résumé des configurations appliquées :"
echo "1. Point d'accès Wi-Fi configuré avec SSID: $SSID et mot de passe: monmotdepasse"
echo "2. Python 3 et Node.js ont été installés"
echo "3. Mosquitto MQTT Broker a été installé et configuré pour écouter sur 0.0.0.0"
echo "4. Les services hostapd, dnsmasq, et mosquitto sont configurés pour démarrer automatiquement au démarrage du système."
echo "5. L'interface eth0 a été configurée pour utiliser DHCP."
echo "6. Fichier de configuration Mosquitto sauvegardé."
echo "7. Utilisateur MQTT 'mqtt_admin' créé avec un mot de passe par défaut."
echo "8. Fichier ACL configuré pour les utilisateurs et topics spécifiques."
echo "Configuration terminée."
