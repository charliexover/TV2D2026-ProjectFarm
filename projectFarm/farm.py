import pygame


CULTIVOS = {
    "zanahoria": {"dias_crecimiento": 3, "color": (170, 135, 55)},
}


class Parcela:
    def __init__(self, x, y):
        self.planta = None
        self.dias_crecimiento = 0
        self.dia_regado = None
        self.rectangulo = pygame.Rect(x, y, 50, 50)

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

    def dibujar(self, pantalla):
        colores = {
            "vacia": (120, 72, 40),
            "creciendo": (70, 140, 60),
            "cosechable": (225, 125, 40),
        }
        etapa = self.obtener_etapa()
        color = CULTIVOS[self.planta]["color"] if etapa == self.planta else colores[etapa]
        pygame.draw.rect(pantalla, color, self.rectangulo)
        pygame.draw.rect(pantalla, (60, 45, 30), self.rectangulo, 2)