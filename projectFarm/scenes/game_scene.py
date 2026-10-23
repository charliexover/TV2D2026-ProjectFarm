import os
import random
import xml.etree.ElementTree as ET

import pygame
from pytmx import TiledTileLayer
from pytmx.util_pygame import load_pygame

from engine.audio import reproducir_sonido_interaccion
from engine.minigame1 import Minijuego1
from engine.scroll import Camera
from engine.spritesheet import Spritesheet
from engine.ui import InterfazEstado, Inventario
from ..entities import Jugador
from ..farm import CULTIVOS, Parcela
from ..scraps import Chatarra
from .skilltree_scene import SkillTreeMenu


class GameScene:
	SEGUNDOS_POR_PUNTO_OXIGENO = 0.2
	DESPLAZAMIENTO_ENTRADA_DATOS_X = 12
	DURACION_ANIMACION_SUENO = 1800
	DURACION_FUNDIDO_SUENO = 800
	DURACION_CARTEL_DIA_SUENO = 2100
	INTERVALO_FRAME_SUENO = 250

	def __init__(
		self,
		game_state,
		inventario,
		al_entrar_casa,
		al_entrar_reciclaje,
		al_entrar_data_center,
		al_entrar_expedicion,
		al_desmayarse=None,
		al_completar_desmayo=None,
	):
		self.game_state = game_state
		self.inventario = inventario
		self.interfaz_estado = InterfazEstado()
		self.jugador = Jugador()
		self.primera_entrada = True
		self.puerta_reentrada = "casa"
		self.fondo = self._cargar_fondo()
		self.menu_habilidades = SkillTreeMenu()
		self.camera = Camera()
		self.origen_mapa = (0, 0)
		self.al_entrar_casa = al_entrar_casa
		self.al_entrar_reciclaje = al_entrar_reciclaje
		self.al_entrar_data_center = al_entrar_data_center
		self.al_entrar_expedicion = al_entrar_expedicion
		self.al_desmayarse = al_desmayarse
		self.al_completar_desmayo = al_completar_desmayo
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
		self.transicion_desmayo_inicio = None
		self.dia_avanzado_durante_desmayo = False
		self.mensaje_resultado_desmayo = None
		self._generar_chatarra()
		self.campos_disponibilidad_parcelas = {
			"Parcela1": "parcela1Disponible",
			"Parcela2": "parcela2Disponible",
			"Parcela3": "parcela3Disponible",
		}
		self.parcelas_por_nodo = {}
		for nombre, area in self.areas_parcelas_mapa.items():
			ancho_grilla = Parcela.TAMANO * 3
			alto_grilla = Parcela.TAMANO * 3
			origen_parcelas = (
				area.left + (area.width - ancho_grilla) // 2,
				area.top + (area.height - alto_grilla) // 2,
			)
			self.parcelas_por_nodo[nombre] = [
				Parcela(
					origen_parcelas[0] + columna * Parcela.TAMANO,
					origen_parcelas[1] + fila * Parcela.TAMANO,
				)
				for fila in range(3)
				for columna in range(3)
			]
		self.parcelas = [
			parcela
			for parcelas in self.parcelas_por_nodo.values()
			for parcela in parcelas
		]
		ruta_sprite_parcela = os.path.join(
			os.path.dirname(__file__), "..", "assets", "parcelaSprite.png"
		)
		sprite_parcela = pygame.image.load(
			os.path.normpath(ruta_sprite_parcela)
		).convert_alpha()
		self.sprites_parcelas_mapa = {}
		self.rectangulos_parcelas_mapa = {}
		for nombre in ("Parcela2", "Parcela3"):
			area = self.areas_parcelas_mapa[nombre]
			self.sprites_parcelas_mapa[nombre] = pygame.transform.scale(
				sprite_parcela,
				(
					sprite_parcela.get_width() * 3,
					sprite_parcela.get_height() * 3,
				),
			)
			self.rectangulos_parcelas_mapa[nombre] = (
				self.sprites_parcelas_mapa[nombre].get_rect(center=area.center)
			)
		self.posiciones_parcelas_mapa = [
			parcela.rectangulo.topleft for parcela in self.parcelas
		]
		self.parcela_seleccionada = None
		self.ultimo_cambio_zona_granja = pygame.time.get_ticks()
		
		
		self.fuente = pygame.font.Font(None, 28)
		self.mensaje_antena = None
		self.mensaje_antena_hasta = 0
		self.minijuego_antena = Minijuego1()
		self.ultimo_update_oxigeno = None
		self.segundos_acumulados_oxigeno = 0
		ruta_efecto = os.path.join(
			os.path.dirname(__file__), "..", "assets", "SoundEffect1.wav"
		)
		self.efecto_accion = pygame.mixer.Sound(os.path.normpath(ruta_efecto))
		ruta_chatarra = os.path.join(
			os.path.dirname(__file__), "..", "assets", "chatarraSprite.png"
		)
		sprite_chatarra = pygame.image.load(ruta_chatarra).convert_alpha()
		self.sprite_chatarra = pygame.transform.scale(
			sprite_chatarra, (Chatarra.TAMANO, Chatarra.TAMANO)
		)
		
		ruta_cosechas = os.path.join(
			os.path.dirname(__file__), "..", "utils", "CosechasSpritesheet.json"
		)
		spritesheet_cosechas = Spritesheet(ruta_cosechas)
		self.sprites_cultivos = {
			tipo: {
				nombre_sprite: spritesheet_cosechas.get_sprite(nombre_sprite)
				for nombre_sprite in (*datos["etapas"], "cosechaSeca")
			}
			for tipo, datos in CULTIVOS.items()
		}


	def obtener_parcela_jugador(self, jugador, posicion=None):
		return next(
			(
				parcela
				for nombre, parcelas in self.parcelas_por_nodo.items()
				if getattr(
					self.game_state,
					self.campos_disponibilidad_parcelas[nombre],
				)
				for parcela in parcelas
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
		capa_antenas = mapa.get_layer_by_name("Antenas")
		self.antenas_mapa = {
			objeto.name: (round(objeto.x * 3), round(objeto.y * 3))
			for objeto in capa_antenas
		}
		capa_parcelas = mapa.get_layer_by_name("Parcelas")
		objetos_parcelas = {
			objeto.name: objeto for objeto in capa_parcelas
		}
		nombres_parcelas = ("Parcela1", "Parcela2", "Parcela3")
		if any(nombre not in objetos_parcelas for nombre in nombres_parcelas):
			raise ValueError("Falta una parcela requerida en la capa 'Parcelas'.")
		self.areas_parcelas_mapa = {
			nombre: pygame.Rect(
				round(objetos_parcelas[nombre].x * 3),
				round(objetos_parcelas[nombre].y * 3),
				round(objetos_parcelas[nombre].width * 3),
				round(objetos_parcelas[nombre].height * 3),
			)
			for nombre in nombres_parcelas
		}
		self.area_parcelas_mapa = self.areas_parcelas_mapa["Parcela1"]
		capa_chatarra = mapa.get_layer_by_name("Chatarra")
		objeto_zona_chatarra = next(
			objeto for objeto in capa_chatarra if objeto.name == "ZonaCh"
		)
		capa_puertas = mapa.get_layer_by_name("Puertas")
		objeto_puerta_casa = next(
			objeto for objeto in capa_puertas if objeto.name == "Casa"
		)
		self.puerta_casa_mapa = (
			round(objeto_puerta_casa.x * 3),
			round(objeto_puerta_casa.y * 3),
		)
		objeto_puerta_reciclaje = next(
			objeto for objeto in capa_puertas if objeto.name == "Reciclaje"
		)
		self.puerta_reciclaje_mapa = (
			round(objeto_puerta_reciclaje.x * 3),
			round(objeto_puerta_reciclaje.y * 3),
		)
		objeto_puerta_datos = next(
			objeto for objeto in capa_puertas if objeto.name == "Datos"
		)
		posicion_sprite_datos_mapa = (
			round(objeto_puerta_datos.x * 3),
			round(objeto_puerta_datos.y * 3),
		)
		self.puerta_datos_mapa = (
			posicion_sprite_datos_mapa[0]
			- self.DESPLAZAMIENTO_ENTRADA_DATOS_X,
			posicion_sprite_datos_mapa[1],
		)
		objeto_puerta_expedicion = next(
			objeto for objeto in capa_puertas if objeto.name == "Expedicion"
		)
		self.puerta_expedicion_mapa = (
			round(objeto_puerta_expedicion.x * 3),
			round(objeto_puerta_expedicion.y * 3),
		)
		ruta_sprite_bloque = os.path.join(
			os.path.dirname(__file__), "..", "assets", "BlockSprite.png"
		)
		sprite_bloque = pygame.image.load(
			os.path.normpath(ruta_sprite_bloque)
		).convert_alpha()
		self.sprite_bloque = pygame.transform.scale(
			sprite_bloque,
			(sprite_bloque.get_width() * 3, sprite_bloque.get_height() * 3),
		)
		self.bloques_edificios = {
			"reciclajeDisponible": (
				"Centro de Reciclaje",
				self.sprite_bloque.get_rect(
					midbottom=self.puerta_reciclaje_mapa
				),
			),
			"centroDatosDisponible": (
				"Centro de Datos",
				self.sprite_bloque.get_rect(
					midbottom=posicion_sprite_datos_mapa
				),
			),
			"expedicionesDisponible": (
				"Centro de Expediciones",
				self.sprite_bloque.get_rect(
					midbottom=self.puerta_expedicion_mapa
				),
			),
		}
		ruta_sprite_oxigeno = os.path.join(
			os.path.dirname(__file__), "..", "assets", "oxigenSprite.png"
		)
		sprite_oxigeno = pygame.image.load(
			os.path.normpath(ruta_sprite_oxigeno)
		).convert_alpha()
		self.sprite_oxigeno = pygame.transform.scale(
			sprite_oxigeno,
			(
				sprite_oxigeno.get_width() * 3,
				sprite_oxigeno.get_height() * 3,
			),
		)
		capa_tanques_oxigeno = mapa.get_layer_by_name("TanquesOxigeno")
		self.tanques_oxigeno_mapa = {
			objeto.name: self.sprite_oxigeno.get_rect(
				midbottom=(round(objeto.x * 3), round(objeto.y * 3))
			)
			for objeto in capa_tanques_oxigeno
			if objeto.name in ("TanqueOeste", "TanqueNorte", "TanqueEste")
		}
		self.campos_uso_tanques = {
			"TanqueOeste": "dia_uso_tanque_oeste",
			"TanqueNorte": "dia_uso_tanque_norte",
			"TanqueEste": "dia_uso_tanque_este",
		}
		self.campos_compra_tanques = {
			"TanqueEste": "tanqueOxigenoEsteDisponible",
			"TanqueOeste": "tanqueOxigenoOesteDisponible",
			"TanqueNorte": "tanqueOxigenoNorteDisponible",
		}
		ruta_sprite_datos = os.path.join(
			os.path.dirname(__file__),
			"..",
			"assets",
			"DataCenterSprite.png",
		)
		sprite_datos = pygame.image.load(
			os.path.normpath(ruta_sprite_datos)
		).convert_alpha()
		self.sprite_data_center = pygame.transform.scale(
			sprite_datos,
			(sprite_datos.get_width() * 3, sprite_datos.get_height() * 3),
		)
		self.sprite_data_center_rect = self.sprite_data_center.get_rect(
			midbottom=posicion_sprite_datos_mapa
		)
		self.colisiones_data_center = self._crear_colisiones_edificio(
			self.sprite_data_center_rect
		)
		posicion_sprite_reciclaje_mapa = self.puerta_reciclaje_mapa
		ruta_sprite_reciclaje = os.path.join(
			os.path.dirname(__file__),
			"..",
			"assets",
			"CentroReciclajeSprite.png",
		)
		sprite_reciclaje = pygame.image.load(
			os.path.normpath(ruta_sprite_reciclaje)
		).convert_alpha()
		self.sprite_centro_reciclaje = pygame.transform.scale(
			sprite_reciclaje,
			(
				sprite_reciclaje.get_width() * 3,
				sprite_reciclaje.get_height() * 3,
			),
		)
		self.sprite_centro_reciclaje_rect = (
			self.sprite_centro_reciclaje.get_rect(
				midbottom=posicion_sprite_reciclaje_mapa
			)
		)
		self.colisiones_reciclaje = self._crear_colisiones_edificio(
			self.sprite_centro_reciclaje_rect
		)
		ruta_sprite_expedicion = os.path.join(
			os.path.dirname(__file__),
			"..",
			"assets",
			"CentroExpedicionSprite.png",
		)
		sprite_expedicion = pygame.image.load(
			os.path.normpath(ruta_sprite_expedicion)
		).convert_alpha()
		self.sprite_centro_expedicion = pygame.transform.scale(
			sprite_expedicion,
			(
				sprite_expedicion.get_width() * 3,
				sprite_expedicion.get_height() * 3,
			),
		)
		self.sprite_centro_expedicion_rect = (
			self.sprite_centro_expedicion.get_rect(
				midbottom=self.puerta_expedicion_mapa
			)
		)
		self.colisiones_expedicion = self._crear_colisiones_edificio(
			self.sprite_centro_expedicion_rect
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

	def _crear_colisiones_edificio(self, rect_edificio):
		ancho_entrada = self.jugador.rectangulo.width + 8
		alto_entrada = self.jugador.rectangulo.height + 8
		ancho_lateral = (rect_edificio.width - ancho_entrada) // 2
		alto_pared = rect_edificio.height - alto_entrada
		return [
			pygame.Rect(
				rect_edificio.left,
				rect_edificio.top,
				rect_edificio.width,
				alto_pared,
			),
			pygame.Rect(
				rect_edificio.left,
				rect_edificio.bottom - alto_entrada,
				ancho_lateral,
				alto_entrada,
			),
			pygame.Rect(
				rect_edificio.right - ancho_lateral,
				rect_edificio.bottom - alto_entrada,
				ancho_lateral,
				alto_entrada,
			),
		]

	def avanzar_dia(self):
		for parcela in self.parcelas:
			parcela.avanzar_dia(self.game_state.dia_actual)
		self.game_state.dia_actual += 1
		if self.game_state.parcela2Comprada:
			self.game_state.parcela2Disponible = True
		if self.game_state.parcela3Comprada:
			self.game_state.parcela3Disponible = True
		if self.game_state.centroDatosComprado:
			self.game_state.centroDatosDisponible = True
		if self.game_state.reciclajeComprado:
			self.game_state.reciclajeDisponible = True
		if self.game_state.expedicionesComprado:
			self.game_state.expedicionesDisponible = True
		if self.game_state.tanqueOxigenoEsteComprado:
			self.game_state.tanqueOxigenoEsteDisponible = True
		if self.game_state.tanqueOxigenoOesteComprado:
			self.game_state.tanqueOxigenoOesteDisponible = True
		if self.game_state.tanqueOxigenoNorteComprado:
			self.game_state.tanqueOxigenoNorteDisponible = True
		self.game_state.oxigeno = 100
		self.segundos_acumulados_oxigeno = 0
		self.ultimo_update_oxigeno = None
		self._generar_chatarra()

	def _iniciar_desmayo(self):
		if self.transicion_desmayo_inicio is not None:
			return
		self.transicion_desmayo_inicio = pygame.time.get_ticks()
		self.dia_avanzado_durante_desmayo = False
		self.canal_musica_sueno = self.musica_sueno.play()

	def _actualizar_desmayo(self):
		inicio = self.transicion_desmayo_inicio
		if inicio is None:
			return

		tiempo_transcurrido = pygame.time.get_ticks() - inicio
		inicio_dia_siguiente = (
			self.DURACION_ANIMACION_SUENO + self.DURACION_FUNDIDO_SUENO
		)
		if (
			tiempo_transcurrido >= inicio_dia_siguiente
			and not self.dia_avanzado_durante_desmayo
		):
			if self.al_desmayarse is None:
				raise RuntimeError(
					"No hay una accion configurada para procesar el desmayo."
				)
			self.mensaje_resultado_desmayo = self.al_desmayarse()
			self.dia_avanzado_durante_desmayo = True

		duracion_total = (
			self.DURACION_ANIMACION_SUENO
			+ self.DURACION_FUNDIDO_SUENO * 2
			+ self.DURACION_CARTEL_DIA_SUENO
		)
		if tiempo_transcurrido < duracion_total:
			return

		if self.canal_musica_sueno is not None:
			self.canal_musica_sueno.stop()
		self.canal_musica_sueno = None
		self.transicion_desmayo_inicio = None
		if self.al_completar_desmayo is None:
			raise RuntimeError(
				"No hay una accion configurada para finalizar el desmayo."
			)
		self.al_completar_desmayo(self.mensaje_resultado_desmayo)

	def _actualizar_oxigeno_exterior(self, jugador_en_movimiento):
		ahora = pygame.time.get_ticks()
		if self.ultimo_update_oxigeno is None:
			self.ultimo_update_oxigeno = ahora
			return

		delta_segundos = max(0, ahora - self.ultimo_update_oxigeno) / 1000
		self.ultimo_update_oxigeno = ahora
		if not jugador_en_movimiento:
			return

		if self.game_state.oxigeno <= 0:
			self.game_state.oxigeno = 0
			self.segundos_acumulados_oxigeno = 0
			return

		self.segundos_acumulados_oxigeno += delta_segundos
		puntos_perdidos = int(
			self.segundos_acumulados_oxigeno
			// self.SEGUNDOS_POR_PUNTO_OXIGENO
		)
		if puntos_perdidos:
			self.game_state.oxigeno = max(
				0, self.game_state.oxigeno - puntos_perdidos
			)
			self.segundos_acumulados_oxigeno %= (
				self.SEGUNDOS_POR_PUNTO_OXIGENO
			)

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

	def _colisiona_con_edificios(self, rectangulo):
		rectangulo_mapa = self.camera.to_map(rectangulo)
		colisiones = []
		if self.game_state.centroDatosDisponible:
			colisiones.extend(self.colisiones_data_center)
		if self.game_state.reciclajeDisponible:
			colisiones.extend(self.colisiones_reciclaje)
		if self.game_state.expedicionesDisponible:
			colisiones.extend(self.colisiones_expedicion)
		colisiones.extend(
			rectangulo
			for atributo_disponible, (_, rectangulo)
			in self.bloques_edificios.items()
			if not getattr(self.game_state, atributo_disponible)
		)
		colisiones.extend(
			rectangulo
			for nombre, rectangulo in self.tanques_oxigeno_mapa.items()
			if getattr(
				self.game_state, self.campos_compra_tanques[nombre]
			)
		)
		return any(rectangulo_mapa.colliderect(colision) for colision in colisiones)

	def update(self, teclas, limites_pantalla, eventos=()):
		if self.transicion_desmayo_inicio is not None:
			self._actualizar_desmayo()
			return

		if self.minijuego_antena.activo:
			if self.minijuego_antena.actualizar(eventos):
				self.game_state.antena_encontrada = True
				self._mostrar_mensaje_antena(
					f"Datos de Antena "
					f"{self.game_state.antena_objetivo} descargados."
				)
			return

		if self.menu_habilidades.procesar_eventos(
			eventos, limites_pantalla, self.game_state
		):
			return

		
		

		rect_fondo = self.fondo.get_rect(center=limites_pantalla.center)
		self.origen_mapa = rect_fondo.topleft
		puerta_casa = (
			self.origen_mapa[0] + self.puerta_casa_mapa[0],
			self.origen_mapa[1] + self.puerta_casa_mapa[1],
		)
		puerta_reciclaje = (
			self.origen_mapa[0] + self.puerta_reciclaje_mapa[0],
			self.origen_mapa[1] + self.puerta_reciclaje_mapa[1],
		)
		puerta_datos = (
			self.origen_mapa[0] + self.puerta_datos_mapa[0],
			self.origen_mapa[1] + self.puerta_datos_mapa[1],
		)
		puerta_expedicion = (
			self.origen_mapa[0] + self.puerta_expedicion_mapa[0],
			self.origen_mapa[1] + self.puerta_expedicion_mapa[1],
		)
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
			punto_entrada = (
				puerta_reciclaje
				if self.puerta_reentrada == "reciclaje"
				else (
					puerta_datos
					if self.puerta_reentrada == "dataCenter"
					else (
						puerta_expedicion
						if self.puerta_reentrada == "expedicion"
						else puerta_casa
					)
				)
			)
			self.jugador.rectangulo.midtop = (
				punto_entrada[0],
				punto_entrada[1] + 8,
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
			) or self._colisiona_con_chatarra(
				self.jugador.rectangulo
			) or self._colisiona_con_edificios(self.jugador.rectangulo):
				self.jugador.rectangulo.y = rect_previo.y

		if rect_destino.x != rect_previo.x:
			self.jugador.rectangulo.x = rect_destino.x
			if any(
				self.camera.to_map(self.jugador.rectangulo).colliderect(colision)
				for colision in self.colisiones_mapa
			) or self._colisiona_con_chatarra(
				self.jugador.rectangulo
			) or self._colisiona_con_edificios(self.jugador.rectangulo):
				self.jugador.rectangulo.x = rect_previo.x

		jugador_en_movimiento = (
			self.jugador.rectangulo.topleft != rect_previo.topleft
		)
		self._actualizar_oxigeno_exterior(jugador_en_movimiento)
		if self.game_state.oxigeno <= 0:
			self._iniciar_desmayo()
			return

		if self.jugador.rectangulo.topleft != rect_previo.topleft:
			self.mensaje_antena = None

		self.camera.update(
			self.jugador.rectangulo, limites_pantalla, limites_mapa
		)
		if self.jugador.rectangulo.collidepoint(puerta_casa):
			self.primera_entrada = True
			self.puerta_reentrada = "casa"
			self.ultimo_update_oxigeno = None
			self.al_entrar_casa()
			return
		if (
			self.game_state.reciclajeDisponible
			and self.jugador.rectangulo.collidepoint(puerta_reciclaje)
		):
			self.primera_entrada = True
			self.puerta_reentrada = "reciclaje"
			self.ultimo_update_oxigeno = None
			self.al_entrar_reciclaje()
			return
		if (
			self.game_state.centroDatosDisponible
			and self.jugador.rectangulo.collidepoint(puerta_datos)
		):
			self.primera_entrada = True
			self.puerta_reentrada = "dataCenter"
			self.ultimo_update_oxigeno = None
			self.al_entrar_data_center()
			return
		if (
			self.game_state.expedicionesDisponible
			and self.jugador.rectangulo.collidepoint(puerta_expedicion)
		):
			self.primera_entrada = True
			self.puerta_reentrada = "expedicion"
			self.ultimo_update_oxigeno = None
			self.al_entrar_expedicion()
			return

		self.parcela_seleccionada = self.obtener_parcela_jugador(self.jugador)
		
		self._interactuar_con_antenas(eventos)
		self._interactuar_con_lugares_construccion(eventos)
		self._interactuar_con_tanques_oxigeno(eventos)

		for evento in eventos:
			if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
				continue
			if self.inventario.seleccionar_slot(
				evento.pos, limites_pantalla.width, limites_pantalla.height
			):
				continue
			posicion_mundo = self.camera.to_world(evento.pos)
			chatarra_clickeada = next(
				(
					pieza
					for pieza in self.chatarra
					if pieza.rectangulo.collidepoint(posicion_mundo)
				),
				None,
			)
			if (
				chatarra_clickeada is not None
				and self.jugador.rectangulo.inflate(
					Chatarra.TAMANO, Chatarra.TAMANO
				).colliderect(chatarra_clickeada.rectangulo)
			):
				if not self.game_state.guanteReforzado:
					self.menu_habilidades.mostrar_mensaje(
						"Necesitas mejores guantes para recoger chatarra."
					)
					return
				indice_chatarra = self.chatarra.index(chatarra_clickeada)
				self.game_state.chatarra += random.randint(1, 4)
				self.chatarra.pop(indice_chatarra)
				self.posiciones_chatarra_mapa.pop(indice_chatarra)
				self.efecto_accion.play()
				continue
			parcela_clickeada = self.obtener_parcela_jugador(
				self.jugador, posicion_mundo
			)
			if parcela_clickeada is None:
				continue
			self.parcela_seleccionada = parcela_clickeada

			if parcela_clickeada.seca:
				if (
					self.inventario.slot_seleccionado == Inventario.SLOT_MANO
					and parcela_clickeada.retirar_seca()
				):
					self.efecto_accion.play()
			elif parcela_clickeada.obtener_etapa() == "cosechable":
				if self.inventario.slot_seleccionado == Inventario.SLOT_MANO:
					tipo_cultivo = parcela_clickeada.planta
					if parcela_clickeada.cosechar(self.game_state.dia_actual):
						cultivo = CULTIVOS[tipo_cultivo]
						setattr(
							self.game_state,
							cultivo["cosecha"],
							getattr(self.game_state, cultivo["cosecha"])
							+ cultivo["cantidad_cosecha"],
						)
						self.efecto_accion.play()
			elif self.inventario.slot_seleccionado in Inventario.SLOTS_SEMILLAS:
				tipo_cultivo = Inventario.SLOTS_SEMILLAS[
					self.inventario.slot_seleccionado
				]
				semilla = CULTIVOS[tipo_cultivo]["semilla"]
				if parcela_clickeada.planta is None and getattr(self.game_state, semilla) > 0:
					parcela_clickeada.plantar(tipo_cultivo)
					setattr(self.game_state, semilla, getattr(self.game_state, semilla) - 1)
					self.efecto_accion.play()
			elif self.inventario.slot_seleccionado == Inventario.SLOT_REGADERA:
				if (
					parcela_clickeada.planta is not None
					and parcela_clickeada.dia_regado != self.game_state.dia_actual
				):
					parcela_clickeada.regar(self.game_state.dia_actual)

	def _mostrar_mensaje_antena(self, texto):
		self.mensaje_antena = texto
		self.mensaje_antena_hasta = pygame.time.get_ticks() + 3000

	def _interactuar_con_antenas(self, eventos):
		jugador_mapa = self.camera.to_map(self.jugador.rectangulo)
		for evento in eventos:
			if evento.type != pygame.KEYDOWN or evento.key != pygame.K_e:
				continue
			for nombre, (x, y) in self.antenas_mapa.items():
				zona_interaccion = pygame.Rect(x - 32, y - 32, 64, 64)
				if not jugador_mapa.colliderect(zona_interaccion):
					continue

				reproducir_sonido_interaccion()
				mision_activa = (
					self.game_state.dia_mision_antena
					== self.game_state.dia_actual
					and self.game_state.antena_objetivo is not None
					and not self.game_state.antena_encontrada
					and not self.game_state.datos_antena_enviados
				)
				if mision_activa and nombre == self.game_state.antena_objetivo:
					self.mensaje_antena = None
					self.minijuego_antena.iniciar()
				elif mision_activa:
					self._mostrar_mensaje_antena(
						f"La Antena {nombre} esta operando correctamente."
						f"{self.game_state.antena_objetivo}."
					)
				else:
					self._mostrar_mensaje_antena(
						f"Antena {nombre}."
					)
				break

	def _interactuar_con_lugares_construccion(self, eventos):
		if not any(
			evento.type == pygame.KEYDOWN and evento.key == pygame.K_e
			for evento in eventos
		):
			return

		jugador_mapa = self.camera.to_map(self.jugador.rectangulo)
		for atributo_disponible, (nombre, rectangulo) in (
			self.bloques_edificios.items()
		):
			if getattr(self.game_state, atributo_disponible):
				continue
			zona_interaccion = rectangulo.inflate(
				self.jugador.rectangulo.width + 24,
				self.jugador.rectangulo.height + 24,
			)
			if jugador_mapa.colliderect(zona_interaccion):
				self._mostrar_mensaje_antena(
					f"Lugar de construccion: {nombre}."
				)
				reproducir_sonido_interaccion()
				break

	def _interactuar_con_tanques_oxigeno(self, eventos):
		if not any(
			evento.type == pygame.KEYDOWN and evento.key == pygame.K_e
			for evento in eventos
		):
			return

		jugador_mapa = self.camera.to_map(self.jugador.rectangulo)
		for nombre, rectangulo in self.tanques_oxigeno_mapa.items():
			if not getattr(
				self.game_state, self.campos_compra_tanques[nombre]
			):
				continue
			zona_interaccion = rectangulo.inflate(
				self.jugador.rectangulo.width + 24,
				self.jugador.rectangulo.height + 24,
			)
			if not jugador_mapa.colliderect(zona_interaccion):
				continue

			campo_uso = self.campos_uso_tanques[nombre]
			if getattr(self.game_state, campo_uso) == self.game_state.dia_actual:
				self._mostrar_mensaje_antena(
					f"El {nombre} ya fue utilizado hoy."
				)
				break

			self.game_state.oxigeno = 100
			setattr(self.game_state, campo_uso, self.game_state.dia_actual)
			self._mostrar_mensaje_antena(
				f"Oxígeno recargado al máximo en el {nombre}."
			)
			reproducir_sonido_interaccion()
			break

	def _envolver_texto_mensaje(self, texto, ancho_maximo):
		lineas = []
		linea = ""
		for palabra in texto.split():
			candidata = f"{linea} {palabra}".strip()
			if linea and self.fuente.size(candidata)[0] > ancho_maximo:
				lineas.append(linea)
				linea = palabra
			else:
				linea = candidata
		if linea:
			lineas.append(linea)
		return lineas

	def draw(self, pantalla):
		if self.minijuego_antena.activo:
			self.minijuego_antena.dibujar(pantalla)
			return

		limites_pantalla = pantalla.get_rect(		)
		if self.fondo is not None:
			rect_fondo = self.camera.apply(
				self.fondo.get_rect(topleft=self.origen_mapa)
			)
			pantalla.blit(self.fondo, rect_fondo)
			if self.game_state.centroDatosDisponible:
				pantalla.blit(
					self.sprite_data_center,
					self.camera.apply(
						self.sprite_data_center_rect.move(self.origen_mapa)
					),
				)
			if self.game_state.reciclajeDisponible:
				pantalla.blit(
					self.sprite_centro_reciclaje,
					self.camera.apply(
						self.sprite_centro_reciclaje_rect.move(
							self.origen_mapa
						)
					),
				)
			if self.game_state.expedicionesDisponible:
				pantalla.blit(
					self.sprite_centro_expedicion,
					self.camera.apply(
						self.sprite_centro_expedicion_rect.move(
							self.origen_mapa
						)
					),
				)
			for atributo_disponible, (_, rectangulo) in (
				self.bloques_edificios.items()
			):
				if getattr(self.game_state, atributo_disponible):
					continue
				pantalla.blit(
					self.sprite_bloque,
					self.camera.apply(rectangulo.move(self.origen_mapa)),
				)
			for nombre, rectangulo in self.tanques_oxigeno_mapa.items():
				if not getattr(
					self.game_state, self.campos_compra_tanques[nombre]
				):
					continue
				pantalla.blit(
					self.sprite_oxigeno,
					self.camera.apply(rectangulo.move(self.origen_mapa)),
				)
		else:
			pantalla.fill((99, 60, 58))
		for nombre, parcelas in self.parcelas_por_nodo.items():
			if not getattr(
				self.game_state,
				self.campos_disponibilidad_parcelas[nombre],
			):
				continue
			if nombre in self.sprites_parcelas_mapa:
				pantalla.blit(
					self.sprites_parcelas_mapa[nombre],
					self.camera.apply(
						self.rectangulos_parcelas_mapa[nombre].move(
							self.origen_mapa
						)
					),
				)
			for parcela in parcelas:
				parcela.dibujar(
					pantalla,
					self.game_state.dia_actual,
					self.sprites_cultivos,
					self.camera.screen_offset,
				)
		for pieza in self.chatarra:
			pieza.dibujar(
				pantalla, self.sprite_chatarra, self.camera.screen_offset
			)
		
		
		desplazamiento_mundo = self.camera.screen_offset
		if self.transicion_desmayo_inicio is None:
			self.jugador.dibujar(pantalla, desplazamiento_mundo)
		else:
			tiempo_transcurrido = (
				pygame.time.get_ticks() - self.transicion_desmayo_inicio
			)
			if tiempo_transcurrido < (
				self.DURACION_ANIMACION_SUENO + self.DURACION_FUNDIDO_SUENO
			):
				indice_sprite = (
					tiempo_transcurrido // self.INTERVALO_FRAME_SUENO
				) % len(self.sprites_sueno)
				sprite_sueno = self.sprites_sueno[indice_sprite]
				posicion_sueno = sprite_sueno.get_rect(
					center=self.jugador.rectangulo.center
				)
				posicion_sueno.move_ip(desplazamiento_mundo)
				pantalla.blit(sprite_sueno, posicion_sueno)
		
		#for i, cuadrado in enumerate(self.cuadrados):
			#pygame.draw.rect(pantalla, self.colores_cuadrados[i], cuadrado)
			#pygame.draw.rect(pantalla, (30, 30, 30), cuadrado, 2)
		
		
		self.interfaz_estado.dibujar(
			pantalla,
			self.game_state,
			mostrar_chatarra=True,
			mostrar_materiales=True,
		)
		self.inventario.dibujar(pantalla, self.game_state)
		jugador_mapa = self.camera.to_map(self.jugador.rectangulo)
		for atributo_disponible, (nombre, rectangulo) in (
			self.bloques_edificios.items()
		):
			if getattr(self.game_state, atributo_disponible):
				continue
			zona_interaccion = rectangulo.inflate(
				self.jugador.rectangulo.width + 24,
				self.jugador.rectangulo.height + 24,
			)
			if jugador_mapa.colliderect(zona_interaccion):
				indicacion = self.fuente.render(
					f"E: lugar de construcción de {nombre}",
					True,
					(255, 255, 255),
				)
				pantalla.blit(
					indicacion,
					indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)),
				)
				break
		for nombre, rectangulo in self.tanques_oxigeno_mapa.items():
			if not getattr(
				self.game_state, self.campos_compra_tanques[nombre]
			):
				continue
			zona_interaccion = rectangulo.inflate(
				self.jugador.rectangulo.width + 24,
				self.jugador.rectangulo.height + 24,
			)
			if not jugador_mapa.colliderect(zona_interaccion):
				continue

			campo_uso = self.campos_uso_tanques[nombre]
			ya_utilizado = (
				getattr(self.game_state, campo_uso)
				== self.game_state.dia_actual
			)
			texto = (
				f"Tanque {nombre} ya utilizado hoy"
				if ya_utilizado
				else f"E: recargar oxígeno - {nombre}"
			)
			indicacion = self.fuente.render(
				texto, True, (255, 255, 255)
			)
			pantalla.blit(
				indicacion,
				indicacion.get_rect(
					midtop=(pantalla.get_width() // 2, 20)
				),
			)
			break
		for nombre, (x, y) in self.antenas_mapa.items():
			zona_interaccion = pygame.Rect(x - 32, y - 32, 64, 64)
			jugador_mapa = self.camera.to_map(self.jugador.rectangulo)
			if jugador_mapa.colliderect(zona_interaccion):
				indicacion = self.fuente.render(
					f"E: interactuar con antena {nombre}",
					True,
					(255, 255, 255),
				)
				pantalla.blit(
					indicacion,
					indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)),
				)
				break
		if (
			self.mensaje_antena is not None
			and pygame.time.get_ticks() < self.mensaje_antena_hasta
		):
			lineas = self._envolver_texto_mensaje(
				self.mensaje_antena, limites_pantalla.width - 240
			)
			alto = max(80, len(lineas) * self.fuente.get_linesize() + 24)
			cuadro_mensaje = pygame.Rect(
				100, limites_pantalla.height - 80 - alto,
				limites_pantalla.width - 200, alto,
			)
			pygame.draw.rect(pantalla, (0, 0, 0), cuadro_mensaje)
			pygame.draw.rect(pantalla, (255, 255, 255), cuadro_mensaje, 2)
			for indice, linea in enumerate(lineas):
				mensaje = self.fuente.render(linea, True, (255, 255, 255))
				pantalla.blit(
					mensaje,
					(
						cuadro_mensaje.left + 20,
						cuadro_mensaje.top + 12
						+ indice * self.fuente.get_linesize(),
					),
				)

		self.menu_habilidades.dibujar(pantalla, self.game_state)
		self._dibujar_transicion_desmayo(pantalla)

	def _dibujar_transicion_desmayo(self, pantalla):
		inicio = self.transicion_desmayo_inicio
		if inicio is None:
			return

		tiempo_transcurrido = pygame.time.get_ticks() - inicio
		inicio_fundido = self.DURACION_ANIMACION_SUENO
		inicio_dia_siguiente = inicio_fundido + self.DURACION_FUNDIDO_SUENO
		inicio_fundido_entrada = (
			inicio_dia_siguiente + self.DURACION_CARTEL_DIA_SUENO
		)
		duracion_total = inicio_fundido_entrada + self.DURACION_FUNDIDO_SUENO
		if tiempo_transcurrido < inicio_fundido:
			return

		if tiempo_transcurrido < inicio_dia_siguiente:
			progreso = (
				tiempo_transcurrido - inicio_fundido
			) / self.DURACION_FUNDIDO_SUENO
			opacidad = round(255 * progreso)
		elif tiempo_transcurrido < inicio_fundido_entrada:
			opacidad = 255
		else:
			progreso = min(
				1,
				(tiempo_transcurrido - inicio_fundido_entrada)
				/ self.DURACION_FUNDIDO_SUENO,
			)
			opacidad = round(255 * (1 - progreso))

		capa_negra = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
		capa_negra.fill((0, 0, 0, opacidad))
		pantalla.blit(capa_negra, (0, 0))
		if inicio_dia_siguiente <= tiempo_transcurrido < duracion_total:
			texto_dia = self.fuente.render(
				f"DIA {self.game_state.dia_actual}", True, (255, 255, 255)
			)
			if tiempo_transcurrido >= inicio_fundido_entrada:
				texto_dia.set_alpha(opacidad)
			pantalla.blit(
				texto_dia,
				texto_dia.get_rect(center=pantalla.get_rect().center),
			)
