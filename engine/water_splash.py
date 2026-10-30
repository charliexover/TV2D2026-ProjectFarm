
import random
import pygame


class GotaAgua:
    
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)

        # Las gotas salen en distintas direcciones.
        self.vx = random.uniform(-85, 85)
        self.vy = random.uniform(-130, -45)

        self.gravedad = 280
        self.vida = random.uniform(0.30, 0.55)
        self.vida_inicial = self.vida

        self.tamano = random.choice([2, 2, 3, 3, 4])

        self.color = random.choice([
            (100, 195, 255),
            (145, 220, 255),
            (190, 240, 255),
            (70, 160, 230),
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


class SistemaSplashAgua:
    def __init__(self):
        self.gotas = []
        self.ultimo_update = pygame.time.get_ticks()

    
    def crear_splash(self, x, y):
        # Salpicadura principal.
        for _ in range(14):
            self.gotas.append(GotaAgua(x, y))

        # Unas gotas extra, más pequeñas y rápidas.
        for _ in range(4):
            gota = GotaAgua(x, y)
            gota.tamano = 2
            gota.vy = random.uniform(-155, -100)
            gota.vida = random.uniform(0.20, 0.35)
            gota.vida_inicial = gota.vida
            self.gotas.append(gota)


    def actualizar(self):
        ahora = pygame.time.get_ticks()
        dt = min((ahora - self.ultimo_update) / 1000, 0.05)
        self.ultimo_update = ahora

        self.gotas = [
            gota for gota in self.gotas
            if gota.actualizar(dt)
        ]

    def dibujar(self, pantalla, desplazamiento):
        for gota in self.gotas:
            gota.dibujar(pantalla, desplazamiento)
