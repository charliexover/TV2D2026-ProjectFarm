import os

import pygame

from engine.input import obtener_posicion_mouse
from projectFarm.localization import (
    LANGUAGE_SPANISH,
    LocalizedFont,
    get_language,
    toggle_language,
)
from projectFarm.save_slots import SaveSlots

MAX_CARACTERES_NOMBRE = 8
ESCALA_MASCOTA = 7

class SaveSlotsScene:
    POSICIONES_GUARDADOS = (
        (0.20, 0.60),
        (0.45, 0.35),
        (0.75, 0.43),
    )

    def __init__(self, save_slots, al_seleccionar, al_volver, al_cambiar_resolucion,
    resoluciones, al_alternar_pantalla_completa):
        self.save_slots = save_slots
        self.al_seleccionar = al_seleccionar
        self.al_volver = al_volver
        self.al_cambiar_resolucion = al_cambiar_resolucion
        self.resoluciones = resoluciones
        self.al_alternar_pantalla_completa = al_alternar_pantalla_completa
        self.pantalla_completa = False
        self.text_renderer = None
        self.fuente_resolucion = LocalizedFont(None, 22)
        self.fuente_titulo = LocalizedFont(None, 48)
        self.fuente = LocalizedFont(None, 32)
        self.fuente_detalle = LocalizedFont(None, 24)
        ruta_assets = os.path.join(
            os.path.dirname(__file__), "..", "assets"
        )
        self.fondo = pygame.image.load(
            os.path.normpath(os.path.join(ruta_assets, "saveScene.png"))
        ).convert()
        self.sprite_guardado = pygame.image.load(
            os.path.normpath(os.path.join(ruta_assets, "starOFF.png"))
        ).convert_alpha()
        self.sprite_guardado_hover = pygame.image.load(
            os.path.normpath(os.path.join(ruta_assets, "starON.png"))
        ).convert_alpha()
        self.sprite_perro = pygame.transform.scale(
            pygame.image.load(
                os.path.normpath(
                    os.path.join(ruta_assets, "dogSpriteChoice.png")
                )
            ).convert_alpha(),
            (15 * ESCALA_MASCOTA, 15 * ESCALA_MASCOTA),
        )
        self.sprite_gato = pygame.transform.scale(
            pygame.image.load(
                os.path.normpath(
                    os.path.join(ruta_assets, "catSpriteChoice.png")
                )
            ).convert_alpha(),
            (17 * ESCALA_MASCOTA, 15 * ESCALA_MASCOTA),
        )

        self.mensaje = None
        self.boton_volver = pygame.Rect(20, 0, 130, 42)

        # Creación del personaje y su mascota
        self.paso_creacion = 0
        self.slot_nueva_partida = None
        self.nombre_jugador = ""
        self.tipo_mascota = ""
        self.nombre_mascota = ""

        self.rect_nombre = pygame.Rect(0, 0, 400, 45)
        self.boton_perro = pygame.Rect(0, 0, 150, 50)
        self.boton_gato = pygame.Rect(0, 0, 150, 50)

    def obtener_rectangulos(self, limites_pantalla):
        ancho = max(48, round(limites_pantalla.width * 0.1))
        alto = max(48, round(limites_pantalla.height * 0.1))
        return [
            pygame.Rect(
                round(limites_pantalla.width * posicion_x) - ancho // 2,
                round(limites_pantalla.height * posicion_y) - alto // 2,
                ancho,
                alto,
            )
            for posicion_x, posicion_y in self.POSICIONES_GUARDADOS[
                :SaveSlots.CANTIDAD_PARTIDAS
            ]
        ]

    @staticmethod
    def obtener_boton_idioma(limites_pantalla):
        return pygame.Rect(
            limites_pantalla.right - 200,
            limites_pantalla.bottom - 62,
            180,
            42,
        )

    @staticmethod
    def obtener_boton_resolucion(limites_pantalla):
        return pygame.Rect(
            limites_pantalla.right - 200,
            limites_pantalla.bottom - 112,
            180,
            42,
        )

    @staticmethod
    def obtener_boton_pantalla_completa(limites_pantalla):
        return pygame.Rect(
            limites_pantalla.right - 200,
            limites_pantalla.bottom - 162,
            180,
            42,
        )

    @staticmethod
    def _detalle_partida(resumen):
        if resumen["estado"] == "vacia":
            return "Espacio vacío - iniciar guardado nuevo"
        if resumen["estado"] == "guardada":
            return (
                f"Continuar - Día {resumen['dia']} | "
                f"Créditos: {resumen['creditos']}"
            )
        return "Archivo de guardado no disponible"

    @staticmethod
    def _nombre_guardado(resumen, indice):
        if resumen["estado"] == "guardada":
            nombre_jugador = resumen.get("nombre_jugador")
            if isinstance(nombre_jugador, str) and nombre_jugador.strip():
                return nombre_jugador.strip()
        return f"Guardado {indice}"

    def seleccionar(self, slot):
        try:
            resumen = self.save_slots.resumenes()[slot]

            if resumen["estado"] == "vacia":
                self.slot_nueva_partida = slot
                self.nombre_jugador = ""
                self.tipo_mascota = ""
                self.nombre_mascota = ""
                self.paso_creacion = 1
                self.mensaje = None
                return

            # Una partida existente se carga directamente.
            self.al_seleccionar(slot)

        except (OSError, ValueError) as error:
            self.mensaje = f"No se pudo abrir la partida: {error}"

    def cancelar_creacion(self):
        self.paso_creacion = 0
        self.slot_nueva_partida = None
        self.nombre_jugador = ""
        self.tipo_mascota = ""
        self.nombre_mascota = ""
        self.mensaje = None

    def confirmar_nombre_jugador(self):
        nombre = self.nombre_jugador.strip()[:MAX_CARACTERES_NOMBRE]

        if not nombre:
            self.mensaje = "Escribe el nombre de tu personaje."
            return

        self.nombre_jugador = nombre
        self.paso_creacion = 2
        self.mensaje = None

    def elegir_mascota(self, tipo):
        self.tipo_mascota = tipo
        self.paso_creacion = 3
        self.nombre_mascota = "Mars"
        self.mensaje = None

    def confirmar_creacion(self):
        nombre = self.nombre_mascota.strip()[:MAX_CARACTERES_NOMBRE]

        try:
            self.al_seleccionar(
                self.slot_nueva_partida,
                self.nombre_jugador,
                self.tipo_mascota,
                nombre,
            )
            self.cancelar_creacion()

        except (OSError, ValueError) as error:
            self.mensaje = f"No se pudo iniciar la partida: {error}"

    def update(self, teclas, limites_pantalla, eventos=()):
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:

                # Paso 1: nombre del jugador
                if self.paso_creacion == 1:
                    if evento.key == pygame.K_ESCAPE:
                        self.cancelar_creacion()
                    elif evento.key == pygame.K_RETURN:
                        self.confirmar_nombre_jugador()
                    elif evento.key == pygame.K_BACKSPACE:
                        self.nombre_jugador = self.nombre_jugador[:-1]
                    elif (
                        evento.unicode
                        and evento.unicode.isprintable()
                        and len(self.nombre_jugador) < MAX_CARACTERES_NOMBRE
                    ):
                        self.nombre_jugador += evento.unicode
                    continue

                # Paso 2: elegir perro o gato
                if self.paso_creacion == 2:
                    if evento.key == pygame.K_ESCAPE:
                        self.cancelar_creacion()
                    elif evento.key in (pygame.K_1, pygame.K_d):
                        self.elegir_mascota("perro")
                    elif evento.key in (pygame.K_2, pygame.K_g):
                        self.elegir_mascota("gato")
                    continue

                # Paso 3: nombre de la mascota
                if self.paso_creacion == 3:
                    if evento.key == pygame.K_ESCAPE:
                        self.cancelar_creacion()
                    elif evento.key == pygame.K_RETURN:
                        self.confirmar_creacion()
                    elif evento.key == pygame.K_BACKSPACE:
                        self.nombre_mascota = self.nombre_mascota[:-1]
                    elif (
                        evento.unicode
                        and evento.unicode.isprintable()
                        and len(self.nombre_mascota) < MAX_CARACTERES_NOMBRE
                    ):
                        self.nombre_mascota += evento.unicode
                    continue

                # Selector de partidas
                if pygame.K_1 <= evento.key <= pygame.K_3:
                    self.seleccionar(evento.key - pygame.K_1)
                    return

                if evento.key == pygame.K_ESCAPE:
                    self.al_volver()
                    return

            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:

                if self.paso_creacion == 2:
                    if self.boton_perro.collidepoint(evento.pos):
                        self.elegir_mascota("perro")
                    elif self.boton_gato.collidepoint(evento.pos):
                        self.elegir_mascota("gato")
                    elif self.boton_volver.collidepoint(evento.pos):
                        self.cancelar_creacion()
                    continue

                if self.paso_creacion in (1, 3):
                    if self.boton_volver.collidepoint(evento.pos):
                        self.cancelar_creacion()
                    continue

                if self.boton_volver.collidepoint(evento.pos):
                    self.al_volver()
                    return
                
                boton_pantalla_completa = self.obtener_boton_pantalla_completa(
                    limites_pantalla
                )

                if boton_pantalla_completa.collidepoint(evento.pos):
                    self.pantalla_completa = self.al_alternar_pantalla_completa()
                    return
                
                boton_resolucion = self.obtener_boton_resolucion(
                    limites_pantalla
                )

                if boton_resolucion.collidepoint(evento.pos):
                    resolucion_actual = pygame.display.get_window_size()

                    if resolucion_actual in self.resoluciones:
                        indice = self.resoluciones.index(resolucion_actual)
                    else:
                        indice = -1

                    siguiente = (indice + 1) % len(self.resoluciones)

                    self.al_cambiar_resolucion(
                        self.resoluciones[siguiente]
                    )
                    return

                boton_idioma = self.obtener_boton_idioma(
                    limites_pantalla
                )

                if boton_idioma.collidepoint(evento.pos):
                    toggle_language()
                    return

                for slot, rectangulo in enumerate(
                    self.obtener_rectangulos(limites_pantalla)
                ):
                    if rectangulo.collidepoint(evento.pos):
                        self.seleccionar(slot)
                        return

    def dibujar_boton(self, pantalla, rectangulo, texto):
        pygame.draw.rect(pantalla, (35, 35, 35), rectangulo)
        pygame.draw.rect(pantalla, (220, 220, 220), rectangulo, 2)

        self.text_renderer.dibujar_texto(
            self.fuente,
            texto,
            True,
            (255, 255, 255),
            rectangulo.center,
            ancla="center",
        )

    def draw(self, pantalla):
        limites = pantalla.get_rect()
        fondo = pygame.transform.scale(self.fondo, limites.size)
        pantalla.blit(fondo, limites)
        self.boton_volver = pygame.Rect(
            20, limites.bottom - 62, 130, 42
        )
        self.dibujar_boton(
            pantalla, self.boton_volver, "Volver"
        )
        boton_idioma = self.obtener_boton_idioma(limites)
        texto_idioma = (
            "Idioma: Español"
            if get_language() == LANGUAGE_SPANISH
            else "Lang.: English"
        )

        if self.paso_creacion == 0:
            boton_pantalla_completa = self.obtener_boton_pantalla_completa(
                limites
            )

            texto_pantalla_completa = (
                "Pantalla completa: Sí"
                if self.pantalla_completa
                else "Pantalla completa: No"
            )

            color = (
                (75, 75, 75)
                if boton_pantalla_completa.collidepoint(obtener_posicion_mouse())
                else (35, 35, 35)
            )

            pygame.draw.rect(
                pantalla,
                color,
                boton_pantalla_completa,
            )
            pygame.draw.rect(
                pantalla,
                (220, 220, 220),
                boton_pantalla_completa,
                2,
            )

            self.text_renderer.dibujar_texto(
                self.fuente_resolucion,
                texto_pantalla_completa,
                True,
                (255, 255, 255),
                boton_pantalla_completa.center,
                ancla="center",
            )

        self.dibujar_boton(pantalla, boton_idioma, texto_idioma)

        if self.paso_creacion == 0:
            boton_resolucion = self.obtener_boton_resolucion(limites)

            resolucion_actual = pygame.display.get_surface().get_size()
            texto_resolucion = (
                f"Resolución: {resolucion_actual[0]}x{resolucion_actual[1]}"
            )

            posicion_mouse = obtener_posicion_mouse()

            color = (
                (75, 75, 75)
                if boton_resolucion.collidepoint(posicion_mouse)
                else (35, 35, 35)
            )

            pygame.draw.rect(
                pantalla,
                color,
                boton_resolucion,
            )
            pygame.draw.rect(
                pantalla,
                (220, 220, 220),
                boton_resolucion,
                2,
            )

            self.text_renderer.dibujar_texto(
                self.fuente_resolucion,
                texto_resolucion,
                True,
                (255, 255, 255),
                boton_resolucion.center,
                ancla="center",
            )

        self.text_renderer.dibujar_texto(
            self.fuente_titulo,
            "Selecciona un guardado",
            True,
            (255, 255, 255),
            (limites.centerx, 45),
            ancla="midtop",
        )

        resumenes = self.save_slots.resumenes()
        rectangulos_guardados = self.obtener_rectangulos(limites)
        posicion_mouse = obtener_posicion_mouse()
        indice_hover = None
        if self.paso_creacion == 0:
            for indice, (rectangulo, resumen) in enumerate(
                zip(rectangulos_guardados, resumenes),
                start=1,
            ):
                esta_encima = rectangulo.collidepoint(posicion_mouse)
                if esta_encima:
                    indice_hover = indice - 1

                sprite = (
                    self.sprite_guardado_hover
                    if esta_encima
                    else self.sprite_guardado
                )

                tamano_sprite = (
                    max(48, round(limites.height * 0.1)),
                    max(48, round(limites.height * 0.1)),
                )
                sprite = pygame.transform.scale(sprite, tamano_sprite)

                pantalla.blit(
                    sprite, sprite.get_rect(center=rectangulo.center)
                )

                self.text_renderer.dibujar_texto(
                    self.fuente,
                    self._nombre_guardado(resumen, indice),
                    True,
                    (255, 255, 255),
                    (rectangulo.centerx, rectangulo.bottom + 8),
                    ancla="midtop",
                )

        if indice_hover is not None:
            resumen = resumenes[indice_hover]

            panel = pygame.Rect(
                0, 0, min(520, limites.width - 32), 66
            )
            panel.center = (limites.centerx, limites.height - 132)

            fondo_panel = pygame.Surface(panel.size, pygame.SRCALPHA)
            fondo_panel.fill((0, 0, 0, 190))
            pantalla.blit(fondo_panel, panel)

            self.text_renderer.dibujar_texto(
                self.fuente,
                self._nombre_guardado(resumen, indice_hover + 1),
                True,
                (255, 255, 255),
                (panel.centerx, panel.top + 7),
                ancla="midtop",
            )

            self.text_renderer.dibujar_texto(
                self.fuente_detalle,
                self._detalle_partida(resumen),
                True,
                (220, 220, 220),
                (panel.centerx, panel.bottom - 6),
                ancla="midbottom",
            )

        self.text_renderer.dibujar_texto(
            self.fuente_detalle,
            "Haz clic en un guardado.",
            True,
            (230, 230, 230),
            (limites.centerx, limites.bottom - 14),
            ancla="midbottom",
        )

        if self.mensaje and self.paso_creacion == 0:
            self.text_renderer.dibujar_texto(
                self.fuente_detalle,
                self.mensaje,
                True,
                (255, 170, 130),
                (limites.centerx, limites.bottom - 52),
                ancla="midbottom",
            )

        if self.paso_creacion:
            superposicion = pygame.Surface(
                limites.size, pygame.SRCALPHA
            )
            superposicion.fill((0, 0, 0, 190))
            pantalla.blit(superposicion, (0, 0))

            alto_panel = 330 if self.paso_creacion == 2 else 270
            panel = pygame.Rect(0, 0, 500, alto_panel)
            panel.center = limites.center
            pygame.draw.rect(pantalla, (54, 48, 43), panel)
            pygame.draw.rect(
                pantalla, (220, 220, 220), panel, 2
            )

            if self.paso_creacion == 1:
                titulo_texto = "Nombre del jugador"
                valor = self.nombre_jugador

            elif self.paso_creacion == 2:
                titulo_texto = "Elige tu mascota"

            else:
                titulo_texto = "Nombre de tu mascota"
                valor = self.nombre_mascota

            self.text_renderer.dibujar_texto(
                self.fuente_titulo,
                titulo_texto,
                True,
                (255, 255, 255),
                (panel.centerx, panel.top + 20),
                ancla="midtop",
            )

            if self.paso_creacion in (1, 3):
                self.rect_nombre = pygame.Rect(
                    panel.left + 40,
                    panel.top + 115,
                    panel.width - 80,
                    42,
                )
                pygame.draw.rect(
                    pantalla, (30, 30, 30), self.rect_nombre
                )
                pygame.draw.rect(
                    pantalla, (220, 220, 220),
                    self.rect_nombre, 2
                )

                self.text_renderer.dibujar_texto(
                    self.fuente,
                    valor,
                    True,
                    (255, 255, 255),
                    (self.rect_nombre.left + 10, self.rect_nombre.top + 8),
                    ancla="topleft",
                )
                self.text_renderer.dibujar_texto(
                    self.fuente_detalle,
                    f"{len(valor)}/{MAX_CARACTERES_NOMBRE}",
                    True,
                    (200, 200, 200),
                    (self.rect_nombre.right, self.rect_nombre.bottom + 18),
                    ancla="midright",
                )

                ayuda = "Enter: continuar | Escape: cancelar"
                self.text_renderer.dibujar_texto(
                    self.fuente_detalle,
                    ayuda,
                    True,
                    (200, 200, 200),
                    (panel.centerx, panel.bottom - 25),
                    ancla="center",
                )

            elif self.paso_creacion == 2:
                self.boton_perro = pygame.Rect(
                    panel.centerx - 195,
                    panel.top + 115,
                    170,
                    150,
                )
                self.boton_gato = pygame.Rect(
                    panel.centerx + 25,
                    panel.top + 115,
                    170,
                    150,
                )
                posicion_mouse = obtener_posicion_mouse()
                for rectangulo, sprite, etiqueta in (
                    (self.boton_perro, self.sprite_perro, "Perro"),
                    (self.boton_gato, self.sprite_gato, "Gato"),
                ):
                    color = (
                        (100, 92, 75)
                        if rectangulo.collidepoint(posicion_mouse)
                        else (35, 35, 35)
                    )
                    pygame.draw.rect(pantalla, color, rectangulo)
                    pygame.draw.rect(
                        pantalla, (220, 220, 220), rectangulo, 2
                    )
                    pantalla.blit(
                        sprite,
                        sprite.get_rect(
                            center=(rectangulo.centerx, rectangulo.top + 58)
                        ),
                    )
                    self.text_renderer.dibujar_texto(
                        self.fuente,
                        etiqueta,
                        True,
                        (255, 255, 255),
                        (rectangulo.centerx, rectangulo.bottom - 20),
                        ancla="center",
                    )

                ayuda = "Haz clic en una imagen o pulsa 1/2"
                self.text_renderer.dibujar_texto(
                    self.fuente_detalle,
                    ayuda,
                    True,
                    (200, 200, 200),
                    (panel.centerx, panel.bottom - 25),
                    ancla="center",
                )

            if self.mensaje:
                self.text_renderer.dibujar_texto(
                    self.fuente_detalle,
                    self.mensaje,
                    True,
                    (255, 170, 130),
                    (panel.centerx, panel.bottom - 5),
                    ancla="center",
                )