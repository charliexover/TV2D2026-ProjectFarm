import pygame


class Jugador:
    def __init__(self, x=100, y=100):
        self.rectangulo = pygame.Rect(x, y, 50, 50)
        self.velocidad = 5

    def actualizar(self, teclas):
        if teclas[pygame.K_a]:
            self.rectangulo.x -= self.velocidad
        if teclas[pygame.K_d]:
            self.rectangulo.x += self.velocidad
        if teclas[pygame.K_w]:
            self.rectangulo.y -= self.velocidad
        if teclas[pygame.K_s]:
            self.rectangulo.y += self.velocidad

    def dibujar(self, pantalla):
        pygame.draw.rect(pantalla, (30, 100, 220), self.rectangulo)
