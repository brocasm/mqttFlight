#!/bin/ash
# Script pour configurer un point d'accès Wi-Fi, installer Python 3, Node.js, et un broker MQTT sur Alpine Linux
# Amélioré avec logs colorés, icônes et progression

# Arrêter le script en cas d'erreur, variable non définie, etc.
set -euo pipefail

# Définition des couleurs et icônes (pour un terminal UTF-8)
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m"  # Pas de couleur
ICON_INFO="💡"
ICON_OK="✅"
ICON_ERROR="❌"
ICON_WARN="⚠️"
ICON_WIFI="📶"
ICON_INSTALL="📦"
ICON_CONF="🔧"
ICON_START="🚀"

# Nombre total d'étapes (à mettre à jour si le script évolue)
TOTAL_STEPS=18
step=1

# Fonctions de log
log_info()   { echo -e "${ICON_INFO} ${BLUE}[INFO]${NC} $1"; }
log_success(){ echo -e "${ICON_OK} ${GREEN}[SUCCESS]${NC} $1"; }
log_error()  { echo -e "${ICON_ERROR} ${RED}[ERROR]${NC} $1"; }
log_warn()   { echo -e "${ICON_WARN} ${YELLOW}[WARN]${NC} $1"; }
progress()   { echo -e "[${step}/${TOTAL_STEPS}] $1"; step=$((step + 1)); }

# Fichier de configuration contenant les variables sensibles
CONFIG_FILE="setup-init.conf"
if [ ! -f "$CONFIG_FILE" ]; then
    log_error "Le fichier de configuration '$CONFIG_FILE' est introuvable."
    exit 1
fi
progress "Chargement de la configuration depuis '$CONFIG_FILE'..."
# Attention : Assure-toi que setup-init.conf est fiable avant de le sourcer
. "$CONFIG_FILE"

# Mise à jour des paquets
progress "${ICON_INSTALL} Mise à jour des paquets..."
apk update && log_success "Paquets mis à jour." || log_error "Erreur lors de la mise à jour des paquets."

# Installation des paquets nécessaires pour le point d'accès Wi-Fi et autres utilitaires
progress "${ICON_INSTALL} Installation des paquets nécessaires (Wi-Fi, serial, etc.)..."
apk add hostapd dnsmasq mosquitto picocom logrotate cronie || {
    log_error "Erreur lors de l'installation des paquets requis."
    exit 1
}
log_success "Paquets installés."

# Récupération d'une partie de l'adresse MAC pour créer le SSID
progress "${ICON_WIFI} Génération du SSID à partir de l'adresse MAC..."
if [ -f /sys/class/net/wlan0/address ]; then
    MAC_ADDRESS=$(cat /sys/class/net/wlan0/address)
    SSID_SUFFIX=${MAC_ADDRESS: -5}  # Les 5 derniers caractères de l'adresse MAC
    SSID="${SSID_PREFIX}-${SSID_SUFFIX}"
    log_success "SSID généré : ${SSID}"
else
    log_error "L'interface wlan0 n'est pas disponible ou ne fournit pas d'adresse MAC."
    exit 1
fi

# Configuration de l'interface réseau
progress "${ICON_CONF} Configuration de l'interface réseau..."
if [ -f configs/interfaces ]; then
    cat configs/interfaces > /etc/network/interfaces
    log_success "Interface réseau configurée."
else
    log_warn "Le fichier 'configs/interfaces' est introuvable. Étape ignorée."
fi

# Configuration de hostapd
progress "${ICON_CONF} Configuration de hostapd..."
if [ -f configs/hostapd.conf ]; then
    sed "s/^ssid=.*/ssid=$SSID/" configs/hostapd.conf | sed "s/^wpa_passphrase=.*/wpa_passphrase=$WIFI_PASSWORD/" > /etc/hostapd/hostapd.conf
    log_success "hostapd configuré."
else
    log_warn "Le fichier 'configs/hostapd.conf' est introuvable. Étape ignorée."
fi

# Configuration de dnsmasq
progress "${ICON_CONF} Configuration de dnsmasq..."
if [ -f configs/dnsmasq.conf ]; then
    cat configs/dnsmasq.conf > /etc/dnsmasq.conf
    log_success "dnsmasq configuré."
else
    log_warn "Le fichier 'configs/dnsmasq.conf' est introuvable. Étape ignorée."
fi

# Activation des services hostapd et dnsmasq
progress "${ICON_START} Activation et démarrage de hostapd et dnsmasq..."
rc-update add hostapd && rc-update add dnsmasq
rc-service hostapd restart && rc-service dnsmasq restart
log_success "Services hostapd et dnsmasq démarrés."

# Installation de Python 3, Node.js et pip
progress "${ICON_INSTALL} Installation de Python 3, Node.js et py3-pip..."
apk add python3 nodejs py3-pip || {
    log_error "Erreur lors de l'installation de Python 3 ou Node.js."
    exit 1
}
log_success "Python 3, Node.js et pip installés."

# Création d'un environnement virtuel et installation des composants pip
progress "${ICON_INSTALL} Création de l'environnement virtuel Python et installation des paquets pip..."
python3 -m venv /root/venv
. /root/venv/bin/activate
pip install --no-cache-dir esptool adafruit-ampy paho-mqtt && log_success "Paquets Python installés." || {
    log_error "Erreur lors de l'installation des paquets Python."
    exit 1
}

