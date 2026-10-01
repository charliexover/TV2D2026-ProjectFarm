import pygame

from engine.game_loop import GameLoop
from .scenes.game_scene import GameScene


class ProjectFarm:
    WIDTH = 800
    HEIGHT = 600
    FPS = 60

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Proyecto Granja")

        self.scene = GameScene()
        self.game_loop = GameLoop(self.screen, self.scene, self.FPS)

    def run(self):
        self.game_loop.run()