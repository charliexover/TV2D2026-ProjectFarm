
import random

import pygame


class ParticulaCosecha:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

        # Las partículas ascienden y se dispersan.
        self.vx = random.uniform(-65, 65)
        self.vy = random.uniform(-115, -35)
        self.gravedad = 100

        self.vida = random.uniform(0.30, 0.55)
        self.tamano = random.choice([2, 3, 3, 4])

        self.color = random.choice([
            (255, 215, 70),   # Dorado
            (255, 235, 130),  # Amarillo claro
            (255, 250, 210),  # Brillo casi blanco
            (235, 165, 45),   # Dorado oscuro
        ])

    def actualizar(self, dt):
        self.vida -= dt

        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravedad * dt

        return self.vida > 0

    def dibujar(self, pantalla, desplazamiento):
        if self.vida <= 0:
            return

        x = round(self.x + desplazamiento[0])
        y = round(self.y + desplazamiento[1])

        pygame.draw.rect(
            pantalla,
            self.color,
            (x, y, self.tamano, self.tamano),
        )


class EfectoCosecha:
    def __init__(self):
        self.particulas = []
        self.ultimo_update = pygame.time.get_ticks()

    def crear(self, x, y):
        # Destellos que salen en todas las direcciones.
        for _ in range(12):
            self.particulas.append(ParticulaCosecha(x, y))

        # Partículas adicionales que suben como recompensa.
        for _ in range(5):
            particula = ParticulaCosecha(x, y)
            particula.vx = random.uniform(-25, 25)
            particula.vy = random.uniform(-100, -60)
            particula.tamano = random.choice([2, 3])
            particula.vida = random.uniform(0.40, 0.60)
            self.particulas.append(particula)

    def actualizar(self):
        ahora = pygame.time.get_ticks()
        dt = min((ahora - self.ultimo_update) / 1000, 0.05)
        self.ultimo_update = ahora

        self.particulas = [
            particula
            for particula in self.particulas
            if particula.actualizar(dt)
        ]

    def dibujar(self, pantalla, desplazamiento):
        for particula in self.particulas:
            particula.dibujar(pantalla, desplazamiento)
