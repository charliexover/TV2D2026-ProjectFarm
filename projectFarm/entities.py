from pathlib import Path

import pygame

from engine.spritesheet import Spritesheet


class Jugador:
    INTERVALO_PARPADEO = 2500
    DURACION_PARPADEO = 140
    INTERVALO_PASO = 180
    TAMANO_SPRITE = (42, 48)

    def __init__(self, x=100, y=100):
        self.rectangulo = pygame.Rect(x, y, 50, 50)
        self.velocidad = 2
        spritesheet_json = Path(__file__).parent / "utils" / "AstroSpritesheet.json"
        spritesheet = Spritesheet(str(spritesheet_json))
        self.sprites = {
            nombre: pygame.transform.scale(
                spritesheet.get_sprite(nombre), self.TAMANO_SPRITE
            )
            for nombre in ("Idle", "Blink", "Walk")
        }
        self.sprites_izquierda = {
            id(sprite): pygame.transform.flip(sprite, True, False)
            for sprite in self.sprites.values()
        }
        self.sprite = self.sprites["Idle"]
        self.mirando_izquierda = False
        self.proximo_parpadeo = pygame.time.get_ticks() + self.INTERVALO_PARPADEO
        self.proximo_cambio_paso = 0
        self.parpadeo_hasta = None
        self.moviendose = False
        self.paso_walk = True

    def actualizar(self, teclas):
        desplazamiento_x = 0
        desplazamiento_y = 0
        if teclas[pygame.K_a]:
            desplazamiento_x -= self.velocidad
        if teclas[pygame.K_d]:
            desplazamiento_x += self.velocidad
        if teclas[pygame.K_w]:
            desplazamiento_y -= self.velocidad
        if teclas[pygame.K_s]:
            desplazamiento_y += self.velocidad

        self.rectangulo.move_ip(desplazamiento_x, desplazamiento_y)
        if desplazamiento_x:
            self.mirando_izquierda = desplazamiento_x < 0
        ahora = pygame.time.get_ticks()

        if desplazamiento_x or desplazamiento_y:
            if not self.moviendose:
                self.paso_walk = True
                self.proximo_cambio_paso = ahora + self.INTERVALO_PASO
                self.moviendose = True
            elif ahora >= self.proximo_cambio_paso:
                self.paso_walk = not self.paso_walk
                self.proximo_cambio_paso = ahora + self.INTERVALO_PASO
            self.sprite = self.sprites["Walk" if self.paso_walk else "Idle"]
            self.parpadeo_hasta = None
            self.proximo_parpadeo = ahora + self.INTERVALO_PARPADEO
        else:
            self.moviendose = False
            if self.parpadeo_hasta is not None and ahora < self.parpadeo_hasta:
                self.sprite = self.sprites["Blink"]
            elif ahora >= self.proximo_parpadeo:
                self.sprite = self.sprites["Blink"]
                self.parpadeo_hasta = ahora + self.DURACION_PARPADEO
                self.proximo_parpadeo = self.parpadeo_hasta + self.INTERVALO_PARPADEO
            else:
                self.sprite = self.sprites["Idle"]
            if self.parpadeo_hasta is not None and ahora >= self.parpadeo_hasta:
                self.parpadeo_hasta = None
                if self.sprite == self.sprites["Blink"]:
                    self.sprite = self.sprites["Idle"]

    def dibujar(self, pantalla):
        sprite = self.sprite
        if self.mirando_izquierda:
            sprite = self.sprites_izquierda[id(self.sprite)]
        posicion = sprite.get_rect(center=self.rectangulo.center)
        pantalla.blit(sprite, posicion)
