import pygame


CULTIVOS = {
    1: {
        "nombre": "zanahoria",
        "dias_crecimiento": 2,
        "color": (170, 135, 55),
        "etapas": [
            "semillaZh",
            "broteZh",
            "maduroZh"
        ]
    },
}


class Parcela:
    TAMANO = 16 * 3

    def __init__(self, x, y):
        self.planta = None
        self.dias_crecimiento = 0
        self.dia_regado = None
        self.rectangulo = pygame.Rect(x, y, self.TAMANO, self.TAMANO)

    def plantar(self, tipo_cultivo):
        if tipo_cultivo not in CULTIVOS:
            raise ValueError(f"Cultivo desconocido: {tipo_cultivo}")
        self.planta = tipo_cultivo
        self.dias_crecimiento = 0
        self.dia_regado = None

    def regar(self, dia_actual):
        if self.planta is not None:
            self.dia_regado = dia_actual


    def avanzar_dia(self, dia_actual):
        if self.planta is not None and self.dia_regado == dia_actual:
            self.dias_crecimiento += 1

    def obtener_etapa(self):
        if self.planta is None:
            return "vacia"

        if self.dias_crecimiento == 0:
            return self.planta
        if self.dias_crecimiento < CULTIVOS[self.planta]["dias_crecimiento"]:
            return "creciendo"
        return "cosechable"

    def cosechar(self):
        if self.obtener_etapa() != "cosechable":
            return False
        self.planta = None
        self.dias_crecimiento = 0
        self.dia_regado = None
        return True

    def dibujar(
        self, pantalla, dia_actual, sprites_cultivos=None, desplazamiento=(0, 0)
    ):
        rectangulo = self.rectangulo.move(desplazamiento)
        color = (
            (105, 65, 40)
            if self.dia_regado == dia_actual
            else (170, 135, 95)
        )
        pygame.draw.rect(pantalla, color, rectangulo)
        if self.planta is not None and sprites_cultivos is not None:
            etapas = CULTIVOS[self.planta]["etapas"]
            indice_etapa = min(self.dias_crecimiento, len(etapas) - 1)
            nombre_sprite = etapas[indice_etapa]
            sprite = sprites_cultivos[self.planta][nombre_sprite]
            pantalla.blit(sprite, sprite.get_rect(center=rectangulo.center))
        pygame.draw.rect(pantalla, (60, 45, 30), rectangulo, 2)