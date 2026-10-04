import pygame


class GameLoop:
    def __init__(self, pantalla, escena, fps=60):
        self.pantalla = pantalla
        self.escena = escena
        self.reloj = pygame.time.Clock()
        self.fps = fps

    def run(self):
        ejecutando = True

        while ejecutando:
            eventos = pygame.event.get()
            for evento in eventos:
                if evento.type == pygame.QUIT:
                    ejecutando = False
                elif evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                    ejecutando = False

            teclas = pygame.key.get_pressed()
            self.escena.update(teclas, self.pantalla.get_rect(), eventos)
            self.escena.draw(self.pantalla)

            pygame.display.flip()
            self.reloj.tick(self.fps)

        pygame.quit()