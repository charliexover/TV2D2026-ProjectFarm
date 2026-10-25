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
        self.velocidad = 3
        spritesheet_json = (
            Path(__file__).parent / "utils" / "AstroSpritesheetNew.json"
        )
        spritesheet = Spritesheet(str(spritesheet_json))
        self.sprites = {
            nombre: pygame.transform.scale(
                spritesheet.get_sprite(nombre), self.TAMANO_SPRITE
            )
            for nombre in ("Idle", "Blink")
        }
        self.sprites_walk = [
            pygame.transform.scale(
                spritesheet.get_sprite(nombre), self.TAMANO_SPRITE
            )
            for nombre in ("Walk_1", "Walk_2")
        ]
        self.sprites_izquierda = {
            id(sprite): pygame.transform.flip(sprite, True, False)
            for sprite in (*self.sprites.values(), *self.sprites_walk)
        }
        self.sprite = self.sprites["Idle"]
        self.mirando_izquierda = False
        self.proximo_parpadeo = pygame.time.get_ticks() + self.INTERVALO_PARPADEO
        self.proximo_cambio_paso = 0
        self.parpadeo_hasta = None
        self.moviendose = False
        self.paso_walk = 0

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
                self.paso_walk = 0
                self.proximo_cambio_paso = ahora + self.INTERVALO_PASO
                self.moviendose = True
            elif ahora >= self.proximo_cambio_paso:
                self.paso_walk = (self.paso_walk + 1) % len(self.sprites_walk)
                self.proximo_cambio_paso = ahora + self.INTERVALO_PASO
            self.sprite = self.sprites_walk[self.paso_walk]
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

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        sprite = self.sprite
        if self.mirando_izquierda:
            sprite = self.sprites_izquierda[id(self.sprite)]
        posicion = sprite.get_rect(center=self.rectangulo.center)
        posicion.move_ip(desplazamiento)
        pantalla.blit(sprite, posicion)


class Rover:
    TAMANO_SPRITE = (48, 48)
    DISTANCIA_PATRULLA = 60
    VELOCIDAD = 24
    INTERVALO_FRAME = 150

    def __init__(self, x, y):
        spritesheet_json = Path(__file__).parent / "utils" / "RoverSprite.json"
        spritesheet = Spritesheet(str(spritesheet_json))
        self.sprites = [
            pygame.transform.scale(sprite, self.TAMANO_SPRITE)
            for sprite in spritesheet.get_animation_frames("default")
        ]
        self.sprites_izquierda = [
            pygame.transform.flip(sprite, True, False)
            for sprite in self.sprites
        ]
        self.rectangulo = self.sprites[0].get_rect(center=(x, y))
        self.posicion_derecha = self.rectangulo.x
        self.posicion_izquierda = (
            self.posicion_derecha - self.DISTANCIA_PATRULLA
        )
        self.posicion_x = float(self.rectangulo.x)
        self.direccion = -1
        self.ultimo_update = pygame.time.get_ticks()
        self.detenido = False

    def actualizar(self, colisiones=(), bloqueos=()):
        # Si el jugador está tocando el Rover, detenerlo.
        if any(
            self.rectangulo.colliderect(bloqueo)
            for bloqueo in bloqueos
        ):
            self.detenido = True
            return

        # Si el jugador ya no lo toca, reanudar el movimiento.
        if self.detenido:
            self.detenido = False
            self.ultimo_update = pygame.time.get_ticks()

        ahora = pygame.time.get_ticks()
        delta = min((ahora - self.ultimo_update) / 1000, 0.1)
        self.ultimo_update = ahora

        if delta == 0:
            return

        posicion_anterior = self.posicion_x
        self.posicion_x += self.VELOCIDAD * delta * self.direccion

        if self.posicion_x <= self.posicion_izquierda:
            self.posicion_x = float(self.posicion_izquierda)
            self.direccion = 1
        elif self.posicion_x >= self.posicion_derecha:
            self.posicion_x = float(self.posicion_derecha)
            self.direccion = -1

        self.rectangulo.x = round(self.posicion_x)

        # Si choca con un obstáculo del mapa, retroceder.
        if any(
            self.rectangulo.colliderect(colision)
            for colision in colisiones
        ):
            self.posicion_x = posicion_anterior
            self.rectangulo.x = round(self.posicion_x)
            self.direccion *= -1

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        if self.detenido:
            # Mostrar únicamente el primer sprite al detenerse.
            frames = (
                self.sprites_izquierda
                if self.direccion < 0
                else self.sprites
            )
            frame = frames[0]
        else:
            # Reproducir la animación mientras se mueve.
            frames = (
                self.sprites_izquierda
                if self.direccion < 0
                else self.sprites
            )
            indice = (
                pygame.time.get_ticks() // self.INTERVALO_FRAME
            ) % len(frames)
            frame = frames[indice]

        pantalla.blit(
            frame,
            self.rectangulo.move(desplazamiento),
        )