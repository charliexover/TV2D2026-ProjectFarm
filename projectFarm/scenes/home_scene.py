
import os

import pygame

from engine.audio import reproducir_sonido_interaccion
from engine.spritesheet import Spritesheet
from engine.ui import InterfazEstado
from projectFarm.entities import Jugador
from projectFarm.farm import CULTIVOS
from projectFarm.mails import GestorCorreos


class HomeScene:
    DURACION_ANIMACION_SUENO = 1800
    DURACION_FUNDIDO = 800
    DURACION_CARTEL_DIA = 2100
    INTERVALO_FRAME_SUENO = 250
    PRECIOS_SEMILLAS = {
        1: 2,
        2: 5,
        3: 7,
        4: 10,
    }

    def __init__(self, game_state, inventario, al_salir_casa, al_avanzar_dia):
        self.name = "Home Scene"
        self.game_state = game_state
        self.gestor_correos = GestorCorreos(game_state)
        self.gestor_correos.actualizar_dia(game_state.dia_actual)
        self.correo_seleccionado = None
        self.interfaz_estado = InterfazEstado()
        self.jugador = Jugador()
        self.primera_entrada = True
        self.primera_visita = True
        self.al_salir_casa = al_salir_casa
        self.al_avanzar_dia = al_avanzar_dia
        self.tamano_cama = (96, 48)
        self.tamano_salida = (70, 50)
        self.tamano_pc = (50, 70)
        self.cuadrados = [
            pygame.Rect(195, 160, 10, 340),
            pygame.Rect(130, 165, 550, 10),
            pygame.Rect(595, 160, 10, 340),
            pygame.Rect(200, 495, 95, 10),
            pygame.Rect(360, 495, 300, 10),
        ]
        self.colores_cuadrados = [(255, 120, 120), (120, 200, 255), (120, 255, 170), (255, 210, 120), (255, 210, 120)]
        self.fuente = pygame.font.Font(None, 28)
        self.fuente_menu_pc = pygame.font.Font(None, 26)
        self.menu_pc = None
        self.mensaje_pc = None
        self.mensaje_pc_hasta = 0
        self.inventario = inventario
        self.fondo = self._cargar_fondo()
        ruta_sueno = os.path.join(
            os.path.dirname(__file__), "..", "utils", "AstroSleeping.json"
        )
        spritesheet_sueno = Spritesheet(ruta_sueno)
        self.sprites_sueno = [
            pygame.transform.scale(sprite, (48, 60))
            for sprite in spritesheet_sueno.get_animation_frames("default")
        ]
        ruta_musica_sueno = os.path.join(
            os.path.dirname(__file__), "..", "assets", "SleepSong.wav"
        )
        self.musica_sueno = pygame.mixer.Sound(
            os.path.normpath(ruta_musica_sueno)
        )
        self.canal_musica_sueno = None
        self.transicion_sueno_inicio = None
        self.dia_mostrado = None
        self.dia_avanzado_durante_sueno = False
        
        self.mensaje_guardado = None
        self.mensaje_guardado_hasta = 0
        self.mensaje_desmayo = None
        self.mensaje_desmayo_hasta = 0

   

    def _cargar_fondo(self):
        ruta_fondo = os.path.join(
            os.path.dirname(__file__), "..", "assets", "spritesheetInterior1.png"
        )
        try:
            fondo = pygame.image.load(ruta_fondo).convert()
            return pygame.transform.scale(
                fondo,
                (fondo.get_width() * 3, fondo.get_height() * 3),
            )
        except (FileNotFoundError, pygame.error):
            return None

    def obtener_cama(self, limites_pantalla):
        cama = pygame.Rect(0, 0, self.tamano_cama[0], self.tamano_cama[1])
        cama.center = (545,230)
        return cama

    def obtener_area_interaccion_cama(self, limites_pantalla):
        return self.obtener_cama(limites_pantalla).inflate(20, 20)

    def obtener_salida(self, limites_pantalla):
        salida = pygame.Rect(0, 0, *self.tamano_salida)
        salida.center = (330, 520)
        return salida

    def obtener_posicion_entrada(self, limites_pantalla):
        salida = self.obtener_salida(limites_pantalla)
        posicion = self.jugador.rectangulo.copy()
        posicion.midbottom = (salida.centerx, salida.top - 8)
        return posicion

    def obtener_pc(self, limites_pantalla):
        pc = pygame.Rect(0, 0, *self.tamano_pc)
        pc.center = (425, 150)
        return pc

    def vender_zanahorias(self):
        creditos = 0
        for cultivo in CULTIVOS.values():
            atributo_cosecha = cultivo["cosecha"]
            cantidad = getattr(self.game_state, atributo_cosecha)
            creditos += cantidad * cultivo["precio_venta"]
            setattr(self.game_state, atributo_cosecha, 0)
        self.game_state.creditos += creditos
        return creditos

    def _obtener_semillas_disponibles(self):
        semillas = []
        for tipo_cultivo, cultivo in CULTIVOS.items():
            if tipo_cultivo == 1:
                semillas.append((tipo_cultivo, cultivo))
                continue

            desbloqueo = self.inventario.DESBLOQUEOS_SEMILLAS.get(
                tipo_cultivo
            )
            if desbloqueo is not None and getattr(
                self.game_state, desbloqueo
            ):
                semillas.append((tipo_cultivo, cultivo))
        return semillas

    def _obtener_rectangulo_menu_pc(self, limites_pantalla):
        if self.menu_pc == "leer_correo":
            alto = 360
        elif self.menu_pc == "correos":
            filas = len(self.gestor_correos.obtener_correos()) + 1
            alto = 136 + max(filas, 1) * 44
        elif self.menu_pc == "principal":
            filas = 3
            alto = 136 + filas * 44
        else:
            filas = len(self._obtener_semillas_disponibles()) + 1
            alto = 136 + filas * 44

        alto = min(alto, limites_pantalla.height - 20)

        return pygame.Rect(
            0,
            0,
            480,
            alto,
        ).move(
            limites_pantalla.centerx - 240,
            limites_pantalla.centery - alto // 2,
        )

    def _obtener_opciones_menu_pc(self):
        if self.menu_pc == "principal":
            return [
                ("Comprar semillas", "comprar"),
                ("Vender cosechas", "vender"),
                (
                    f"Leer correos ({self.gestor_correos.cantidad_no_leidos()})",
                    "correos",
                ),
            ]

        if self.menu_pc == "correos":
            opciones = []

            for correo in self.gestor_correos.obtener_correos():
                identificador = correo["id"]

                indicador = (
                    "[Nuevo] "
                    if not self.gestor_correos.esta_leido(identificador)
                    else ""
                )

                opciones.append(
                    (
                        f"{indicador}{correo['asunto']}",
                        f"correo:{identificador}",
                    )
                )

            if not opciones:
                opciones.append(("No tienes correos", "sin_correos"))

            opciones.append(("Volver", "volver"))
            return opciones

        if self.menu_pc == "leer_correo":
            return [
                ("Volver a la bandeja", "volver_bandeja"),
            ]

        opciones = [
            (
                f"{cultivo['nombre'].capitalize()} - "
                f"{self.PRECIOS_SEMILLAS[tipo]} cr. "
                f"(tienes {getattr(self.game_state, cultivo['semilla'])})",
                tipo,
            )
            for tipo, cultivo in self._obtener_semillas_disponibles()
        ]

        opciones.append(("Volver", "volver"))
        return opciones

    def _obtener_rectangulos_opciones_menu_pc(self, limites_pantalla):
        rect_dialogo = self._obtener_rectangulo_menu_pc(limites_pantalla)
        return [
            (
                accion,
                pygame.Rect(
                    rect_dialogo.left + 24,
                    rect_dialogo.top + 64 + indice * 44,
                    rect_dialogo.width - 48,
                    36,
                ),
            )
            for indice, (_, accion) in enumerate(
                self._obtener_opciones_menu_pc()
            )
        ]

    def _procesar_click_menu_pc(self, posicion, limites_pantalla):
        if self.menu_pc == "leer_correo":
            rect_dialogo = self._obtener_rectangulo_menu_pc(
                limites_pantalla
            )

            rect_volver = pygame.Rect(
                rect_dialogo.left + 24,
                rect_dialogo.bottom - 52,
                rect_dialogo.width - 48,
                36,
            )

            if rect_volver.collidepoint(posicion):
                self.menu_pc = "correos"
                self.correo_seleccionado = None

            return
        for accion, rectangulo in self._obtener_rectangulos_opciones_menu_pc(
            limites_pantalla
        ):
            if not rectangulo.collidepoint(posicion):
                continue

            if accion == "comprar":
                self.menu_pc = "semillas"
                self.mensaje_pc = None

            elif accion == "vender":
                creditos = self.vender_zanahorias()
                self._mostrar_mensaje_pc(
                    f"Cosechas vendidas por {creditos} créditos."
                    if creditos
                    else "No tienes cosechas para vender."
                )
                self.menu_pc = None

            elif accion == "correos":
                self.menu_pc = "correos"
                self.mensaje_pc = None

            elif isinstance(accion, str) and accion.startswith("correo:"):
                identificador = accion.split(":", 1)[1]

                self.correo_seleccionado = next(
                    (
                        correo
                        for correo in self.gestor_correos.obtener_correos()
                        if correo["id"] == identificador
                    ),
                    None,
                )

                if self.correo_seleccionado is not None:
                    self.gestor_correos.marcar_leido(identificador)
                    self.menu_pc = "leer_correo"

            elif accion == "volver_bandeja":
                self.menu_pc = "correos"
                self.correo_seleccionado = None

            elif accion == "sin_correos":
                pass

            elif accion == "volver":
                if self.menu_pc == "semillas":
                    self.menu_pc = "principal"
                elif self.menu_pc == "correos":
                    self.menu_pc = "principal"

                self.mensaje_pc = None

            else:
                self._comprar_semilla(accion)

            return

    def _comprar_semilla(self, tipo_cultivo):
        cultivo = CULTIVOS[tipo_cultivo]
        if tipo_cultivo != 1:
            desbloqueo = self.inventario.DESBLOQUEOS_SEMILLAS.get(
                tipo_cultivo
            )
            if desbloqueo is None or not getattr(
                self.game_state, desbloqueo
            ):
                self.mensaje_pc = "Esa semilla todavía está bloqueada."
                return

        precio = self.PRECIOS_SEMILLAS[tipo_cultivo]
        if self.game_state.creditos < precio:
            self._mostrar_mensaje_pc("No tienes créditos suficientes.")
            return

        self.game_state.creditos -= precio
        atributo_semilla = cultivo["semilla"]
        setattr(
            self.game_state,
            atributo_semilla,
            getattr(self.game_state, atributo_semilla) + 1,
        )
        self._mostrar_mensaje_pc(
            f"Compraste una semilla de {cultivo['nombre']} por "
            f"{precio} créditos."
        )

    def _mostrar_mensaje_pc(self, mensaje):
        self.mensaje_pc = mensaje
        self.mensaje_pc_hasta = pygame.time.get_ticks() + 4000

    def dibujar_menu_pc(self, pantalla):
        limites_pantalla = pantalla.get_rect()
        rect_dialogo = self._obtener_rectangulo_menu_pc(limites_pantalla)
        pygame.draw.rect(pantalla, (0, 0, 0), rect_dialogo)
        pygame.draw.rect(pantalla, (255, 255, 255), rect_dialogo, 2)

        if self.menu_pc == "principal":
            titulo = "Terminal de la colonia"
        elif self.menu_pc == "semillas":
            titulo = "Comprar semillas"
        elif self.menu_pc == "correos":
            titulo = "Bandeja de entrada"
        else:
            titulo = "Correo"
        texto_titulo = self.fuente.render(titulo, True, (255, 255, 255))
        if self.menu_pc == "leer_correo":
            self.dibujar_correo_seleccionado(
                pantalla,
                rect_dialogo,
            )

            rect_volver = pygame.Rect(
                rect_dialogo.left + 24,
                rect_dialogo.bottom - 52,
                rect_dialogo.width - 48,
                36,
            )

            pygame.draw.rect(
                pantalla,
                (30, 35, 45),
                rect_volver,
            )
            pygame.draw.rect(
                pantalla,
                (220, 220, 220),
                rect_volver,
                1,
            )

            texto_volver = self.fuente_menu_pc.render(
                "Volver a la bandeja",
                True,
                (255, 255, 255),
            )

            pantalla.blit(
                texto_volver,
                texto_volver.get_rect(center=rect_volver.center),
            )

            
            return

        opciones = self._obtener_opciones_menu_pc()
        rectangulos = self._obtener_rectangulos_opciones_menu_pc(
            limites_pantalla
        )
        for (etiqueta, _), (_, rectangulo) in zip(opciones, rectangulos):
            color = (
                (55, 55, 55)
                if rectangulo.collidepoint(pygame.mouse.get_pos())
                else (30, 35, 45)
            )
            pygame.draw.rect(pantalla, color, rectangulo)
            pygame.draw.rect(pantalla, (220, 220, 220), rectangulo, 1)
            texto = self.fuente_menu_pc.render(
                etiqueta, True, (255, 255, 255)
            )
            pantalla.blit(
                texto,
                texto.get_rect(center=rectangulo.center),
            )

        instruccion = self.fuente_menu_pc.render(
            "E o Esc: cerrar / volver", True, (190, 190, 190)
        )
        pantalla.blit(
            instruccion,
            instruccion.get_rect(
                midbottom=(rect_dialogo.centerx, rect_dialogo.bottom - 8)
            ),
        )

        if (
            self.mensaje_pc is not None
            and pygame.time.get_ticks() < self.mensaje_pc_hasta
        ):
            mensaje = self.fuente_menu_pc.render(
                self.mensaje_pc, True, (255, 235, 150)
            )
            pantalla.blit(
                mensaje,
                mensaje.get_rect(
                    midbottom=(rect_dialogo.centerx, rect_dialogo.bottom - 38)
                ),
            )

    def dibujar_correo_seleccionado(self, pantalla, rect_dialogo):
        correo = self.correo_seleccionado

        if correo is None:
            return

        color_texto = (255, 255, 255)
        margen = 24
        ancho_texto = rect_dialogo.width - margen * 2

        remitente = self.fuente_menu_pc.render(
            f"De: {correo['remitente']}",
            True,
            (180, 210, 255),
        )

        pantalla.blit(
            remitente,
            (rect_dialogo.left + margen, rect_dialogo.top + 65),
        )

        asunto = self.fuente_menu_pc.render(
            correo["asunto"],
            True,
            color_texto,
        )

        pantalla.blit(
            asunto,
            (rect_dialogo.left + margen, rect_dialogo.top + 95),
        )

        pygame.draw.line(
            pantalla,
            (100, 100, 100),
            (rect_dialogo.left + margen, rect_dialogo.top + 125),
            (rect_dialogo.right - margen, rect_dialogo.top + 125),
        )

        y = rect_dialogo.top + 140
        alto_linea = self.fuente_menu_pc.get_linesize()

        for parrafo in correo["mensaje"].split("\n"):
            if not parrafo:
                y += alto_linea
                continue

            palabras = parrafo.split()
            linea_actual = ""

            for palabra in palabras:
                prueba = (
                    f"{linea_actual} {palabra}"
                    if linea_actual
                    else palabra
                )

                if (
                    self.fuente_menu_pc.size(prueba)[0] > ancho_texto
                    and linea_actual
                ):
                    superficie = self.fuente_menu_pc.render(
                        linea_actual,
                        True,
                        color_texto,
                    )
                    pantalla.blit(
                        superficie,
                        (rect_dialogo.left + margen, y),
                    )
                    y += alto_linea
                    linea_actual = palabra
                else:
                    linea_actual = prueba

            if linea_actual:
                superficie = self.fuente_menu_pc.render(
                    linea_actual,
                    True,
                    color_texto,
                )
                pantalla.blit(
                    superficie,
                    (rect_dialogo.left + margen, y),
                )
                y += alto_linea

            y += 5

    def dibujar_mensaje_pc(self, pantalla):
        mensaje = self.fuente.render(
            self.mensaje_pc, True, (255, 255, 255)
        )
        cuadro = mensaje.get_rect(
            midtop=(pantalla.get_width() // 2, 64)
        ).inflate(24, 16)
        pygame.draw.rect(pantalla, (0, 0, 0), cuadro)
        pygame.draw.rect(pantalla, (255, 255, 255), cuadro, 2)
        pantalla.blit(mensaje, mensaje.get_rect(center=cuadro.center))

    @property
    def duracion_transicion_sueno(self):
        return (
            self.DURACION_ANIMACION_SUENO
            + self.DURACION_FUNDIDO * 2
            + self.DURACION_CARTEL_DIA
        )

    def iniciar_sueno(self):
        self.transicion_sueno_inicio = pygame.time.get_ticks()
        self.dia_avanzado_durante_sueno = False
        self.canal_musica_sueno = self.musica_sueno.play()

    def actualizar_sueno(self):
        inicio_sueno = self.transicion_sueno_inicio
        if inicio_sueno is None:
            return
        tiempo_transcurrido = pygame.time.get_ticks() - inicio_sueno
        inicio_cartel_dia = (
            self.DURACION_ANIMACION_SUENO + self.DURACION_FUNDIDO
        )
        if (
            tiempo_transcurrido >= inicio_cartel_dia
            and not self.dia_avanzado_durante_sueno
        ):
            self.mensaje_guardado = self.al_avanzar_dia()
            self.gestor_correos.actualizar_dia(
            self.game_state.dia_actual
            )
            self.mensaje_guardado_hasta = pygame.time.get_ticks() + 5000
            self.dia_mostrado = self.game_state.dia_actual
            self.dia_avanzado_durante_sueno = True

        if tiempo_transcurrido >= self.duracion_transicion_sueno:
            if self.canal_musica_sueno is not None:
                self.canal_musica_sueno.stop()
            self.canal_musica_sueno = None
            self.transicion_sueno_inicio = None

    def update(self, teclas, limites_pantalla, eventos=()):
        if self.transicion_sueno_inicio is not None:
            self.actualizar_sueno()
            return

        if self.menu_pc is not None:
            for evento in eventos:
                if evento.type == pygame.KEYDOWN and evento.key in (
                    pygame.K_ESCAPE,
                    pygame.K_e,
                ):
                    if self.menu_pc == "semillas":
                        self.menu_pc = "principal"
                        self.mensaje_pc = None

                    elif self.menu_pc == "correos":
                        self.menu_pc = "principal"
                        self.mensaje_pc = None

                    elif self.menu_pc == "leer_correo":
                        self.menu_pc = "correos"
                        self.correo_seleccionado = None

                    else:
                        self.menu_pc = None

                    return
                if (
                    evento.type == pygame.MOUSEBUTTONDOWN
                    and evento.button == 1
                ):
                    self._procesar_click_menu_pc(
                        evento.pos, limites_pantalla
                    )
                    return
            return

        

        if self.primera_entrada:
            if self.primera_visita:
                self.jugador.rectangulo.center = (
                    limites_pantalla.centerx,
                    limites_pantalla.centery + 30,
                )
                self.primera_visita = False
            else:
                self.jugador.rectangulo = self.obtener_posicion_entrada(
                    limites_pantalla
                )

            self.primera_entrada = False

        # Movimiento del jugador: se ejecuta en cada actualización.
        rect_previo = self.jugador.rectangulo.copy()
        self.jugador.actualizar(teclas)
        self.jugador.rectangulo.clamp_ip(limites_pantalla)

        cama = self.obtener_cama(limites_pantalla)

        for cuadrado in [*self.cuadrados, cama]:
            if self.jugador.rectangulo.colliderect(cuadrado):
                self.jugador.rectangulo = rect_previo
                break
            self.jugador.rectangulo.clamp_ip(limites_pantalla)

            cama = self.obtener_cama(limites_pantalla)

            for cuadrado in [*self.cuadrados, cama]:
                if self.jugador.rectangulo.colliderect(cuadrado):
                    self.jugador.rectangulo = rect_previo
                    break
        salida = self.obtener_salida(limites_pantalla)
        if self.jugador.rectangulo.colliderect(salida):
            self.primera_entrada = True
            self.al_salir_casa()
            return
        
        area_interaccion_cama = self.obtener_area_interaccion_cama(
            limites_pantalla
        )
        for evento in eventos:
            if evento.type != pygame.KEYDOWN:
                continue
            if evento.key != pygame.K_e:
                continue
            if self.jugador.rectangulo.colliderect(area_interaccion_cama):
                reproducir_sonido_interaccion()
                self.iniciar_sueno()

            elif self.jugador.rectangulo.colliderect(
                self.obtener_pc(limites_pantalla)
            ):
                reproducir_sonido_interaccion()
                self.menu_pc = "principal"
                self.mensaje_pc = None

    def draw(self, pantalla):
        pantalla.fill((0, 0, 0))
        limites_pantalla = pantalla.get_rect()
        if self.fondo is not None:
            pantalla.blit(self.fondo, self.fondo.get_rect(center=limites_pantalla.center))
        else:
            pantalla.fill((99, 60, 58))

        #for i, cuadrado in enumerate(self.cuadrados):
            #pygame.draw.rect(pantalla, self.colores_cuadrados[i], cuadrado)
            #pygame.draw.rect(pantalla, (30, 30, 30), cuadrado, 2)

        self.interfaz_estado.dibujar(pantalla, self.game_state)
        
        salida = self.obtener_salida(limites_pantalla)
        #pygame.draw.rect(pantalla, (120, 255, 120), salida)
        pc = self.obtener_pc(limites_pantalla)
        #pygame.draw.rect(pantalla, (95, 125, 135), pc)
        #pygame.draw.rect(pantalla, (60, 45, 30), pc, 3)

        
        if self.transicion_sueno_inicio is None:
            self.jugador.dibujar(pantalla)
        else:
            tiempo_transcurrido = (
                pygame.time.get_ticks() - self.transicion_sueno_inicio
            )
            if tiempo_transcurrido < (
                self.DURACION_ANIMACION_SUENO + self.DURACION_FUNDIDO
            ):
                indice_sprite = (
                    tiempo_transcurrido // self.INTERVALO_FRAME_SUENO
                ) % len(self.sprites_sueno)
                sprite_sueno = self.sprites_sueno[indice_sprite]
                cama = self.obtener_cama(limites_pantalla)
                pantalla.blit(
                    sprite_sueno,
                    sprite_sueno.get_rect(
                        center=(cama.centerx - 10, cama.centery - 25)
                    ),
                )
        if self.transicion_sueno_inicio is None:
            if self.menu_pc is not None:
                self.dibujar_menu_pc(pantalla)
            elif self.mensaje_pc is not None and pygame.time.get_ticks() < self.mensaje_pc_hasta:
                self.dibujar_mensaje_pc(pantalla)
            elif self.jugador.rectangulo.colliderect(
                self.obtener_area_interaccion_cama(limites_pantalla)
            ):
                indicacion = self.fuente.render(
                    "E: avanzar dia", True, (255, 255, 255)
                )
                pantalla.blit(
                    indicacion,
                    indicacion.get_rect(
                        midtop=(pantalla.get_width() // 2, 20)
                    ),
                )
            elif self.jugador.rectangulo.colliderect(salida):
                indicacion = self.fuente.render(
                    "Salida automatica", True, (255, 255, 255)
                )
                pantalla.blit(
                    indicacion,
                    indicacion.get_rect(
                        midtop=(pantalla.get_width() // 2, 20)
                    ),
                )
            elif self.jugador.rectangulo.colliderect(pc):
                indicacion = self.fuente.render(
                    "E: interactuar con la PC",
                    True,
                    (255, 255, 255),
                )
                pantalla.blit(
                    indicacion,
                    indicacion.get_rect(
                        midtop=(pantalla.get_width() // 2, 30)
                    ),
                )
        self.inventario.dibujar(pantalla, self.game_state)
        if (
            self.mensaje_desmayo is not None
            and pygame.time.get_ticks() < self.mensaje_desmayo_hasta
        ):
            lineas_mensaje = (
                "Por desmayarte, la agencia te descontó el 50%",
                "de los créditos que poseías.",
            )
            superficies = [
                self.fuente_menu_pc.render(
                    linea, True, (255, 255, 255)
                )
                for linea in lineas_mensaje
            ]
            cuadro = pygame.Rect(
                0,
                0,
                max(superficie.get_width() for superficie in superficies) + 32,
                sum(superficie.get_height() for superficie in superficies) + 24,
            )
            cuadro.midtop = (pantalla.get_width() // 2, 88)
            pygame.draw.rect(pantalla, (0, 0, 0), cuadro)
            pygame.draw.rect(pantalla, (255, 255, 255), cuadro, 2)
            for indice, superficie in enumerate(superficies):
                pantalla.blit(
                    superficie,
                    superficie.get_rect(
                        midtop=(
                            cuadro.centerx,
                            cuadro.top + 8 + indice * superficie.get_height(),
                        )
                    ),
                )
        if (
            self.mensaje_guardado is not None
            and pygame.time.get_ticks() < self.mensaje_guardado_hasta
        ):
            color = (
                (255, 180, 140)
                if "no se pudo guardar" in self.mensaje_guardado.lower()
                else (255, 255, 255)
            )
            mensaje = self.fuente.render(self.mensaje_guardado, True, color)
            pantalla.blit(
                mensaje,
                mensaje.get_rect(midtop=(pantalla.get_width() // 2, 52)),
            )
        self.dibujar_transicion_sueno(pantalla)

    def dibujar_transicion_sueno(self, pantalla):
        inicio_sueno = self.transicion_sueno_inicio
        if inicio_sueno is None:
            return

        tiempo_transcurrido = pygame.time.get_ticks() - inicio_sueno
        inicio_fundido = self.DURACION_ANIMACION_SUENO
        inicio_cartel_dia = inicio_fundido + self.DURACION_FUNDIDO
        inicio_fundido_entrada = inicio_cartel_dia + self.DURACION_CARTEL_DIA
        capa_negra = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
        opacidad = 0

        if tiempo_transcurrido < inicio_fundido:
            return
        if tiempo_transcurrido < inicio_cartel_dia:
            progreso = (
                tiempo_transcurrido - inicio_fundido
            ) / self.DURACION_FUNDIDO
            opacidad = round(255 * progreso)
        elif tiempo_transcurrido < inicio_fundido_entrada:
            opacidad = 255
        else:
            progreso = min(
                1,
                (tiempo_transcurrido - inicio_fundido_entrada)
                / self.DURACION_FUNDIDO,
            )
            opacidad = round(255 * (1 - progreso))

        capa_negra.fill((0, 0, 0, opacidad))
        pantalla.blit(capa_negra, (0, 0))

        if tiempo_transcurrido >= inicio_cartel_dia:
            superficie_dia = self.fuente.render(
                f"DIA {self.dia_mostrado}", True, (255, 255, 255)
            )
            if tiempo_transcurrido >= inicio_fundido_entrada:
                superficie_dia.set_alpha(opacidad)
            pantalla.blit(
                superficie_dia,
                superficie_dia.get_rect(center=pantalla.get_rect().center),
            )