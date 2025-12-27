# Schéma de Fonctionnement - Workflow de la Méthode Extract

## Vue d'ensemble du Workflow Complet

```mermaid
flowchart TD
    Start([POST /documents/{id}/extract]) --> Validate{Document existe?}
    
    Validate -->|Non| Error404[404 Not Found]
    Validate -->|Oui| CheckStatus{Status = EXTRACTING?}
    
    CheckStatus -->|Oui| Error409[409 Conflict]
    CheckStatus -->|Non| UpdateStatus[Update status = EXTRACTING]
    
    UpdateStatus --> InitPipeline[Initialiser ExtractionPipeline]
    
    InitPipeline --> Extract[1. Extraction Base<br/>PDF/Office/Images]
    
    Extract --> ExtractResult{Contenu extrait?}
    ExtractResult -->|Non| ErrorExtract[Erreur: Aucun contenu]
    ExtractResult -->|Oui| ProcessImages[2. Traitement Images + OCR Amélioré]
    
    ProcessImages --> OCRWorkflow[Workflow OCR Multi-tentatives]
    
    OCRWorkflow --> PreprocessImages[Preprocessing Avancé<br/>ImagePreprocessor]
    PreprocessImages --> MultiAttempt[Multi-tentatives OCR<br/>Plusieurs PSM modes]
    MultiAttempt --> SelectBest[Sélection Meilleur Résultat]
    SelectBest --> PostCorrect[Correction Post-OCR<br/>OcrCorrector]
    
    PostCorrect --> Enrichment[3. Enrichissement<br/>SpaCy NLP + Normalisation]
    
    Enrichment --> Structure[4. Structuration<br/>Organisation hiérarchique]
    
    Structure --> SaveDB[5. Sauvegarde Base de Données]
    
    SaveDB --> UpdateCompleted[Update status = COMPLETED]
    UpdateCompleted --> Success[202 Accepted<br/>Retour résultat]
    
    Error404 --> End([Fin])
    Error409 --> End
    ErrorExtract --> Rollback[ROLLBACK DB]
    Rollback --> UpdateFailed[Update status = FAILED]
    UpdateFailed --> Error500[500 Internal Server Error]
    Error500 --> End
    Success --> End
    
    style Start fill:#e1f5ff
    style Success fill:#d4edda
    style Error404 fill:#f8d7da
    style Error409 fill:#f8d7da
    style Error500 fill:#f8d7da
    style Extract fill:#fff3cd
    style ProcessImages fill:#fff3cd
    style OCRWorkflow fill:#cfe2ff
    style PreprocessImages fill:#cfe2ff
    style MultiAttempt fill:#cfe2ff
    style PostCorrect fill:#cfe2ff
    style Enrichment fill:#fff3cd
    style Structure fill:#fff3cd
    style SaveDB fill:#d1ecf1
```

## Workflow Détaillé de l'OCR Amélioré

