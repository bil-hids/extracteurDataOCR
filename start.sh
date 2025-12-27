#!/bin/bash
# Script de démarrage pour Linux/macOS

echo "========================================"
echo "Extracteur de Données - Démarrage"
echo "========================================"
echo ""

# Vérifier si Python est installé
if ! command -v python3 &> /dev/null; then
    echo "ERREUR: Python 3 n'est pas installé"
    echo "Veuillez installer Python 3.11+"
    exit 1
fi

echo "Installation/Vérification des dépendances..."
python3 install_dependencies.py

echo ""
echo "Démarrage du serveur..."
echo ""
python3 run.py

