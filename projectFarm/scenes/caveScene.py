import os
import xml.etree.ElementTree as ET

import pygame

from projectFarm.localization import LocalizedFont
from pytmx.util_pygame import load_pygame

from engine.ui import InterfazEstado
from projectFarm.entities import Jugador


class CaveScene:
    ESCALA = 3
    RADIO_LINTERNA = 75

    def __init__(self, game_state, inventario, al_salir):
        self.name = "Cave Scene"
        self.game_state = game_state
        self.inventario = inventario
        self.interfaz_estado = InterfazEstado()
        self.jugador = Jugador()
        self.al_salir = al_salir
        self.primera_entrada = True
        self.fuente = LocalizedFont(None, 28)
        self.mensaje = None
        self.mensaje_hasta = 0
        self.ruta_mapa = os.path.normpath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "assets",
                "InteriorCave.tmx",
            )
        )
        (
            self.fondo,
            self.entrada_mapa,
            self.mate_mapa,
        ) = self._cargar_mapa()
        self.colisiones_mapa = self._cargar_colisiones()

    def _cargar_mapa(self):
        mapa = load_pygame(self.ruta_mapa)
        ruta_fondo = os.path.normpath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "assets",
                "InteriorCave.png",
            )
        )
        fondo = pygame.image.load(ruta_fondo).convert_alpha()
        tamano_mapa = (mapa.width * mapa.tilewidth, mapa.height * mapa.tileheight)
        if fondo.get_size() != tamano_mapa:
            raise ValueError(
                "InteriorCave.png debe coincidir con las dimensiones del mapa."
            )
        fondo = pygame.transform.scale(
            fondo,
            (fondo.get_width() * self.ESCALA, fondo.get_height() * self.ESCALA),
        )

        raiz_mapa = ET.parse(self.ruta_mapa).getroot()
        capa_cueva = next(
            (
                capa
                for capa in raiz_mapa.findall("objectgroup")
                if capa.attrib.get("name") == "Cueva"
            ),
            None,
        )
        if capa_cueva is None:
            raise ValueError("Falta la capa 'Cueva' en InteriorCave.tmx.")
        objeto_entrada = next(
            (
                objeto
                for objeto in capa_cueva.findall("object")
                if objeto.attrib.get("name") == "Entrada"
            ),
            None,
        )
        if objeto_entrada is None:
            raise ValueError(
                "Falta el objeto 'Entrada' en la capa 'Cueva'."
            )
        objeto_mate = next(
            (
                objeto
                for objeto in capa_cueva.findall("object")
                if objeto.attrib.get("name") == "Mate"
            ),
            None,
        )
        if objeto_mate is None:
            raise ValueError("Falta el objeto 'Mate' en la capa 'Cueva'.")
        entrada = (
            round(float(objeto_entrada.attrib["x"]) * self.ESCALA),
            round(float(objeto_entrada.attrib["y"]) * self.ESCALA),
        )
        mate = (
            round(float(objeto_mate.attrib["x"]) * self.ESCALA),
            round(float(objeto_mate.attrib["y"]) * self.ESCALA),
        )
        ruta_mate = os.path.normpath(
            os.path.join(
                os.path.dirname(__file__),
                "..",
                "assets",
                "mate.png",
            )
        )
        self.sprite_mate = pygame.transform.scale(
            pygame.image.load(ruta_mate).convert_alpha(),
            (self.ESCALA * 16, self.ESCALA * 16),
        )
        return fondo, entrada, mate

    def _cargar_colisiones(self):
        raiz_mapa = ET.parse(self.ruta_mapa).getroot()
        ancho_tile = int(raiz_mapa.attrib["tilewidth"])
        colisiones_por_gid = {}
        for nodo_tileset in raiz_mapa.findall("tileset"):
            first_gid = int(nodo_tileset.attrib["firstgid"])
            ruta_tileset = os.path.normpath(
                os.path.join(
                    os.path.dirname(self.ruta_mapa),
                    nodo_tileset.attrib["source"],
                )
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
                    for ox, oy, ancho, alto in colisiones_por_gid.get(
                        gid, ()
                    ):
                        colisiones.append(
                            pygame.Rect(
                                round((x * ancho_tile + ox) * self.ESCALA),
                                round((y * ancho_tile + oy) * self.ESCALA),
                                round(ancho * self.ESCALA),
                                round(alto * self.ESCALA),
                            )
                        )
        return colisiones

    def _salir_por_entrada(self):
        x, y = self.entrada_mapa
        zona_salida = pygame.Rect(x - 32, y - 32, 64, 64)
        if not self.jugador.rectangulo.colliderect(zona_salida):
            return False
        self.al_salir()
        return True

    def _linterna_equipada(self):
        return (
            self.game_state.linternaComprada
            and self.inventario.slot_seleccionado
            == self.inventario.SLOT_LINTERNA
        )

    def _interactuar_con_mate(self, eventos):
        if (
            self.game_state.mateRecolectado
            or not self._linterna_equipada()
        ):
            return
        zona_mate = pygame.Rect(
            self.mate_mapa[0] - 24,
            self.mate_mapa[1] - 24,
            48,
            48,
        )
        if not self.jugador.rectangulo.colliderect(zona_mate):
            return
        if any(
            evento.type == pygame.KEYDOWN and evento.key == pygame.K_e
            for evento in eventos
        ):
            self.game_state.mateRecolectado = True
            self.game_state.dia_recoleccion_mate = (
                self.game_state.dia_actual
            )
            self.mensaje = "Recogiste el mate."
            self.mensaje_hasta = pygame.time.get_ticks() + 3000

    def update(self, teclas, _limites_pantalla, eventos=()):
        if self.primera_entrada:
            self.jugador.rectangulo.center = (
                self.entrada_mapa[0],
                self.entrada_mapa[1] - 70,
            )
            self.primera_entrada = False

        if self._salir_por_entrada():
            return

        self._interactuar_con_mate(eventos)
        rect_previo = self.jugador.rectangulo.copy()
        self.jugador.actualizar(teclas)
        self.jugador.rectangulo.clamp_ip(self.fondo.get_rect())
        rect_destino = self.jugador.rectangulo.copy()

        self.jugador.rectangulo.x = rect_previo.x
        if rect_destino.y != rect_previo.y:
            self.jugador.rectangulo.y = rect_destino.y
            if any(
                self.jugador.rectangulo.colliderect(colision)
                for colision in self.colisiones_mapa
            ):
                self.jugador.rectangulo.y = rect_previo.y

        if rect_destino.x != rect_previo.x:
            self.jugador.rectangulo.x = rect_destino.x
            if any(
                self.jugador.rectangulo.colliderect(colision)
                for colision in self.colisiones_mapa
            ):
                self.jugador.rectangulo.x = rect_previo.x
        self._salir_por_entrada()

    def draw(self, pantalla):
        pantalla.fill((0, 0, 0))
        rect_fondo = self.fondo.get_rect(center=pantalla.get_rect().center)
        pantalla.blit(self.fondo, rect_fondo)

        tiene_luz = self._linterna_equipada()
        if tiene_luz and not self.game_state.mateRecolectado:
            pantalla.blit(
                self.sprite_mate,
                self.sprite_mate.get_rect(
                    center=(
                        rect_fondo.left + self.mate_mapa[0],
                        rect_fondo.top + self.mate_mapa[1],
                    )
                ),
            )

        centro_jugador = self.jugador.rectangulo.center
        centro_luz = (
            rect_fondo.left + centro_jugador[0],
            rect_fondo.top + centro_jugador[1],
        )
        capa_oscuridad = pygame.Surface(
            pantalla.get_size(),
            pygame.SRCALPHA,
        )
        capa_oscuridad.fill((0, 0, 0, 255))
        if tiene_luz:
            diametro_luz = self.RADIO_LINTERNA * 2 + 1
            mascara_luz = pygame.Surface(
                (diametro_luz, diametro_luz),
                pygame.SRCALPHA,
            )
            mascara_luz.fill((0, 0, 0, 255))
            pygame.draw.circle(
                mascara_luz,
                (0, 0, 0, 0),
                (self.RADIO_LINTERNA, self.RADIO_LINTERNA),
                self.RADIO_LINTERNA,
            )
            capa_oscuridad.blit(
                mascara_luz,
                (
                    centro_luz[0] - self.RADIO_LINTERNA,
                    centro_luz[1] - self.RADIO_LINTERNA,
                ),
                special_flags=pygame.BLEND_RGBA_MIN,
            )
        pantalla.blit(capa_oscuridad, (0, 0))
        self.jugador.dibujar(pantalla, rect_fondo.topleft)

        zona_salida = pygame.Rect(
            self.entrada_mapa[0] - 32,
            self.entrada_mapa[1] - 32,
            64,
            64,
        )
        if self.jugador.rectangulo.colliderect(zona_salida):
            indicacion = self.fuente.render(
                "Salida de la cueva",
                True,
                (255, 255, 255),
            )
            pantalla.blit(
                indicacion,
                indicacion.get_rect(
                    midtop=(pantalla.get_width() // 2, 20)
                ),
            )
        if (
            self._linterna_equipada()
            and not self.game_state.mateRecolectado
            and self.jugador.rectangulo.colliderect(
                pygame.Rect(
                    self.mate_mapa[0] - 24,
                    self.mate_mapa[1] - 24,
                    48,
                    48,
                )
            )
        ):
            indicacion = self.fuente.render(
                "E: recoger el mate",
                True,
                (255, 255, 255),
            )
            pantalla.blit(
                indicacion,
                indicacion.get_rect(
                    midtop=(pantalla.get_width() // 2, 48)
                ),
            )
        if (
            self.mensaje is not None
            and pygame.time.get_ticks() < self.mensaje_hasta
        ):
            mensaje = self.fuente.render(
                self.mensaje,
                True,
                (255, 255, 255),
            )
            pantalla.blit(
                mensaje,
                mensaje.get_rect(
                    midtop=(pantalla.get_width() // 2, 76)
                ),
            )
        self.interfaz_estado.dibujar(
            pantalla,
            self.game_state,
            dentro_zona_segura=True,
        )