```mermaid
sequenceDiagram
    participant ImageProcessor
    participant OcrService
    participant ImagePreprocessor
    participant Tesseract
    participant OcrCorrector
    participant Result

    ImageProcessor->>OcrService: extract_text(image_data, lang="fra+eng")
    
    Note over OcrService: Multi-tentatives activé
    
    loop Pour chaque méthode de preprocessing
        OcrService->>ImagePreprocessor: preprocess(image, method)
        
        alt Méthode Advanced
            ImagePreprocessor->>ImagePreprocessor: 1. Upscaling si < 300 DPI
            ImagePreprocessor->>ImagePreprocessor: 2. Conversion niveaux de gris
            ImagePreprocessor->>ImagePreprocessor: 3. Correction rotation
            ImagePreprocessor->>ImagePreprocessor: 4. Amélioration contraste adaptative
            ImagePreprocessor->>ImagePreprocessor: 5. Binarisation adaptative (Otsu)
            ImagePreprocessor->>ImagePreprocessor: 6. Débruitage avancé
            ImagePreprocessor->>ImagePreprocessor: 7. Amélioration netteté
        else Méthode Aggressive
            ImagePreprocessor->>ImagePreprocessor: Upscaling x2 + Binarisation Otsu + Débruitage morphologique
        else Méthode Basic
            ImagePreprocessor->>ImagePreprocessor: Contraste + Netteté + Débruitage simple
        end
        
        ImagePreprocessor-->>OcrService: processed_image
        
        loop Pour chaque PSM mode (6, 11, 3, 12)
            OcrService->>Tesseract: image_to_string(processed_image, config="--psm X --oem 3")
            Tesseract-->>OcrService: (ocr_text, ocr_data)
            
            OcrService->>OcrService: Calculer confiance moyenne
            OcrService->>OcrService: Stocker résultat (text, confidence, config)
        end
    end
    
    OcrService->>OcrService: Trier résultats par confiance
    OcrService->>OcrService: Sélectionner meilleur résultat
    
    OcrService->>OcrCorrector: correct_with_confidence(best_text, best_confidence)
    
    Note over OcrCorrector: Corrections appliquées
    
    OcrCorrector->>OcrCorrector: 1. Correction patterns regex
    OcrCorrector->>OcrCorrector: 2. Correction mots complets
    OcrCorrector->>OcrCorrector: 3. Correction dates contextuelle
    OcrCorrector->>OcrCorrector: 4. Correction nombres
    OcrCorrector->>OcrCorrector: 5. Correction mots français
    OcrCorrector->>OcrCorrector: 6. Nettoyage final
    
    OcrCorrector-->>OcrService: (corrected_text, adjusted_confidence)
    
    OcrService-->>ImageProcessor: (corrected_text, confidence)
    
    ImageProcessor->>ImageProcessor: Créer TextBlock depuis OCR
    ImageProcessor-->>Result: (processed_image, ocr_text_block)
```

## Architecture des Composants OCR

```mermaid
graph TB
    subgraph "ImageProcessor"
        IP[ImageProcessor.process]
    end
    
    subgraph "OcrService - Service Principal"
        OS[OcrService]
        OS -->|utilise| MultiAttempt[Multi-tentatives]
        OS -->|sélectionne| BestResult[Meilleur Résultat]
    end
    
    subgraph "ImagePreprocessor - Preprocessing"
        IPP[ImagePreprocessor]
        IPP --> Upscale[Upscaling 300 DPI]
        IPP --> Rotate[Correction Rotation]
        IPP --> Contrast[Contraste Adaptatif]
        IPP --> Binarize[Binarisation Otsu]
        IPP --> Denoise[Débruitage Avancé]
        IPP --> Sharpen[Netteté]
    end
    
    subgraph "Tesseract OCR"
        TESS[Tesseract Engine]
        TESS --> PSM6[PSM 6: Bloc uniforme]
        TESS --> PSM11[PSM 11: Texte dense]
        TESS --> PSM3[PSM 3: Auto complet]
        TESS --> PSM12[PSM 12: Avec OSD]
    end
    
    subgraph "OcrCorrector - Post-traitement"
        OC[OcrCorrector]
        OC --> Patterns[Correction Patterns]
        OC --> Words[Correction Mots]
        OC --> Dates[Correction Dates]
        OC --> Numbers[Correction Nombres]
        OC --> Clean[Nettoyage]
    end
    
    IP -->|appelle| OS
    OS -->|utilise| IPP
    OS -->|appelle| TESS
    OS -->|utilise| OC
    
    style OS fill:#cfe2ff
    style IPP fill:#fff3cd
    style TESS fill:#d1ecf1
    style OC fill:#d4edda
```

## Flux de Données Détaillé

```mermaid
flowchart LR
    subgraph "Input"
        ImageData[Image Data<br/>bytes]
    end
    
    subgraph "Preprocessing Multi-Méthodes"
        Method1[Method: Advanced<br/>Upscale + Binarisation Otsu]
        Method2[Method: Aggressive<br/>Upscale x2 + Morphologique]
        Method3[Method: Basic<br/>Contraste + Netteté]
    end
    
    subgraph "OCR Multi-PSM"
        PSM6[PSM 6<br/>Bloc uniforme]
        PSM11[PSM 11<br/>Texte dense]
        PSM3[PSM 3<br/>Auto complet]
        PSM12[PSM 12<br/>Avec OSD]
    end
    
    subgraph "Sélection"
        Compare[Comparer Résultats<br/>Par Confiance]
        Select[Meilleur Résultat]
    end
    
    subgraph "Correction"
        Correct[OcrCorrector<br/>Post-traitement]
    end
    
    subgraph "Output"
        Result[Texte Corrigé<br/>+ Confiance]
    end
    
    ImageData --> Method1
    ImageData --> Method2
    ImageData --> Method3
    
    Method1 --> PSM6
    Method1 --> PSM11
    Method1 --> PSM3
    Method1 --> PSM12
    
    Method2 --> PSM6
    Method2 --> PSM11
    Method2 --> PSM3
    Method2 --> PSM12
    
    Method3 --> PSM6
    Method3 --> PSM11
    Method3 --> PSM3
    Method3 --> PSM12
    
    PSM6 --> Compare
    PSM11 --> Compare
    PSM3 --> Compare
    PSM12 --> Compare
    
    Compare --> Select
    Select --> Correct
    Correct --> Result
    
    style ImageData fill:#e1f5ff
    style Result fill:#d4edda
    style Compare fill:#fff3cd
    style Correct fill:#cfe2ff
```

