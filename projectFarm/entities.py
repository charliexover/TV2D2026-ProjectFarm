import pygame


class Jugador:
    def __init__(self, x=100, y=100):
        self.rectangulo = pygame.Rect(x, y, 50, 50)
        self.velocidad = 5

    def actualizar(self, teclas):
        if teclas[pygame.K_LEFT]:
            self.rectangulo.x -= self.velocidad
        if teclas[pygame.K_RIGHT]:
            self.rectangulo.x += self.velocidad
        if teclas[pygame.K_UP]:
            self.rectangulo.y -= self.velocidad
        if teclas[pygame.K_DOWN]:
            self.rectangulo.y += self.velocidad

    def dibujar(self, pantalla):
        pygame.draw.rect(pantalla, (30, 100, 220), self.rectangulo)
