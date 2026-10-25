import pygame

from projectFarm.save_slots import SaveSlots

MAX_CARACTERES_NOMBRE = 8

class SaveSlotsScene:
    def __init__(self, save_slots, al_seleccionar, al_volver):
        self.save_slots = save_slots
        self.al_seleccionar = al_seleccionar
        self.al_volver = al_volver

        self.fuente_titulo = pygame.font.Font(None, 48)
        self.fuente = pygame.font.Font(None, 32)
        self.fuente_detalle = pygame.font.Font(None, 24)

        self.mensaje = None
        self.boton_volver = pygame.Rect(20, 20, 130, 42)

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
        ancho = min(560, limites_pantalla.width - 40)
        alto = 82
        separacion = 14
        inicio_y = (
            limites_pantalla.height - (3 * alto + 2 * separacion)
        ) // 2

        return [
            pygame.Rect(
                (limites_pantalla.width - ancho) // 2,
                inicio_y + slot * (alto + separacion),
                ancho,
                alto,
            )
            for slot in range(SaveSlots.CANTIDAD_PARTIDAS)
        ]

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
        self.nombre_mascota = ""
        self.mensaje = None

    def confirmar_creacion(self):
        nombre = self.nombre_mascota.strip()[:MAX_CARACTERES_NOMBRE]

        if not nombre:
            self.mensaje = "Escribe el nombre de tu mascota."
            return

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

                for slot, rectangulo in enumerate(
                    self.obtener_rectangulos(limites_pantalla)
                ):
                    if rectangulo.collidepoint(evento.pos):
                        self.seleccionar(slot)
                        return

    def dibujar_boton(self, pantalla, rectangulo, texto):
        pygame.draw.rect(pantalla, (35, 35, 35), rectangulo)
        pygame.draw.rect(pantalla, (220, 220, 220), rectangulo, 2)

        superficie = self.fuente.render(
            texto, True, (255, 255, 255)
        )
        pantalla.blit(
            superficie,
            superficie.get_rect(center=rectangulo.center),
        )

    def draw(self, pantalla):
        pantalla.fill((54, 48, 43))
        limites = pantalla.get_rect()

        self.dibujar_boton(
            pantalla, self.boton_volver, "Volver"
        )

        titulo = self.fuente_titulo.render(
            "Selecciona una partida",
            True,
            (255, 255, 255),
        )
        pantalla.blit(
            titulo,
            titulo.get_rect(midtop=(limites.centerx, 45)),
        )

        resumenes = self.save_slots.resumenes()

        for indice, (rectangulo, resumen) in enumerate(
            zip(self.obtener_rectangulos(limites), resumenes),
            start=1,
        ):
            pygame.draw.rect(pantalla, (35, 35, 35), rectangulo)
            pygame.draw.rect(
                pantalla, (220, 220, 220), rectangulo, 2
            )

            titulo_slot = self.fuente.render(
                f"Partida {indice}", True, (255, 255, 255)
            )
            pantalla.blit(
                titulo_slot,
                (rectangulo.left + 16, rectangulo.top + 10),
            )

            if resumen["estado"] == "vacia":
                detalle = "Espacio vacio - iniciar partida nueva"
            elif resumen["estado"] == "guardada":
                detalle = (
                    f"Continuar - Dia {resumen['dia']} | "
                    f"Creditos: {resumen['creditos']}"
                )
            else:
                detalle = "Archivo de guardado no disponible"

            superficie = self.fuente_detalle.render(
                detalle, True, (220, 220, 220)
            )
            pantalla.blit(
                superficie,
                (rectangulo.left + 16, rectangulo.top + 48),
            )

        indicacion = self.fuente_detalle.render(
            "Haz clic en un espacio o pulsa 1, 2 o 3.",
            True,
            (230, 230, 230),
        )
        pantalla.blit(
            indicacion,
            indicacion.get_rect(
                midbottom=(limites.centerx, limites.bottom - 24)
            ),
        )

        if self.mensaje and self.paso_creacion == 0:
            mensaje = self.fuente_detalle.render(
                self.mensaje, True, (255, 170, 130)
            )
            pantalla.blit(
                mensaje,
                mensaje.get_rect(
                    midbottom=(limites.centerx, limites.bottom - 52)
                ),
            )

        if self.paso_creacion:
            superposicion = pygame.Surface(
                limites.size, pygame.SRCALPHA
            )
            superposicion.fill((0, 0, 0, 190))
            pantalla.blit(superposicion, (0, 0))

            panel = pygame.Rect(0, 0, 500, 270)
            panel.center = limites.center
            pygame.draw.rect(pantalla, (54, 48, 43), panel)
            pygame.draw.rect(
                pantalla, (220, 220, 220), panel, 2
            )

            if self.paso_creacion == 1:
                titulo_texto = "Nombre del jugador"
                indicacion_texto = "Escribe tu nombre y pulsa Enter"
                valor = self.nombre_jugador

            elif self.paso_creacion == 2:
                titulo_texto = "Elige tu mascota"
                indicacion_texto = "Selecciona perro o gato"

            else:
                titulo_texto = "Nombre de tu mascota"
                indicacion_texto = (
                    f"Tu mascota sera un {self.tipo_mascota}"
                )
                valor = self.nombre_mascota

            superficie_titulo = self.fuente_titulo.render(
                titulo_texto, True, (255, 255, 255)
            )
            pantalla.blit(
                superficie_titulo,
                superficie_titulo.get_rect(
                    midtop=(panel.centerx, panel.top + 20)
                ),
            )

            superficie_indicacion = self.fuente_detalle.render(
                indicacion_texto, True, (230, 230, 230)
            )
            pantalla.blit(
                superficie_indicacion,
                superficie_indicacion.get_rect(
                    center=(panel.centerx, panel.top + 90)
                ),
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

                superficie_nombre = self.fuente.render(
                    valor, True, (255, 255, 255)
                )
                pantalla.blit(
                    superficie_nombre,
                    (
                        self.rect_nombre.left + 10,
                        self.rect_nombre.top + 8,
                    ),
                )
                contador = self.fuente_detalle.render(
                    f"{len(valor)}/{MAX_CARACTERES_NOMBRE}",
                    True,
                    (200, 200, 200),
                )

                pantalla.blit(
                    contador,
                    contador.get_rect(
                        midright=(
                            self.rect_nombre.right,
                            self.rect_nombre.bottom + 18,
                        )
                    ),
                )

                ayuda = "Enter: continuar | Escape: cancelar"
                superficie_ayuda = self.fuente_detalle.render(
                    ayuda, True, (200, 200, 200)
                )
                pantalla.blit(
                    superficie_ayuda,
                    superficie_ayuda.get_rect(
                        center=(panel.centerx, panel.bottom - 25)
                    ),
                )

            elif self.paso_creacion == 2:
                self.boton_perro = pygame.Rect(
                    panel.centerx - 165,
                    panel.top + 125,
                    150,
                    50,
                )
                self.boton_gato = pygame.Rect(
                    panel.centerx + 15,
                    panel.top + 125,
                    150,
                    50,
                )

                self.dibujar_boton(
                    pantalla, self.boton_perro, "1 - Perro"
                )
                self.dibujar_boton(
                    pantalla, self.boton_gato, "2 - Gato"
                )

                ayuda = "Tambien puedes pulsar D o G"
                superficie_ayuda = self.fuente_detalle.render(
                    ayuda, True, (200, 200, 200)
                )
                pantalla.blit(
                    superficie_ayuda,
                    superficie_ayuda.get_rect(
                        center=(panel.centerx, panel.bottom - 25)
                    ),
                )

            if self.mensaje:
                error = self.fuente_detalle.render(
                    self.mensaje, True, (255, 170, 130)
                )
                pantalla.blit(
                    error,
                    error.get_rect(
                        center=(panel.centerx, panel.bottom - 5)
                    ),
                )