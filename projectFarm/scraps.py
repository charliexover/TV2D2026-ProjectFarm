import random

import pygame


class Chatarra:
    TAMANO = 16 * 3

    def __init__(self, x, y):
        self.rectangulo = pygame.Rect(x, y, self.TAMANO, self.TAMANO)

    @classmethod
    def generar_en(cls, zona):
        if zona.width < cls.TAMANO or zona.height < cls.TAMANO:
            raise ValueError("La zona de chatarra debe caber al menos un cuadrado")

        cantidad = random.randint(2, 5)
        chatarra = []
        for _ in range(cantidad):
            for _ in range(1000):
                x = random.randint(zona.left, zona.right - cls.TAMANO)
                y = random.randint(zona.top, zona.bottom - cls.TAMANO)
                pieza = cls(x, y)
                if not any(
                    pieza.rectangulo.colliderect(otra.rectangulo)
                    for otra in chatarra
                ):
                    chatarra.append(pieza)
                    break
            else:
                raise ValueError(
                    "No se pudo ubicar toda la chatarra sin superposiciones"
                )
        return chatarra

    def dibujar(self, pantalla, desplazamiento=(0, 0)):
        rectangulo = self.rectangulo.move(desplazamiento)
        pygame.draw.rect(pantalla, (115, 125, 130), rectangulo)
        pygame.draw.rect(pantalla, (55, 65, 70), rectangulo, 2)
        pygame.draw.line(
            pantalla,
            (175, 185, 190),
            (rectangulo.left + 5, rectangulo.top + 8),
            (rectangulo.right - 6, rectangulo.top + 8),
            2,
        )