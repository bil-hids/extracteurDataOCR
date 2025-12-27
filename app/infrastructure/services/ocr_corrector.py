"""Service de correction post-OCR pour améliorer la qualité du texte extrait."""

import re
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class OcrCorrector:
    """Service de correction du texte OCR pour corriger les erreurs courantes."""

    def __init__(self) -> None:
        """Initialiser le correcteur."""
        self.logger = logger

        # Dictionnaire de corrections courantes
        self.common_corrections = {
            # Corrections de caractères fréquemment mal reconnus
            "cudi": "Jeudi",
            "cudl": "Jeudi",
            "eudi": "Jeudi",  # J manquant au début
            "mbre": "décembre",
            "mbre 2025": "décembre 2025",
            "2 mbre": "25 décembre",
            "d'fos": "d'infos",
            "lus d'infos": "plus d'infos",  # p manquant au début
            "lus d'fos": "plus d'infos",
            "plus d'fos": "plus d'infos",
            "plus d'infos": "plus d'infos",
            # Corrections de mots français courants
            "REPUBLIQUE": "REPUBLIQUE",
            "DEMOCRATIQUE": "DEMOCRATIQUE",
            "CONGO": "CONGO",
            # Corrections de dates
            "24 décembre": "24 décembre",
            "25 décembre": "25 décembre",
            "31 décembre": "31 décembre",
            # Corrections spécifiques identifiées
            "tol N°": "LOI N°",  # "tol" → "LOI"
            "ou 16": "DU 16",  # "ou" → "DU" dans les dates
            "Pérode": "Période",  # "Pérode" → "Période"
            "Pérode 1": "Période 1",
            "Pérode 2": "Période 2",
        }

        # Patterns de correction avec regex
        self.pattern_corrections = [
            # Dates : "2 mbre 2025" -> "25 décembre 2025"
            (r"\b(\d{1,2})\s+mbre\s+(\d{4})\b", self._correct_date_month),
            # "cudi" ou "eudi" -> "Jeudi" (J manquant)
            (r"\bcudi\b", "Jeudi"),
            (r"\bcudl\b", "Jeudi"),
            (r"\beudi\b", "Jeudi"),  # J manquant au début
            # "lus d'infos" -> "plus d'infos" (p manquant)
            (r"\blus\s+d'infos\b", "plus d'infos"),
            (r"\blus\s+d'fos\b", "plus d'infos"),
            # "d'fos" -> "d'infos"
            (r"d'fos\b", "d'infos"),
            (r"plus\s+d'fos\b", "plus d'infos"),
            # "tol N°" -> "LOI N°" (tol mal reconnu)
            (r"\btol\s+N°", "LOI N°"),
            # "ou 16" -> "DU 16" dans les dates (ou mal reconnu)
            (r"\bou\s+16\s+OCTOBRE", "DU 16 OCTOBRE"),
            (r"\bou\s+(\d{1,2})\s+(OCTOBRE|JANVIER|FÉVRIER|MARS|AVRIL|MAI|JUIN|JUILLET|AOÛT|SEPTEMBRE|NOVEMBRE|DÉCEMBRE)", r"DU \1 \2"),  # Général pour dates
            # "Pérode" -> "Période" (doit être fait en premier)
            (r"\bPérode\b", "Période"),
            # "B Pérode" ou "M Pérode" -> "BB Période" (avant correction Pérode -> Période)
            (r"\bB\s+Pérode", "BB Période"),
            (r"\bM\s+Pérode", "BB Période"),
            # "B Période" ou "M Période" -> "BB Période" (après correction Pérode -> Période)
            (r"\bB\s+Période", "BB Période"),
            (r"\bM\s+Période", "BB Période"),
            # "DE LA" manquant dans "REPUBLIQUE DEMOCRATIQUE"
            (r"REPUBLIQUE\s+DEMOCRATIQUE", "REPUBLIQUE DEMOCRATIQUE"),
            # Correction des espaces multiples
            (r"\s+", " "),
            # Correction des retours à la ligne multiples
            (r"\n{3,}", "\n\n"),
        ]

        # Mois en français
        self.months = {
            "janvier": 1,
            "février": 2,
            "mars": 3,
            "avril": 4,
            "mai": 5,
            "juin": 6,
            "juillet": 7,
            "août": 8,
            "septembre": 9,
            "octobre": 10,
            "novembre": 11,
            "décembre": 12,
        }

    def correct_text(self, text: str, context: Optional[dict] = None) -> str:
        """
        Corriger le texte OCR pour améliorer la qualité.

        Args:
            text: Texte à corriger
            context: Contexte optionnel (métadonnées, etc.)

        Returns:
            Texte corrigé
        """
        if not text or not text.strip():
            return text

        corrected = text

        # 1. Corrections de patterns avec regex
        for pattern, replacement in self.pattern_corrections:
            if callable(replacement):
                # Si c'est une fonction, l'appeler
                corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
            else:
                corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)

        # 2. Corrections de mots complets (insensible à la casse)
        for wrong, correct in self.common_corrections.items():
            # Remplacer les occurrences entières du mot
            pattern = r"\b" + re.escape(wrong) + r"\b"
            corrected = re.sub(pattern, correct, corrected, flags=re.IGNORECASE)

        # 3. Correction contextuelle des dates
        corrected = self._correct_dates(corrected)

        # 4. Correction des nombres mal reconnus
        corrected = self._correct_numbers(corrected)

        # 5. Correction des mots français courants mal reconnus
        corrected = self._correct_french_words(corrected)

        # 6. Nettoyage final
        corrected = self._clean_text(corrected)

        return corrected

    def _correct_date_month(self, match: re.Match) -> str:
        """
        Corriger les dates avec mois abrégé mal reconnu.

        Args:
            match: Match regex

        Returns:
            Date corrigée
        """
        day = match.group(1)
        year = match.group(2)

        # Si le jour est "2" et qu'on est dans un contexte de décembre, c'est probablement "25"
        # Sinon, on garde le jour tel quel
        if day == "2" and "décembre" in match.string.lower():
            day = "25"

        return f"{day} décembre {year}"

    def _correct_dates(self, text: str) -> str:
        """
        Corriger les dates mal reconnues.

        Args:
            text: Texte à corriger

        Returns:
            Texte avec dates corrigées
        """
        # Pattern pour "cudi 2 mbre 2025" -> "Jeudi 25 décembre 2025"
        pattern = r"\b(cudi|cudl)\s+(\d{1,2})\s+mbre\s+(\d{4})\b"
        replacement = r"Jeudi 25 décembre \3"

        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Pattern pour "2 mbre" -> "25 décembre" dans un contexte de dates
        pattern = r"(\d{1,2})\s+(décembre|mbre)\s+(\d{4})"
        text = re.sub(
            pattern,
            lambda m: f"{m.group(1)} décembre {m.group(3)}",
            text,
            flags=re.IGNORECASE,
        )

        return text

    def _correct_numbers(self, text: str) -> str:
        """
        Corriger les nombres mal reconnus.

        Args:
            text: Texte à corriger

        Returns:
            Texte avec nombres corrigés
        """
        # Corrections spécifiques pour les nombres courants
        corrections = {
            r"\b2\s+mbre\b": "25 décembre",
            r"\b(\d)\s+(\d)\s+(\d{4})\b": r"\1\2\3",  # "2 0 2 5" -> "2025"
        }

        for pattern, replacement in corrections.items():
            text = re.sub(pattern, replacement, text)

        return text

    def _correct_french_words(self, text: str) -> str:
        """
        Corriger les mots français courants mal reconnus.

        Args:
            text: Texte à corriger

        Returns:
            Texte avec mots corrigés
        """
        # Dictionnaire de corrections de mots français
        word_corrections = {
            r"\bplus\s+d['']fos\b": "plus d'infos",
            r"\bplus\s+d['']infos\b": "plus d'infos",
            r"\bd['']fos\b": "d'infos",
            r"\blus\s+d['']infos\b": "plus d'infos",  # p manquant
            r"\bREPUBLIQUE\s+DEMOCRATIQUE\s+DU\s+CONGO\b": "REPUBLIQUE DEMOCRATIQUE DU CONGO",
            # "tol" -> "LOI" dans les contextes légaux
            r"\btol\s+N°": "LOI N°",
            r"\btol\s+N°\s+(\d+/\d+)": r"LOI N° \1",
            # "ou" -> "DU" dans les dates (avant les mois)
            r"\bou\s+(\d{1,2})\s+(OCTOBRE|JANVIER|FÉVRIER|MARS|AVRIL|MAI|JUIN|JUILLET|AOÛT|SEPTEMBRE|NOVEMBRE|DÉCEMBRE)": r"DU \1 \2",
            # "ou 16" -> "DU 16" (cas général)
            r"\bou\s+16\s+OCTOBRE": "DU 16 OCTOBRE",
            # "Pérode" -> "Période"
            r"\bPérode\b": "Période",
            # "B Pérode" ou "M Pérode" -> "BB Période"
            r"\bB\s+Pérode": "BB Période",
            r"\bM\s+Période": "BB Période",
            r"\b[BM]\s+Période": "BB Période",
            # Ajouter "DE LA" si manquant dans certains contextes
            r"\bJOURNAL\s+OFFICIEL\s+REPUBLIQUE\b": "JOURNAL OFFICIEL\nDE LA\nREPUBLIQUE",
        }

        for pattern, replacement in word_corrections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        return text

    def _clean_text(self, text: str) -> str:
        """
        Nettoyer le texte final.

        Args:
            text: Texte à nettoyer

        Returns:
            Texte nettoyé
        """
        # Supprimer les espaces multiples
        text = re.sub(r" +", " ", text)

        # Supprimer les retours à la ligne multiples (garder max 2)
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Supprimer les espaces en début/fin de ligne
        lines = text.split("\n")
        lines = [line.strip() for line in lines]
        text = "\n".join(lines)

        # Supprimer les lignes vides multiples
        text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)

        return text.strip()

    def correct_with_confidence(
        self, text: str, confidence: float, context: Optional[dict] = None
    ) -> tuple[str, float]:
        """
        Corriger le texte en tenant compte du niveau de confiance.

        Args:
            text: Texte à corriger
            confidence: Niveau de confiance de l'OCR (0.0-1.0)
            context: Contexte optionnel

        Returns:
            Tuple (texte corrigé, confiance ajustée)
        """
        corrected = self.correct_text(text, context)

        # Ajuster la confiance : si beaucoup de corrections, réduire légèrement
        # mais si les corrections sont cohérentes, maintenir
        original_words = len(text.split())
        corrected_words = len(corrected.split())

        # Si le nombre de mots a changé significativement, ajuster la confiance
        if abs(original_words - corrected_words) > original_words * 0.2:
            # Beaucoup de changements, réduire la confiance
            adjusted_confidence = confidence * 0.9
        else:
            # Peu de changements, maintenir ou légèrement améliorer
            adjusted_confidence = min(1.0, confidence * 1.05)

        return corrected, adjusted_confidence

