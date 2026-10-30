import pygame


class TitleScene:
    def __init__(self, al_iniciar_partida):
        self.al_iniciar_partida = al_iniciar_partida
        self.fuente = pygame.font.Font(None, 48)
        self.texto = self.fuente.render(
            "Proyecto Granja", True, (255, 255, 255)
        )
        self.boton_rect = self.texto.get_rect()
        self.fuente_pie = pygame.font.Font(None, 20)
        self.texto_pie = self.fuente_pie.render(
            "© 2026 - TV2D Facultad de Ingeniera Tecnólogo en Informática  Desarrollado por Charliexover", True, (220, 220, 220)
        )
        self.pie_rect = self.texto_pie.get_rect()

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
        pantalla.fill((99, 60, 58))

        # Título centrado
        self.boton_rect.center = pantalla.get_rect().center
        pantalla.blit(self.texto, self.boton_rect)

        # Pie de página centrado en el borde inferior
        self.pie_rect.midbottom = (
            pantalla.get_rect().centerx,
            pantalla.get_height() - 10
        )
        pantalla.blit(self.texto_pie, self.pie_rect)