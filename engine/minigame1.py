import random

import pygame

from engine.audio import reproducir_sonido_interaccion


class Minijuego1:
    CANTIDAD_ACIERTOS = 3
    VELOCIDAD_PUNTO = 0.85
    ANCHO_ZONA = 0.13

    def __init__(self):
        self.activo = False
        self.completado = False
        self.aciertos = 0
        self.posicion_punto = 0.0
        self.direccion = 1
        self.inicio_zona = 0.5
        self.ultimo_update = None
        self.puede_acertar = True
        self.mensaje = "Presiona E cuando el punto este en la zona."
        self.fuente_titulo = pygame.font.Font(None, 40)
        self.fuente = pygame.font.Font(None, 28)

    def iniciar(self):
        self.activo = True
        self.completado = False
        self.aciertos = 0
        self.posicion_punto = 0.0
        self.direccion = 1
        self.inicio_zona = random.uniform(0.05, 1 - self.ANCHO_ZONA - 0.05)
        self.ultimo_update = pygame.time.get_ticks()
        self.puede_acertar = True
        self.mensaje = "Presiona E cuando el punto este en la zona."

    def actualizar(self, eventos):
        if not self.activo:
            return self.completado

        ahora = pygame.time.get_ticks()
        if self.ultimo_update is None:
            self.ultimo_update = ahora
        delta = min((ahora - self.ultimo_update) / 1000, 0.05)
        self.ultimo_update = ahora
        self.posicion_punto += self.direccion * self.VELOCIDAD_PUNTO * delta
        if self.posicion_punto >= 1:
            self.posicion_punto = 1
            self.direccion = -1
        elif self.posicion_punto <= 0:
            self.posicion_punto = 0
            self.direccion = 1

        dentro_de_zona = self.inicio_zona <= self.posicion_punto <= (
            self.inicio_zona + self.ANCHO_ZONA
        )
        if not dentro_de_zona:
            self.puede_acertar = True

        for evento in eventos:
            if evento.type != pygame.KEYDOWN or evento.key != pygame.K_e:
                continue

            reproducir_sonido_interaccion()
            if dentro_de_zona and self.puede_acertar:
                self.aciertos += 1
                self.puede_acertar = False
                if self.aciertos == self.CANTIDAD_ACIERTOS:
                    self.completado = True
                    self.activo = False
                    self.mensaje = "Datos descargados correctamente."
                    return True
                self.mensaje = f"Sigue descargando datos."
            elif dentro_de_zona:
                self.mensaje = "Espera a que el punto vuelva a la zona."
            else:
                self.aciertos = 0
                self.puede_acertar = True
                self.mensaje = "Datos corruptos vuelve a intentarlo."

        return False

    def dibujar(self, pantalla):
        limites = pantalla.get_rect()
        velo = pygame.Surface(limites.size, pygame.SRCALPHA)
        velo.fill((0, 0, 0, 190))
        pantalla.blit(velo, (0, 0))

        tarjeta = pygame.Rect(0, 0, min(600, limites.width - 40), 250)
        tarjeta.center = limites.center
        pygame.draw.rect(pantalla, (25, 30, 38), tarjeta)
        pygame.draw.rect(pantalla, (255, 255, 255), tarjeta, 2)

        titulo = self.fuente_titulo.render(
            "Procedimiento de descarga de datos", True, (255, 255, 255)
        )
        pantalla.blit(
            titulo,
            titulo.get_rect(midtop=(tarjeta.centerx, tarjeta.top + 20)),
        )

        texto = self.fuente.render(self.mensaje, True, (230, 230, 230))
        pantalla.blit(
            texto,
            texto.get_rect(center=(tarjeta.centerx, tarjeta.top + 82)),
        )
        marcador = self.fuente.render(
            f"Mb: {self.aciertos}/3", True, (255, 255, 255)
        )
        pantalla.blit(
            marcador,
            marcador.get_rect(center=(tarjeta.centerx, tarjeta.top + 116)),
        )

        ancho_linea = tarjeta.width - 80
        inicio_x = tarjeta.left + 40
        fin_x = inicio_x + ancho_linea
        y = tarjeta.top + 170
        pygame.draw.line(
            pantalla, (190, 190, 190), (inicio_x, y), (fin_x, y), 8
        )
        zona = pygame.Rect(
            round(inicio_x + ancho_linea * self.inicio_zona),
            y - 12,
            round(ancho_linea * self.ANCHO_ZONA),
            24,
        )
        pygame.draw.rect(pantalla, (55, 190, 105), zona)
        x_punto = round(inicio_x + ancho_linea * self.posicion_punto)
        pygame.draw.circle(pantalla, (255, 225, 80), (x_punto, y), 10)

        instruccion = self.fuente.render(
            "Pulsa E para acertar", True, (255, 255, 255)
        )
        pantalla.blit(
            instruccion,
            instruccion.get_rect(midtop=(tarjeta.centerx, tarjeta.top + 198)),
        )