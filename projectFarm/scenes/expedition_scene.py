import os
import random
import xml.etree.ElementTree as ET

import pygame
from pytmx import TiledTileLayer
from pytmx.util_pygame import load_pygame

from engine.audio import reproducir_sonido_interaccion
from engine.ui import InterfazEstado
from projectFarm.entities import Jugador, Rover
from projectFarm.recompensasExpe import SistemaRecompensas, HITOS_ROVER


class ExpeditionScene:
    ESCALA = 3
    TAMANO_ZONA_INTERACCION_PC = 48
    PUNTOS_INTERES = (
        ("Colonia Marciana", (862, 147)),
        ("Valles Marineris", (466, 361)),
        ("Cráter Jezero", (1250, 181)),
        ("Monte Olimpo", (59, 181)),
    )
    RADIO_MARCADOR = 7
    RADIO_CLIC_MARCADOR = 12
    EXPEDICIONES = {
        "jezero": {
            "nombre": "Cráter Jezero",
            "tipo": "corta",
            "dias": 2,
            "coste": 30,
            "probabilidad_exito": 0.85,
            "recompensas": (25, 5, 2),
        },
        "marineris": {
            "nombre": "Valles Marineris",
            "tipo": "intermedia",
            "dias": 4,
            "coste": 70,
            "probabilidad_exito": 0.70,
            "recompensas": (15, 50, 5),
        },
        "olimpo": {
            "nombre": "Monte Olimpo",
            "tipo": "larga",
            "dias": 6,
            "coste": 150,
            "probabilidad_exito": 0.55,
            "recompensas": (10, 20, 50),
        },
    }
    DESTINO_POR_LUGAR = {
        "Cráter Jezero": "jezero",
        "Valles Marineris": "marineris",
        "Monte Olimpo": "olimpo",
    }

    def __init__(self, game_state, inventario, al_salir):
        self.name = "Expedition Scene"
        self.game_state = game_state
        self.inventario = inventario
        self.interfaz_estado = InterfazEstado()
        self.jugador = Jugador()
        self.sistema_recompensas = SistemaRecompensas()
        self.mensaje_rover = ""
        self.tiempo_mensaje_rover = 0
        self.DURACION_MENSAJE_ROVER = 4000  # 4 segundos
        self.ventana_hitos_rover = False
        self.creditos_hitos_mensaje = 0
        self.primera_entrada = True
        self.al_salir = al_salir
        self.fuente = pygame.font.Font(None, 28)
        self.fuente_monitor = pygame.font.Font(None, 18)

        ruta_mapa = os.path.normpath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "assets",
                "InteriorExpedicion.tmx",
            )
        )
        mapa = load_pygame(ruta_mapa)
        self.fondo = self._renderizar_mapa(mapa)
        self.salida_mapa = self._cargar_salida(ruta_mapa)
        self.pc_mapa = self._cargar_objeto_punto(ruta_mapa, "Pc")
        self.rover = Rover(
            *self._cargar_objeto_punto(ruta_mapa, "Rover1", "Npc")
        )
        self.colisiones_mapa = self._cargar_colisiones(
            ruta_mapa, mapa.tilewidth
        )
        self.monitor_abierto = False
        self.arrastrando_mapa = False
        self.punto_seleccionado = None
        self._cargar_monitor()

    def _cargar_objeto_punto(self, ruta_mapa, nombre, nombre_capa="Objeto"):
        raiz_mapa = ET.parse(ruta_mapa).getroot()
        capa_objetos = next(
            (
                capa
                for capa in raiz_mapa.findall("objectgroup")
                if capa.attrib.get("name") == nombre_capa
            ),
            None,
        )
        if capa_objetos is None:
            raise ValueError(
                f"No se encontró la capa de objetos '{nombre_capa}'."
            )

        objeto = next(
            (
                objeto
                for objeto in capa_objetos.findall("object")
                if objeto.attrib.get("name") == nombre
            ),
            None,
        )
        if objeto is None:
            raise ValueError(
                f"No se encontró el objeto '{nombre}' "
                f"en la capa '{nombre_capa}'."
            )

        return (
            round(float(objeto.attrib["x"]) * self.ESCALA),
            round(float(objeto.attrib["y"]) * self.ESCALA),
        )

    def _cargar_monitor(self):
        ruta_assets = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "assets")
        )

        # Cargar el fondo del monitor.
        ruta_fondo = os.path.join(ruta_assets, "MapMonitor.png")
        imagen_fondo = pygame.image.load(ruta_fondo).convert_alpha()

        self.fondo_monitor = pygame.transform.scale(
            imagen_fondo,
            (
                imagen_fondo.get_width() * self.ESCALA,
                imagen_fondo.get_height() * self.ESCALA,
            ),
        )

        # Zona visible donde se muestra el mapa de Marte.
        # Los valores se expresan en píxeles de pantalla.
        self.zona_mars_monitor = pygame.Rect(
            30,  # X
            24,  # Y
            396,  # Ancho
            260,  # Alto
        )

        # Imagen del planeta.
        self.imagen_mars = pygame.image.load(
            os.path.join(ruta_assets, "MarsPlanet.png")
        ).convert_alpha()

        self.posicion_mars = pygame.Vector2(
            self.zona_mars_monitor.centerx - self.imagen_mars.get_width() // 2,
            self.zona_mars_monitor.centery - self.imagen_mars.get_height() // 2,
        )

        self._limitar_posicion_mars()

    

    def _limitar_posicion_mars(self):
        self.posicion_mars.x = min(
            self.zona_mars_monitor.left,
            max(
                self.zona_mars_monitor.right - self.imagen_mars.get_width(),
                self.posicion_mars.x,
            ),
        )
        self.posicion_mars.y = min(
            self.zona_mars_monitor.top,
            max(
                self.zona_mars_monitor.bottom - self.imagen_mars.get_height(),
                self.posicion_mars.y,
            ),
        )

    def _obtener_rectangulo_monitor(self, limites_pantalla):
        rect_monitor = self.fondo_monitor.get_rect(
            center=limites_pantalla.center
        )

        # Desplazar el monitor hacia arriba.
        rect_monitor.y -= 90

        return rect_monitor

    def _obtener_botones_monitor(self, rect_monitor):
        y = rect_monitor.bottom + 190 - 29
        ancho = min(220, rect_monitor.width - 20)

        boton_enviar = pygame.Rect(
            rect_monitor.centerx - ancho // 2,
            y,
            ancho,
            24,
        )

        return boton_enviar, pygame.Rect(0, 0, 0, 0)

    def _iniciar_expedicion(self, destino):
        expedicion = self.EXPEDICIONES[destino]
        if self.game_state.expedicion_activa is not None:
            return False
        if self.game_state.creditos < expedicion["coste"]:
            self.game_state.resultado_ultima_expedicion = (
                "No tienes créditos suficientes para enviar el Rover."
            )
            return False

        self.game_state.creditos -= expedicion["coste"]
        self.game_state.expedicion_activa = destino
        self.game_state.dia_finalizacion_expedicion = (
            self.game_state.dia_actual + expedicion["dias"]
        )
        self.game_state.resultado_ultima_expedicion = ""
        return True

    def procesar_fin_dia(self):
        destino = self.game_state.expedicion_activa
        if destino is None:
            return

        expedicion = self.EXPEDICIONES[destino]
        if self.game_state.dia_actual < self.game_state.dia_finalizacion_expedicion:
            return

        exitosa = random.random() < expedicion["probabilidad_exito"]
        multiplicador = 1 if exitosa else 0.5
        tierra, atmosfera, minerales = (
            int(cantidad * multiplicador)
            for cantidad in expedicion["recompensas"]
        )
        self.game_state.muestras_tierra += tierra
        self.game_state.muestras_atmosfera += atmosfera
        self.game_state.minerales_recogidos += minerales
        self.game_state.expedicion_activa = None
        self.game_state.dia_finalizacion_expedicion = None
        resultado = "exitosa" if exitosa else "fallida"
        self.game_state.resultado_ultima_expedicion = (
            f"{expedicion['nombre']}: {resultado}. +{tierra} tierra, "
            f"+{atmosfera} atmósfera, +{minerales} minerales."
        )

    def _renderizar_mapa(self, mapa):
        fondo = pygame.Surface(
            (mapa.width * mapa.tilewidth, mapa.height * mapa.tileheight),
            pygame.SRCALPHA,
        )
        for capa in mapa.layers:
            if not isinstance(capa, TiledTileLayer) or not capa.visible:
                continue
            for x, y, imagen in capa.tiles():
                fondo.blit(imagen, (x * mapa.tilewidth, y * mapa.tileheight))

        return pygame.transform.scale(
            fondo,
            (
                fondo.get_width() * self.ESCALA,
                fondo.get_height() * self.ESCALA,
            ),
        )

    def _cargar_salida(self, ruta_mapa):
        raiz_mapa = ET.parse(ruta_mapa).getroot()
        capa_objetos = next(
            (
                capa
                for capa in raiz_mapa.findall("objectgroup")
                if capa.attrib.get("name") == "Objeto"
            ),
            None,
        )
        if capa_objetos is None:
            raise ValueError("No se encontró la capa de objetos 'Objeto'.")

        salida = next(
            (
                objeto
                for objeto in capa_objetos.findall("object")
                if objeto.attrib.get("name") == "Salida"
            ),
            None,
        )
        if salida is None:
            raise ValueError(
                "No se encontró el objeto 'Salida' en la capa 'Objeto'."
            )

        return pygame.Rect(
            round(float(salida.attrib["x"]) * self.ESCALA),
            round(float(salida.attrib["y"]) * self.ESCALA),
            round(float(salida.attrib["width"]) * self.ESCALA),
            round(float(salida.attrib["height"]) * self.ESCALA),
        )

    def _cargar_colisiones(self, ruta_mapa, ancho_tile):
        raiz_mapa = ET.parse(ruta_mapa).getroot()
        colisiones_por_gid = {}

        for nodo_tileset in raiz_mapa.findall("tileset"):
            first_gid = int(nodo_tileset.attrib["firstgid"])
            ruta_tileset = os.path.join(
                os.path.dirname(ruta_mapa), nodo_tileset.attrib["source"]
            )
            raiz_tileset = ET.parse(ruta_tileset).getroot()

            for nodo_tile in raiz_tileset.findall("tile"):
                rectangulos = []
                for objeto in nodo_tile.findall("./objectgroup/object"):
                    x = float(objeto.attrib.get("x", 0))
                    y = float(objeto.attrib.get("y", 0))
                    ancho = float(objeto.attrib.get("width", 0))
                    alto = float(objeto.attrib.get("height", 0))
                    if ancho > 0 and alto > 0:
                        rectangulos.append((x, y, ancho, alto))
                if rectangulos:
                    colisiones_por_gid[
                        first_gid + int(nodo_tile.attrib["id"])
                    ] = rectangulos

        colisiones = []
        for capa in raiz_mapa.findall("layer"):
            if capa.attrib.get("visible", "1") == "0":
                continue
            datos = capa.find("data")
            if datos is None or datos.attrib.get("encoding") != "csv":
                continue

            for y, fila in enumerate((datos.text or "").strip().splitlines()):
                for x, valor in enumerate(fila.split(",")):
                    if not valor.strip():
                        continue
                    gid = int(valor) & 0x1FFFFFFF
                    for ox, oy, ancho, alto in colisiones_por_gid.get(gid, ()):
                        colisiones.append(
                            pygame.Rect(
                                round(
                                    (
                                        x * ancho_tile
                                        + ox
                                    )
                                    * self.ESCALA
                                ),
                                round(
                                    (
                                        y * ancho_tile
                                        + oy
                                    )
                                    * self.ESCALA
                                ),
                                round(ancho * self.ESCALA),
                                round(alto * self.ESCALA),
                            )
                        )
        return colisiones

    def _obtener_rectangulo_salida(self, origen_mapa):
        return self.salida_mapa.move(origen_mapa)

    def _obtener_posicion_entrada(self, origen_mapa):
        salida = self._obtener_rectangulo_salida(origen_mapa)
        posicion = self.jugador.rectangulo.copy()
        posicion.midbottom = (salida.centerx, salida.top - 8)
        return posicion

    def update(self, teclas, limites_pantalla, eventos=()):
        rect_fondo = self.fondo.get_rect(center=limites_pantalla.center)
        salida = self._obtener_rectangulo_salida(rect_fondo.topleft)
        if self.primera_entrada:
            self.jugador.rectangulo = self._obtener_posicion_entrada(
                rect_fondo.topleft
            )
            self.primera_entrada = False

        if self.mensaje_rover:
            ahora = pygame.time.get_ticks()

            if ahora - self.tiempo_mensaje_rover >= self.DURACION_MENSAJE_ROVER:
                self.mensaje_rover = ""

        # Zona de interacción con el Rover, en coordenadas de pantalla.
        zona_rover = self.rover.rectangulo.move(rect_fondo.topleft)
        zona_rover = zona_rover.inflate(30, 30)

        pc = pygame.Rect(
            (0, 0),
            (self.TAMANO_ZONA_INTERACCION_PC,) * 2,
        )
        pc.center = (
            rect_fondo.left + self.pc_mapa[0],
            rect_fondo.top + self.pc_mapa[1],
        )
        area_interaccion_pc = pc.inflate(40, 40)

        # Ventana de hitos del Rover.
        if self.ventana_hitos_rover:
            for evento in eventos:
                if evento.type == pygame.KEYDOWN:
                    if evento.key in (pygame.K_e, pygame.K_ESCAPE):
                        self.ventana_hitos_rover = False

                elif evento.type == pygame.MOUSEBUTTONDOWN:
                    if evento.button == 1:
                        rect_ventana = self._obtener_rectangulo_hitos(
                            limites_pantalla
                        )
                        rect_cerrar = pygame.Rect(
                            rect_ventana.right - 35,
                            rect_ventana.top + 10,
                            25,
                            25,
                        )

                        if rect_cerrar.collidepoint(evento.pos):
                            self.ventana_hitos_rover = False

            return

        if self.monitor_abierto:
            rect_monitor = self._obtener_rectangulo_monitor(limites_pantalla)
            zona_mars = self.zona_mars_monitor.move(rect_monitor.topleft)
            for evento in eventos:
                if evento.type == pygame.KEYDOWN and evento.key == pygame.K_e:
                    self.monitor_abierto = False
                    self.arrastrando_mapa = False
                elif (
                    evento.type == pygame.MOUSEBUTTONDOWN
                    and evento.button == 3
                ):
                    self.monitor_abierto = False
                    self.arrastrando_mapa = False
                elif (
                    evento.type == pygame.MOUSEBUTTONDOWN
                    and evento.button == 1
                ):
                    boton_enviar, boton_cancelar = (
                        self._obtener_botones_monitor(rect_monitor)
                    )
                    destino = self.DESTINO_POR_LUGAR.get(
                        self.punto_seleccionado
                    )
                    if (
                        destino is not None
                        and boton_enviar.collidepoint(evento.pos)
                    ):
                        if self._iniciar_expedicion(destino):
                            self.punto_seleccionado = None
                        continue
                    if (
                        destino is not None
                        and boton_cancelar.collidepoint(evento.pos)
                    ):
                        self.punto_seleccionado = None
                        continue
                    if not zona_mars.collidepoint(evento.pos):
                        continue

                    posicion_imagen = (
                        evento.pos[0]
                        - rect_monitor.left
                        - round(self.posicion_mars.x),
                        evento.pos[1]
                        - rect_monitor.top
                        - round(self.posicion_mars.y),
                    )
                    punto_seleccionado = next(
                        (
                            nombre
                            for nombre, (x, y) in self.PUNTOS_INTERES
                            if (posicion_imagen[0] - x) ** 2
                            + (posicion_imagen[1] - y) ** 2
                            <= self.RADIO_CLIC_MARCADOR**2
                        ),
                        None,
                    )
                    if punto_seleccionado is not None:
                        self.punto_seleccionado = punto_seleccionado
                        self.arrastrando_mapa = False
                    else:
                        self.punto_seleccionado = None
                        self.arrastrando_mapa = True
                elif evento.type == pygame.MOUSEBUTTONUP and evento.button == 1:
                    self.arrastrando_mapa = False
                elif (
                    evento.type == pygame.MOUSEMOTION
                    and self.arrastrando_mapa
                ):
                    self.posicion_mars.x += evento.rel[0]
                    self.posicion_mars.y += evento.rel[1]
                    self._limitar_posicion_mars()
            return

        for evento in eventos:
            if evento.type != pygame.KEYDOWN or evento.key != pygame.K_e:
                continue

            # Interacción con el PC.
            if self.jugador.rectangulo.colliderect(area_interaccion_pc):
                reproducir_sonido_interaccion()
                self.monitor_abierto = True
                self.arrastrando_mapa = False
                return

            # Interacción con el Rover.
            if self.jugador.rectangulo.colliderect(zona_rover):
                reproducir_sonido_interaccion()

                creditos, _ = (
                    self.sistema_recompensas
                    .reclamar_recompensas_rover(self.game_state)
                )

                self.creditos_hitos_mensaje = creditos
                self.ventana_hitos_rover = True
                return

        rect_previo = self.jugador.rectangulo.copy()

        # Colisiones del mapa en coordenadas de pantalla.
        colisiones = [
            colision.move(rect_fondo.topleft)
            for colision in self.colisiones_mapa
        ]

        # Convertir la posición del jugador a coordenadas locales del mapa.
        rect_jugador_mapa = self.jugador.rectangulo.move(
            -rect_fondo.left,
            -rect_fondo.top,
        )

        # Rover trabaja con coordenadas locales del mapa.
        self.rover.actualizar(
            self.colisiones_mapa,
            (rect_jugador_mapa,),
        )

        # Añadir el Rover a las colisiones del jugador,
        # utilizando coordenadas de pantalla.
        colisiones.append(
            self.rover.rectangulo.move(rect_fondo.topleft)
        )

        self.jugador.actualizar(teclas)
        self.jugador.rectangulo.clamp_ip(rect_fondo)

        rect_destino = self.jugador.rectangulo.copy()

        self.jugador.rectangulo.x = rect_previo.x
        if rect_destino.y != rect_previo.y:
            self.jugador.rectangulo.y = rect_destino.y
            if (
                not self.jugador.rectangulo.colliderect(salida)
                and any(
                    self.jugador.rectangulo.colliderect(colision)
                    for colision in colisiones
                )
            ):
                self.jugador.rectangulo.y = rect_previo.y

        if rect_destino.x != rect_previo.x:
            self.jugador.rectangulo.x = rect_destino.x
            if (
                not self.jugador.rectangulo.colliderect(salida)
                and any(
                    self.jugador.rectangulo.colliderect(colision)
                    for colision in colisiones
                )
            ):
                self.jugador.rectangulo.x = rect_previo.x

        if self.jugador.rectangulo.colliderect(salida):
            self.primera_entrada = True
            self.al_salir()

    def draw(self, pantalla):
        pantalla.fill((0, 0, 0))
        limites_pantalla = pantalla.get_rect()
        rect_fondo = self.fondo.get_rect(center=limites_pantalla.center)
        pantalla.blit(self.fondo, rect_fondo)

        if self.monitor_abierto:
            rect_monitor = self._obtener_rectangulo_monitor(limites_pantalla)
            pantalla.blit(self.fondo_monitor, rect_monitor)
            zona_mars = self.zona_mars_monitor.move(rect_monitor.topleft)
            recorte_previo = pantalla.get_clip()
            pantalla.set_clip(zona_mars)
            pantalla.blit(
                self.imagen_mars,
                (
                    rect_monitor.left + round(self.posicion_mars.x),
                    rect_monitor.top + round(self.posicion_mars.y),
                ),
            )
            for nombre, (x, y) in self.PUNTOS_INTERES:
                posicion_marcador = (
                    rect_monitor.left + round(self.posicion_mars.x) + x,
                    rect_monitor.top + round(self.posicion_mars.y) + y,
                )

                color = (
                    (70, 210, 130)
                    if nombre == "Colonia Marciana"
                    else (220, 35, 35)
                )

                pygame.draw.circle(
                    pantalla,
                    (255, 255, 255),
                    posicion_marcador,
                    self.RADIO_MARCADOR + 2,
                )
                pygame.draw.circle(
                    pantalla,
                    color,
                    posicion_marcador,
                    self.RADIO_MARCADOR,
                )
            pantalla.set_clip(recorte_previo)
            pantalla.blit(
                self.fuente.render(
                    "Arrastra para explorar | E o clic derecho: cerrar",
                    True,
                    (255, 255, 255),
                ),
                (50, 10),
            )
            self._dibujar_panel_expediciones(pantalla, rect_monitor)
            self.interfaz_estado.dibujar(pantalla, self.game_state)
            return

        self.rover.dibujar(pantalla, rect_fondo.topleft)
        self.jugador.dibujar(pantalla)
        self.interfaz_estado.dibujar(pantalla, self.game_state)
        if self.ventana_hitos_rover:
            self._dibujar_ventana_hitos_rover(pantalla)
            return
        
        if self.mensaje_rover:
            texto = self.fuente.render(
                self.mensaje_rover,
                True,
                (255, 255, 255)
            )

            fondo_texto = texto.get_rect(
                midbottom=(pantalla.get_width() // 2,
                        pantalla.get_height() - 30)
            ).inflate(20, 12)

            pygame.draw.rect(pantalla, (30, 30, 30), fondo_texto)
            pantalla.blit(texto, texto.get_rect(center=fondo_texto.center))

        salida = self._obtener_rectangulo_salida(rect_fondo.topleft)
        if self.jugador.rectangulo.colliderect(salida):
            indicacion = self.fuente.render(
                "Salida automatica", True, (255, 255, 255)
            )
            pantalla.blit(
                indicacion,
                indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)),
            )
            return

        pc = pygame.Rect(
            (0, 0),
            (self.TAMANO_ZONA_INTERACCION_PC,) * 2,
        )
        pc.center = (
            rect_fondo.left + self.pc_mapa[0],
            rect_fondo.top + self.pc_mapa[1],
        )
        if self.jugador.rectangulo.colliderect(pc.inflate(40, 40)):
            indicacion = self.fuente.render(
                "E: consultar mapa", True, (255, 255, 255)
            )
            pantalla.blit(
                indicacion,
                indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)),
            )

    def _dibujar_panel_expediciones(self, pantalla, rect_monitor):
        # Colores de la interfaz.
        fondo = (13, 20, 30)
        borde = (54, 85, 105)
        azul = (75, 190, 230)
        blanco = (230, 240, 245)
        gris = (145, 165, 180)
        verde = (70, 210, 130)
        amarillo = (245, 195, 75)

        # Fuentes del panel.
        fuente_titulo = pygame.font.Font(None, 22)
        fuente_datos = pygame.font.Font(None, 18)
        fuente_pequena = pygame.font.Font(None, 16)

        # Panel inferior, separado del monitor principal.
        y = rect_monitor.bottom + 10

        panel = pygame.Rect(
            rect_monitor.left,
            y,
            rect_monitor.width,
            180,
        )

        # Fondo y bordes.
        pygame.draw.rect(pantalla, fondo, panel)
        pygame.draw.rect(pantalla, borde, panel, 1)

        # Línea decorativa superior.
        pygame.draw.line(
            pantalla,
            azul,
            (panel.left + 2, panel.top + 1),
            (panel.right - 2, panel.top + 1),
            2,
        )

        # Encabezado.
        encabezado = fuente_titulo.render(
            "INFORME DE EXPLORACION",
            True,
            azul,
        )
        pantalla.blit(
            encabezado,
            (panel.left + 10, panel.top + 6),
        )

        # Indicador de conexión.
        pygame.draw.circle(
            pantalla,
            verde,
            (panel.right - 15, panel.top + 15),
            4,
        )

        # Separador del encabezado.
        pygame.draw.line(
            pantalla,
            borde,
            (panel.left + 8, panel.top + 27),
            (panel.right - 8, panel.top + 27),
        )

        # --------------------------------------------------
        # Muestras recopiladas.
        # --------------------------------------------------
        muestras = (
            ("TIERRA", self.game_state.muestras_tierra),
            ("ATMOSFERA", self.game_state.muestras_atmosfera),
            ("MINERALES", self.game_state.minerales_recogidos),
        )

        margen = 10
        separacion = 6
        ancho_tarjeta = (
            panel.width - margen * 2 - separacion * 2
        ) // 3

        y_tarjetas = panel.top + 34
        alto_tarjeta = 34

        for indice, (nombre, cantidad) in enumerate(muestras):
            x = (
                panel.left
                + margen
                + indice * (ancho_tarjeta + separacion)
            )

            tarjeta = pygame.Rect(
                x,
                y_tarjetas,
                ancho_tarjeta,
                alto_tarjeta,
            )

            pygame.draw.rect(
                pantalla,
                (22, 34, 47),
                tarjeta,
            )
            pygame.draw.rect(
                pantalla,
                borde,
                tarjeta,
                1,
            )

            etiqueta = fuente_pequena.render(
                nombre,
                True,
                gris,
            )
            valor = fuente_datos.render(
                str(cantidad),
                True,
                blanco,
            )

            pantalla.blit(
                etiqueta,
                (tarjeta.left + 5, tarjeta.top + 3),
            )
            pantalla.blit(
                valor,
                (tarjeta.left + 5, tarjeta.top + 16),
            )

        # --------------------------------------------------
        # Estado actual del Rover.
        # --------------------------------------------------
        y_estado = y_tarjetas + alto_tarjeta + 8

        destino_activo = self.game_state.expedicion_activa

        if destino_activo is None:
            color_estado = verde
            texto_estado = "ROVER DISPONIBLE"
        else:
            expedicion_activa = self.EXPEDICIONES[destino_activo]

            dias_restantes = max(
                0,
                self.game_state.dia_finalizacion_expedicion
                - self.game_state.dia_actual,
            )

            color_estado = amarillo
            texto_estado = (
                f"EN MISION: {expedicion_activa['nombre']} "
                f"({dias_restantes} dias)"
            )

        pygame.draw.circle(
            pantalla,
            color_estado,
            (panel.left + 16, y_estado + 7),
            4,
        )

        pantalla.blit(
            fuente_datos.render(
                texto_estado,
                True,
                color_estado,
            ),
            (panel.left + 27, y_estado),
        )

        # --------------------------------------------------
        # Resultado de la última expedición.
        # --------------------------------------------------
        mensaje = self.game_state.resultado_ultima_expedicion

        if mensaje:
            texto_mensaje = fuente_pequena.render(
                mensaje,
                True,
                amarillo,
            )

            # Evitar que el texto sobresalga del panel.
            ancho_maximo = panel.width - 20

            if texto_mensaje.get_width() > ancho_maximo:
                texto_mensaje = pygame.transform.scale(
                    texto_mensaje,
                    (
                        ancho_maximo,
                        texto_mensaje.get_height(),
                    ),
                )

            pantalla.blit(
                texto_mensaje,
                (panel.left + 10, y_estado + 16),
            )

        # Límite inferior de la zona de información.
        limite_informacion = panel.bottom - 38
        desplazamiento_detalles = 30 if mensaje else 16
        # --------------------------------------------------
        # Detalles de la expedición seleccionada.
        # --------------------------------------------------
        destino_seleccionado = self.DESTINO_POR_LUGAR.get(
            self.punto_seleccionado
        )

        if (
            self.punto_seleccionado is not None
            and destino_seleccionado is None
        ):
            pantalla.blit(
                fuente_pequena.render(
                    self.punto_seleccionado,
                    True,
                    blanco,
                ),
                (panel.left + 10, y_estado + desplazamiento_detalles),
            )

        if destino_seleccionado is not None:
            expedicion = self.EXPEDICIONES[destino_seleccionado]

            detalles = (
                f"{expedicion['nombre']} | "
                f"{expedicion['dias']} dias | "
                f"{expedicion['coste']} creditos"
            )

            recompensa = expedicion["recompensas"]

            texto_detalles = fuente_pequena.render(
                detalles,
                True,
                blanco,
            )

            texto_recompensas = fuente_pequena.render(
                f"TIERRA +{recompensa[0]}  |  "
                f"ATMOSFERA +{recompensa[1]}  |  "
                f"MINERALES +{recompensa[2]}",
                True,
                gris,
            )

            y_detalles = y_estado + desplazamiento_detalles
            y_recompensas = y_detalles + 14

            if y_recompensas + texto_recompensas.get_height() <= limite_informacion:
                pantalla.blit(
                    texto_detalles,
                    (panel.left + 10, y_detalles),
                )

                pantalla.blit(
                    texto_recompensas,
                    (panel.left + 10, y_recompensas),
                )
            elif y_detalles + texto_detalles.get_height() <= limite_informacion:
                pantalla.blit(
                    texto_detalles,
                    (panel.left + 10, y_detalles),
                )

        # --------------------------------------------------
        # Botón de confirmar envío.
        # --------------------------------------------------
        boton_enviar, _ = self._obtener_botones_monitor(rect_monitor)

        alto_boton = 24
        margen_inferior = 5
        ancho_boton = min(220, panel.width - 20)

        boton_enviar = pygame.Rect(
            panel.centerx - ancho_boton // 2,
            panel.bottom - alto_boton - margen_inferior,
            ancho_boton,
            alto_boton,
        )

        puede_enviar = (
            destino_seleccionado is not None
            and destino_activo is None
            and self.game_state.creditos
            >= self.EXPEDICIONES[destino_seleccionado]["coste"]
        )

        self._dibujar_boton(
            pantalla,
            boton_enviar,
            "CONFIRMAR ENVIO",
            puede_enviar,
        )

    def _dibujar_boton(self, pantalla, rectangulo, texto, habilitado):
        if texto == "CONFIRMAR ENVIO":
            color_fondo = (
                (25, 105, 75)
                if habilitado
                else (40, 48, 57)
            )
            color_borde = (
                (75, 220, 150)
                if habilitado
                else (75, 85, 95)
            )
            color_texto = (
                (220, 255, 235)
                if habilitado
                else (125, 135, 145)
            )
        else:
            color_fondo = (35, 45, 58)
            color_borde = (90, 115, 135)
            color_texto = (200, 215, 225)

        pygame.draw.rect(
            pantalla,
            color_fondo,
            rectangulo,
        )

        pygame.draw.rect(
            pantalla,
            color_borde,
            rectangulo,
            1,
        )

        etiqueta = pygame.font.Font(None, 18).render(
            texto,
            True,
            color_texto,
        )

        pantalla.blit(
            etiqueta,
            etiqueta.get_rect(center=rectangulo.center),
        )

    def _obtener_rectangulo_hitos(self, limites_pantalla):
        ancho = min(680, limites_pantalla.width - 30)
        alto = min(520, limites_pantalla.height - 30)

        return pygame.Rect(
            limites_pantalla.centerx - ancho // 2,
            limites_pantalla.centery - alto // 2,
            ancho,
            alto,
        )


    def _dibujar_ventana_hitos_rover(self, pantalla):
        # Oscurecer el escenario detrás de la ventana.
        oscurecimiento = pygame.Surface(
            pantalla.get_size(),
            pygame.SRCALPHA,
        )
        oscurecimiento.fill((0, 0, 0, 180))
        pantalla.blit(oscurecimiento, (0, 0))

        rect_ventana = self._obtener_rectangulo_hitos(
            pantalla.get_rect()
        )

        # Fondo y borde de la ventana.
        pygame.draw.rect(
            pantalla,
            (25, 32, 40),
            rect_ventana,
        )
        pygame.draw.rect(
            pantalla,
            (150, 175, 190),
            rect_ventana,
            2,
        )

        # Título.
        titulo = self.fuente.render(
            "Hitos de exploración del Rover",
            True,
            (255, 255, 255),
        )

        pantalla.blit(
            titulo,
            titulo.get_rect(
                midtop=(rect_ventana.centerx, rect_ventana.top + 14)
            ),
        )

        # Botón para cerrar.
        rect_cerrar = pygame.Rect(
            rect_ventana.right - 35,
            rect_ventana.top + 10,
            25,
            25,
        )

        pygame.draw.rect(
            pantalla,
            (130, 45, 45),
            rect_cerrar,
        )

        texto_cerrar = self.fuente_monitor.render(
            "X",
            True,
            (255, 255, 255),
        )

        pantalla.blit(
            texto_cerrar,
            texto_cerrar.get_rect(center=rect_cerrar.center),
        )

        # Créditos obtenidos en esta interacción.
        if self.creditos_hitos_mensaje > 0:
            texto_creditos = self.fuente_monitor.render(
                f"¡Recompensas obtenidas: "
                f"+{self.creditos_hitos_mensaje} créditos!",
                True,
                (120, 230, 140),
            )
        else:
            texto_creditos = self.fuente_monitor.render(
                "Consulta tu progreso y completa nuevos hitos.",
                True,
                (210, 210, 210),
            )

        pantalla.blit(
            texto_creditos,
            texto_creditos.get_rect(
                midtop=(rect_ventana.centerx, rect_ventana.top + 52)
            ),
        )

        # Agrupar los hitos por tipo de muestra.
        categorias = (
            ("Muestras de tierra", "muestras_tierra"),
            ("Muestras de atmósfera", "muestras_atmosfera"),
            ("Minerales recogidos", "minerales_recogidos"),
        )

        x_texto = rect_ventana.left + 24
        y = rect_ventana.top + 85

        ancho_barra = rect_ventana.width - 110
        alto_barra = 7

        for nombre_categoria, atributo in categorias:
            # Encabezado de categoría.
            encabezado = self.fuente_monitor.render(
                nombre_categoria,
                True,
                (100, 200, 240),
            )
            pantalla.blit(encabezado, (x_texto, y))
            y += 23

            cantidad_actual = getattr(
                self.game_state,
                atributo,
            )

            hitos_categoria = [
                hito
                for hito in HITOS_ROVER
                if hito["atributo"] == atributo
            ]

            for hito in hitos_categoria:
                cantidad_requerida = hito["cantidad"]
                completado = (
                    hito["id"]
                    in self.game_state.hitos_rover_reclamados
                )

                # Casilla del hito.
                rect_check = pygame.Rect(
                    x_texto,
                    y + 2,
                    16,
                    16,
                )

                color_check = (
                    (45, 165, 80)
                    if completado
                    else (75, 85, 95)
                )

                pygame.draw.rect(
                    pantalla,
                    color_check,
                    rect_check,
                )
                pygame.draw.rect(
                    pantalla,
                    (220, 230, 235),
                    rect_check,
                    1,
                )

                # Dibujar una marca de verificación.
                if completado:
                    pygame.draw.line(
                        pantalla,
                        (255, 255, 255),
                        (rect_check.left + 3, rect_check.centery),
                        (rect_check.left + 7, rect_check.bottom - 4),
                        2,
                    )
                    pygame.draw.line(
                        pantalla,
                        (255, 255, 255),
                        (rect_check.left + 7, rect_check.bottom - 4),
                        (rect_check.right - 2, rect_check.top + 3),
                        2,
                    )

                # Información del hito.
                texto_hito = (
                    f"{cantidad_actual} / {cantidad_requerida} muestras"
                    f"    |    Recompensa: {hito['creditos']} créditos"
                )

                color_texto = (
                    (130, 230, 145)
                    if completado
                    else (230, 230, 230)
                )

                superficie_texto = self.fuente_monitor.render(
                    texto_hito,
                    True,
                    color_texto,
                )

                pantalla.blit(
                    superficie_texto,
                    (x_texto + 26, y),
                )

                # Barra de progreso.
                x_barra = rect_ventana.right - 65
                y_barra = y + 6

                rect_barra = pygame.Rect(
                    x_barra,
                    y_barra,
                    38,
                    alto_barra,
                )

                pygame.draw.rect(
                    pantalla,
                    (65, 75, 85),
                    rect_barra,
                )

                progreso = min(
                    1.0,
                    cantidad_actual / cantidad_requerida,
                )

                if progreso > 0:
                    pygame.draw.rect(
                        pantalla,
                        (45, 190, 95),
                        (
                            rect_barra.left,
                            rect_barra.top,
                            round(rect_barra.width * progreso),
                            rect_barra.height,
                        ),
                    )

                y += 28

            y += 5

        # Instrucción para cerrar la ventana.
        pie = self.fuente_monitor.render(
            "Pulsa E o ESC para cerrar",
            True,
            (190, 200, 210),
        )

        pantalla.blit(
            pie,
            pie.get_rect(
                midbottom=(
                    rect_ventana.centerx,
                    rect_ventana.bottom - 10,
                )
            ),
        )