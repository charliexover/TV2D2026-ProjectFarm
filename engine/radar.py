from collections.abc import Iterable
import random

import pygame

from projectFarm.localization import LocalizedFont


class Radar:
    ANCHO = 190
    ALTO = 190
    MARGEN_X = 1
    MARGEN_Y = 12
    ZOOM = 3

    COLOR_FONDO = (12, 19, 24, 215)
    COLOR_BORDE = (95, 125, 137, 230)
    COLOR_EDIFICIO = (75, 190, 235)
    COLOR_CHATARRA = (245, 163, 65)
    COLOR_CULTIVO = (255, 220, 70)
    COLOR_COSECHABLE = (105, 220, 115)
    COLOR_JUGADOR = (255, 245, 180)
    COLOR_ANTENA = (205, 125, 245)
    COLOR_GENERADOR = (255, 105, 95)

    def __init__(self):
        self.fuente = LocalizedFont(None, 18)
        self.fuente_titulo = LocalizedFont(None, 22)

    def dibujar(
        self,
        pantalla,
        tamano_mapa,
        posicion_jugador,
        edificios: Iterable[tuple[int, int]],
        chatarra: Iterable[tuple[int, int]],
        cultivos: Iterable[tuple[int, int]],
        cultivos_cosechables: Iterable[tuple[int, int]],
        antenas: Iterable[tuple[int, int]] = (),
        generador: tuple[int, int] | None = None,
        interferencia: bool = False,
    ):
        ancho_mapa, alto_mapa = tamano_mapa
        if ancho_mapa <= 0 or alto_mapa <= 0:
            raise ValueError("El tamaño del mapa debe ser positivo.")

        panel = pygame.Surface((self.ANCHO, self.ALTO), pygame.SRCALPHA)
        rect_panel = panel.get_rect(topleft=(self.MARGEN_X, self.MARGEN_Y))
        pygame.draw.rect(
            panel,
            self.COLOR_FONDO,
            rect_panel,
            border_radius=8,
            border_top_left_radius=0,
            border_top_right_radius=0,
        )
        pygame.draw.rect(
            panel,
            self.COLOR_BORDE,
            rect_panel,
            width=1,
            border_radius=8,
            border_top_left_radius=0,
            border_top_right_radius=0,
        )


        area_mapa = pygame.Rect(10, 30, self.ANCHO - 20, 78)
        pygame.draw.rect(panel, (18, 30, 36, 235), area_mapa)
        pygame.draw.rect(panel, (67, 91, 101), area_mapa, width=1)

        escala = self.ZOOM * min(
            (area_mapa.width - 6) / ancho_mapa,
            (area_mapa.height - 6) / alto_mapa,
        )
        ancho_render = max(1, round(ancho_mapa * escala))
        alto_render = max(1, round(alto_mapa * escala))
        mapa_render = pygame.Rect(
            round(area_mapa.centerx - posicion_jugador[0] * escala),
            round(area_mapa.centery - posicion_jugador[1] * escala),
            ancho_render,
            alto_render,
        )
        clip_anterior = panel.get_clip()
        panel.set_clip(area_mapa)
        for indice in range(1, 4):
            x = area_mapa.left + round(area_mapa.width * indice / 4)
            y = area_mapa.top + round(area_mapa.height * indice / 4)
            pygame.draw.line(
                panel,
                (39, 56, 63),
                (x, area_mapa.top),
                (x, area_mapa.bottom),
            )
            pygame.draw.line(
                panel,
                (39, 56, 63),
                (area_mapa.left, y),
                (area_mapa.right, y),
            )

        for puntos, color, radio in (
            (edificios, self.COLOR_EDIFICIO, 4),
            (chatarra, self.COLOR_CHATARRA, 1),
            (cultivos, self.COLOR_CULTIVO, 1),
            (cultivos_cosechables, self.COLOR_COSECHABLE, 1),
            (antenas, self.COLOR_ANTENA, 2),
            (() if generador is None else (generador,), self.COLOR_GENERADOR, 3),
            ((posicion_jugador,), self.COLOR_JUGADOR, 3),
        ):
            self._dibujar_puntos(
                panel,
                mapa_render,
                (ancho_mapa, alto_mapa),
                puntos,
                color,
                radio,
                parpadeo=interferencia,
            )
        if interferencia:
            self._dibujar_interferencia(panel, area_mapa)
        panel.set_clip(clip_anterior)

        self._dibujar_leyenda(panel)
        pantalla.blit(panel, rect_panel)

    def _dibujar_puntos(
        self,
        superficie,
        area_mapa,
        tamano_mapa,
        puntos,
        color,
        radio,
        parpadeo=False,
    ):
        ancho_mapa, alto_mapa = tamano_mapa
        fase = pygame.time.get_ticks() // 140
        for x, y in puntos:
            if not (0 <= x <= ancho_mapa and 0 <= y <= alto_mapa):
                continue
            if parpadeo and (fase + int(x) * 3 + int(y) * 5) % 4 < 2:
                continue
            posicion = (
                area_mapa.left + round(x * area_mapa.width / ancho_mapa),
                area_mapa.top + round(y * area_mapa.height / alto_mapa),
            )
            pygame.draw.rect(
                superficie,
                color,
                pygame.Rect(0, 0, radio * 2, radio * 2).move(
                    posicion[0] - radio,
                    posicion[1] - radio,
                ),
            )

    def _dibujar_interferencia(self, superficie, area_mapa):
        ahora = pygame.time.get_ticks()
        ruido = random.Random(ahora // 80)
        velo = pygame.Surface(area_mapa.size, pygame.SRCALPHA)
        velo.fill((218, 164, 92, 28))
        superficie.blit(velo, area_mapa.topleft)

        for y in range(area_mapa.top, area_mapa.bottom, 4):
            pygame.draw.line(
                superficie,
                (185, 203, 195, 55),
                (area_mapa.left, y),
                (area_mapa.right - 1, y),
            )

        for _ in range(24):
            x = ruido.randrange(area_mapa.left, area_mapa.right)
            y = ruido.randrange(area_mapa.top, area_mapa.bottom)
            ancho = ruido.randint(1, 5)
            pygame.draw.rect(
                superficie,
                (225, 222, 190, ruido.randint(70, 145)),
                (x, y, ancho, 1),
            )

        franja_y = area_mapa.top + (ahora // 35) % area_mapa.height
        pygame.draw.line(
            superficie,
            (232, 210, 165, 110),
            (area_mapa.left, franja_y),
            (area_mapa.right - 1, franja_y),
            2,
        )

    def _dibujar_leyenda(self, panel):
        elementos = (
            ("Edif.", self.COLOR_EDIFICIO, (8, 113)),
            ("Chatarra", self.COLOR_CHATARRA, (76, 113)),
            ("Cultivo", self.COLOR_CULTIVO, (8, 132)),
            ("Cosechable", self.COLOR_COSECHABLE, (76, 132)),
            ("Antena", self.COLOR_ANTENA, (8, 151)),
            ("Generador", self.COLOR_GENERADOR, (76, 151)),
            ("Jugador", self.COLOR_JUGADOR, (8, 170)),
        )
        for etiqueta, color, (x, y) in elementos:
            pygame.draw.rect(panel, color, (x + 1, y + 3, 6, 6))
            texto = self.fuente.render(etiqueta, True, (220, 230, 230))
            panel.blit(texto, (x + 12, y))