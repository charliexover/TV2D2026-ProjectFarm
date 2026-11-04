
import os
import pygame
from ..entities import Jugador

class TitleScene:
    
    def __init__(self, al_iniciar_partida):
        self.al_iniciar_partida = al_iniciar_partida
        self.jugador = Jugador()
        self.jugador.rectangulo.center = (80, 95)
        # Fundido del panorama
        self.duracion_fundido = 2.0  # Segundos
        self.fundiendo = False
        self.opacidad_fundido = 0
        self.fase_fundido = "salida"
        self.tiempo_fundido = 0

        # Animación de caminar
        self.astro_frame = 0
        self.astro_ultimo_cambio = pygame.time.get_ticks()

        # Fondo del menú
        ruta_assets = os.path.join(
            os.path.dirname(__file__), "..", "assets"
        )

        self.fondo_menu = pygame.image.load(
            os.path.join(ruta_assets, "TitleScene.png")
        ).convert_alpha()

        # Panorama de Marte, sin escalar
        self.parallax = pygame.image.load(
            os.path.join(ruta_assets, "MarsParallax.jpg")
        ).convert()

        self.offset_parallax = self.parallax.get_width() * 0.60
        self.velocidad_parallax = 60

        self.tiempo_anterior = pygame.time.get_ticks()

        # Título
        self.fuente = pygame.font.Font(None, 48)
        self.texto = self.fuente.render(
            "Iniciar partida", True, (255, 255, 255)
        )
        self.boton_rect = self.texto.get_rect()

        # Pie de página
        self.fuente_pie = pygame.font.Font(None, 18)
        self.texto_pie = self.fuente_pie.render(
            "© 2026 - TV2D Facultad de Ingeniería "
            "Tecnólogo en Informática - Desarrollado por Charliexover",
            True,
            (220, 220, 220)
        )
        self.pie_rect = self.texto_pie.get_rect()

        # Fondo parallax
        ruta_fondo = os.path.join(
            os.path.dirname(__file__),
            "..",
            "assets",
            "MarsParallax.jpg"
        )

        

    def update(self, teclas, limites_pantalla, eventos=()):
        ahora = pygame.time.get_ticks()
        dt = (ahora - self.tiempo_anterior) / 1000.0
        self.tiempo_anterior = ahora

        # Animación de caminar sin desplazar a Astro
        if ahora - self.astro_ultimo_cambio >= self.jugador.INTERVALO_PASO:
            self.astro_frame = (self.astro_frame + 1) % len(
                self.jugador.sprites_walk
            )
            self.astro_ultimo_cambio = ahora

        self.jugador.sprite = self.jugador.sprites_walk[self.astro_frame]
        self.jugador.mirando_izquierda = True

        # Desplazamiento y fundido del panorama
        if not self.fundiendo and self.opacidad_fundido < 255:
            self.offset_parallax += self.velocidad_parallax * dt

            # Comenzar el fundido al acercarse al final
            if self.offset_parallax >= self.parallax.get_width() - 100:
                self.fundiendo = True
                self.tiempo_fundido = 0

        if self.fundiendo:
            self.tiempo_fundido += dt

            progreso = min(
                self.tiempo_fundido / self.duracion_fundido,
                1.0
            )

            self.opacidad_fundido = int(255 * progreso)

            if progreso >= 1.0:
                self.opacidad_fundido = 255
                self.fundiendo = False

        # Actualizar posición del botón
        self.boton_rect.center = (
            limites_pantalla.centerx - 150,
            limites_pantalla.centery
        )

        # Detectar clic en iniciar partida
        for evento in eventos:
            if (
                evento.type == pygame.MOUSEBUTTONDOWN
                and evento.button == 1
                and self.boton_rect.collidepoint(evento.pos)
            ):
                self.al_iniciar_partida()
                return
            
    def draw(self, pantalla):
        ancho = pantalla.get_width()
        alto = pantalla.get_height()

        escala_x = ancho / 160
        escala_y = alto / 160

        # Fondo estático
        fondo = pygame.transform.scale(
            self.fondo_menu,
            (ancho, alto)
        )
        pantalla.blit(fondo, (0, 0))

        # Hueco central de 160x64
        zona = pygame.Rect(
            0,
            int(48 * escala_y),
            ancho,
            int(64 * escala_y)
        )

        # Centrar panorama verticalmente sin escalar
        y = zona.y + (zona.height - self.parallax.get_height()) // 2 + 450

        offset = int(self.offset_parallax)

        # Recortar el dibujo al hueco central
        pantalla.set_clip(zona)

        pantalla.blit(
            self.parallax,
            (offset, y)
        )

        pantalla.blit(
            self.parallax,
            (offset - self.parallax.get_width(), y)
        )

        

        # Dibujar a Astro dentro del panorama
        self.jugador.rectangulo.center = (
            ancho // 2 + 90,
            zona.bottom - 70
        )

        self.jugador.dibujar(pantalla)

        # Fundido negro que cubre todo el panorama y a Astro
        if self.opacidad_fundido > 0:
            superficie_negra = pygame.Surface(
                (ancho, zona.height),
                pygame.SRCALPHA
            )

            superficie_negra.fill(
                (0, 0, 0, self.opacidad_fundido)
            )

            pantalla.blit(superficie_negra, zona.topleft)

        pantalla.set_clip(None)
        pantalla.set_clip(None)

        # Título
        self.boton_rect.center = (
            pantalla.get_rect().centerx - 150,
            pantalla.get_rect().centery
        )
        pantalla.blit(self.texto, self.boton_rect)

        # Pie de página
        self.pie_rect.midbottom = (
            pantalla.get_rect().centerx,
            pantalla.get_height() - 1
        )
        pantalla.blit(self.texto_pie, self.pie_rect)
