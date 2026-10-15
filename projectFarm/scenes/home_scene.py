
import json
import os

import pygame

from engine.spritesheet import Spritesheet
from projectFarm.entities import Jugador


class HomeScene:
    def __init__(self, game_state, inventario, al_salir_casa, al_avanzar_dia):
        self.name = "Home Scene"
        self.game_state = game_state
        self.jugador = Jugador()
        self.primera_entrada = True
        self.primera_visita = True
        self.al_salir_casa = al_salir_casa
        self.al_avanzar_dia = al_avanzar_dia
        self.tamano_cama = (96, 48)
        self.tamano_salida = (70, 50)
        self.tamano_pc = (50, 70)
        self.cuadrados = [
            pygame.Rect(195, 160, 10, 340),
            pygame.Rect(130, 165, 550, 10),
            pygame.Rect(595, 160, 10, 340),
            pygame.Rect(200, 495, 95, 10),
            pygame.Rect(360, 495, 300, 10),
        ]
        self.colores_cuadrados = [(255, 120, 120), (120, 200, 255), (120, 255, 170), (255, 210, 120), (255, 210, 120)]
        self.fuente = pygame.font.Font(None, 28)
        self.inventario = inventario
        self.fondo = self._cargar_fondo()
        
    def _cargar_fondo(self):
        ruta_fondo = os.path.join(
            os.path.dirname(__file__), "..", "assets", "spritesheetInterior1.png"
        )
        try:
            fondo = pygame.image.load(ruta_fondo).convert()
            return pygame.transform.scale(
                fondo,
                (fondo.get_width() * 3, fondo.get_height() * 3),
            )
        except (FileNotFoundError, pygame.error):
            return None

    def obtener_cama(self, limites_pantalla):
        cama = pygame.Rect(0, 0, self.tamano_cama[0], self.tamano_cama[1])
        cama.center = (545,230)
        return cama

    def obtener_area_interaccion_cama(self, limites_pantalla):
        return self.obtener_cama(limites_pantalla).inflate(20, 20)

    def obtener_salida(self, limites_pantalla):
        salida = pygame.Rect(0, 0, *self.tamano_salida)
        salida.center = (330, 520)
        return salida

    def obtener_posicion_entrada(self, limites_pantalla):
        salida = self.obtener_salida(limites_pantalla)
        posicion = self.jugador.rectangulo.copy()
        posicion.midbottom = (salida.centerx, salida.top - 8)
        return posicion

    def obtener_pc(self, limites_pantalla):
        pc = pygame.Rect(0, 0, *self.tamano_pc)
        pc.center = (425, 150)
        return pc

    def vender_zanahorias(self):
        zanahorias = self.game_state.zanahorias_cosechadas
        self.game_state.creditos += zanahorias * 2
        self.game_state.zanahorias_cosechadas = 0

    def update(self, teclas, limites_pantalla, eventos=()):
        if self.primera_entrada:
            if self.primera_visita:
                self.jugador.rectangulo.center = (
                    limites_pantalla.centerx,
                    limites_pantalla.centery + 30,
                )
                self.primera_visita = False
            else:
                self.jugador.rectangulo = self.obtener_posicion_entrada(
                    limites_pantalla
                )
            self.primera_entrada = False
        rect_previo = self.jugador.rectangulo.copy()
        self.jugador.actualizar(teclas)
        self.jugador.rectangulo.clamp_ip(limites_pantalla)
        cama = self.obtener_cama(limites_pantalla)
        for cuadrado in [*self.cuadrados, cama]:
            if self.jugador.rectangulo.colliderect(cuadrado):
                self.jugador.rectangulo = rect_previo
                break
        salida = self.obtener_salida(limites_pantalla)
        if self.jugador.rectangulo.colliderect(salida):
            self.primera_entrada = True
            self.al_salir_casa()
            return
        area_interaccion_cama = self.obtener_area_interaccion_cama(
            limites_pantalla
        )
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_e:
                if self.jugador.rectangulo.colliderect(area_interaccion_cama):
                    self.al_avanzar_dia()
                elif self.jugador.rectangulo.colliderect(
                    self.obtener_pc(limites_pantalla)
                ):
                    self.vender_zanahorias()

    def draw(self, pantalla):
        pantalla.fill((0, 0, 0))
        limites_pantalla = pantalla.get_rect()
        if self.fondo is not None:
            pantalla.blit(self.fondo, self.fondo.get_rect(center=limites_pantalla.center))
        else:
            pantalla.fill((99, 60, 58))

        #for i, cuadrado in enumerate(self.cuadrados):
            #pygame.draw.rect(pantalla, self.colores_cuadrados[i], cuadrado)
            #pygame.draw.rect(pantalla, (30, 30, 30), cuadrado, 2)

        texto_dia = self.fuente.render(f"Dia = {self.game_state.dia_actual}", True, (255, 255, 255))
        pantalla.blit(texto_dia, (10, 10))
        texto_zanahorias = self.fuente.render(f"Zanahorias cosechadas = {self.game_state.zanahorias_cosechadas}", True, (255, 255, 255))
        pantalla.blit(texto_zanahorias, (10, 122))
        texto_resistencia = self.fuente.render(f"Resistencia = {self.game_state.resistencia}", True, (255, 255, 255))
        pantalla.blit(texto_resistencia, (10, 150))
        texto_creditos = self.fuente.render(f"Creditos = {self.game_state.creditos}", True, (255, 255, 255))
        pantalla.blit(texto_creditos, (10, 178))
        
        salida = self.obtener_salida(limites_pantalla)
        #pygame.draw.rect(pantalla, (120, 255, 120), salida)
        pc = self.obtener_pc(limites_pantalla)
        #pygame.draw.rect(pantalla, (95, 125, 135), pc)
        #pygame.draw.rect(pantalla, (60, 45, 30), pc, 3)

        self.jugador.dibujar(pantalla)
        if self.jugador.rectangulo.colliderect(
            self.obtener_area_interaccion_cama(limites_pantalla)
        ):
            indicacion = self.fuente.render("E: avanzar dia", True, (255, 255, 255))
            pantalla.blit(indicacion, indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)))
        elif self.jugador.rectangulo.colliderect(salida):
            indicacion = self.fuente.render("Salida automatica", True, (255, 255, 255))
            pantalla.blit(indicacion, indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)))
        elif self.jugador.rectangulo.colliderect(pc):
            indicacion = self.fuente.render(
                "E: vender zanahorias (2 creditos c/u)",
                True,
                (255, 255, 255),
            )
            pantalla.blit(indicacion, indicacion.get_rect(midtop=(pantalla.get_width() // 2, 30)))
        self.inventario.dibujar(pantalla, self.game_state.semilla_zanahoria)