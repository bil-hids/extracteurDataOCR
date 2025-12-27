# Système d'extraction et prétraitement de données

Système modulaire de niveau production pour l'extraction et le prétraitement de données depuis multiples formats de fichiers (PDF, Office, images).

## Fonctionnalités

- **Extraction multi-formats** : PDF, Word, Excel, images (OCR)
- **Enrichissement NLP** : NER, détection de structure, extraction de relations avec SpaCy
- **Structuration intelligente** : Transformation en données structurées JSON
- **API REST** : FastAPI avec documentation automatique
- **Traitement asynchrone** : Pipeline de traitement non-bloquant

## Installation

### Prérequis

- Python 3.11+
- Tesseract OCR (pour l'extraction d'images) - optionnel mais recommandé

### Installation automatique (recommandé)

Le système vérifie et installe automatiquement les dépendances au démarrage, mais vous pouvez aussi les installer manuellement :

```bash
# Installation automatique de toutes les dépendances
python install_dependencies.py
```

Ou installation manuelle :

```bash
# 1. Installer les packages Python
pip install -r requirements/base.txt

# 2. Installer le modèle SpaCy français
python -m spacy download fr_core_news_md

# 3. Installer Tesseract OCR (selon votre OS)
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr tesseract-ocr-fra
# macOS: brew install tesseract tesseract-lang
```

Pour le développement :

```bash
pip install -r requirements/dev.txt
```

## Configuration

Copier `.env.example` vers `.env` et ajuster les paramètres :

```bash
cp .env.example .env
```

## Utilisation

### Démarrer le serveur

L'application vérifie et installe automatiquement les dépendances au démarrage :

```bash
uvicorn app.main:app --reload
```

L'API sera disponible sur `http://localhost:8000`

Documentation interactive : `http://localhost:8000/docs`

**Note** : Au premier démarrage, l'application peut prendre quelques instants pour installer les dépendances manquantes (modèle SpaCy, etc.).

## Architecture

Le système suit une architecture en couches (Clean Architecture) :

- **Domain** : Entités métier et value objects
- **Infrastructure** : Extracteurs, processeurs, structurateurs
- **Application** : Use cases et pipelines
- **API** : Endpoints FastAPI

## Tests

```bash
pytest
```

## Licence

MIT

"# extracteurDataOCR" 
