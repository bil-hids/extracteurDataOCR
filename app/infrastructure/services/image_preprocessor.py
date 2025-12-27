"""Preprocessing avancé d'images pour améliorer la qualité OCR."""

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class ImagePreprocessor:
    """Preprocessing avancé d'images pour optimiser l'OCR."""

    def __init__(self) -> None:
        """Initialiser le preprocesseur."""
        self.logger = logger

    def preprocess(
        self,
        image: Image.Image,
        method: str = "advanced",
        target_dpi: int = 300,
    ) -> Image.Image:
        """
        Préprocesser une image pour améliorer l'OCR.

        Args:
            image: Image PIL à préprocesser
            method: Méthode de preprocessing ('basic', 'advanced', 'aggressive')
            target_dpi: DPI cible pour l'upscaling (défaut: 300)

        Returns:
            Image préprocessée
        """
        if method == "basic":
            return self._preprocess_basic(image)
        elif method == "advanced":
            return self._preprocess_advanced(image, target_dpi)
        elif method == "aggressive":
            return self._preprocess_aggressive(image, target_dpi)
        else:
            return self._preprocess_advanced(image, target_dpi)

    def _preprocess_basic(self, image: Image.Image) -> Image.Image:
        """Preprocessing basique (méthode actuelle)."""
        # Convertir en niveaux de gris
        if image.mode != "L":
            image = image.convert("L")

        # Améliorer le contraste
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)

        # Améliorer la netteté
        image = image.filter(ImageFilter.SHARPEN)

        # Réduire le bruit
        image = image.filter(ImageFilter.MedianFilter(size=3))

        return image

    def _preprocess_advanced(
        self, image: Image.Image, target_dpi: int = 300
    ) -> Image.Image:
        """Preprocessing avancé avec plusieurs améliorations."""
        # 1. Upscaling si nécessaire
        image = self._upscale_if_needed(image, target_dpi)

        # 2. Convertir en niveaux de gris de manière optimale
        if image.mode != "L":
            # Convertir RGB/RGBA en niveaux de gris avec pondération
            image = image.convert("L")

        # 3. Correction de rotation (détection automatique)
        image = self._correct_rotation(image)

        # 4. Amélioration du contraste adaptatif
        image = self._enhance_contrast_adaptive(image)

        # 5. Binarisation adaptative
        image = self._adaptive_binarization(image)

        # 6. Débruitage avancé
        image = self._advanced_denoising(image)

        # 7. Amélioration finale de la netteté
        image = image.filter(ImageFilter.SHARPEN)

        return image

    def _preprocess_aggressive(
        self, image: Image.Image, target_dpi: int = 300
    ) -> Image.Image:
        """Preprocessing agressif pour images de mauvaise qualité."""
        # Upscaling plus agressif
        image = self._upscale_if_needed(image, target_dpi * 2)

        # Convertir en niveaux de gris
        if image.mode != "L":
            image = image.convert("L")

        # Correction de rotation
        image = self._correct_rotation(image)

        # Amélioration du contraste très agressive
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(3.0)

        # Binarisation Otsu
        image = self._otsu_binarization(image)

        # Débruitage morphologique
        image = self._morphological_denoising(image)

        # Amélioration de la netteté
        image = image.filter(ImageFilter.SHARPEN)
        image = image.filter(ImageFilter.EDGE_ENHANCE)

        return image

    def _upscale_if_needed(self, image: Image.Image, target_dpi: int) -> Image.Image:
        """
        Upscaler l'image si sa résolution est inférieure à target_dpi.

        Args:
            image: Image à upscaler
            target_dpi: DPI cible

        Returns:
            Image upscalée si nécessaire
        """
        # Estimation de la résolution actuelle (approximative)
        # On suppose que l'image fait environ 8.5x11 pouces si c'est un document
        width, height = image.size
        estimated_dpi = max(width, height) / 11.0  # Approximation

        if estimated_dpi < target_dpi:
            scale_factor = target_dpi / estimated_dpi
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)

            # Utiliser Lanczos pour un upscaling de qualité
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.logger.debug(
                f"Image upscalée de {width}x{height} à {new_width}x{new_height} "
                f"(facteur: {scale_factor:.2f})"
            )

        return image

    def _correct_rotation(self, image: Image.Image) -> Image.Image:
        """
        Détecter et corriger la rotation de l'image.

        Args:
            image: Image à corriger

        Returns:
            Image corrigée
        """
        # Pour l'instant, on utilise auto_rotate de PIL
        # Une implémentation plus avancée pourrait utiliser Hough Transform
        try:
            # Tenter la correction automatique
            image = ImageOps.exif_transpose(image)
        except Exception:
            pass

        return image

    def _enhance_contrast_adaptive(self, image: Image.Image) -> Image.Image:
        """
        Améliorer le contraste de manière adaptative selon l'histogramme.

        Args:
            image: Image à améliorer

        Returns:
            Image avec contraste amélioré
        """
        # Convertir en numpy pour analyse
        img_array = np.array(image)

        # Calculer l'histogramme
        hist, _ = np.histogram(img_array.flatten(), 256, [0, 256])

        # Calculer le contraste actuel (écart-type)
        contrast = np.std(img_array)

        # Si le contraste est faible, l'améliorer
        if contrast < 30:
            enhancer = ImageEnhance.Contrast(image)
            # Ajuster le facteur selon le contraste
            factor = min(2.5, 30.0 / max(contrast, 1.0))
            image = enhancer.enhance(factor)
            self.logger.debug(f"Contraste amélioré (facteur: {factor:.2f})")

        return image

    def _adaptive_binarization(self, image: Image.Image) -> Image.Image:
        """
        Binarisation adaptative pour améliorer le contraste texte/fond.

        Args:
            image: Image en niveaux de gris

        Returns:
            Image binarisée
        """
        try:
            # Convertir en numpy
            img_array = np.array(image)

            # Méthode adaptative : utiliser un seuil adaptatif par région
            # Pour simplifier, on utilise Otsu global
            from skimage.filters import threshold_otsu
            from skimage import img_as_ubyte

            threshold = threshold_otsu(img_array)
            binary = img_array > threshold
            binary_img = img_as_ubyte(binary)

            # Convertir back en PIL Image
            return Image.fromarray(binary_img, mode="L")
        except ImportError:
            # Si scikit-image n'est pas disponible, utiliser une méthode simple
            self.logger.debug("scikit-image non disponible, utilisation de binarisation simple")
            return self._simple_binarization(image)
        except Exception as e:
            self.logger.warning(f"Erreur lors de la binarisation adaptative: {e}")
            return self._simple_binarization(image)

    def _otsu_binarization(self, image: Image.Image) -> Image.Image:
        """
        Binarisation Otsu pour images de mauvaise qualité.

        Args:
            image: Image en niveaux de gris

        Returns:
            Image binarisée
        """
        try:
            from skimage.filters import threshold_otsu
            from skimage import img_as_ubyte

            img_array = np.array(image)
            threshold = threshold_otsu(img_array)
            binary = img_array > threshold
            binary_img = img_as_ubyte(binary)

            return Image.fromarray(binary_img, mode="L")
        except ImportError:
            return self._simple_binarization(image)
        except Exception as e:
            self.logger.warning(f"Erreur lors de la binarisation Otsu: {e}")
            return self._simple_binarization(image)

    def _simple_binarization(self, image: Image.Image) -> Image.Image:
        """
        Binarisation simple avec seuil fixe.

        Args:
            image: Image en niveaux de gris

        Returns:
            Image binarisée
        """
        # Convertir en numpy
        img_array = np.array(image)

        # Seuil adaptatif basé sur la médiane
        threshold = np.median(img_array)

        # Binariser
        binary = img_array > threshold
        binary_img = (binary * 255).astype(np.uint8)

        return Image.fromarray(binary_img, mode="L")

    def _advanced_denoising(self, image: Image.Image) -> Image.Image:
        """
        Débruitage avancé avec filtres morphologiques.

        Args:
            image: Image à débruitée

        Returns:
            Image débruitée
        """
        # Appliquer un filtre médian pour réduire le bruit
        image = image.filter(ImageFilter.MedianFilter(size=3))

        # Appliquer un léger flou gaussien pour lisser
        # Note: PIL n'a pas de filtre gaussien direct, on utilise BoxBlur
        image = image.filter(ImageFilter.BoxBlur(radius=0.5))

        return image

    def _morphological_denoising(self, image: Image.Image) -> Image.Image:
        """
        Débruitage morphologique pour images très bruitées.

        Args:
            image: Image à débruitée

        Returns:
            Image débruitée
        """
        try:
            from skimage.morphology import opening, closing
            from skimage import img_as_ubyte

            img_array = np.array(image)

            # Opening pour supprimer le bruit blanc
            opened = opening(img_array > 128)

            # Closing pour remplir les trous
            closed = closing(opened)

            result = img_as_ubyte(closed)

            return Image.fromarray(result, mode="L")
        except ImportError:
            # Fallback sur méthode simple
            return self._advanced_denoising(image)
        except Exception as e:
            self.logger.warning(f"Erreur lors du débruitage morphologique: {e}")
            return self._advanced_denoising(image)

