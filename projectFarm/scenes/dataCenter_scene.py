
import os
import random

import pygame

from engine.audio import reproducir_sonido_interaccion
from engine.spritesheet import Spritesheet
from engine.ui import InterfazEstado
from projectFarm.entities import Jugador


class DataCenterScene:
    def __init__(self, game_state, inventario, al_salir_casa):
        self.name = "Data Center Scene"
        self.game_state = game_state
        self.interfaz_estado = InterfazEstado()
        self.jugador = Jugador()
        self.primera_entrada = True
        self.primera_visita = True
        self.al_salir_casa = al_salir_casa
        self.tamano_salida = (70, 50)
        self.cuadrados = [
            pygame.Rect(195, 160, 10, 340),
            pygame.Rect(130, 165, 550, 10),
            pygame.Rect(595, 160, 10, 340),
            pygame.Rect(200, 495, 95, 10),
            pygame.Rect(360, 495, 300, 10),
        ]
        self.server1 = pygame.Rect(210, 170, 90, 210)
        self.pc = pygame.Rect(360, 170, 80, 50)
        self.server2 = pygame.Rect(495, 170, 90, 210)
        self.cuadrados.extend((self.server1, self.server2, self.pc))
        self.colores_cuadrados = [
            (255, 120, 120),
            (120, 200, 255),
            (120, 255, 170),
            (255, 210, 120),
            (255, 210, 120),
            (120, 255, 170),
            (255, 210, 120),
            (255, 210, 120),
        ]
        self.fuente = pygame.font.Font(None, 28)
        self.inventario = inventario
        self.fondo = self._cargar_fondo()
        self.mensaje_antena = None

    def interactuar_pc(self):
        if self.game_state.dia_mision_antena != self.game_state.dia_actual:
            self.game_state.dia_mision_antena = self.game_state.dia_actual
            self.game_state.antena_objetivo = random.choice(
                ("CH4", "BG5", "RM2", "TS7")
            )
            self.game_state.antena_encontrada = False
            self.game_state.datos_antena_enviados = False

        if self.game_state.datos_antena_enviados:
            self.mensaje_antena = "Los datos de hoy ya fueron enviados."
        elif self.game_state.antena_encontrada:
            self.game_state.creditos += 25
            self.game_state.datos_antena_enviados = True
            self.mensaje_antena = "Datos enviados. +25 creditos."
        else:
            self.mensaje_antena = (
                f"Datos pendientes en Antena: {self.game_state.antena_objetivo}. "
                "Descarga los datos y vuelve a esta PC."
            )
        
    def _envolver_texto_mensaje(self, texto, ancho_maximo):
        lineas = []
        linea = ""
        for palabra in texto.split():
            candidata = f"{linea} {palabra}".strip()
            if linea and self.fuente.size(candidata)[0] > ancho_maximo:
                lineas.append(linea)
                linea = palabra
            else:
                linea = candidata
        if linea:
            lineas.append(linea)
        return lineas

    def _cargar_fondo(self):
        ruta_fondo = os.path.join(
            os.path.dirname(__file__), "..", "assets", "spritesheetInterior3.png"
        )
        try:
            fondo = pygame.image.load(ruta_fondo).convert()
            return pygame.transform.scale(
                fondo,
                (fondo.get_width() * 3, fondo.get_height() * 3),
            )
        except (FileNotFoundError, pygame.error):
            return None

    
    def obtener_salida(self, limites_pantalla):
        salida = pygame.Rect(0, 0, *self.tamano_salida)
        salida.center = (330, 520)
        return salida

    def obtener_posicion_entrada(self, limites_pantalla):
        salida = self.obtener_salida(limites_pantalla)
        posicion = self.jugador.rectangulo.copy()
        posicion.midbottom = (salida.centerx, salida.top - 8)
        return posicion



    def update(self, teclas, limites_pantalla, eventos=()):
        if self.primera_entrada:
            self.jugador.rectangulo = self.obtener_posicion_entrada(
                limites_pantalla
            )
            self.primera_visita = False
            self.primera_entrada = False

        rect_previo = self.jugador.rectangulo.copy()
        self.jugador.actualizar(teclas)
        self.jugador.rectangulo.clamp_ip(limites_pantalla)
        for cuadrado in self.cuadrados:
            if self.jugador.rectangulo.colliderect(cuadrado):
                self.jugador.rectangulo = rect_previo
                break

        if self.jugador.rectangulo.topleft != rect_previo.topleft:
            self.mensaje_antena = None

        salida = self.obtener_salida(limites_pantalla)
        if self.jugador.rectangulo.colliderect(salida):
            self.primera_entrada = True
            self.al_salir_casa()
            return

        for evento in eventos:
            if (
                evento.type == pygame.KEYDOWN
                and evento.key == pygame.K_e
                and self.jugador.rectangulo.colliderect(self.pc.inflate(40, 40))
            ):
                reproducir_sonido_interaccion()
                self.interactuar_pc()

    def draw(self, pantalla):
        pantalla.fill((0, 0, 0))
        limites_pantalla = pantalla.get_rect()
        if self.fondo is not None:
            pantalla.blit(
                self.fondo, self.fondo.get_rect(center=limites_pantalla.center)
            )
        else:
            pantalla.fill((99, 60, 58))

        self.interfaz_estado.dibujar(
            pantalla,
            self.game_state,
            mostrar_chatarra=True,
            mostrar_procesamiento=True,
            mostrar_materiales=True,
        )

        salida = self.obtener_salida(limites_pantalla)
        self.jugador.dibujar(pantalla)
        if self.jugador.rectangulo.colliderect(salida):
            indicacion = self.fuente.render(
                "Salida automatica", True, (255, 255, 255)
            )
            pantalla.blit(
                indicacion,
                indicacion.get_rect(
                    midtop=(pantalla.get_width() // 2, 20)
                ),
            )
        elif self.jugador.rectangulo.colliderect(self.pc.inflate(40, 40)):
            indicacion = self.fuente.render(
                "E: consultar PC", True, (255, 255, 255)
            )
            pantalla.blit(
                indicacion,
                indicacion.get_rect(
                    midtop=(pantalla.get_width() // 2, 20)
                ),
            )

        if self.mensaje_antena is not None:
            lineas = self._envolver_texto_mensaje(
                self.mensaje_antena, limites_pantalla.width - 240
            )
            alto = max(80, len(lineas) * self.fuente.get_linesize() + 24)
            cuadro_mensaje = pygame.Rect(
                100, limites_pantalla.height - 80 - alto,
                limites_pantalla.width - 200, alto,
            )
            pygame.draw.rect(pantalla, (0, 0, 0), cuadro_mensaje)
            pygame.draw.rect(pantalla, (255, 255, 255), cuadro_mensaje, 2)
            for indice, linea in enumerate(lineas):
                mensaje = self.fuente.render(linea, True, (255, 255, 255))
                pantalla.blit(
                    mensaje,
                    (
                        cuadro_mensaje.left + 20,
                        cuadro_mensaje.top + 12
                        + indice * self.fuente.get_linesize(),
                    ),
                )