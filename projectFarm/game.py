import pygame

from engine.game_loop import GameLoop
from engine.text_renderer import TextRenderer
from projectFarm.scenes import SceneManager


class ProjectFarm:
    WIDTH = 800
    HEIGHT = 600
    FPS = 60

    RESOLUCIONES = [
        (800, 600),
        (1024, 768),
        (1280, 720),
        (1366, 768),
        (1600, 900),
        (1920, 1080),
    ]

    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        pygame.display.set_caption("Proyecto Granja")
        self.resolucion_ventana = (self.WIDTH, self.HEIGHT)
        self.pantalla_completa = False

        self.screen = pygame.display.set_mode(
            (self.WIDTH, self.HEIGHT),
            pygame.RESIZABLE,
        )

        self.canvas = pygame.Surface((self.WIDTH, self.HEIGHT))

        # Renderizador compartido para todos los textos.
        self.text_renderer = TextRenderer()

        self.scene = SceneManager(
            self.cambiar_resolucion,
            self.RESOLUCIONES,
            self.alternar_pantalla_completa,
            self.text_renderer,
        )

        self.game_loop = GameLoop(
            self.canvas,
            self.scene,
            self.FPS,
            self.text_renderer,
        )

    def cambiar_resolucion(self, resolucion):
        self.resolucion_ventana = resolucion

        self.screen = pygame.display.set_mode(
            resolucion,
            pygame.RESIZABLE,
        )

        self.pantalla_completa = False

    def alternar_pantalla_completa(self):
        if self.pantalla_completa:
            self.screen = pygame.display.set_mode(
                self.resolucion_ventana,
                pygame.RESIZABLE,
            )
            self.pantalla_completa = False
        else:
            self.resolucion_ventana = pygame.display.get_window_size()

            self.screen = pygame.display.set_mode(
                (0, 0),
                pygame.FULLSCREEN,
            )
            self.pantalla_completa = True

        return self.pantalla_completa

    def run(self):
        self.game_loop.run()