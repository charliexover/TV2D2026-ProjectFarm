from pathlib import Path

import pygame


_sonido_interaccion = None
_sonido_pc = None
_sonido_tomar_chatarra = None
_volumen_efectos = 1.0
_sonidos_efectos = set()


def registrar_sonido_efecto(sonido):
    _sonidos_efectos.add(sonido)
    sonido.set_volume(_volumen_efectos)
    return sonido


def establecer_volumen_efectos(volumen):
    global _volumen_efectos
    _volumen_efectos = max(0.0, min(1.0, volumen))
    for sonido in _sonidos_efectos:
        sonido.set_volume(_volumen_efectos)
    if _sonido_interaccion is not None:
        _sonido_interaccion.set_volume(_volumen_efectos)


def reproducir_sonido_interaccion():
    global _sonido_interaccion
    if _sonido_interaccion is None:
        ruta_sonido = (
            Path(__file__).parent.parent
            / "projectFarm"
            / "sounds"
            / "SoundEffect4.wav"
        )
        _sonido_interaccion = registrar_sonido_efecto(
            pygame.mixer.Sound(str(ruta_sonido))
        )
    _sonido_interaccion.play()


def reproducir_sonido_pc():
    global _sonido_pc
    if _sonido_pc is None:
        ruta_sonido = Path(__file__).parent.parent / "projectFarm" / "sounds" / "pc.wav"
        _sonido_pc = registrar_sonido_efecto(
            pygame.mixer.Sound(str(ruta_sonido))
        )
    _sonido_pc.play()


def reproducir_sonido_tomar_chatarra():
    global _sonido_tomar_chatarra
    if _sonido_tomar_chatarra is None:
        ruta_sonido = (
            Path(__file__).parent.parent
            / "projectFarm"
            / "sounds"
            / "tomarChatarra.wav"
        )
        _sonido_tomar_chatarra = registrar_sonido_efecto(
            pygame.mixer.Sound(str(ruta_sonido))
        )
    _sonido_tomar_chatarra.play()
