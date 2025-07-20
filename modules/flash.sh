#!/bin/sh
# Script pour flasher un fichier binaire sur un ESP8266
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
ICON_FLASH="🔧"

# Nombre total d'étapes (à mettre à jour si le script évolue)
TOTAL_STEPS=4
step=1

# Fonctions de log
log_info()   { echo -e "${ICON_INFO} ${BLUE}[INFO]${NC} $1"; }
log_success(){ echo -e "${ICON_OK} ${GREEN}[SUCCESS]${NC} $1"; }
log_error()  { echo -e "${ICON_ERROR} ${RED}[ERROR]${NC} $1"; }
log_warn()   { echo -e "${ICON_WARN} ${YELLOW}[WARN]${NC} $1"; }
progress()   { echo -e "[${step}/${TOTAL_STEPS}] $1"; step=$((step + 1)); }

# Vérifie si le fichier binaire existe
progress "${ICON_FLASH} Vérification de l'existence du fichier binaire..."
if [ ! -f "ESP8266/ESP8266.bin" ]; then
    log_error "Le fichier ESP8266.bin n'existe pas dans le répertoire courant."
    exit 1
fi
log_success "Fichier binaire trouvé."

# Active l'environnement virtuel
progress "${ICON_FLASH} Activation de l'environnement virtuel..."
source /root/venv/bin/activate
log_success "Environnement virtuel activé."

# Efface la mémoire flash de l'ESP8266
progress "${ICON_FLASH} Effacement de la mémoire flash..."
esptool --port /dev/ttyUSB0 erase_flash && log_success "Mémoire flash effacée." || {
    log_error "Erreur lors de l'effacement de la mémoire flash."
    deactivate
    exit 1
}

# Écrit le fichier binaire sur l'ESP8266
progress "${ICON_FLASH} Écriture du fichier binaire sur l'ESP8266..."
esptool --port /dev/ttyUSB0 --baud 460800 write_flash --flash-size=detect 0 ESP8266/ESP8266.bin && log_success "Fichier binaire écrit avec succès." || {
    log_error "Erreur lors de l'écriture du fichier binaire."
    deactivate
    exit 1
}

# Désactive l'environnement virtuel
progress "${ICON_FLASH} Désactivation de l'environnement virtuel..."
deactivate
log_success "Environnement virtuel désactivé."

# Appelle le script de transfert
progress "${ICON_FLASH} Appel du script de transfert..."
./transfer.sh
log_success "Script de transfert exécuté."

log_success "Flashing terminé avec succès."