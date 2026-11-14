
import pygame

from engine.input import actualizar_posicion_mouse


class GameLoop:
    def __init__(self, pantalla, escena, fps=60, text_renderer=None):
        self.pantalla = pantalla
        self.escena = escena
        self.reloj = pygame.time.Clock()
        self.fps = fps
        self.text_renderer = text_renderer

        self.rect_destino = pygame.Rect(0, 0, 800, 600)
        self.escala = 1

    def _calcular_area_juego(self):
        ventana = pygame.display.get_surface()
        ancho_ventana, alto_ventana = ventana.get_size()

        ancho_original = self.pantalla.get_width()
        alto_original = self.pantalla.get_height()

        self.escala = min(
            ancho_ventana / ancho_original,
            alto_ventana / alto_original,
        )

        ancho = int(ancho_original * self.escala)
        alto = int(alto_original * self.escala)

        x = (ancho_ventana - ancho) // 2
        y = (alto_ventana - alto) // 2

        self.rect_destino = pygame.Rect(x, y, ancho, alto)

    def _convertir_posicion_mouse(self, posicion):
        if not self.rect_destino.collidepoint(posicion):
            return (-1, -1)

        x = (posicion[0] - self.rect_destino.x) / self.escala
        y = (posicion[1] - self.rect_destino.y) / self.escala

        return (int(x), int(y))

    def _convertir_eventos(self, eventos):
        eventos_convertidos = []

        for evento in eventos:
            if evento.type in (
                pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP,
                pygame.MOUSEMOTION,
            ):
                datos = evento.dict.copy()

                datos["pos"] = self._convertir_posicion_mouse(
                    evento.pos
                )

                if evento.type == pygame.MOUSEMOTION:
                    datos["rel"] = (
                        int(evento.rel[0] / self.escala),
                        int(evento.rel[1] / self.escala),
                    )

                evento = pygame.event.Event(evento.type, datos)

            eventos_convertidos.append(evento)

        return eventos_convertidos

    def _dibujar_pantalla_escalada(self):
        ventana = pygame.display.get_surface()

        imagen = pygame.transform.scale(
            self.pantalla,
            self.rect_destino.size,
        )

        ventana.fill((0, 0, 0))
        ventana.blit(imagen, self.rect_destino.topleft)

    def run(self):
        ejecutando = True

        while ejecutando:
            eventos = pygame.event.get()

            self._calcular_area_juego()

            posicion_mouse = self._convertir_posicion_mouse(
                pygame.mouse.get_pos()
            )
            actualizar_posicion_mouse(posicion_mouse)

            eventos = self._convertir_eventos(eventos)

            for evento in eventos:
                if evento.type == pygame.QUIT:
                    ejecutando = False

            teclas = pygame.key.get_pressed()

            self.escena.update(
                teclas,
                self.pantalla.get_rect(),
                eventos,
            )

            if getattr(self.escena, "solicitar_cierre", False):
                ejecutando = False
                continue

            if self.text_renderer is not None:
                self.text_renderer.comenzar_frame()

            self.escena.draw(self.pantalla)

            
            self._dibujar_pantalla_escalada()

            ventana = pygame.display.get_surface()

            if self.text_renderer is not None:
                self.text_renderer.dibujar_pendientes(
                    ventana,
                    self.escala,
                    self.rect_destino.topleft,
                )

            if hasattr(self.escena, "dibujar_transicion_sueno"):
                self.escena.dibujar_transicion_sueno(
                    ventana,
                    self.escala,
                    self.rect_destino.topleft,
                )

            if hasattr(self.escena, "dibujar_transicion_desmayo"):
                self.escena.dibujar_transicion_desmayo(
                    ventana,
                    self.escala,
                    self.rect_destino.topleft,
                )

            pygame.display.flip()
            self.reloj.tick(self.fps)

        pygame.quit()
