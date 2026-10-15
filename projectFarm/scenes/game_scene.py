import os
import xml.etree.ElementTree as ET

import pygame
from pytmx import TiledTileLayer
from pytmx.util_pygame import load_pygame

from engine.scroll import Camera
from engine.spritesheet import Spritesheet
from engine.ui import Inventario
from ..entities import Jugador
from ..farm import CULTIVOS, Parcela
from ..scraps import Chatarra


class GameScene:
	def __init__(self, game_state, inventario, al_entrar_casa):
		self.game_state = game_state
		self.inventario = inventario
		self.jugador = Jugador()
		self.primera_entrada = True
		self.fondo = self._cargar_fondo()
		self.camera = Camera()
		self.origen_mapa = (0, 0)
		self.puerta = pygame.Rect(400, 230, 50, 70)
		self.al_entrar_casa = al_entrar_casa
		self._generar_chatarra()
		ancho_grilla = Parcela.TAMANO * 3
		alto_grilla = Parcela.TAMANO * 3
		origen_parcelas = (
			self.area_parcelas_mapa.left
			+ (self.area_parcelas_mapa.width - ancho_grilla) // 2,
			self.area_parcelas_mapa.top
			+ (self.area_parcelas_mapa.height - alto_grilla) // 2,
		)
		self.parcelas = [
			Parcela(
				origen_parcelas[0] + columna * Parcela.TAMANO,
				origen_parcelas[1] + fila * Parcela.TAMANO,
			)
			for fila in range(3)
			for columna in range(3)
		]
		self.posiciones_parcelas_mapa = [
			parcela.rectangulo.topleft for parcela in self.parcelas
		]
		self.parcela_seleccionada = None
		self.ultimo_cambio_zona_granja = pygame.time.get_ticks()
		
		
		self.fuente = pygame.font.Font(None, 28)
		
		ruta_zanahoria = os.path.join(
			os.path.dirname(__file__), "..", "utils", "ZanahoriaCrecimiento.json"
		)
		spritesheet_zanahoria = Spritesheet(ruta_zanahoria)
		self.sprites_cultivos = {
			tipo: {
				nombre_sprite: spritesheet_zanahoria.get_sprite(nombre_sprite)
				for nombre_sprite in datos["etapas"]
			}
			for tipo, datos in CULTIVOS.items()
		}


	def obtener_parcela_jugador(self, jugador, posicion=None):
		return next(
			(
				parcela
				for parcela in self.parcelas
				if jugador.rectangulo.colliderect(parcela.rectangulo)
				and (posicion is None or parcela.rectangulo.collidepoint(posicion))
			),
			None,
		)

	
	def _cargar_fondo(self):
		ruta_mapa = os.path.join(
			os.path.dirname(__file__), "..", "assets", "MarsMap.tmx"
		)
		mapa = load_pygame(os.path.normpath(ruta_mapa))
		capa_parcelas = mapa.get_layer_by_name("Parcelas")
		objeto_parcela = next(
			objeto for objeto in capa_parcelas if objeto.name == "Parcela1"
		)
		capa_chatarra = mapa.get_layer_by_name("Chatarra")
		objeto_zona_chatarra = next(
			objeto for objeto in capa_chatarra if objeto.name == "ZonaCh"
		)
		self.area_parcelas_mapa = pygame.Rect(
			round(objeto_parcela.x * 3),
			round(objeto_parcela.y * 3),
			round(objeto_parcela.width * 3),
			round(objeto_parcela.height * 3),
		)
		self.zona_chatarra_mapa = pygame.Rect(
			round(objeto_zona_chatarra.x * 3),
			round(objeto_zona_chatarra.y * 3),
			round(objeto_zona_chatarra.width * 3),
			round(objeto_zona_chatarra.height * 3),
		)
		self.colisiones_mapa = self._cargar_colisiones(
			os.path.normpath(ruta_mapa), mapa.tilewidth
		)
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
			fondo, (fondo.get_width() * 3, fondo.get_height() * 3)
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
					if ancho <= 0 or alto <= 0:
						continue
					rectangulos.append((x, y, ancho, alto))
				if rectangulos:
					colisiones_por_gid[first_gid + int(nodo_tile.attrib["id"])] = (
						rectangulos
					)

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
								round((x * ancho_tile + ox) * 3),
								round((y * ancho_tile + oy) * 3),
								round(ancho * 3),
								round(alto * 3),
							)
						)
		return colisiones

	def avanzar_dia(self):
		for parcela in self.parcelas:
			parcela.avanzar_dia(self.game_state.dia_actual)
		self.game_state.dia_actual += 1
		self.game_state.resistencia = 100
		self._generar_chatarra()

	def _generar_chatarra(self):
		self.chatarra = Chatarra.generar_en(self.zona_chatarra_mapa)
		self.posiciones_chatarra_mapa = [
			pieza.rectangulo.topleft for pieza in self.chatarra
		]

	def _colisiona_con_chatarra(self, rectangulo):
		rectangulo_mapa = self.camera.to_map(rectangulo)
		return any(
			rectangulo_mapa.colliderect(
				pieza.rectangulo.move(
					-self.origen_mapa[0],
					-self.origen_mapa[1],
				)
			)
			for pieza in self.chatarra
		)

	def update(self, teclas, limites_pantalla, eventos=()):
		
		

		rect_fondo = self.fondo.get_rect(center=limites_pantalla.center)
		self.origen_mapa = rect_fondo.topleft
		limites_mapa = pygame.Rect(
			self.origen_mapa,
			(self.fondo.get_width(), self.fondo.get_height()),
		)
		for parcela, (x, y) in zip(
			self.parcelas, self.posiciones_parcelas_mapa
		):
			parcela.rectangulo.topleft = (
				self.origen_mapa[0] + x,
				self.origen_mapa[1] + y,
			)
		for pieza, (x, y) in zip(
			self.chatarra, self.posiciones_chatarra_mapa
		):
			pieza.rectangulo.topleft = (
				self.origen_mapa[0] + x,
				self.origen_mapa[1] + y,
			)
		if self.primera_entrada:
			self.jugador.rectangulo.midtop = (
				self.puerta.centerx,
				self.puerta.bottom + 8,
			)
			self.primera_entrada = False
		self.camera.update(
			self.jugador.rectangulo, limites_pantalla, limites_mapa
		)
		rect_previo = self.jugador.rectangulo.copy()
		self.jugador.actualizar(teclas)
		self.jugador.rectangulo.clamp_ip(limites_mapa)
		rect_destino = self.jugador.rectangulo.copy()

		self.jugador.rectangulo.x = rect_previo.x
		if rect_destino.y != rect_previo.y:
			self.jugador.rectangulo.y = rect_destino.y
			if any(
				self.camera.to_map(self.jugador.rectangulo).colliderect(colision)
				for colision in self.colisiones_mapa
			) or self._colisiona_con_chatarra(self.jugador.rectangulo):
				self.jugador.rectangulo.y = rect_previo.y

		if rect_destino.x != rect_previo.x:
			self.jugador.rectangulo.x = rect_destino.x
			if any(
				self.camera.to_map(self.jugador.rectangulo).colliderect(colision)
				for colision in self.colisiones_mapa
			) or self._colisiona_con_chatarra(self.jugador.rectangulo):
				self.jugador.rectangulo.x = rect_previo.x

		self.camera.update(
			self.jugador.rectangulo, limites_pantalla, limites_mapa
		)
		if self.jugador.rectangulo.colliderect(self.puerta):
			self.primera_entrada = True
			self.al_entrar_casa()
			return

		self.parcela_seleccionada = self.obtener_parcela_jugador(self.jugador)
		
		for evento in eventos:
			if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
				continue
			if self.inventario.seleccionar_slot(
				evento.pos, limites_pantalla.width, limites_pantalla.height
			):
				continue
			parcela_clickeada = self.obtener_parcela_jugador(
				self.jugador, self.camera.to_world(evento.pos)
			)
			if parcela_clickeada is None:
				continue
			self.parcela_seleccionada = parcela_clickeada

			if parcela_clickeada.obtener_etapa() == "cosechable":
				if self.inventario.slot_seleccionado == Inventario.SLOT_MANO:
					parcela_clickeada.cosechar()
					self.game_state.zanahorias_cosechadas += 1
					self.game_state.resistencia -= 15
			elif self.inventario.slot_seleccionado == Inventario.SLOT_SEMILLA_ZANAHORIA:
				if parcela_clickeada.planta is None and self.game_state.semilla_zanahoria > 0:
					parcela_clickeada.plantar(1)
					self.game_state.semilla_zanahoria -= 1
					self.game_state.resistencia -= 10
			elif self.inventario.slot_seleccionado == Inventario.SLOT_REGADERA:
				if (
					parcela_clickeada.planta is not None
					and parcela_clickeada.dia_regado != self.game_state.dia_actual
				):
					parcela_clickeada.regar(self.game_state.dia_actual)
					self.game_state.resistencia -= 5

	def draw(self, pantalla):
		limites_pantalla = pantalla.get_rect()
		if self.fondo is not None:
			rect_fondo = self.camera.apply(
				self.fondo.get_rect(topleft=self.origen_mapa)
			)
			pantalla.blit(self.fondo, rect_fondo)
			for colision in self.colisiones_mapa:
				pygame.draw.rect(
					pantalla,
					(255, 0, 0),
					self.camera.apply(
						colision.move(self.camera.world_bounds.topleft)
					),
					1,
				)
		else:
			pantalla.fill((99, 60, 58))
		for parcela in self.parcelas:
			parcela.dibujar(
				pantalla,
				self.game_state.dia_actual,
				self.sprites_cultivos,
				self.camera.screen_offset,
			)
		for pieza in self.chatarra:
			pieza.dibujar(pantalla, self.camera.screen_offset)
		
		
		desplazamiento_mundo = self.camera.screen_offset
		self.jugador.dibujar(pantalla, desplazamiento_mundo)
		
		#for i, cuadrado in enumerate(self.cuadrados):
			#pygame.draw.rect(pantalla, self.colores_cuadrados[i], cuadrado)
			#pygame.draw.rect(pantalla, (30, 30, 30), cuadrado, 2)
		
		texto_dia = self.fuente.render(f"Dia = {self.game_state.dia_actual}", True, (255, 255, 255))
		pantalla.blit(texto_dia, (10, 10))
		etapa = (
			self.parcela_seleccionada.obtener_etapa()
			if self.parcela_seleccionada is not None
			else "-"
		)
		if self.parcela_seleccionada is not None and etapa == self.parcela_seleccionada.planta:
			etapa = CULTIVOS[etapa]["nombre"]
		texto_etapa = self.fuente.render(f"Etapa = {etapa}", True, (255, 255, 255))
		pantalla.blit(texto_etapa, (10, 38))
		texto_semilla = self.fuente.render(f"Semillas = {self.game_state.semilla_zanahoria}", True, (255, 255, 255))
		pantalla.blit(texto_semilla, (10, 66))
		if self.parcela_seleccionada is not None and self.parcela_seleccionada.planta is not None:
			regada = self.parcela_seleccionada.dia_regado == self.game_state.dia_actual
			texto_riego = self.fuente.render(f"Regada hoy = {'si' if regada else 'no'}", True, (255, 255, 255))
			pantalla.blit(texto_riego, (10, 94))
		texto_zanahorias = self.fuente.render(f"Zanahorias cosechadas = {self.game_state.zanahorias_cosechadas}", True, (255, 255, 255))
		pantalla.blit(texto_zanahorias, (10, 122))
		texto_resistencia = self.fuente.render(f"Resistencia = {self.game_state.resistencia}", True, (255, 255, 255))
		pantalla.blit(texto_resistencia, (10, 150))
		texto_creditos = self.fuente.render(f"Creditos = {self.game_state.creditos}", True, (255, 255, 255))
		pantalla.blit(texto_creditos, (10, 178))
		self.inventario.dibujar(pantalla, self.game_state.semilla_zanahoria)
