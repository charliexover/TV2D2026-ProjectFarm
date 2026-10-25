import pygame


CULTIVOS = {
    1: {
        "nombre": "zanahoria",
        "dias_crecimiento": 2,
        "precio_venta": 4,
        "cantidad_cosecha": 1,
        "semilla": "semilla_zanahoria",
        "cosecha": "zanahorias_cosechadas",
        "color": (170, 135, 55),
        "etapas": [
            "semillaZh",
            "broteZh",
            "maduroZh"
        ]
    },
    2: {
        "nombre": "papa",
        "dias_crecimiento": 3,
        "precio_venta": 6,
        "cantidad_cosecha": 3,
        "semilla": "semilla_papa",
        "cosecha": "papas_cosechadas",
        "color": (170, 135, 55),
        "etapas": ["semillaP", "broteP", "maduroP"],
    },
    3: {
        "nombre": "tomate",
        "dias_crecimiento": 6,
        "precio_venta": 9,
        "cantidad_cosecha": 5,
        "semilla": "semilla_tomate",
        "cosecha": "tomates_cosechadas",
        "color": (170, 135, 55),
        "etapas": ["semillaT", "broteT", "maduroT"],
    },
    4: {
        "nombre": "repollo",
        "dias_crecimiento": 4,
        "precio_venta": 22,
        "cantidad_cosecha": 1,
        "semilla": "semilla_repollo",
        "cosecha": "repollos_cosechadas",
        "color": (170, 135, 55),
        "etapas": ["semillaR", "broteR", "maduroR"],
    },
}


class Parcela:
    TAMANO = 48

    def __init__(self, x, y):
        self.planta = None
        self.dias_crecimiento = 0
        self.dia_regado = None
        self.dia_maduro = None
        self.seca = False
        self.rectangulo = pygame.Rect(x, y, self.TAMANO, self.TAMANO)

    def plantar(self, tipo_cultivo):
        if tipo_cultivo not in CULTIVOS:
            raise ValueError(f"Cultivo desconocido: {tipo_cultivo}")
        self.planta = tipo_cultivo
        self.dias_crecimiento = 0
        self.dia_regado = None
        self.dia_maduro = None
        self.seca = False

    def regar(self, dia_actual):
        if self.planta is not None and not self.seca:
            self.dia_regado = dia_actual


    def avanzar_dia(self, dia_actual):
        if self.planta is None or self.seca:
            return

        if (
            self.planta == 3
            and self.dia_maduro is not None
            and dia_actual + 1 > self.dia_maduro + 2
        ):
            self.planta = None
            self.dias_crecimiento = 0
            self.dia_regado = None
            self.dia_maduro = None
            self.seca = False
            return

        if self.obtener_etapa() == "cosechable":
            return

        if self.dia_regado != dia_actual:
            self.seca = True
            return

        if self.dia_regado == dia_actual:
            self.dias_crecimiento += 1
            if (
                self.planta == 3
                and self.dia_maduro is None
                and self.dias_crecimiento >= CULTIVOS[self.planta]["dias_crecimiento"]
            ):
                self.dia_maduro = dia_actual + 1

    def obtener_etapa(self):
        if self.planta is None:
            return "vacia"
        if self.seca:
            return "seca"

        if self.dias_crecimiento == 0:
            return self.planta
        if self.dias_crecimiento < CULTIVOS[self.planta]["dias_crecimiento"]:
            return "creciendo"
        return "cosechable"

    def retirar_seca(self):
        if not self.seca:
            return False
        self.planta = None
        self.dias_crecimiento = 0
        self.dia_regado = None
        self.dia_maduro = None
        self.seca = False
        return True

    def cosechar(self, dia_actual):
        if self.obtener_etapa() != "cosechable":
            return False
        if self.planta == 3:
            if (
                self.dia_maduro is not None
                and dia_actual >= self.dia_maduro + 2
            ):
                self.planta = None
                self.dias_crecimiento = 0
                self.dia_regado = None
                self.dia_maduro = None
                self.seca = False
                return True
            self.dias_crecimiento = CULTIVOS[self.planta]["dias_crecimiento"] - 1
            self.dia_regado = None
            return True
        self.planta = None
        self.dias_crecimiento = 0
        self.dia_regado = None
        self.dia_maduro = None
        self.seca = False
        return True

    def dibujar(
        self,
        pantalla,
        dia_actual,
        sprites_cultivos=None,
        desplazamiento=(0, 0),
    ):
        rectangulo = self.rectangulo.move(desplazamiento)
        color = (
            (105, 65, 40)
            if self.dia_regado == dia_actual
            else (170, 135, 95)
        )
        pygame.draw.rect(pantalla, color, rectangulo)
        if self.planta is not None and sprites_cultivos is not None:
            if self.seca:
                nombre_sprite = "cosechaSeca"
            if self.seca:
                nombre_sprite = "cosechaSeca"
            else:
                etapas = CULTIVOS[self.planta]["etapas"]
                dias_necesarios = CULTIVOS[self.planta]["dias_crecimiento"]

                if self.dias_crecimiento == 0:
                    indice_etapa = 0  # Semilla
                elif self.dias_crecimiento < dias_necesarios:
                    indice_etapa = 1  # Brote
                else:
                    indice_etapa = 2  # Maduro

                nombre_sprite = etapas[indice_etapa]

            sprite = sprites_cultivos[self.planta][nombre_sprite]
            pantalla.blit(
                sprite,
                sprite.get_rect(center=rectangulo.center),
            )
        pygame.draw.rect(pantalla, (60, 45, 30), rectangulo, 2)