## Exemple de Corrections Appliquées

```mermaid
flowchart TD
    Start[Texte OCR Brut] --> Step1[Étape 1: Patterns Regex]
    
    Step1 -->|"cudi"| Step1a["Jeudi"]
    Step1 -->|"2 mbre 2025"| Step1b["25 décembre 2025"]
    Step1 -->|"d'fos"| Step1c["d'infos"]
    
    Step1a --> Step2[Étape 2: Mots Complets]
    Step1b --> Step2
    Step1c --> Step2
    
    Step2 --> Step3[Étape 3: Dates Contextuelles]
    Step3 --> Step4[Étape 4: Nombres]
    Step4 --> Step5[Étape 5: Mots Français]
    Step5 --> Step6[Étape 6: Nettoyage]
    
    Step6 --> End[Texte Corrigé Final]
    
    style Start fill:#f8d7da
    style End fill:#d4edda
    style Step1 fill:#fff3cd
    style Step2 fill:#fff3cd
    style Step3 fill:#fff3cd
    style Step4 fill:#fff3cd
    style Step5 fill:#fff3cd
    style Step6 fill:#cfe2ff
```

## Détails Techniques des PSM Modes

| PSM Mode | Description | Utilisation |
|----------|-------------|-------------|
| **3** | Segmentation automatique complète (défaut) | Documents variés |
| **6** | Bloc uniforme de texte | Texte en colonne unique |
| **11** | Texte dense | Texte dense sans structure claire |
| **12** | Texte avec OSD | Détection orientation et script |

## Méthodes de Preprocessing

| Méthode | Caractéristiques | Cas d'usage |
|---------|------------------|-------------|
| **Basic** | Contraste + Netteté + Débruitage simple | Images de bonne qualité |
| **Advanced** | Upscaling + Binarisation Otsu + Débruitage avancé | Images normales |
| **Aggressive** | Upscaling x2 + Binarisation Otsu + Morphologique | Images de mauvaise qualité |

## Exemples de Corrections

### Avant → Après

1. **"cudi 2 mbre 2025"** → **"Jeudi 25 décembre 2025"**
   - Correction pattern "cudi" → "Jeudi"
   - Correction date "2 mbre" → "25 décembre"

2. **"plus d'fos"** → **"plus d'infos"**
   - Correction pattern "d'fos" → "d'infos"

3. **"JOURNAL OFFICIEL\nREPUBLIQUE DEMOCRATIQUE DU CONGO"** → **"JOURNAL OFFICIEL\nDE LA\nREPUBLIQUE DEMOCRATIQUE DU CONGO"**
   - Correction contextuelle des mots manquants

## Diagramme de Séquence Complet - Extraction avec OCR

