import pygame
import random

CULTIVOS = {
    1: {
        "nombre": "zanahoria",
        "dias_crecimiento": 2,
        "precio_venta": 8,
        "cantidad_cosecha": 1,
        "semilla": "semilla_zanahoria",
        "cosecha": "zanahorias_cosechadas",
        "color": (170, 135, 55),
        "etapas": [
            "semillaZh",
            "broteZh",
            "maduroZh"
        ],
        "tamano_etapas": {
            "maduroZh": (48, 96),
        },
    },
    2: {
        "nombre": "papa",
        "dias_crecimiento": 3,
        "precio_venta": 12,
        "cantidad_cosecha": 3,
        "semilla": "semilla_papa",
        "cosecha": "papas_cosechadas",
        "color": (170, 135, 55),
        "etapas": ["semillaP", "broteP", "maduroP"],
    },
    3: {
        "nombre": "tomate",
        "dias_crecimiento": 6,
        "precio_venta": 18,
        "cantidad_cosecha": 5,
        "semilla": "semilla_tomate",
        "cosecha": "tomates_cosechadas",
        "color": (170, 135, 55),
        "etapas": ["semillaT", "broteT", "maduroT"],
        "tamano_etapas": {
            "broteT": (48, 96),
            "maduroT": (48, 96),
        },
    },
    4: {
        "nombre": "repollo",
        "dias_crecimiento": 4,
        "precio_venta": 44,
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
        self.rotacion_semilla = 0
        self.rectangulo = pygame.Rect(x, y, self.TAMANO, self.TAMANO)

    def plantar(self, tipo_cultivo):
        if tipo_cultivo not in CULTIVOS:
            raise ValueError(f"Cultivo desconocido: {tipo_cultivo}")
        self.planta = tipo_cultivo
        self.dias_crecimiento = 0
        self.dia_regado = None
        self.dia_maduro = None
        self.seca = False
        self.rotacion_semilla = random.choice([0, 90, 180, 270])

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

    def dibujar_cultivo(
    self,
    pantalla,
    sprites_cultivos,
    desplazamiento=(0, 0),
    ):
        if self.planta is None:
            return

        rectangulo = self.rectangulo.move(desplazamiento)

        if self.seca:
            nombre_sprite = "cosechaSeca"
        else:
            etapas = CULTIVOS[self.planta]["etapas"]
            dias_necesarios = CULTIVOS[self.planta]["dias_crecimiento"]

            if self.dias_crecimiento == 0:
                indice_etapa = 0
            elif self.dias_crecimiento < dias_necesarios:
                indice_etapa = 1
            else:
                indice_etapa = 2

            nombre_sprite = etapas[indice_etapa]

        sprite = sprites_cultivos[self.planta][nombre_sprite]

        if self.dias_crecimiento == 0 and not self.seca:
            sprite = pygame.transform.rotate(
                sprite,
                self.rotacion_semilla,
            )

        pantalla.blit(
            sprite,
            sprite.get_rect(midbottom=rectangulo.midbottom),
        )

    def dibujar(
    self,
    pantalla,
    dia_actual,
    sprites_cultivos=None,
    desplazamiento=(0, 0),
    sprites_tierra=None,
    dibujar_planta=True,
    ):
        rectangulo = self.rectangulo.move(desplazamiento)

        # Dibujar la tierra debajo de todo.
        if sprites_tierra is not None:
            nombre_tierra = (
                "mojada"
                if self.dia_regado == dia_actual
                else "seca"
            )

            pantalla.blit(
                sprites_tierra[nombre_tierra],
                rectangulo,
            )

        # Dibujar el cultivo por encima de la tierra.
        if dibujar_planta and self.planta is not None and sprites_cultivos is not None:
            self.dibujar_cultivo(
                pantalla,
                sprites_cultivos,
                desplazamiento,
            )
