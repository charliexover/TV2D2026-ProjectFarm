import random

import pygame


class ParticulaPower:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vida = random.uniform(0.25, 0.5)
        self.vida_inicial = self.vida
        self.tamano = random.randint(2, 4)
        self.vx = random.uniform(-75, 75)
        self.vy = random.uniform(-150, -60)
        self.gravedad = 300
        self.color = random.choice(
            ((255, 215, 90), (255, 145, 35), (255, 245, 180))
        )

    def actualizar(self, delta):
        self.vida -= delta
        self.x += self.vx * delta
        self.y += self.vy * delta
        self.vy += self.gravedad * delta
        return self.vida > 0

    def dibujar(self, pantalla, desplazamiento):
        if self.vida <= 0:
            return

        factor = max(0, self.vida / self.vida_inicial)
        tamano = max(1, round(self.tamano * factor))
        centro = (
            round(self.x + desplazamiento[0]),
            round(self.y + desplazamiento[1]),
        )
        pygame.draw.rect(
            pantalla,
            self.color,
            (
                centro[0] - tamano,
                centro[1] - tamano,
                tamano * 2,
                tamano * 2,
            ),
        )


class EfectoPower:
    INTERVALO_CHISPAS = 0.24

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.particulas = []
        self.tiempo_chispas = 0
        self.ultimo_update = pygame.time.get_ticks()

    def actualizar(self, activo=True):
        ahora = pygame.time.get_ticks()
        delta = min((ahora - self.ultimo_update) / 1000, 0.05)
        self.ultimo_update = ahora

        if not activo:
            self.apagar()
            return

        self.tiempo_chispas += delta
        while self.tiempo_chispas >= self.INTERVALO_CHISPAS:
            self.tiempo_chispas -= self.INTERVALO_CHISPAS
            for _ in range(random.randint(1, 2)):
                self.particulas.append(
                    ParticulaPower(
                        self.x + random.uniform(-5, 5),
                        self.y + random.uniform(-3, 3),
                    )
                )

        self.particulas = [
            particula
            for particula in self.particulas
            if particula.actualizar(delta)
        ]

    def apagar(self):
        self.particulas.clear()
        self.tiempo_chispas = 0

    def dibujar(self, pantalla, desplazamiento):
        for particula in self.particulas:
            particula.dibujar(pantalla, desplazamiento)
