
from engine.ui import Inventario
from projectFarm.scenes.game_scene import GameScene
from projectFarm.scenes.home_scene import HomeScene
from projectFarm.scenes.title_scene import TitleScene
from projectFarm.game_state import GameState


class SceneManager:
    def __init__(self):
        self.escenas = {}
        self.escena_actual = None
        self.game_state = GameState()
        self.inventario = Inventario()
        self.granja = GameScene(self.game_state, self.inventario, self.cambiar_a_casa)
        self.casa = HomeScene(
            self.game_state,
            self.inventario,
            self.cambiar_a_granja,
            self.granja.avanzar_dia,
        )
        self.titulo = TitleScene(self.cambiar_a_granja)
        self.registrar_escena("granja", self.granja, inicial=False)
        self.registrar_escena("casa", self.casa, inicial=False)
        self.registrar_escena("titulo", self.titulo, inicial=True)

    def registrar_escena(self, nombre, escena, inicial=False):
        if nombre in self.escenas:
            raise ValueError(f"Ya existe una escena registrada con el nombre: {nombre}")

        self.escenas[nombre] = escena
        if inicial or self.escena_actual is None:
            self.escena_actual = escena

    def cambiar_escena(self, nombre):
        try:
            self.escena_actual = self.escenas[nombre]
        except KeyError:
            raise KeyError(f"No hay una escena registrada con el nombre: {nombre}") from None

    def cambiar_a_granja(self):
        self.cambiar_escena("granja")

    def cambiar_a_casa(self):
        self.cambiar_escena("casa")

    def cambiar_a_titulo(self):
        self.cambiar_escena("titulo")

    def update(self, teclas, limites_pantalla, eventos=()):
        self.escena_actual.update(teclas, limites_pantalla, eventos)

    def draw(self, pantalla):
        self.escena_actual.draw(pantalla)