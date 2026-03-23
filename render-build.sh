#!/usr/bin/env bash
# exit on error
set -o errexit

echo "─── 🚀 DÉBUT DU BUILD AGRIDIRECT ───"

echo "📦 Installation des dépendances..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "🎨 Collecte des fichiers statiques UI..."
python manage.py collectstatic --no-input

echo "🛡️ Application des migrations (Base de données)..."
python manage.py migrate --no-input

echo "🌱 Initialisation des données (Produits & Admin)..."
python manage.py seed_initial_data
python manage.py seed_dummy_data

echo "✅ BUILD TERMINÉ AVEC SUCCÈS !"
