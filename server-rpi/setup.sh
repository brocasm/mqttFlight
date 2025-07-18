#!/bin/ash
# Script pour configurer un point d'accès Wi-Fi, installer Python 3, Node.js, et un broker MQTT sur Alpine Linux
# Mettre à jour les paquets
echo "Mise à jour des paquets..."
apk update
# Installer les paquets nécessaires pour le point d'accès Wi-Fi
echo "Installation des paquets nécessaires pour le point d'accès Wi-Fi..."
apk add hostapd dnsmasq mosquitto python3 py3-pip picocom

# Installer les composant pip
python3 -v venv /root/venv
source /root/venv/bin/activate
pip install esptool adafruit-ampy
# Obtenir une fraction de l'adresse MAC pour le SSID
MAC_ADDRESS=$(cat /sys/class/net/wlan1/address)
SSID_SUFFIX=${MAC_ADDRESS: -5} # Prendre les 5 derniers caractères de l'adresse MAC
SSID="mqttFlight-rpi-$SSID_SUFFIX"
# Configurer l'interface réseau
echo "Configuration de l'interface réseau..."
cat > /etc/network/interfaces <<EOF
auto lo
iface lo inet loopback
auto eth0
iface eth0 inet dhcp
auto wlan1
iface wlan1 inet static
    address 192.168.42.1
    netmask 255.255.255.0
EOF
# Configurer hostapd pour le point d'accès Wi-Fi
echo "Configuration de hostapd..."
cat > /etc/hostapd/hostapd.conf <<EOF
interface=wlan1
driver=nl80211
ssid=$SSID
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=monmotdepasse
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF
# Configurer dnsmasq pour le DHCP
echo "Configuration de dnsmasq..."
cat > /etc/dnsmasq.conf <<EOF
interface=wlan1
dhcp-range=192.168.42.2,192.168.42.255,255.255.255.0,24h
EOF
# Activer et redémarrer les services
echo "Activation et redémarrage des services..."
rc-update add hostapd
rc-update add dnsmasq
service hostapd restart
service dnsmasq restart
# Installer Python 3 et Node.js
echo "Installation de Python 3 et Node.js..."
apk add python3 nodejs npm
# Sauvegarder le fichier de configuration Mosquitto
echo "Sauvegarde du fichier de configuration Mosquitto..."
cp /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.bak
# Configurer Mosquitto MQTT Broker
echo "Configuration de Mosquitto MQTT Broker..."
cat > /etc/mosquitto/mosquitto.conf <<EOF
listener 1883 0.0.0.0
protocol mqtt

# Persistance des messages
persistence true
persistence_file mosquitto.db
persistence_location /var/lib/mosquitto/

# Sécurité
allow_anonymous false
password_file /etc/mosquitto/pwfile

# Certificats TLS (commenté pour l'instant)
#cafile /etc/mosquitto/certs/ca.crt
#certfile /etc/mosquitto/certs/server.crt
#keyfile /etc/mosquitto/certs/server.key

# Logs
log_dest file /var/log/mosquitto/mosquitto.log
log_type all
log_timestamp true

# Limites de connexion
max_connections 100
max_queued_messages 100

# Qualité de Service (QoS)
max_inflight_messages 20
max_queued_messages 100

# Autorisation
acl_file /etc/mosquitto/acl.conf

# Monitoring
sys_interval 10
EOF
# Créer un utilisateur MQTT
echo "Création d'un utilisateur MQTT..."
mosquitto_passwd -c -b /etc/mosquitto/pwfile mqtt_admin monmotdepasse
# Créer un fichier ACL de base
echo "Création d'un fichier ACL de base..."
cat > /etc/mosquitto/acl.conf <<EOF
# Exemple de fichier ACL pour Mosquitto

# Autoriser l'utilisateur mqtt_admin à tout faire
user mqtt_admin
topic readwrite #

# Autoriser les modules ESP32/D1 Mini à publier et souscrire à des topics spécifiques
user esp_module_1
topic read sim/data/#
topic write sim/status/module_1/#

user esp_module_2
topic read sim/data/#
topic write sim/status/module_2/#
EOF
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
