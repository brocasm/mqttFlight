#!/bin/sh
# Script pour transférer des fichiers sur un ESP8266
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
ICON_TRANSFER="📤"

# Nombre total d'étapes (à mettre à jour si le script évolue)
TOTAL_STEPS=10
step=1

DIR_TO_TRANSFER="/root/mqttFlight/modules/src"

# Fonctions de log
log_info()   { echo -e "${ICON_INFO} ${BLUE}[INFO]${NC} $1"; }
log_success(){ echo -e "${ICON_OK} ${GREEN}[SUCCESS]${NC} $1"; }
log_error()  { echo -e "${ICON_ERROR} ${RED}[ERROR]${NC} $1"; }
log_warn()   { echo -e "${ICON_WARN} ${YELLOW}[WARN]${NC} $1"; }
progress()   { echo -e "[${step}/${TOTAL_STEPS}] $1"; step=$((step + 1)); }

# Active l'environnement virtuel
progress "${ICON_TRANSFER} Activation de l'environnement virtuel..."
source /root/venv/bin/activate
log_success "Environnement virtuel activé."

# Liste des fichiers à transférer (sans le chemin)
files=$(ls "$DIR_TO_TRANSFER")

# Chemin source des fichiers
source_path="/root/mqttFlight/modules/src"

# Transfère chaque fichier sur l'ESP8266
for file in $files; do
    source_file="$source_path/$file"
    progress "${ICON_TRANSFER} Transfert de $source_file sur l'ESP8266..."
    ampy --port /dev/ttyUSB0 put $source_file && log_success "Transfert de $file terminé avec succès." || {
        log_error "Erreur lors du transfert de $file."
        deactivate
        exit 1
    }
done

# Crée le dossier core sur l'ESP8266
progress "${ICON_TRANSFER} Création du dossier core sur l'ESP8266..."
ampy --port /dev/ttyUSB0 mkdir /core && log_success "Dossier core créé avec succès." || {
    log_error "Erreur lors de la création du dossier core."
    deactivate
    exit 1
}

# Transfère tous les fichiers du dossier core en conservant leur structure
core_path="$source_path/core"
for file in $(find "$core_path" -type f); do
    relative_path="${file#$source_path/}"
    progress "${ICON_TRANSFER} Transfert de $file sur l'ESP8266 avec le chemin $relative_path..."
    ampy --port /dev/ttyUSB0 put "$file" "$relative_path" && log_success "Transfert de $file terminé avec succès." || {
        log_error "Erreur lors du transfert de $file."
        deactivate
        exit 1
    }
done

# Liste les fichiers à la racine de l'ESP8266
progress "${ICON_TRANSFER} Liste des fichiers à la racine de l'ESP8266 :"
ampy --port /dev/ttyUSB0 ls
log_success "Liste des fichiers à la racine de l'ESP8266 affichée."

# Liste les fichiers dans le dossier core de l'ESP8266
progress "${ICON_TRANSFER} Liste des fichiers dans le dossier core de l'ESP8266 :"
ampy --port /dev/ttyUSB0 ls /core
log_success "Liste des fichiers dans le dossier core de l'ESP8266 affichée."

# Désactive l'environnement virtuel
progress "${ICON_TRANSFER} Désactivation de l'environnement virtuel..."
deactivate
log_success "Environnement virtuel désactivé."

log_success "Transfert terminé avec succès."