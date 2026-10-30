
import random

import pygame


class Particula:
    def __init__(self, x, y, rafaga=False):
        self.x = float(x)
        self.y = float(y)
        self.rafaga = rafaga
        

        if rafaga:
            self.vida = random.uniform(1.2, 2.5)
            self.vx = random.uniform(-260, -140)
            self.vy = random.uniform(-30, 20)
            self.tamano = random.randint(6, 12) if rafaga else random.randint(1, 3)
        else:
            self.vida = random.uniform(2.0, 4.0)
            self.vx = random.uniform(-35, -12)
            self.vy = random.uniform(-7, 3)
            self.tamano = random.choice([1, 2, 2, 3])

        self.color = random.choice([
            (180, 119, 77),
            (195, 133, 87),
            (155, 98, 65),
            (211, 153, 105),
            (135, 87, 60),
        ])

        self.vida_inicial = self.vida

    def actualizar(self, dt, intensidad_viento):
        self.vida -= dt

        self.x += self.vx * intensidad_viento * dt
        self.y += self.vy * dt

        return self.vida > 0

    
    def dibujar(self, pantalla):
        # Las partículas desaparecen suavemente al envejecer.
        proporcion = self.vida / self.vida_inicial

        if proporcion < 0.2:
            return

        tamano = self.tamano

        if self.rafaga:
            tamano = max(1, round(tamano * proporcion))

        pygame.draw.rect(
            pantalla,
            self.color,
            (
                round(self.x),
                round(self.y),
                tamano,
                tamano,
            ),
        )



class SistemaParticulas:
    MAX_PARTICULAS = 450

    def __init__(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        self.particulas = []
        self.offset_camara_anterior = (0, 0)

        self.ultimo_update = pygame.time.get_ticks()

        # Polvo ambiental.
        self.tiempo_polvo = 0
        self.intervalo_polvo = 0.12

        # Ráfagas ocasionales.
        self.tiempo_hasta_rafaga = random.uniform(5, 9)
        self.duracion_rafaga = 0
        self.tiempo_particulas_rafaga = 0

        self.intensidad_viento = 1.0
        self.intensidad_objetivo = 1.0

    def reiniciar(self, ancho, alto):
        self.ancho = ancho
        self.alto = alto
        self.particulas.clear()
        self.tiempo_polvo = 0
        self.tiempo_hasta_rafaga = random.uniform(5, 9)
        self.duracion_rafaga = 0
        self.tiempo_particulas_rafaga = 0
        self.intensidad_viento = 1.0
        self.intensidad_objetivo = 1.0
        self.ultimo_update = pygame.time.get_ticks()
        self.offset_camara_anterior = (0, 0)

    def actualizar_camara(self, offset_camara):
        desplazamiento_x = offset_camara[0] - self.offset_camara_anterior[0]
        desplazamiento_y = offset_camara[1] - self.offset_camara_anterior[1]

        for particula in self.particulas:
            particula.x -= desplazamiento_x
            particula.y -= desplazamiento_y

        self.offset_camara_anterior = offset_camara

    def actualizar(self, desplazamiento_x=0, desplazamiento_y=0, tormenta=False,):
        ahora = pygame.time.get_ticks()
        dt = min((ahora - self.ultimo_update) / 1000, 0.05)
        self.ultimo_update = ahora

        # Compensar el movimiento de la cámara para que el polvo
        # conserve su posición respecto al escenario.
        for particula in self.particulas:
            particula.x -= desplazamiento_x
            particula.y -= desplazamiento_y


        # Control de las ráfagas.
        if self.duracion_rafaga > 0:
            self.duracion_rafaga -= dt
            self.tiempo_particulas_rafaga += dt

            if self.duracion_rafaga <= 0:
                self.duracion_rafaga = 0
                self.intensidad_objetivo = 1.0
        else:
            self.tiempo_hasta_rafaga -= dt

            if self.tiempo_hasta_rafaga <= 0:
                self.duracion_rafaga = random.uniform(1.5, 3.0)
                self.tiempo_particulas_rafaga = 0
                self.tiempo_hasta_rafaga = random.uniform(6, 12)
                self.intensidad_objetivo = random.uniform(2.0, 2.8)

        if tormenta:
            self.intensidad_objetivo = 3.0
            
        # El viento aumenta y disminuye gradualmente.
        diferencia = self.intensidad_objetivo - self.intensidad_viento
        self.intensidad_viento += diferencia * min(dt * 1.5, 1)

        # Polvo ambiental: lento y relativamente discreto.
        self.tiempo_polvo += dt

        intervalo_actual = 0.006 if tormenta else self.intervalo_polvo

        while self.tiempo_polvo >= intervalo_actual:
            self.tiempo_polvo -= intervalo_actual

            probabilidad = 1.0 if tormenta else 0.7

            if random.random() < probabilidad:
                x = random.uniform(0, self.ancho)
                y = random.uniform(0, self.alto)

                self._crear_particula(x, y, rafaga=tormenta)
                
        # Durante las ráfagas se levanta mucho más polvo.
        if self.duracion_rafaga > 0:
            while self.tiempo_particulas_rafaga >= 0.035:
                self.tiempo_particulas_rafaga -= 0.035

                if random.random() < 0.9:
                    x = random.uniform(0, self.ancho)
                    y = random.uniform(self.alto * 0.35, self.alto * 0.95)

                    self._crear_particula(x, y, rafaga=True)

        # Actualizar y eliminar partículas fuera de pantalla.
        particulas_activas = []

        for particula in self.particulas:
            sigue_activa = particula.actualizar(
                dt,
                self.intensidad_viento,
            )

            if (
                sigue_activa
                and -15 < particula.x < self.ancho + 15
                and -15 < particula.y < self.alto + 15
            ):
                particulas_activas.append(particula)

        self.particulas = particulas_activas

    def _crear_particula(self, x, y, rafaga=False):
        if len(self.particulas) >= self.MAX_PARTICULAS:
            return

        self.particulas.append(Particula(x, y, rafaga))

    def dibujar(self, pantalla):
        for particula in self.particulas:
            particula.dibujar(pantalla)
