
import pygame


_posicion_mouse = (-1, -1)


def actualizar_posicion_mouse(posicion):
    global _posicion_mouse
    _posicion_mouse = posicion


def obtener_posicion_mouse():
    return _posicion_mouse
