from pathlib import Path

import pygame


_sonido_interaccion = None


def reproducir_sonido_interaccion():
    global _sonido_interaccion
    if _sonido_interaccion is None:
        ruta_sonido = (
            Path(__file__).parent.parent
            / "projectFarm"
            / "assets"
            / "SoundEffect4.wav"
        )
        _sonido_interaccion = pygame.mixer.Sound(str(ruta_sonido))
    _sonido_interaccion.play()
