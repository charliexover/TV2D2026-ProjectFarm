import os

import pygame

from projectFarm.localization import LocalizedFont


class EndingScene:
    FRASES = (
        "La misión de la agencia fue un éxito.",
        "A lo largo de los meses,",
        "muchos astronautas empezaron a poblar Marte.",
        "Yo regresé a la Tierra,",
        "mi misión personal no había terminado...",
        "Usé todo el dinero que había ganado",
        " y después de unos días de recuperación, al fin todo había pasado.",
    )
    DURACION_FUNDIDO_TEXTO = 0.75
    DURACION_ESPERA_TEXTO = 1.0
    DURACION_FUNDIDO_FONDO = 1.5
    ESPERA_FRASES_FINALES = 2.0
    DURACION_FRASE_FINAL = 4.0
    INTERVALO_FRAME_MASCOTA = 180
    POSICION_MASCOTA = (38, 73)
    VELOCIDAD_CREDITOS = 25
    CREDITOS = (
        ("CRÉDITOS", "titulo"),
        ("Desarrollo y programación", "seccion"),
        ("Charliexover", "texto"),
        ("Arte y animaciones", "seccion"),
        ("Charliexover", "texto"),
        ("Recursos fotográficos", "seccion"),
        ("Mars in Full View (PIA05049)", "texto"),
        ("NASA / Jet Propulsion Laboratory (JPL) / Cornell University", "texto"),
        ("Fuente: NASA Science Photojournal", "texto"),
        ("Mapa de la superficie de Marte", "texto"),
        ("Fuente: NASA Mars Trek Mars Mapping Portal", "texto"),
        ("NASA / Jet Propulsion Laboratory (JPL)", "texto"),
        ("Herramientas utilizadas", "seccion"),
        ("Libresprite", "texto"),
        ("Tiled", "texto"),
        ("Visual Studio Code", "texto"),
        ("Pygame", "texto"),
        ("Música y sonido", "seccion"),
        ("MarsAndMeIntro, OneDayInMars, OneTormentDayInMars, HappyEnding", "texto"),
        ("Compuestas en OFFBEAT Demo por Charliexover", "texto"),
        ("Efectos de sonido editados con AudioMass - Audio editor", "texto"),
        ("Gracias especiales", "seccion"),
        ("Biogeorge", "texto"),
        ("Remmnt", "texto"),
        ("", "texto"),
        ("", "texto"),
        ("", "texto"),
        ("", "texto"),
        ("", "texto"),
        ("Gracias por jugar", "texto"),
    )

    def __init__(
        self,
        game_state=None,
        posicion_mascota=None,
        al_volver_titulo=None,
    ):
        self.al_volver_titulo = al_volver_titulo
        self.creditos_completados = False
        self.musica_ending_iniciada = False
        self.musica_exterior_iniciada = False
        self.posicion_mascota = (
            self.POSICION_MASCOTA
            if posicion_mascota is None
            else posicion_mascota
        )
        ruta_pets = os.path.join(
            os.path.dirname(__file__), "..", "assets", "pets.png"
        )
        self.fondo_pets = pygame.image.load(
            os.path.normpath(ruta_pets)
        ).convert()
        ruta_titulo = os.path.join(
            os.path.dirname(__file__), "..", "assets", "TitleScene.png"
        )
        self.imagen_titulo = pygame.image.load(
            os.path.normpath(ruta_titulo)
        ).convert_alpha()
        self.titulo_escalado = None
        self.tamano_pantalla_titulo = None
        tipo_mascota = getattr(game_state, "tipo_mascota", "perro")
        nombre_mascota = (
            getattr(game_state, "nombre_mascota", None) or "mi mascota"
        )
        frases_finales = (
            "A partir de ahora, queda disfrutar",
            f"Solo {nombre_mascota} y yo",
        )
        nombre_sprite = (
            "catSprites.png"
            if tipo_mascota == "gato"
            else "dogSprites.png"
        )
        ruta_mascota = os.path.join(
            os.path.dirname(__file__), "..", "assets", nombre_sprite
        )
        spritesheet_mascota = pygame.image.load(
            os.path.normpath(ruta_mascota)
        ).convert_alpha()
        self.frames_mascota = [
            pygame.transform.scale(
                spritesheet_mascota.subsurface(
                    pygame.Rect(indice * 26, 0, 26, 38)
                ),
                (78, 114),
            )
            for indice in range(spritesheet_mascota.get_width() // 26)
        ]
        self.fuente = LocalizedFont(None, 36)
        self.fuentes_creditos = {
            "titulo": LocalizedFont(None, 48),
            "seccion": LocalizedFont(None, 36),
            "texto": LocalizedFont(None, 30),
        }
        self.superficies_creditos = [
            (
                self.fuentes_creditos[estilo].render(
                    texto, True, (255, 255, 255)
                ),
                34 if estilo == "titulo" else 18 if estilo == "seccion" else 50,
            )
            for texto, estilo in self.CREDITOS
        ]
        self.alto_creditos = sum(
            superficie.get_height() + espacio
            for superficie, espacio in self.superficies_creditos
        )
        self.superficies_frases = [
            self._renderizar_frase(frase)
            for frase in self.FRASES
        ]
        self.superficies_frases_finales = [
            self._renderizar_frase(frase) for frase in frases_finales
        ]
        self.inicio = pygame.time.get_ticks()
        self.tiempo_transcurrido = 0.0
        self.fondo_escalado = None
        self.tamano_pantalla_fondo = None
        self.duracion_frase = (
            self.DURACION_FUNDIDO_TEXTO * 2
            + self.DURACION_ESPERA_TEXTO
        )
        self.duracion_secuencia = len(self.FRASES) * self.duracion_frase
        self.inicio_frases_finales = (
            self.duracion_secuencia
            + self.DURACION_FUNDIDO_FONDO
            + self.ESPERA_FRASES_FINALES
        )
        self.inicio_titulo = (
            self.inicio_frases_finales
            + len(self.superficies_frases_finales) * self.DURACION_FRASE_FINAL
        )
        self.inicio_creditos = self.inicio_titulo

    def _iniciar_musica_ending(self):
        ruta_musica = os.path.join(
            os.path.dirname(__file__), "..", "sounds", "HappyEnding.wav"
        )
        pygame.mixer.music.load(os.path.normpath(ruta_musica))
        pygame.mixer.music.play()
        self.musica_ending_iniciada = True

    def _iniciar_musica_exterior(self):
        ruta_musica = os.path.join(
            os.path.dirname(__file__), "..", "sounds", "OneDayInMars.wav"
        )
        pygame.mixer.music.load(os.path.normpath(ruta_musica))
        pygame.mixer.music.play(-1)
        self.musica_exterior_iniciada = True

    def _renderizar_frase(self, frase):
        alto_linea = self.fuente.get_linesize()
        lineas = [
            self.fuente.render(linea, True, (255, 255, 255))
            for linea in frase.splitlines()
        ]
        superficie = pygame.Surface(
            (
                max(linea.get_width() for linea in lineas),
                len(lineas) * alto_linea,
            ),
            pygame.SRCALPHA,
        )
        for indice, linea in enumerate(lineas):
            superficie.blit(
                linea,
                linea.get_rect(
                    midtop=(
                        superficie.get_width() // 2,
                        indice * alto_linea,
                    )
                ),
            )
        return superficie

    def update(self, teclas, limites_pantalla, eventos=()):
        self.tiempo_transcurrido = max(
            0.0,
            (pygame.time.get_ticks() - self.inicio) / 1000.0,
        )
        if not self.musica_ending_iniciada:
            self._iniciar_musica_ending()
        elif (
            not self.musica_exterior_iniciada
            and not pygame.mixer.music.get_busy()
        ):
            self._iniciar_musica_exterior()
        if self.tiempo_transcurrido >= self.inicio_titulo:
            desplazamiento_final = self._desplazamiento_final_creditos(
                limites_pantalla.height
            )
            tiempo_hasta_final = (
                desplazamiento_final / self.VELOCIDAD_CREDITOS
            )
            self.creditos_completados = (
                self.tiempo_transcurrido
                >= self.inicio_creditos + tiempo_hasta_final
            )
        if self.creditos_completados and self.al_volver_titulo is not None:
            if any(
                evento.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN)
                for evento in eventos
            ):
                self.al_volver_titulo()

    def _desplazamiento_final_creditos(self, alto_pantalla):
        superficie_final, _ = self.superficies_creditos[-1]
        alto_previo = sum(
            superficie.get_height() + espacio
            for superficie, espacio in self.superficies_creditos[:-1]
        )
        return (
            alto_pantalla + alto_previo
            - (alto_pantalla - superficie_final.get_height()) / 2
        )

    def _obtener_fondo_escalado(self, tamano):
        if self.tamano_pantalla_fondo != tamano:
            escala = min(
                tamano[0] / self.fondo_pets.get_width(),
                tamano[1] / self.fondo_pets.get_height(),
            )
            tamano_fondo = (
                round(self.fondo_pets.get_width() * escala),
                round(self.fondo_pets.get_height() * escala),
            )
            self.fondo_escalado = pygame.transform.scale(
                self.fondo_pets, tamano_fondo
            )
            self.tamano_pantalla_fondo = tamano
        posicion = self.fondo_escalado.get_rect(
            center=(tamano[0] // 2, tamano[1] // 2)
        )
        return self.fondo_escalado, posicion

    def _obtener_titulo_escalado(self, tamano):
        if self.tamano_pantalla_titulo != tamano:
            escala = min(
                tamano[0] / self.imagen_titulo.get_width(),
                tamano[1] / self.imagen_titulo.get_height(),
            )
            tamano_titulo = (
                round(self.imagen_titulo.get_width() * escala),
                round(self.imagen_titulo.get_height() * escala),
            )
            self.titulo_escalado = pygame.transform.scale(
                self.imagen_titulo, tamano_titulo
            )
            self.tamano_pantalla_titulo = tamano
        posicion = self.titulo_escalado.get_rect(
            center=(tamano[0] // 2, tamano[1] // 2)
        )
        return self.titulo_escalado, posicion

    def draw(self, pantalla):
        pantalla.fill((0, 0, 0))
        tiempo = self.tiempo_transcurrido

        if tiempo < self.duracion_secuencia:
            indice_frase = min(
                int(tiempo / self.duracion_frase),
                len(self.superficies_frases) - 1,
            )
            tiempo_frase = tiempo - indice_frase * self.duracion_frase
            if tiempo_frase < self.DURACION_FUNDIDO_TEXTO:
                opacidad = int(
                    255 * tiempo_frase / self.DURACION_FUNDIDO_TEXTO
                )
            elif tiempo_frase < (
                self.DURACION_FUNDIDO_TEXTO
                + self.DURACION_ESPERA_TEXTO
            ):
                opacidad = 255
            else:
                progreso = (
                    tiempo_frase
                    - self.DURACION_FUNDIDO_TEXTO
                    - self.DURACION_ESPERA_TEXTO
                ) / self.DURACION_FUNDIDO_TEXTO
                opacidad = int(255 * (1 - progreso))

            texto = self.superficies_frases[indice_frase]
            texto.set_alpha(max(0, min(255, opacidad)))
            pantalla.blit(texto, texto.get_rect(center=pantalla.get_rect().center))
            return

        tiempo_fondo = tiempo - self.duracion_secuencia
        opacidad_fondo = min(
            255,
            int(255 * tiempo_fondo / self.DURACION_FUNDIDO_FONDO),
        )
        fondo, posicion_fondo = self._obtener_fondo_escalado(
            pantalla.get_size()
        )
        fondo.set_alpha(opacidad_fondo)
        pantalla.blit(fondo, posicion_fondo)
        indice_frame = (
            int(tiempo_fondo * 1000 / self.INTERVALO_FRAME_MASCOTA)
            % len(self.frames_mascota)
        )
        mascota = self.frames_mascota[indice_frame]
        mascota.set_alpha(opacidad_fondo)
        centro_mascota = (
            posicion_fondo.left
            + round(
                self.posicion_mascota[0]
                * posicion_fondo.width
                / self.fondo_pets.get_width()
            ),
            posicion_fondo.top
            + round(
                self.posicion_mascota[1]
                * posicion_fondo.height
                / self.fondo_pets.get_height()
            ),
        )
        pantalla.blit(
            mascota,
            mascota.get_rect(center=centro_mascota),
        )
        if self.inicio_frases_finales <= tiempo < self.inicio_titulo:
            indice_frase = int(
                (tiempo - self.inicio_frases_finales)
                / self.DURACION_FRASE_FINAL
            )
            texto = self.superficies_frases_finales[indice_frase]
            pantalla.blit(texto, texto.get_rect(center=pantalla.get_rect().center))
        elif tiempo >= self.inicio_titulo:
            titulo, posicion_titulo = self._obtener_titulo_escalado(
                pantalla.get_size()
            )
            pantalla.blit(titulo, posicion_titulo)
            desplazamiento = min(
                (tiempo - self.inicio_creditos) * self.VELOCIDAD_CREDITOS,
                self._desplazamiento_final_creditos(
                    pantalla.get_height()
                ),
            )
            y = pantalla.get_height() - desplazamiento
            for superficie, espacio in self.superficies_creditos:
                rectangulo = superficie.get_rect(
                    midtop=(pantalla.get_width() // 2, round(y))
                )
                if rectangulo.bottom >= 0 and rectangulo.top < pantalla.get_height():
                    pantalla.blit(superficie, rectangulo)
                y += superficie.get_height() + espacio