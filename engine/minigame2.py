import random
from itertools import combinations

import pygame

from engine.audio import reproducir_sonido_pc


class Minijuego2:
    CANTIDAD_LUCES = 6

    def __init__(self):
        self.activo = False
        self.completado = False
        self.luces = [True] * self.CANTIDAD_LUCES
        self.rectangulos_luces = []
        self.fuente_titulo = pygame.font.Font(None, 42)
        self.fuente = pygame.font.Font(None, 26)
        self.mensaje = ""

    def iniciar(self):
        self.luces = [True] * self.CANTIDAD_LUCES
        while (
            all(self.luces)
            or not any(self.luces)
            or self._cantidad_minima_movimientos() < 2
        ):
            self.luces = [True] * self.CANTIDAD_LUCES
            for _ in range(random.randint(4, 8)):
                self._cambiar_luces(random.randrange(self.CANTIDAD_LUCES))

        self.activo = True
        self.completado = False
        self.mensaje = "Enciende las seis luces verdes."

    def _cambiar_luces(self, indice):
        for indice_afectado in (indice - 1, indice, indice + 1):
            if 0 <= indice_afectado < self.CANTIDAD_LUCES:
                self.luces[indice_afectado] = not self.luces[indice_afectado]

    def _cantidad_minima_movimientos(self):
        for cantidad in range(1, self.CANTIDAD_LUCES + 1):
            for seleccion in combinations(
                range(self.CANTIDAD_LUCES), cantidad
            ):
                luces = self.luces.copy()
                for indice in seleccion:
                    for indice_afectado in (
                        indice - 1,
                        indice,
                        indice + 1,
                    ):
                        if 0 <= indice_afectado < self.CANTIDAD_LUCES:
                            luces[indice_afectado] = not luces[
                                indice_afectado
                            ]
                if all(luces):
                    return cantidad
        return self.CANTIDAD_LUCES + 1

    def actualizar(self, eventos, limites_pantalla):
        if not self.activo:
            return self.completado

        self.rectangulos_luces = self._obtener_rectangulos_luces(
            limites_pantalla
        )
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                self.activo = False
                self.mensaje = "Minijuego cerrado."
                return False
            if (
                evento.type != pygame.MOUSEBUTTONDOWN
                or evento.button != 1
            ):
                continue

            for indice, rectangulo in enumerate(self.rectangulos_luces):
                if not rectangulo.collidepoint(evento.pos):
                    continue

                reproducir_sonido_pc()
                self._cambiar_luces(indice)
                if all(self.luces):
                    self.completado = True
                    self.activo = False
                    self.mensaje = "Todas las luces estan encendidas."
                    return True
                break

        return False

    def _obtener_rectangulos_luces(self, limites_pantalla):
        ancho_tarjeta = min(720, max(280, limites_pantalla.width - 32))
        tarjeta = pygame.Rect(0, 0, ancho_tarjeta, 300)
        tarjeta.center = limites_pantalla.center
        separacion = 12
        tamano = min(
            72,
            max(28, (tarjeta.width - 64 - separacion * 4) // self.CANTIDAD_LUCES),
        )
        ancho_total = self.CANTIDAD_LUCES * tamano + (
            self.CANTIDAD_LUCES - 1
        ) * separacion
        inicio_x = tarjeta.centerx - ancho_total // 2
        y = tarjeta.top + 118
        return [
            pygame.Rect(
                inicio_x + indice * (tamano + separacion),
                y,
                tamano,
                tamano,
            )
            for indice in range(self.CANTIDAD_LUCES)
        ]

    def dibujar(self, pantalla):
        limites = pantalla.get_rect()
        ancho_tarjeta = min(720, max(280, limites.width - 32))
        tarjeta = pygame.Rect(0, 0, ancho_tarjeta, 300)
        tarjeta.center = limites.center
        pygame.draw.rect(pantalla, (25, 30, 38), tarjeta)
        pygame.draw.rect(pantalla, (230, 235, 235), tarjeta, 2)

        titulo = self.fuente_titulo.render(
            "Reparacion de la linea", True, (255, 255, 255)
        )
        pantalla.blit(
            titulo,
            titulo.get_rect(midtop=(tarjeta.centerx, tarjeta.top + 20)),
        )
        texto = self.fuente.render(self.mensaje, True, (225, 225, 225))
        pantalla.blit(
            texto,
            texto.get_rect(center=(tarjeta.centerx, tarjeta.top + 82)),
        )

        rectangulos = self._obtener_rectangulos_luces(limites)
        self.rectangulos_luces = rectangulos
        for indice, rectangulo in enumerate(rectangulos):
            color = (45, 205, 95) if self.luces[indice] else (70, 75, 82)
            pygame.draw.rect(pantalla, color, rectangulo)

        ayuda = pygame.font.Font(None, 22).render(
            "Clic para cambiar luces | Esc: salir", True, (190, 195, 200)
        )
        pantalla.blit(
            ayuda,
            ayuda.get_rect(midbottom=(tarjeta.centerx, tarjeta.bottom - 12)),
        )