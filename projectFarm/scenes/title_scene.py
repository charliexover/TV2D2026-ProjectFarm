import pygame


class TitleScene:
    def __init__(self, al_iniciar_partida):
        self.al_iniciar_partida = al_iniciar_partida
        self.fuente = pygame.font.Font(None, 48)
        self.texto = self.fuente.render("Nueva partida", True, (255, 255, 255))
        self.boton_rect = self.texto.get_rect()

    def update(self, teclas, limites_pantalla, eventos=()):
        self.boton_rect.center = limites_pantalla.center
        for evento in eventos:
            if (
                evento.type == pygame.MOUSEBUTTONDOWN
                and evento.button == 1
                and self.boton_rect.collidepoint(evento.pos)
            ):
                self.al_iniciar_partida()
                return

    def draw(self, pantalla):
        self.boton_rect.center = pantalla.get_rect().center
        pantalla.fill((99, 60, 58))
        pantalla.blit(self.texto, self.boton_rect)