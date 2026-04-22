#!/bin/bash
# ================================================================
# Script de déploiement Odoo ERP Commercial sur Azure VM
# ================================================================
# Usage: chmod +x deploy.sh && sudo ./deploy.sh
# ================================================================

set -e

echo "=========================================="
echo " Déploiement Odoo ERP Commercial - Azure"
echo "=========================================="

# --- 1. Mise à jour du système ---
echo "[1/7] Mise à jour du système..."
apt-get update && apt-get upgrade -y

# --- 2. Installation de Docker ---
echo "[2/7] Installation de Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
    usermod -aG docker $USER
    echo "Docker installé avec succès"
else
    echo "Docker déjà installé"
fi

# --- 3. Installation de Docker Compose ---
echo "[3/7] Installation de Docker Compose..."
if ! command -v docker compose &> /dev/null; then
    apt-get install -y docker-compose-plugin
    echo "Docker Compose installé"
else
    echo "Docker Compose déjà installé"
fi

# --- 4. Installation de Git ---
echo "[4/7] Installation de Git..."
apt-get install -y git

# --- 5. Cloner le projet ---
echo "[5/7] Clonage du projet..."
PROJECT_DIR="/opt/odoo-erp-commercial"
if [ -d "$PROJECT_DIR" ]; then
    echo "Projet déjà cloné, mise à jour..."
    cd $PROJECT_DIR
    git pull origin main
else
    git clone https://github.com/belhaid2001-star/odoo-erp-commercial.git $PROJECT_DIR
    cd $PROJECT_DIR
fi

# --- 6. Configurer le swap (important pour 1 Go RAM) ---
echo "[6/7] Configuration du swap (2 Go)..."
if [ ! -f /swapfile ]; then
    fallocate -l 2G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
    echo "Swap de 2 Go activé"
else
    echo "Swap déjà configuré"
fi

# --- 7. Copier la config de production ---
echo "[7/7] Configuration et lancement..."
cp deploy/odoo.prod.conf config/odoo.conf

# Créer les dossiers certbot
mkdir -p deploy/certbot/conf deploy/certbot/www

# Lancer avec le docker-compose de production et attendre que les services soient sains
docker compose -f deploy/docker-compose.prod.yml up -d --wait
docker compose -f deploy/docker-compose.prod.yml ps

echo ""
echo "=========================================="
echo " DÉPLOIEMENT TERMINÉ !"
echo "=========================================="
echo ""
echo " Odoo est accessible sur : http://$(curl -s ifconfig.me):80"
echo ""
echo " Identifiants par défaut :"
echo "   - Email    : admin"
echo "   - Mot de passe : admin"
echo "   - Master Password : admin_odoo_2026"
echo ""
echo " Pour activer HTTPS avec un domaine :"
echo "   1. Pointer votre domaine vers cette IP"
echo "   2. Exécuter : sudo ./deploy/setup-ssl.sh votre-domaine.com"
echo ""
echo "=========================================="
