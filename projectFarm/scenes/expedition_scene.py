import os
import random
import xml.etree.ElementTree as ET

import pygame
from pytmx import TiledTileLayer
from pytmx.util_pygame import load_pygame

from engine.audio import reproducir_sonido_interaccion
from engine.ui import InterfazEstado
from projectFarm.entities import Jugador


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
            "recompensas": (6, 4, 2),
        },
        "marineris": {
            "nombre": "Valles Marineris",
            "tipo": "intermedia",
            "dias": 4,
            "coste": 70,
            "probabilidad_exito": 0.70,
            "recompensas": (12, 8, 6),
        },
        "olimpo": {
            "nombre": "Monte Olimpo",
            "tipo": "larga",
            "dias": 7,
            "coste": 150,
            "probabilidad_exito": 0.55,
            "recompensas": (20, 14, 10),
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
        self.colisiones_mapa = self._cargar_colisiones(
            ruta_mapa, mapa.tilewidth
        )
        self.monitor_abierto = False
        self.arrastrando_mapa = False
        self.punto_seleccionado = None
        self._cargar_monitor()

    def _cargar_objeto_punto(self, ruta_mapa, nombre):
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
                f"No se encontró el objeto '{nombre}' en la capa 'Objeto'."
            )

        return (
            round(float(objeto.attrib["x"]) * self.ESCALA),
            round(float(objeto.attrib["y"]) * self.ESCALA),
        )

    def _cargar_monitor(self):
        ruta_assets = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "assets")
        )
        ruta_mapa_monitor = os.path.join(ruta_assets, "MapMonitor.tmx")
        mapa_monitor = load_pygame(ruta_mapa_monitor)
        self.fondo_monitor = self._renderizar_mapa(mapa_monitor)
        self.zona_mars_monitor = self._cargar_zona_mars(ruta_mapa_monitor)
        self.imagen_mars = pygame.image.load(
            os.path.join(ruta_assets, "MarsPlanet.png")
        ).convert_alpha()
        self.posicion_mars = pygame.Vector2(
            self.zona_mars_monitor.centerx - self.imagen_mars.get_width() // 2,
            self.zona_mars_monitor.centery - self.imagen_mars.get_height() // 2,
        )
        self._limitar_posicion_mars()

    def _cargar_zona_mars(self, ruta_mapa_monitor):
        raiz_mapa = ET.parse(ruta_mapa_monitor).getroot()
        capa_monitor = next(
            (
                capa
                for capa in raiz_mapa.findall("objectgroup")
                if capa.attrib.get("name") == "Monitor"
            ),
            None,
        )
        if capa_monitor is None:
            raise ValueError(
                "No se encontró la capa de objetos 'Monitor'."
            )

        objeto_mars = next(
            (
                objeto
                for objeto in capa_monitor.findall("object")
                if objeto.attrib.get("name") == "Mars"
            ),
            None,
        )
        if objeto_mars is None:
            raise ValueError(
                "No se encontró la zona 'Mars' en la capa 'Monitor'."
            )

        return pygame.Rect(
            round(float(objeto_mars.attrib["x"]) * self.ESCALA),
            round(float(objeto_mars.attrib["y"]) * self.ESCALA),
            round(float(objeto_mars.attrib["width"]) * self.ESCALA),
            round(float(objeto_mars.attrib["height"]) * self.ESCALA),
        )

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
        return self.fondo_monitor.get_rect(center=limites_pantalla.center)

    def _obtener_botones_monitor(self, rect_monitor):
        y = rect_monitor.bottom - 29
        return (
            pygame.Rect(rect_monitor.left + 30, y, 180, 26),
            pygame.Rect(rect_monitor.right - 210, y, 180, 26),
        )

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

        pc = pygame.Rect(
            (0, 0),
            (self.TAMANO_ZONA_INTERACCION_PC,) * 2,
        )
        pc.center = (
            rect_fondo.left + self.pc_mapa[0],
            rect_fondo.top + self.pc_mapa[1],
        )
        area_interaccion_pc = pc.inflate(40, 40)

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
            if (
                evento.type == pygame.KEYDOWN
                and evento.key == pygame.K_e
                and self.jugador.rectangulo.colliderect(area_interaccion_pc)
            ):
                reproducir_sonido_interaccion()
                self.monitor_abierto = True
                self.arrastrando_mapa = False
                return

        rect_previo = self.jugador.rectangulo.copy()
        self.jugador.actualizar(teclas)
        self.jugador.rectangulo.clamp_ip(rect_fondo)
        rect_destino = self.jugador.rectangulo.copy()
        colisiones = [
            colision.move(rect_fondo.topleft)
            for colision in self.colisiones_mapa
        ]

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
            for _, (x, y) in self.PUNTOS_INTERES:
                posicion_marcador = (
                    rect_monitor.left + round(self.posicion_mars.x) + x,
                    rect_monitor.top + round(self.posicion_mars.y) + y,
                )
                pygame.draw.circle(
                    pantalla,
                    (255, 255, 255),
                    posicion_marcador,
                    self.RADIO_MARCADOR + 2,
                )
                pygame.draw.circle(
                    pantalla,
                    (220, 35, 35),
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

        self.jugador.dibujar(pantalla)
        self.interfaz_estado.dibujar(pantalla, self.game_state)

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
        y = self.zona_mars_monitor.bottom + rect_monitor.top + 25
        panel = pygame.Rect(
            rect_monitor.left + 4,
            y - 8,
            rect_monitor.width - 8,
            rect_monitor.bottom - y - 4,
        )
        pygame.draw.rect(pantalla, (0, 0, 0), panel)

        muestras = (
            f"Muestras: tierra {self.game_state.muestras_tierra} | "
            f"atmósfera {self.game_state.muestras_atmosfera} | "
            f"minerales {self.game_state.minerales_recogidos}"
        )
        pantalla.blit(
            self.fuente_monitor.render(muestras, True, (255, 255, 255)),
            (rect_monitor.left + 8, y),
        )

        destino_activo = self.game_state.expedicion_activa
        if destino_activo is None:
            estado = "Rover disponible"
        else:
            expedicion_activa = self.EXPEDICIONES[destino_activo]
            dias_restantes = max(
                0,
                self.game_state.dia_finalizacion_expedicion
                - self.game_state.dia_actual,
            )
            estado = (
                f"Rover en {expedicion_activa['nombre']}: "
                f"{dias_restantes} días restantes"
            )
        pantalla.blit(
            self.fuente_monitor.render(estado, True, (255, 255, 255)),
            (rect_monitor.left + 8, y + 20),
        )

        mensaje = self.game_state.resultado_ultima_expedicion
        if mensaje:
            pantalla.blit(
                self.fuente_monitor.render(
                    mensaje, True, (255, 235, 150)
                ),
                (rect_monitor.left + 8, y + 38),
            )

        destino_seleccionado = self.DESTINO_POR_LUGAR.get(
            self.punto_seleccionado
        )
        if destino_seleccionado is None:
            if self.punto_seleccionado is not None:
                pantalla.blit(
                    self.fuente_monitor.render(
                        self.punto_seleccionado, True, (255, 255, 255)
                    ),
                    (rect_monitor.left + 8, y + 58),
                )
            return

        expedicion = self.EXPEDICIONES[destino_seleccionado]
        resumen = (
            f"{expedicion['nombre']} ({expedicion['tipo']}): "
            f"{expedicion['dias']} días, {expedicion['coste']} cr., "
            f"{expedicion['probabilidad_exito']:.0%} éxito"
        )
        recompensa = expedicion["recompensas"]
        resumen_recompensa = (
            f"Éxito: {recompensa[0]} tierra / {recompensa[1]} atmósfera / "
            f"{recompensa[2]} minerales; fallo: mitad."
        )
        pantalla.blit(
            self.fuente_monitor.render(resumen, True, (255, 255, 255)),
            (rect_monitor.left + 8, y + 56),
        )
        pantalla.blit(
            self.fuente_monitor.render(
                resumen_recompensa, True, (255, 255, 255)
            ),
            (rect_monitor.left + 8, y + 73),
        )

        boton_enviar, boton_cancelar = self._obtener_botones_monitor(
            rect_monitor
        )
        puede_enviar = (
            destino_activo is None
            and self.game_state.creditos >= expedicion["coste"]
        )
        self._dibujar_boton(
            pantalla,
            boton_enviar,
            "Confirmar envío",
            puede_enviar,
        )
        self._dibujar_boton(
            pantalla, boton_cancelar, "Cancelar", True
        )

    def _dibujar_boton(self, pantalla, rectangulo, texto, habilitado):
        color = (35, 110, 55) if habilitado else (70, 70, 70)
        pygame.draw.rect(pantalla, color, rectangulo)
        pygame.draw.rect(pantalla, (255, 255, 255), rectangulo, 1)
        etiqueta = self.fuente_monitor.render(
            texto, True, (255, 255, 255)
        )
        pantalla.blit(
            etiqueta,
            etiqueta.get_rect(center=rectangulo.center),
        )