```mermaid
sequenceDiagram
    participant Client
    participant Endpoint as POST /extract
    participant Pipeline as ExtractionPipeline
    participant Extractor as BaseExtractor
    participant ImageProc as ImageProcessor
    participant OcrService as OcrService
    participant Preprocessor as ImagePreprocessor
    participant Tesseract as Tesseract OCR
    participant Corrector as OcrCorrector
    participant TextEnricher as TextEnricher
    participant Structurer as ContentStructurer
    participant DB as Base de données

    Client->>Endpoint: POST /documents/{id}/extract
    
    Note over Endpoint: Validation et Initialisation
    Endpoint->>Endpoint: Vérifier document existe
    Endpoint->>Endpoint: Vérifier status != EXTRACTING
    Endpoint->>DB: UPDATE status = EXTRACTING
    
    Endpoint->>Pipeline: process(file_path, document)
    
    Note over Pipeline: 1. Extraction Base (10%)
    Pipeline->>Extractor: extract(file_path)
    Extractor->>Extractor: Extraire texte, tableaux, images
    Extractor-->>Pipeline: ExtractionResult
    
    Note over Pipeline: 2. Traitement Images + OCR (25%)
    Pipeline->>ImageProc: process_batch(images)
    
    loop Pour chaque image
        ImageProc->>OcrService: extract_text(image_data)
        
        Note over OcrService: Multi-tentatives activées
        
        loop Méthodes preprocessing (advanced, aggressive, basic)
            OcrService->>Preprocessor: preprocess(image, method)
            
            alt Method = Advanced
                Preprocessor->>Preprocessor: Upscale si < 300 DPI
                Preprocessor->>Preprocessor: Convertir niveaux de gris
                Preprocessor->>Preprocessor: Corriger rotation
                Preprocessor->>Preprocessor: Améliorer contraste adaptatif
                Preprocessor->>Preprocessor: Binarisation Otsu
                Preprocessor->>Preprocessor: Débruitage avancé
                Preprocessor->>Preprocessor: Améliorer netteté
            else Method = Aggressive
                Preprocessor->>Preprocessor: Upscale x2 + Binarisation + Morphologique
            else Method = Basic
                Preprocessor->>Preprocessor: Contraste + Netteté + Débruitage
            end
            
            Preprocessor-->>OcrService: processed_image
            
            loop PSM modes (6, 11, 3, 12)
                OcrService->>Tesseract: image_to_string(processed_image, config="--psm X --oem 3")
                Tesseract-->>OcrService: (ocr_text, ocr_data)
                OcrService->>OcrService: Calculer confiance moyenne
                OcrService->>OcrService: Stocker (text, confidence, config)
            end
        end
        
        OcrService->>OcrService: Trier résultats par confiance
        OcrService->>OcrService: Sélectionner meilleur résultat
        
        OcrService->>Corrector: correct_with_confidence(best_text, best_confidence)
        
        Corrector->>Corrector: Correction patterns regex
        Corrector->>Corrector: Correction mots complets
        Corrector->>Corrector: Correction dates
        Corrector->>Corrector: Correction nombres
        Corrector->>Corrector: Nettoyage final
        
        Corrector-->>OcrService: (corrected_text, adjusted_confidence)
        OcrService-->>ImageProc: (corrected_text, confidence)
        
        ImageProc->>ImageProc: Créer TextBlock depuis OCR
    end
    
    ImageProc-->>Pipeline: (processed_images, ocr_text_blocks)
    Pipeline->>Pipeline: Ajouter ocr_text_blocks aux text_blocks
    
    Note over Pipeline: 3. Enrichissement (40%)
    Pipeline->>TextEnricher: enrich_batch(text_blocks)
    TextEnricher->>TextEnricher: SpaCy NLP (NER, structure)
    TextEnricher-->>Pipeline: enriched_texts
    
    Pipeline->>Pipeline: normalize_batch(tables)
    
    Note over Pipeline: 4. Structuration (70%)
    Pipeline->>Structurer: structure(extraction_result)
    Structurer-->>Pipeline: content_blocks
    Pipeline->>Pipeline: document_structurer.structure()
    Pipeline-->>Endpoint: StructuredData
    
    Note over Endpoint: 5. Sauvegarde (100%)
    Endpoint->>DB: DELETE anciens content_blocks
    Endpoint->>DB: INSERT nouveaux content_blocks
    Endpoint->>DB: INSERT/UPDATE structured_data
    Endpoint->>DB: UPDATE status = COMPLETED
    
    Endpoint-->>Client: 202 Accepted {message, document_id, blocks_count}
```

## Performance et Optimisation

- **Multi-tentatives** : Jusqu'à 12 combinaisons testées (3 méthodes × 4 PSM modes)
- **Sélection intelligente** : Choix du meilleur résultat par confiance
- **Correction ciblée** : Corrections spécifiques pour erreurs courantes
- **Fallback** : Si toutes les tentatives échouent, utilisation de la méthode basique
- **Parallélisation** : Traitement des images en batch pour améliorer les performances

