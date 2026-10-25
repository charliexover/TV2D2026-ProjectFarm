
import os

import pygame

from engine.audio import reproducir_sonido_interaccion
from engine.spritesheet import Spritesheet
from engine.ui import InterfazEstado
from projectFarm.entities import Jugador


class RecycleScene:
    def __init__(self, game_state, inventario, al_salir_casa):
        self.name = "Recycle Scene"
        self.game_state = game_state
        self.interfaz_estado = InterfazEstado()
        self.jugador = Jugador()
        self.primera_entrada = True
        self.primera_visita = True
        self.inicio_animacion_chatarra = None
        self.al_salir_casa = al_salir_casa
        self.tamano_salida = (70, 50)
        self.cuadrados = [
            pygame.Rect(195, 160, 10, 340),
            pygame.Rect(130, 165, 550, 10),
            pygame.Rect(595, 160, 10, 340),
            pygame.Rect(200, 495, 95, 10),
            pygame.Rect(360, 495, 300, 10),
        ]
        self.materiales_entrada = pygame.Rect(310, 330, 44, 44)
        self.materiales_salida = pygame.Rect(490, 330, 44, 44)
        self.cajas = pygame.Rect(200,100,500,200)
        self.cuadrados.extend(
            (self.materiales_entrada, self.materiales_salida, self.cajas)
        )
        self.colores_cuadrados = [
            (255, 120, 120),
            (120, 200, 255),
            (120, 255, 170),
            (255, 210, 120),
            (255, 210, 120),
            (255, 210, 120),
            (180, 210, 255),
            (180, 210, 255),
        ]
        self.fuente = pygame.font.Font(None, 28)
        self.inventario = inventario
        self.fondo = self._cargar_fondo()
        ruta_chatarra = os.path.join(
            os.path.dirname(__file__), "..", "assets", "chatarraSprite.png"
        )
        sprite_chatarra = pygame.image.load(ruta_chatarra).convert_alpha()
        self.sprite_chatarra = pygame.transform.scale(
            sprite_chatarra,
            (sprite_chatarra.get_width() * 3, sprite_chatarra.get_height() * 3),
        )
        
    def _cargar_fondo(self):
        ruta_fondo = os.path.join(
            os.path.dirname(__file__), "..", "assets", "spritesheetInterior2.png"
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

        salida = self.obtener_salida(limites_pantalla)
        if self.jugador.rectangulo.colliderect(salida):
            self.primera_entrada = True
            self.al_salir_casa()
            return

        area_interaccion_materiales = self.materiales_entrada.inflate(40, 40)
        for evento in eventos:
            if evento.type != pygame.KEYDOWN or evento.key != pygame.K_e:
                continue
            if (
                self.jugador.rectangulo.colliderect(area_interaccion_materiales)
                and self.game_state.estado_procesamiento != "procesandose"
                and self.game_state.chatarra > 0
            ):
                reproducir_sonido_interaccion()
                self.game_state.chatarra_en_proceso = min(
                    20, self.game_state.chatarra
                )
                self.game_state.chatarra -= self.game_state.chatarra_en_proceso
                self.game_state.estado_procesamiento = "procesandose"
                self.game_state.dia_inicio_procesamiento = (
                    self.game_state.dia_actual
                )
                self.inicio_animacion_chatarra = pygame.time.get_ticks()
            elif (
                self.jugador.rectangulo.colliderect(
                    self.materiales_salida.inflate(40, 40)
                )
                and self.game_state.estado_procesamiento == "procesandose"
                and self.game_state.dia_actual
                >= self.game_state.dia_inicio_procesamiento + 2
            ):
                reproducir_sonido_interaccion()
                self.game_state.materiales += (
                    self.game_state.chatarra_en_proceso
                )
                self.game_state.chatarra_en_proceso = 0
                self.game_state.estado_procesamiento = "inactivo"
                self.game_state.dia_inicio_procesamiento = None
                self.inicio_animacion_chatarra = None


    def draw(self, pantalla):
        pantalla.fill((0, 0, 0))
        limites_pantalla = pantalla.get_rect()
        if self.fondo is not None:
            pantalla.blit(self.fondo, self.fondo.get_rect(center=limites_pantalla.center))
        else:
            pantalla.fill((99, 60, 58))

        """ for i, cuadrado in enumerate(self.cuadrados):
            pygame.draw.rect(pantalla, self.colores_cuadrados[i], cuadrado)
            pygame.draw.rect(pantalla, (30, 30, 30), cuadrado, 2) """

        self.interfaz_estado.dibujar(
            pantalla,
            self.game_state,
            mostrar_chatarra=True,
            mostrar_procesamiento=True,
            mostrar_materiales=True,
        )

        if (
            self.game_state.estado_procesamiento == "procesandose"
            and self.inicio_animacion_chatarra is not None
        ):
            inicio = (
                self.materiales_entrada.right
                + self.sprite_chatarra.get_width() // 2,
                self.materiales_entrada.centery,
            )
            fin = (
                self.materiales_salida.left
                - self.sprite_chatarra.get_width() // 2,
                self.materiales_salida.centery,
            )
            distancia = fin[0] - inicio[0]
            velocidad = 20
            duracion_recorrido = distancia / velocidad
            duracion_ciclo = duracion_recorrido + 0.4
            tiempo_ciclo = (
                (pygame.time.get_ticks() - self.inicio_animacion_chatarra)
                / 1000
            ) % duracion_ciclo
            if tiempo_ciclo < duracion_recorrido:
                progreso = tiempo_ciclo / duracion_recorrido
                posicion = (
                    round(inicio[0] + distancia * progreso),
                    round(inicio[1] + (fin[1] - inicio[1]) * progreso),
                )
                rect_sprite = self.sprite_chatarra.get_rect(center=posicion)
                pantalla.blit(self.sprite_chatarra, rect_sprite)

        salida = self.obtener_salida(limites_pantalla)
        #pygame.draw.rect(pantalla, (120, 255, 120), salida)
        
        self.jugador.dibujar(pantalla)
        if (
            self.jugador.rectangulo.colliderect(
                self.materiales_entrada.inflate(40, 40)
            )
            and self.game_state.estado_procesamiento != "procesandose"
        ):
            texto_interaccion = (
                "E: procesar hasta 20 de chatarra"
                if self.game_state.chatarra > 0
                else "Necesitas chatarra"
            )
            indicacion = self.fuente.render(
                texto_interaccion, True, (255, 255, 255)
            )
            pantalla.blit(
                indicacion,
                indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)),
            )
        if (
            self.jugador.rectangulo.colliderect(
                self.materiales_salida.inflate(40, 40)
            )
            and self.game_state.estado_procesamiento == "procesandose"
        ):
            dias_procesando = (
                self.game_state.dia_actual
                - self.game_state.dia_inicio_procesamiento
            )
            texto_interaccion = (
                f"E: retirar {self.game_state.chatarra_en_proceso} materiales"
                if dias_procesando >= 2
                else f"Procesando: faltan {2 - dias_procesando} dias"
            )
            indicacion = self.fuente.render(
                texto_interaccion, True, (255, 255, 255)
            )
            pantalla.blit(
                indicacion,
                indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)),
            )
        if self.jugador.rectangulo.colliderect(salida):
            indicacion = self.fuente.render("Salida automatica", True, (255, 255, 255))
            pantalla.blit(indicacion, indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)))