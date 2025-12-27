"""Enrichisseur de texte avec SpaCy."""

import asyncio
from typing import Any

import spacy
from spacy import Language
from spacy.lang.fr import French

from app.core.exceptions import EnrichmentError
from app.core.logging import get_logger
from app.domain.value_objects.extraction_result import TextBlock
from app.infrastructure.processors.base import BaseProcessor


class TextEnricher(BaseProcessor):
    """Enrichisseur de texte avec NLP avancé (SpaCy)."""

    def __init__(self, model_name: str = "fr_core_news_md", logger: Any = None) -> None:
        """Initialiser l'enrichisseur."""
        super().__init__(logger or get_logger(__name__))
        self.model_name = model_name
        self.nlp: Language | None = None
        self._load_model()

    def _load_model(self) -> None:
        """Charger le modèle SpaCy."""
        try:
            self.nlp = spacy.load(self.model_name)
            self.logger.info(f"Modèle SpaCy chargé: {self.model_name}")
        except OSError:
            self.logger.warning(
                f"Modèle {self.model_name} non trouvé, utilisation du modèle français de base"
            )
            self.nlp = French()
            # Ajouter le pipeline de base
            if not self.nlp.has_pipe("ner"):
                self.nlp.add_pipe("ner")

    async def enrich(self, text_block: TextBlock) -> TextBlock:
        """
        Enrichir un bloc de texte avec NLP.

        Args:
            text_block: Bloc de texte à enrichir

        Returns:
            Bloc de texte enrichi avec entités, relations, etc.
        """
        if not self.nlp:
            raise EnrichmentError("Modèle SpaCy non chargé")

        try:
            loop = asyncio.get_event_loop()
            enriched = await loop.run_in_executor(None, self._enrich_sync, text_block)
            return enriched
        except Exception as e:
            self.logger.exception(f"Erreur lors de l'enrichissement: {e}")
            raise EnrichmentError(f"Échec de l'enrichissement: {str(e)}")

    def _enrich_sync(self, text_block: TextBlock) -> TextBlock:
        """Enrichissement synchrone."""
        if not self.nlp:
            return text_block

        doc = self.nlp(text_block.content)

        # Extraire les entités nommées
        entities = self._extract_entities(doc)

        # Détecter la structure
        structure = self._detect_structure(doc)

        # Extraire les relations
        relations = self._extract_relations(doc)

        # Calculer le score de pertinence
        relevance_score = self._calculate_relevance_score(doc, entities)

        # Détecter la langue
        language = self._detect_language(doc)

        # Extraire les phrases clés
        key_phrases = self._extract_key_phrases(doc)

        # Mettre à jour les métadonnées - créer un nouveau dict pour éviter les problèmes avec Pydantic
        additional_metadata = dict(text_block.metadata.additional_metadata)
        additional_metadata.update(
            {
                "entities": entities,
                "structure": structure,
                "relations": relations,
                "key_phrases": key_phrases,
                "language": language,
                "token_count": len(doc),
                "sentence_count": len(list(doc.sents)),
                "relevance_score": relevance_score,
            }
        )

        # Créer une nouvelle instance de ContentMetadata avec les valeurs mises à jour
        from app.domain.value_objects.content_metadata import ContentMetadata
        
        updated_metadata = ContentMetadata(
            page_number=text_block.metadata.page_number,
            position=text_block.metadata.position,
            order=text_block.metadata.order,
            section_id=text_block.metadata.section_id,
            section_level=text_block.metadata.section_level,
            section_title=text_block.metadata.section_title,
            language=language,
            confidence=relevance_score,
            extraction_method=text_block.metadata.extraction_method,
            additional_metadata=additional_metadata,
        )

        # Créer un nouveau TextBlock avec les métadonnées mises à jour
        return TextBlock(
            content=text_block.content,
            metadata=updated_metadata,
        )

    def _extract_entities(self, doc: Any) -> list[dict[str, Any]]:
        """Extraire les entités nommées avec contexte."""
        entities = []
        for ent in doc.ents:
            entities.append(
                {
                    "text": ent.text,
                    "label": ent.label_,
                    "start": ent.start_char,
                    "end": ent.end_char,
                    "confidence": 1.0,  # SpaCy ne fournit pas de confiance par défaut
                }
            )
        return entities

    def _detect_structure(self, doc: Any) -> dict[str, Any]:
        """Détecter la structure du texte (titres, paragraphes, listes)."""
        structure = {
            "headings": [],
            "paragraphs": [],
            "lists": [],
        }

        # Détecter les phrases courtes qui pourraient être des titres
        for sent in doc.sents:
            if len(sent) <= 10 and sent.text.strip().isupper():
                structure["headings"].append({"text": sent.text, "level": 1})
            else:
                structure["paragraphs"].append(sent.text)

        return structure

    def _extract_relations(self, doc: Any) -> list[dict[str, Any]]:
        """Extraire les relations entre entités."""
        relations = []

        # Relations basiques basées sur la proximité et les dépendances
        entities = list(doc.ents)
        for i, ent1 in enumerate(entities):
            for ent2 in entities[i + 1 :]:
                # Vérifier la proximité
                distance = abs(ent1.start - ent2.start)
                if distance < 50:  # Entités proches
                    relations.append(
                        {
                            "entity1": ent1.text,
                            "entity2": ent2.text,
                            "type": "proximity",
                            "distance": distance,
                        }
                    )

        return relations

    def _calculate_relevance_score(
        self, doc: Any, entities: list[dict[str, Any]]
    ) -> float:
        """Calculer un score de pertinence basé sur la densité d'entités et mots-clés."""
        if not doc:
            return 0.0

        # Score basé sur la densité d'entités
        entity_density = len(entities) / max(len(doc), 1)

        # Score basé sur les mots-clés (entités importantes)
        important_labels = {"PERSON", "ORG", "MONEY", "DATE", "LOC"}
        important_entities = sum(1 for e in entities if e["label"] in important_labels)
        keyword_score = important_entities / max(len(entities), 1)

        # Score combiné
        relevance = (entity_density * 0.5) + (keyword_score * 0.5)

        return min(relevance, 1.0)

    def _detect_language(self, doc: Any) -> str:
        """Détecter la langue du texte."""
        # SpaCy détecte automatiquement la langue depuis le modèle
        if hasattr(doc, "lang_"):
            return doc.lang_
        return "fr"  # Par défaut

    def _extract_key_phrases(self, doc: Any) -> list[str]:
        """Extraire les phrases clés (phrases avec entités)."""
        key_phrases = []

        for sent in doc.sents:
            # Si la phrase contient des entités, c'est une phrase clé
            if any(ent in sent for ent in doc.ents):
                key_phrases.append(sent.text.strip())

        return key_phrases[:5]  # Limiter à 5 phrases

    async def enrich_batch(self, text_blocks: list[TextBlock]) -> list[TextBlock]:
        """Enrichir plusieurs blocs de texte en parallèle."""
        tasks = [self.enrich(block) for block in text_blocks]
        return await asyncio.gather(*tasks)

    async def process(self, *args: Any, **kwargs: Any) -> Any:
        """Implémentation de la méthode abstraite process."""
        # Si un TextBlock est passé, utiliser enrich
        if args and isinstance(args[0], TextBlock):
            return await self.enrich(args[0])
        # Sinon, passer à enrich_batch si c'est une liste
        if args and isinstance(args[0], list):
            return await self.enrich_batch(args[0])
        raise ValueError("TextEnricher.process() attend un TextBlock ou une liste de TextBlock")

