# Guide de démarrage rapide

## Installation rapide

### Méthode automatique (recommandée)

L'application installe automatiquement toutes les dépendances au démarrage !

**Windows :**
```bash
start.bat
```

**Linux/macOS :**
```bash
chmod +x start.sh
./start.sh
```

**Ou manuellement :**
```bash
python run.py
```

### Méthode manuelle

1. Installer les dépendances :
```bash
python install_dependencies.py
```

2. Installer Tesseract OCR (optionnel mais recommandé) :
   - Windows : Télécharger depuis https://github.com/UB-Mannheim/tesseract/wiki
   - Linux : `sudo apt-get install tesseract-ocr tesseract-ocr-fra`
   - macOS : `brew install tesseract tesseract-lang`

3. Configurer l'environnement :
```bash
cp .env.example .env
# Éditer .env selon vos besoins
```

4. Initialiser la base de données :
```bash
alembic upgrade head
```

5. Démarrer :
```bash
uvicorn app.main:app --reload
```

## Démarrage

L'application vérifie et installe automatiquement les dépendances au démarrage. Vous pouvez utiliser :

- **Script simplifié** : `python run.py` ou `start.bat` / `start.sh`
- **Méthode classique** : `uvicorn app.main:app --reload`

**Note** : Au premier démarrage, l'installation des dépendances peut prendre quelques minutes.

L'API sera disponible sur `http://localhost:8000`

Documentation interactive : `http://localhost:8000/docs`

## Utilisation de l'API

### Uploader un document

```bash
curl -X POST "http://localhost:8000/api/v1/documents" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@document.pdf"
```

### Vérifier le statut

```bash
curl "http://localhost:8000/api/v1/documents/{document_id}"
```

### Lancer l'extraction

```bash
curl -X POST "http://localhost:8000/api/v1/documents/{document_id}/extract"
```

## Structure des données

Les données structurées sont organisées en :
- **Blocs de texte** : Avec entités nommées, structure, relations
- **Tableaux** : Avec schéma automatique et typage des colonnes
- **Images** : Avec métadonnées et texte OCR si disponible

Chaque bloc contient des métadonnées complètes pour la préparation RAG.