# Sauvegarde et configuration de Mosquitto
progress "${ICON_CONF} Sauvegarde et configuration de Mosquitto..."
if [ -f /etc/mosquitto/mosquitto.conf ]; then
    cp /etc/mosquitto/mosquitto.conf /etc/mosquitto/mosquitto.conf.bak
    log_info "Sauvegarde du fichier de configuration Mosquitto effectuée."
    mkdir /var/lib/mosquitto/
    log_info "Création du répertoire /var/lib/mosquitto."
fi
if [ -f configs/mosquitto.conf ]; then
    cat configs/mosquitto.conf > /etc/mosquitto/mosquitto.conf
    log_success "Mosquitto configuré."
else
    log_warn "Le fichier 'configs/mosquitto.conf' est introuvable. Étape ignorée."
fi

# Création d'un utilisateur MQTT
progress "${ICON_CONF} Création d'un utilisateur MQTT..."
mosquitto_passwd -c -b /etc/mosquitto/pwfile "$MQTT_USER" "$MQTT_PASSWORD" && log_success "Utilisateur MQTT créé." || {
    log_error "Erreur lors de la création de l'utilisateur MQTT."
    exit 1
}

# Création d'un fichier ACL de base
progress "${ICON_CONF} Création d'un fichier ACL pour Mosquitto..."
if [ -f configs/acl.conf ]; then
    cat configs/acl.conf > /etc/mosquitto/acl.conf
    log_success "Fichier ACL configuré."
else
    log_warn "Le fichier 'configs/acl.conf' est introuvable. Étape ignorée."
fi

# Définir les permissions pour les fichiers de configuration Mosquitto
progress "${ICON_CONF} Définition des permissions pour Mosquitto..."
chown mosquitto:mosquitto /etc/mosquitto/pwfile
chmod 644 /etc/mosquitto/pwfile
chown mosquitto:mosquitto -R /etc/mosquitto/
chmod 755 /etc/mosquitto/
chown mosquitto:mosquitto /etc/mosquitto/acl.conf
chmod 644 /etc/mosquitto/acl.conf
mkdir -p /var/lib/mosquitto/
chown -R mosquitto:mosquitto /var/lib/mosquitto/
chmod -R 770 /var/lib/mosquitto/
mkdir -p /var/log/mosquitto/
chown -R mosquitto:mosquitto /var/log/mosquitto/
chmod -R 770 /var/log/mosquitto/
log_success "Permissions définies pour Mosquitto."

# Rendre les scripts additionnels exécutables
progress "${ICON_INSTALL} Mise en exécution des scripts additionnels..."
if [ -d ../modules ]; then
    chmod +x ../modules/flash.sh ../modules/transfer.sh
    log_success "Scripts additionnels rendus exécutables."
else
    log_warn "Le dossier 'modules' n'existe pas. Étape ignorée."
fi

# Installation et activation du script init.d personnalisé
progress "${ICON_CONF} Installation et activation du script init.d 'mqttFlight-modulesrc'..."
if [ -f configs/init.d/mqttFlight-modulesrc ]; then
    cat configs/init.d/mqttFlight-modulesrc > /etc/init.d/mqttFlight-modulesrc
    chmod +x /etc/init.d/mqttFlight-modulesrc
    rc-update add mqttFlight-modulesrc
    rc-service mqttFlight-modulesrc restart
    log_success "Script init.d 'mqttFlight-modulesrc' installé et démarré."
else
    log_warn "Le fichier 'configs/init.d/mqttFlight-modulesrc' est introuvable. Étape ignorée."
fi

# Configuration de logrotate et des tâches cron
progress "${ICON_CONF} Configuration de logrotate et des tâches cron..."
if [ -f configs/logrotate/mosquitto ]; then
    cat configs/logrotate/mosquitto > /etc/logrotate.d/mosquitto
    log_success "logrotate pour Mosquitto configuré."
else
    log_warn "Le fichier 'configs/logrotate/mosquitto' est introuvable."
fi
if [ -f configs/crontabs/root ]; then
    cat configs/crontabs/root > /etc/crontabs/root
    log_success "Cron configuré."
else
    log_warn "Le fichier 'configs/crontabs/root' est introuvable."
fi
rc-update add crond
rc-service crond start

# Activation et redémarrage de Mosquitto
progress "${ICON_START} Activation et redémarrage de Mosquitto..."
rc-update add mosquitto
rc-service mosquitto restart
log_success "Mosquitto activé et redémarré."

# Affichage du résumé final
echo -e "\n${ICON_OK} ${GREEN}Résumé des configurations appliquées :${NC}"
echo "1. Point d'accès Wi-Fi configuré avec SSID : ${SSID} et mot de passe : ${WIFI_PASSWORD}"
echo "2. Python 3 et Node.js installés, environnement Python configuré"
echo "3. Mosquitto MQTT Broker sauvegardé, configuré et redémarré"
echo "4. Services hostapd et dnsmasq démarrés et ajoutés au démarrage"
echo "5. Utilisateur MQTT '${MQTT_USER}' créé et fichier ACL en place"
echo "6. Script init.d 'mqttFlight-modulesrc' installé et démarré"
echo "7. logrotate et cron configurés"

log_success "Configuration terminée avec succès."
