import os
import random
import math
import xml.etree.ElementTree as ET

import pygame

from projectFarm.localization import LocalizedFont, translate
from pytmx import TiledTileLayer
from pytmx.util_pygame import load_pygame

from engine.audio import (
	registrar_sonido_efecto,
	reproducir_sonido_interaccion,
	reproducir_sonido_pc,
)
from engine.harvest_effect import EfectoCosecha
from engine.minigame1 import Minijuego1
from engine.minigame2 import Minijuego2
from engine.power_effect import EfectoPower
from engine.radar import Radar
from engine.scroll import Camera
from engine.spritesheet import Spritesheet
from engine.ui import InterfazEstado, Inventario
from engine.water_splash import SistemaSplashAgua
from ..entities import Jugador
from ..farm import CULTIVOS, Parcela
from ..recompensasExpe import hitos_rover_completados
from ..scraps import Chatarra
from .skilltree_scene import SkillTreeMenu
from engine.particle_system import SistemaParticulas


class GameScene:
	SEGUNDOS_POR_PUNTO_OXIGENO = 2
	MULTIPLICADOR_OXIGENO_ZONA_SEGURA_TORMENTA = 5
	MULTIPLICADOR_VELOCIDAD_TORMENTA = 0.8
	FUERZA_VIENTO_TORMENTA = 0.5
	COSTO_REPARACION_POWER = 10
	ENERGIA_INICIAL_GENERADOR = 10
	ENERGIA_POR_POWER = 15
	DESPLAZAMIENTO_ENTRADA_DATOS_X = 12
	DURACION_ANIMACION_SUENO = 1800
	DURACION_FUNDIDO_SUENO = 800
	DURACION_CARTEL_DIA_SUENO = 2100
	DURACION_FUNDIDO_ENDING = 1200
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
		al_entrar_cueva=None,
		al_ending=None,
	):
		self.game_state = game_state
		self.inventario = inventario
		sprite_cursor_guante = pygame.transform.scale(
			self.inventario.sprite_mano, (24, 24)
		)
		sprite_cursor_guante_reforzado = pygame.transform.scale(
			self.inventario.sprite_mano_reforzada, (24, 24)
		)
		self.cursor_guante = pygame.cursors.Cursor(
			(2, 2), sprite_cursor_guante
		)
		self.cursor_guante_reforzado = pygame.cursors.Cursor(
			(2, 2), sprite_cursor_guante_reforzado
		)
		sprite_cursor_regadera = pygame.transform.scale(
			self.inventario.sprite_regadera, (24, 24)
		)
		sprite_cursor_regadera_mejorada = pygame.transform.scale(
			self.inventario.sprite_regadera_mejorada, (24, 24)
		)
		self.cursor_regadera = pygame.cursors.Cursor(
			(2, 2), sprite_cursor_regadera
		)
		self.cursor_regadera_mejorada = pygame.cursors.Cursor(
			(2, 2), sprite_cursor_regadera_mejorada
		)
		self.cursores_semillas = {
			f"semilla_{cultivo}": pygame.cursors.Cursor(
				(2, 2),
				pygame.transform.scale(
					self.inventario.sprites_semillas[cultivo],
					(24, 24),
				),
			)
			for cultivo in Inventario.SLOTS_SEMILLAS.values()
		}
		self.cursor_guante_activo = False
		self.tipo_cursor_guante = None
		self.interfaz_estado = InterfazEstado()
		self.jugador = Jugador()
		self.radar = Radar()
		self.radar_visible = game_state.radarComprado
		self.acumulador_viento_x = 0.0
		self.pausado = False
		self.primera_entrada = True
		self.puerta_reentrada = "casa"
		self.fondo = self._cargar_fondo()
		self.efectos_power = {
			nombre: EfectoPower(x, y)
			for nombre, (x, y) in self.energia_mapa.items()
			if nombre != "Generador"
		}
		self.menu_habilidades = SkillTreeMenu()
		self.ventana_generador_abierta = False
		self.power_pendiente_confirmacion = None
		self.camera = Camera()
		self.origen_mapa = (0, 0)
		self.particulas = None
		self.splash_riego = SistemaSplashAgua()
		self.efecto_cosecha = EfectoCosecha()
		self.descargaDatos1Comprado = False
		self.descargaDatos2Comprado = False
		self.al_entrar_casa = al_entrar_casa
		self.al_entrar_reciclaje = al_entrar_reciclaje
		self.al_entrar_data_center = al_entrar_data_center
		self.al_entrar_expedicion = al_entrar_expedicion
		self.al_desmayarse = al_desmayarse
		self.al_completar_desmayo = al_completar_desmayo
		self.al_entrar_cueva = al_entrar_cueva
		self.al_ending = al_ending
		ruta_sueno = os.path.join(
			os.path.dirname(__file__), "..", "utils", "AstroSleeping.json"
		)
		spritesheet_sueno = Spritesheet(ruta_sueno)
		self.sprites_sueno = [
			pygame.transform.scale(sprite, (48, 60))
			for sprite in spritesheet_sueno.get_animation_frames("default")
		]
		ruta_musica_sueno = os.path.join(
			os.path.dirname(__file__), "..", "sounds", "SleepSong.wav"
		)
		self.musica_sueno = pygame.mixer.Sound(
			os.path.normpath(ruta_musica_sueno)
		)
		self.canal_musica_sueno = None
		self.transicion_desmayo_inicio = None
		self.transicion_ending_inicio = None
		self.dia_avanzado_durante_desmayo = False
		self.mensaje_resultado_desmayo = None
		self._generar_chatarra()
		self.campos_disponibilidad_parcelas = {
			"Parcela1": "parcela1Disponible",
		}
		self.parcelas_por_nodo = {}

		COLUMNAS_PARCELAS = 15
		FILAS_PARCELAS = 6

		for nombre, area in self.areas_parcelas_mapa.items():
			ancho_grilla = Parcela.TAMANO * COLUMNAS_PARCELAS
			alto_grilla = Parcela.TAMANO * FILAS_PARCELAS

			origen_parcelas = (
				area.left + (area.width - ancho_grilla) // 2,
				area.top + (area.height - alto_grilla) // 2,
			)

			self.parcelas_por_nodo[nombre] = [
				Parcela(
					origen_parcelas[0] + columna * Parcela.TAMANO,
					origen_parcelas[1] + fila * Parcela.TAMANO,
				)
				for fila in range(FILAS_PARCELAS)
				for columna in range(COLUMNAS_PARCELAS)
			]

		self.parcelas = [
			parcela
			for parcelas in self.parcelas_por_nodo.values()
			for parcela in parcelas
		]
		
		self.posiciones_parcelas_mapa = [
			parcela.rectangulo.topleft for parcela in self.parcelas
		]
		self.parcela_seleccionada = None
		self.ultimo_cambio_zona_granja = pygame.time.get_ticks()
		
		
		self.fuente = LocalizedFont(None, 28)
		self.mensaje_antena = None
		self.mensaje_antena_hasta = 0
		self.minijuego_antena = Minijuego1()
		self.minijuego_power = Minijuego2()
		self.power_en_minijuego = None
		self.ultimo_update_oxigeno = None
		self.segundos_acumulados_oxigeno = 0
		ruta_efecto = os.path.join(
			os.path.dirname(__file__), "..", "sounds", "SoundEffect1.wav"
		)
		self.efecto_accion = registrar_sonido_efecto(
			pygame.mixer.Sound(os.path.normpath(ruta_efecto))
		)
		self.sonido_cosechar = registrar_sonido_efecto(
			pygame.mixer.Sound(
				os.path.normpath(
					os.path.join(
						os.path.dirname(__file__), "..", "sounds", "cosechar.wav"
					)
				)
			)
		)
		self.sonido_tomar_chatarra = registrar_sonido_efecto(
			pygame.mixer.Sound(
				os.path.normpath(
					os.path.join(
						os.path.dirname(__file__),
						"..",
						"sounds",
						"tomarChatarra.wav",
					)
				)
			)
		)
		self.sonido_mate = registrar_sonido_efecto(
			pygame.mixer.Sound(
				os.path.normpath(
					os.path.join(
						os.path.dirname(__file__),
						"..",
						"sounds",
						"ruidoMate.wav",
					)
				)
			)
		)
		self.sonidos_riego = []
		for nombre_sonido in ("regando1.wav", "regando2.wav"):
			ruta_sonido_riego = os.path.join(
				os.path.dirname(__file__), "..", "sounds", nombre_sonido
			)
			self.sonidos_riego.append(
				registrar_sonido_efecto(
					pygame.mixer.Sound(os.path.normpath(ruta_sonido_riego))
				)
			)
		self.sonidos_plantar = []
		for nombre_sonido in ("plantar1.wav", "plantar2.wav"):
			ruta_sonido_plantar = os.path.join(
				os.path.dirname(__file__), "..", "sounds", nombre_sonido
			)
			self.sonidos_plantar.append(
				registrar_sonido_efecto(
					pygame.mixer.Sound(os.path.normpath(ruta_sonido_plantar))
				)
			)
		ruta_chatarra = os.path.join(
			os.path.dirname(__file__), "..", "assets", "chatarraSprite.png"
		)
		sprite_chatarra = pygame.image.load(ruta_chatarra).convert_alpha()
		self.sprite_chatarra = pygame.transform.scale(
			sprite_chatarra, (Chatarra.TAMANO, Chatarra.TAMANO)
		)
		ruta_entrada_cueva = os.path.join(
			os.path.dirname(__file__), "..", "assets", "caveEntrance.png"
		)
		self.sprite_entrada_cueva = pygame.transform.scale(
			pygame.image.load(ruta_entrada_cueva).convert_alpha(),
			(48, 48),
		)
		
		ruta_cosechas = os.path.join(
			os.path.dirname(__file__), "..", "utils", "CosechasSpritesheetVersionFinal.json"
		)
		spritesheet_cosechas = Spritesheet(ruta_cosechas)
		self.sprites_cultivos = {
			tipo: {
				nombre_sprite: pygame.transform.scale(
					spritesheet_cosechas.get_sprite(nombre_sprite),
					datos.get("tamano_etapas", {}).get(
						nombre_sprite,
						(48, 48),
					),
				)
				for nombre_sprite in (*datos["etapas"], "cosechaSeca")
			}
			for tipo, datos in CULTIVOS.items()
		}
		self.sprites_tierra = {
			"seca": pygame.transform.scale(
				spritesheet_cosechas.get_sprite("tierraSeca"),
				(48, 48),
			),
			"mojada": pygame.transform.scale(
				spritesheet_cosechas.get_sprite("tierraMojada"),
				(48, 48),
			),
		}


	def obtener_parcela_jugador(self, jugador, posicion=None):
		if not self.game_state.parcela1Disponible:
			return None

		return next(
			(
				parcela
				for parcela in self.parcelas_por_nodo["Parcela1"]
				if jugador.rectangulo.colliderect(parcela.rectangulo)
				and (
					posicion is None
					or parcela.rectangulo.collidepoint(posicion)
				)
			),
			None,
		)

	
	def _cargar_fondo(self):
		ruta_mapa = os.path.join(
			os.path.dirname(__file__), "..", "assets", "MarsMap.tmx"
		)
		mapa = load_pygame(os.path.normpath(ruta_mapa))
		capa_zona_oxigeno = mapa.get_layer_by_name("ZonaOxigeno")

		objeto_zona_segura = next(
			objeto
			for objeto in capa_zona_oxigeno
			if objeto.name == "zonaSegura"
		)

		self.zona_segura_oxigeno = pygame.Rect(
			round(objeto_zona_segura.x * 3),
			round(objeto_zona_segura.y * 3),
			round(objeto_zona_segura.width * 3),
			round(objeto_zona_segura.height * 3),
		)
		capa_antenas = mapa.get_layer_by_name("Antenas")
		self.antenas_mapa = {
			objeto.name: (round(objeto.x * 3), round(objeto.y * 3))
			for objeto in capa_antenas
		}
		capa_cueva = mapa.get_layer_by_name("Cueva")
		objeto_entrada_cueva = next(
			(
				objeto
				for objeto in capa_cueva
				if objeto.name == "Entrada"
			),
			None,
		)
		if objeto_entrada_cueva is None:
			raise ValueError(
				"Falta el objeto 'Entrada' en la capa 'Cueva'."
			)
		self.entrada_cueva_mapa = (
			round(objeto_entrada_cueva.x * 3),
			round(objeto_entrada_cueva.y * 3),
		)
		capa_salida = mapa.get_layer_by_name("Salida")
		objeto_ending = next(
			(
				objeto
				for objeto in capa_salida
				if objeto.name == "Ending"
			),
			None,
		)
		if objeto_ending is None:
			raise ValueError(
				"Falta el objeto 'Ending' en la capa 'Salida'."
			)
		self.zona_ending_mapa = pygame.Rect(
			round(objeto_ending.x * 3),
			round(objeto_ending.y * 3),
			round(objeto_ending.width * 3),
			round(objeto_ending.height * 3),
		)
		capa_energia = mapa.get_layer_by_name("Energia")
		objetos_energia = {
			objeto.name: objeto for objeto in capa_energia
		}
		nombres_powers = tuple(f"Power{indice}" for indice in range(1, 7))
		nombres_energia = ("Generador", *nombres_powers)
		if any(nombre not in objetos_energia for nombre in nombres_energia):
			raise ValueError(
				"La capa 'Energia' debe contener 'Generador' y 'Power1' a 'Power6'."
			)
		self.energia_mapa = {
			nombre: (
				round(objetos_energia[nombre].x * 3),
				round(objetos_energia[nombre].y * 3),
			)
			for nombre in nombres_energia
		}
		capa_parcelas = mapa.get_layer_by_name("Parcelas")
		objetos_parcelas = {
			objeto.name: objeto for objeto in capa_parcelas
		}
		nombre = "Parcela1"

		if nombre not in objetos_parcelas:
			raise ValueError(
				"Falta la parcela 'Parcela1' en la capa 'Parcelas'."
			)

		self.areas_parcelas_mapa = {
			nombre: pygame.Rect(
				round(objetos_parcelas[nombre].x * 3),
				round(objetos_parcelas[nombre].y * 3),
				round(objetos_parcelas[nombre].width * 3),
				round(objetos_parcelas[nombre].height * 3),
			)
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
		if self.game_state.centroDatosComprado:
			self.game_state.centroDatosDisponible = True
		if self.game_state.reciclajeComprado:
			self.game_state.reciclajeDisponible = True
		if self.game_state.expedicionesComprado:
			self.game_state.expedicionesDisponible = True
		if self.game_state.centro_datos_completado:
			self.game_state.estrella_centro_datos = True
		if hitos_rover_completados(self.game_state):
			self.game_state.estrella_expediciones = True
		if self._obtener_progreso_energia() == 100:
			self.game_state.estrella_generador = True
		if self.game_state.creditos_acumulados >= 100_000:
			self.game_state.estrella_creditos = True
		if (
			self.game_state.mateRecolectado
			and not self.game_state.bono_mate_creditos_otorgado
			and self.game_state.dia_recoleccion_mate is not None
			and self.game_state.dia_actual
			> self.game_state.dia_recoleccion_mate
		):
			creditos_faltantes = max(
				0, 100_000 - self.game_state.creditos_acumulados
			)
			bono_creditos = (creditos_faltantes + 1) // 2
			self.game_state.creditos_acumulados += bono_creditos
			self.game_state.bono_mate_creditos_otorgado = True
			if bono_creditos:
				self._mostrar_mensaje_antena(
					f"El mate te ayudó a conseguir {bono_creditos} créditos."
				)
		if (
			self.game_state.dia_interaccion_pared is not None
			and self.game_state.dia_actual
			> self.game_state.dia_interaccion_pared
		):
			self.game_state.martilloDisponible = True
		self.game_state.oxigeno = self.game_state.oxigeno_maximo
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

		jugador_mapa = self.camera.to_map(
			self.jugador.rectangulo
		)

		dentro_zona_segura = self.zona_segura_oxigeno.collidepoint(
			jugador_mapa.center
		)

		if dentro_zona_segura:
			multiplicador_oxigeno = (
				self.MULTIPLICADOR_OXIGENO_ZONA_SEGURA_TORMENTA
				if (
					self.game_state.tormenta_arena
					and not self.game_state.trajeAntiTormentaComprado
				)
				else 1
			)
		else:
			multiplicador_oxigeno = 10

		self.segundos_acumulados_oxigeno += (
			delta_segundos * multiplicador_oxigeno
		)

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

	def _pausar_consumo_oxigeno(self):
		self.ultimo_update_oxigeno = pygame.time.get_ticks()

	def _zona_segura_protege_jugador(self, jugador_mapa):
		return self.zona_segura_oxigeno.collidepoint(jugador_mapa.center) and (
			not self.game_state.tormenta_arena
			or self.game_state.trajeAntiTormentaComprado
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
		
		return any(rectangulo_mapa.colliderect(colision) for colision in colisiones)

	def update(self, teclas, limites_pantalla, eventos=()):
		for nombre, efecto in self.efectos_power.items():
			indice_power = int(nombre.removeprefix("Power")) - 1
			efecto.actualizar(
				activo=not self.game_state.powers_reparados[indice_power]
			)

		for evento in eventos:
			if (
				self.game_state.radarComprado
				and evento.type == pygame.KEYDOWN
				and evento.key == pygame.K_r
			):
				self.radar_visible = not self.radar_visible

		if self.transicion_desmayo_inicio is not None:
			self._actualizar_desmayo()
			return

		if self.transicion_ending_inicio is not None:
			transcurrido = (
				pygame.time.get_ticks() - self.transicion_ending_inicio
			)
			if transcurrido >= self.DURACION_FUNDIDO_ENDING:
				self.al_ending()
			return

		if self.power_pendiente_confirmacion is not None:
			for evento in eventos:
				if evento.type != pygame.KEYDOWN:
					continue
				if evento.key == pygame.K_ESCAPE:
					self.power_pendiente_confirmacion = None
					return
				if evento.key != pygame.K_e:
					continue

				indice_power = self.power_pendiente_confirmacion
				self.power_pendiente_confirmacion = None
				if self.game_state.materiales < self.COSTO_REPARACION_POWER:
					self._mostrar_mensaje_antena(
						f"Necesitas {self.COSTO_REPARACION_POWER} materiales para reparar esta línea."
					)
					return
				self.game_state.materiales -= self.COSTO_REPARACION_POWER
				self.game_state.powers_pagados[indice_power] = True
				self.power_en_minijuego = indice_power
				self.minijuego_power.iniciar()
				return
			return

		if self.minijuego_antena.activo:
			self._pausar_consumo_oxigeno()
			if self.minijuego_antena.actualizar(eventos):
				self.game_state.antena_encontrada = True
				self._mostrar_mensaje_antena(
					f"Datos de Antena "
					f"{self.game_state.antena_objetivo} descargados."
				)
			return

		if self.minijuego_power.activo:
			self._pausar_consumo_oxigeno()
			indice_power = self.power_en_minijuego
			if self.minijuego_power.actualizar(eventos, limites_pantalla):
				if indice_power is None:
					raise RuntimeError(
						"El minijuego termino sin un Power asignado."
					)
				self.game_state.powers_reparados[indice_power] = True
				self.game_state.powers_pagados[indice_power] = False
				nombre = f"Power{indice_power + 1}"
				self.efectos_power[nombre].apagar()
				progreso = self._obtener_progreso_energia()
				self._mostrar_mensaje_antena(
					f"Línea {indice_power + 1} reparada. "
					"Energía del generador: "
					f"{progreso}%."
				)
				self.power_en_minijuego = None
			elif not self.minijuego_power.activo:
				self.power_en_minijuego = None
				self._mostrar_mensaje_antena(
					"Interactúa con la línea para reintentar."
				)
			return

		if self.ventana_generador_abierta:
			if any(
				evento.type == pygame.KEYDOWN
				and evento.key == pygame.K_ESCAPE
				for evento in eventos
			):
				self.ventana_generador_abierta = False
			return

		if self.menu_habilidades.procesar_eventos(
			eventos, limites_pantalla, self.game_state
		):
			return

		for evento in eventos:
					if evento.type == pygame.KEYDOWN and evento.key == pygame.K_TAB:
						self.interfaz_estado.mostrar_inventario = (
							not self.interfaz_estado.mostrar_inventario
						)
						if self.interfaz_estado.mostrar_inventario:
							reproducir_sonido_pc()
					elif (
						evento.type == pygame.KEYDOWN
						and evento.key == pygame.K_e
						and self.inventario.slot_seleccionado
						== Inventario.SLOT_MATE
					):
						self.sonido_mate.play()
					elif (
						evento.type == pygame.KEYDOWN
						and pygame.K_1 <= evento.key <= pygame.K_9
					):
						self.inventario.slot_seleccionado = (
							evento.key - pygame.K_1
						)

		if self.interfaz_estado.mostrar_inventario:
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
						else (
							(
								self.origen_mapa[0]
								+ self.entrada_cueva_mapa[0],
								self.origen_mapa[1]
								+ self.entrada_cueva_mapa[1],
							)
							if self.puerta_reentrada == "cueva"
							else puerta_casa
						)
					)
				)
			)
			if self.puerta_reentrada == "cueva":
				self.jugador.rectangulo.center = (
					punto_entrada[0],
					punto_entrada[1] + 80,
				)
			else:
				self.jugador.rectangulo.midtop = (
					punto_entrada[0],
					punto_entrada[1] + 8,
				)
			self.primera_entrada = False
		self.camera.update(
			self.jugador.rectangulo, limites_pantalla, limites_mapa
		)
		rect_previo = self.jugador.rectangulo.copy()
		hay_tormenta = self.game_state.tormenta_arena
		multiplicador_velocidad = (
			self.MULTIPLICADOR_VELOCIDAD_TORMENTA
			if hay_tormenta
			else 1.0
		)
		self.jugador.actualizar(teclas, multiplicador_velocidad)
		self._aplicar_viento()
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

		if self.particulas is None:
			self.particulas = SistemaParticulas(
				limites_pantalla.width,
				limites_pantalla.height,
			)

		self.particulas.actualizar(
			tormenta=self.game_state.tormenta_arena
		)
		self.particulas.actualizar_camara(self.camera.offset)
		self.splash_riego.actualizar()
		self.efecto_cosecha.actualizar()

		if (
			self.al_ending is not None
			and self._tiene_todas_las_estrellas()
			and self.camera.to_map(
				self.jugador.rectangulo
			).colliderect(self.zona_ending_mapa)
		):
			self.transicion_ending_inicio = pygame.time.get_ticks()
			return
			
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
		
		if self._interactuar_con_energia(eventos):
			return
		if self._interactuar_con_cueva(eventos):
			return
		self._interactuar_con_antenas(eventos)
		self._interactuar_con_lugares_construccion(eventos)

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
				self.sonido_tomar_chatarra.play()
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
						self.efecto_cosecha.crear(
							parcela_clickeada.rectangulo.centerx,
							parcela_clickeada.rectangulo.centery,
						)
						self.sonido_cosechar.play()

			elif self.inventario.slot_seleccionado in Inventario.SLOTS_SEMILLAS:
				tipo_cultivo = Inventario.SLOTS_SEMILLAS[
					self.inventario.slot_seleccionado
				]
				semilla = CULTIVOS[tipo_cultivo]["semilla"]

				if (
					parcela_clickeada.planta is None
					and getattr(self.game_state, semilla) > 0
				):
					parcela_clickeada.plantar(tipo_cultivo)
					setattr(
						self.game_state,
						semilla,
						getattr(self.game_state, semilla) - 1,
					)
					random.choice(self.sonidos_plantar).play()

			elif self.inventario.slot_seleccionado == Inventario.SLOT_REGADERA:
				if self.game_state.mejorRegaderaComprada:
					self._regar_parcelas_cercanas(parcela_clickeada)
				elif (
					parcela_clickeada.planta is not None
					and parcela_clickeada.dia_regado != self.game_state.dia_actual
				):
					parcela_clickeada.regar(self.game_state.dia_actual)
					self.splash_riego.crear_splash(
						parcela_clickeada.rectangulo.centerx,
						parcela_clickeada.rectangulo.centery + 5,
					)
					random.choice(self.sonidos_riego).play()

	def _regar_parcelas_cercanas(self, parcela_central):
		tamano = Parcela.TAMANO
		zona_riego = pygame.Rect(
			parcela_central.rectangulo.x - tamano,
			parcela_central.rectangulo.y - tamano,
			tamano * 3,
			tamano * 3,
		)
		se_rego_parcela = False
		for parcela in self.parcelas_por_nodo["Parcela1"]:
			if (
				not zona_riego.colliderect(parcela.rectangulo)
				or parcela.planta is None
				or parcela.dia_regado == self.game_state.dia_actual
			):
				continue
			parcela.regar(self.game_state.dia_actual)
			self.splash_riego.crear_splash(
				parcela.rectangulo.centerx,
				parcela.rectangulo.centery + 5,
			)
			se_rego_parcela = True
		if se_rego_parcela:
			random.choice(self.sonidos_riego).play()

	def _aplicar_viento(self):
		if not self.game_state.tormenta_arena:
			self.acumulador_viento_x = 0.0
			return

		intensidad_viento = self.FUERZA_VIENTO_TORMENTA * (
			1 + 0.2 * math.sin(pygame.time.get_ticks() / 700)
		)
		self.acumulador_viento_x -= intensidad_viento
		desplazamiento_x = int(self.acumulador_viento_x)
		self.acumulador_viento_x -= desplazamiento_x
		self.jugador.rectangulo.move_ip(desplazamiento_x, 0)


	def _mostrar_mensaje_antena(self, texto):
		self.mensaje_antena = texto
		self.mensaje_antena_hasta = pygame.time.get_ticks() + 3000

	def _interactuar_con_cueva(self, eventos):
		x, y = self.entrada_cueva_mapa
		zona_interaccion = pygame.Rect(x - 32, y - 32, 64, 64)
		jugador_mapa = self.camera.to_map(self.jugador.rectangulo)
		presiono_interactuar = any(
			evento.type == pygame.KEYDOWN and evento.key == pygame.K_e
			for evento in eventos
		)
		if self.game_state.cuevaAbierta:
			if not jugador_mapa.colliderect(zona_interaccion):
				return False
			self.ultimo_update_oxigeno = None
			if self.al_entrar_cueva is None:
				raise RuntimeError(
					"No se configuró la transición a la escena de la cueva."
				)
			self.al_entrar_cueva()
			return True

		if not jugador_mapa.colliderect(zona_interaccion):
			return False

		clic_entrada = False
		for evento in eventos:
			if (
				evento.type != pygame.MOUSEBUTTONDOWN
				or evento.button != 1
			):
				continue
			posicion_mundo = self.camera.to_world(evento.pos)
			posicion_mapa = (
				posicion_mundo[0] - self.origen_mapa[0],
				posicion_mundo[1] - self.origen_mapa[1],
			)
			if zona_interaccion.collidepoint(posicion_mapa):
				clic_entrada = True
				break

		if presiono_interactuar or clic_entrada:
			if self.game_state.dia_interaccion_pared is None:
				self.game_state.dia_interaccion_pared = (
					self.game_state.dia_actual
				)
		if presiono_interactuar:
			self._mostrar_mensaje_antena(
				"Esta parte del muro no parece muy solido"
			)
			return True
		if not clic_entrada:
			return False
		if (
			not self.game_state.martilloComprado
			or self.inventario.slot_seleccionado
			!= Inventario.SLOT_MARTILLO
		):
			self._mostrar_mensaje_antena(
				"Necesitas tener el martillo equipado para romper el muro."
			)
			return True

		self.game_state.cuevaAbierta = True
		self.sonido_cosechar.play()
		self._mostrar_mensaje_antena("Rompiste el muro.")
		return True

	def _interactuar_con_antenas(self, eventos):
		if self.game_state.centro_datos_completado:
			return
		jugador_mapa = self.camera.to_map(self.jugador.rectangulo)
		for evento in eventos:
			if evento.type != pygame.KEYDOWN or evento.key != pygame.K_e:
				continue
			for nombre, (x, y) in self.antenas_mapa.items():
				zona_interaccion = pygame.Rect(x - 32, y - 32, 64, 64)
				if not jugador_mapa.colliderect(zona_interaccion):
					continue

				reproducir_sonido_pc()
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

	def _obtener_progreso_energia(self):
		powers_reparados = sum(self.game_state.powers_reparados)
		return min(
			100,
			self.ENERGIA_INICIAL_GENERADOR
			+ powers_reparados * self.ENERGIA_POR_POWER,
		)

	def _interactuar_con_energia(self, eventos):
		if not any(
			evento.type == pygame.KEYDOWN and evento.key == pygame.K_e
			for evento in eventos
		):
			return False

		jugador_mapa = self.camera.to_map(self.jugador.rectangulo)
		for nombre, (x, y) in self.energia_mapa.items():
			zona_interaccion = pygame.Rect(x - 32, y - 32, 64, 64)
			if not jugador_mapa.colliderect(zona_interaccion):
				continue

			reproducir_sonido_pc()
			if nombre == "Generador":
				self.ventana_generador_abierta = True
				return True

			indice_power = int(nombre.removeprefix("Power")) - 1
			if self.game_state.powers_reparados[indice_power]:
				self._mostrar_mensaje_antena(
					f"Línea {indice_power + 1} ya está reparada."
				)
				return True

			if (
				not self.game_state.powers_pagados[indice_power]
				and self.game_state.materiales < self.COSTO_REPARACION_POWER
			):
				self._mostrar_mensaje_antena(
					f"Necesitas {self.COSTO_REPARACION_POWER} materiales para reparar esta línea."
				)
				return True

			if not self.game_state.powers_pagados[indice_power]:
				self.power_pendiente_confirmacion = indice_power
				return True
			self.power_en_minijuego = indice_power
			self.minijuego_power.iniciar()
			return True

		return False

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
					f"Lugar de construcción: {nombre}."
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

	def restablecer_cursor(self):
		if self.cursor_guante_activo:
			pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
			self.cursor_guante_activo = False
			self.tipo_cursor_guante = None

	def _actualizar_cursor_guante(self):
		posicion_mundo = self.camera.to_world(pygame.mouse.get_pos())
		sobre_parcela_al_alcance = (
			self.obtener_parcela_jugador(self.jugador, posicion_mundo)
			is not None
		)
		sobre_chatarra_cercana = (
			any(
				pieza.rectangulo.collidepoint(posicion_mundo)
				and self.jugador.rectangulo.inflate(
					Chatarra.TAMANO, Chatarra.TAMANO
				).colliderect(pieza.rectangulo)
				for pieza in self.chatarra
			)
		)
		interfaz_bloquea_cursor = (
			not self.pausado
			and not self.menu_habilidades.abierto
			and self.menu_habilidades.dialogo is None
			and not self.ventana_generador_abierta
			and self.power_pendiente_confirmacion is None
			and self.transicion_desmayo_inicio is None
			and self.transicion_ending_inicio is None
		)
		tipo_cursor = None
		if interfaz_bloquea_cursor and sobre_parcela_al_alcance:
			if self.inventario.slot_seleccionado == Inventario.SLOT_MANO:
				tipo_cursor = (
					"reforzado"
					if self.game_state.guanteReforzado
					else "normal"
				)
			elif (
				self.inventario.slot_seleccionado
				== Inventario.SLOT_REGADERA
			):
				tipo_cursor = (
					"regadera_mejorada"
					if self.game_state.mejorRegaderaComprada
					else "regadera"
				)
			elif (
				self.inventario.slot_seleccionado
				in Inventario.SLOTS_SEMILLAS
			):
				tipo_cultivo = Inventario.SLOTS_SEMILLAS[
					self.inventario.slot_seleccionado
				]
				tipo_cursor = f"semilla_{tipo_cultivo}"
		if (
			tipo_cursor is None
			and interfaz_bloquea_cursor
			and sobre_chatarra_cercana
		):
			if self.game_state.guanteReforzado:
				tipo_cursor = "reforzado"
			elif self.inventario.slot_seleccionado == Inventario.SLOT_MANO:
				tipo_cursor = "normal"

		if tipo_cursor != self.tipo_cursor_guante:
			if tipo_cursor is None:
				self.restablecer_cursor()
				return
			cursores = {
				"normal": self.cursor_guante,
				"reforzado": self.cursor_guante_reforzado,
				"regadera": self.cursor_regadera,
				"regadera_mejorada": self.cursor_regadera_mejorada,
			}
			if tipo_cursor in self.cursores_semillas:
				cursor = self.cursores_semillas[tipo_cursor]
			else:
				cursor = cursores[tipo_cursor]
			pygame.mouse.set_cursor(cursor)
			self.cursor_guante_activo = True
			self.tipo_cursor_guante = tipo_cursor

	def draw(self, pantalla):
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
			if self.game_state.cuevaAbierta:
				rect_entrada_cueva = self.sprite_entrada_cueva.get_rect(
					center=(
						self.origen_mapa[0] + self.entrada_cueva_mapa[0],
						self.origen_mapa[1] + self.entrada_cueva_mapa[1],
					)
				)
				pantalla.blit(
					self.sprite_entrada_cueva,
					self.camera.apply(rect_entrada_cueva),
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
			
		else:
			pantalla.fill((99, 60, 58))
		parcelas_visibles = []

		if self.game_state.parcela1Disponible:
			for parcela in self.parcelas_por_nodo["Parcela1"]:
				parcela.dibujar(
					pantalla,
					self.game_state.dia_actual,
					self.sprites_cultivos,
					self.camera.screen_offset,
					self.sprites_tierra,
					dibujar_planta=False,
				)
				parcelas_visibles.append(parcela)


		# Segunda pasada: dibujar los cultivos que no son tomates.
		for parcela in parcelas_visibles:
			if parcela.planta is None:
				continue

			nombre_cultivo = CULTIVOS[parcela.planta]["nombre"]

			if nombre_cultivo != "tomate":
				parcela.dibujar_cultivo(
					pantalla,
					self.sprites_cultivos,
					self.camera.screen_offset,
				)


		
		
				
		# Tercera pasada: dibujar las semillas detrás del jugador
		# y ordenar los tomates crecidos por profundidad Y.

		elementos_profundidad = []

		for parcela in parcelas_visibles:
			if (
				parcela.planta is not None
				and CULTIVOS[parcela.planta]["nombre"] == "tomate"
			):
				# Las semillas y los cultivos secos se dibujan antes
				# del jugador, independientemente de su posición.
				if parcela.dias_crecimiento == 0 or parcela.seca:
					parcela.dibujar_cultivo(
						pantalla,
						self.sprites_cultivos,
						self.camera.screen_offset,
					)
				else:
					# Ajustar la profundidad para que el tomate
					# no quede delante del jugador demasiado pronto.
					y_profundidad = parcela.rectangulo.bottom - 8

					elementos_profundidad.append(
						(
							y_profundidad,
							1,
							"tomate",
							parcela,
						)
					)

		# Agregar al jugador a la lista de profundidad.
		elementos_profundidad.append(
			(
				self.jugador.rectangulo.bottom,
				0,
				"jugador",
				None,
			)
		)

		# Dibujar de atrás hacia adelante según la posición Y.
		for _, _, tipo, elemento in sorted(
			elementos_profundidad,
			key=lambda item: (item[0], item[1]),
		):
			if tipo == "tomate":
				elemento.dibujar_cultivo(
					pantalla,
					self.sprites_cultivos,
					self.camera.screen_offset,
				)
			elif self.transicion_desmayo_inicio is None:
				self.jugador.dibujar(
					pantalla,
					self.camera.screen_offset,
					viento=(
						self.game_state.tormenta_arena
						and not self.pausado
					),
				)


		for pieza in self.chatarra:
			pieza.dibujar(
				pantalla, self.sprite_chatarra, self.camera.screen_offset
			)

		if self.particulas is not None:
			self.particulas.dibujar(pantalla)
			self.splash_riego.dibujar(
				pantalla,
				self.camera.screen_offset,
			)
			self.efecto_cosecha.dibujar(
				pantalla,
				self.camera.screen_offset,
			)
		desplazamiento_efectos_power = (
			self.origen_mapa[0] + self.camera.screen_offset[0],
			self.origen_mapa[1] + self.camera.screen_offset[1],
		)
		for efecto in self.efectos_power.values():
			efecto.dibujar(pantalla, desplazamiento_efectos_power)

		if self.game_state.tormenta_arena:
			capa_tormenta = pygame.Surface(
				pantalla.get_size(),
				pygame.SRCALPHA,
			)
			capa_tormenta.fill((190, 45, 20, 100))
			pantalla.blit(capa_tormenta, (0, 0))
		
		# Durante el desmayo, mantener la animación de sueño.
		if self.transicion_desmayo_inicio is not None:
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
				posicion_sueno.move_ip(self.camera.screen_offset)
				pantalla.blit(sprite_sueno, posicion_sueno)
		
		#for i, cuadrado in enumerate(self.cuadrados):
			#pygame.draw.rect(pantalla, self.colores_cuadrados[i], cuadrado)
			#pygame.draw.rect(pantalla, (30, 30, 30), cuadrado, 2)
		
		if self.game_state.tormenta_arena:
			capa_tormenta = pygame.Surface(
				pantalla.get_size(),
				pygame.SRCALPHA,
			)
			capa_tormenta.fill((205, 105, 45, 45))
			pantalla.blit(capa_tormenta, (0, 0))

		if self.minijuego_power.activo:
			self.restablecer_cursor()
			self.minijuego_power.dibujar(pantalla)
			self._dibujar_interfaz_estado(pantalla)
			return

		if self.minijuego_antena.activo:
			self.restablecer_cursor()
			self.minijuego_antena.dibujar(pantalla)
			self._dibujar_interfaz_estado(pantalla)
			return

		jugador_mapa = self.camera.to_map(
			self.jugador.rectangulo
		)

		dentro_zona_segura = self._zona_segura_protege_jugador(jugador_mapa)

		self.interfaz_estado.dibujar(
			pantalla,
			self.game_state,
			mostrar_chatarra=True,
			mostrar_materiales=True,
			dentro_zona_segura=dentro_zona_segura,
		)
		self.inventario.dibujar(pantalla, self.game_state)
		edificios_radar = [
			self.puerta_casa_mapa,
		]
		edificios_radar.extend(
			rectangulo.midbottom
			for atributo_disponible, (_, rectangulo)
			in self.bloques_edificios.items()
			if getattr(self.game_state, atributo_disponible)
		)
		chatarra_radar = (
			self.camera.to_map(pieza.rectangulo).center
			for pieza in self.chatarra
		)
		cultivos_radar = (
			self.camera.to_map(parcela.rectangulo).center
			for parcela in self.parcelas
			if parcela.planta is not None
			and parcela.obtener_etapa() != "cosechable"
		)
		cultivos_cosechables_radar = (
			self.camera.to_map(parcela.rectangulo).center
			for parcela in self.parcelas
			if parcela.obtener_etapa() == "cosechable"
		)
		if self.game_state.radarComprado and self.radar_visible:
			self.radar.dibujar(
				pantalla,
				self.fondo.get_size(),
				self.camera.to_map(self.jugador.rectangulo).center,
				edificios_radar,
				chatarra_radar,
				cultivos_radar,
				cultivos_cosechables_radar,
				antenas=self.antenas_mapa.values(),
				generador=self.energia_mapa["Generador"],
				interferencia=self.game_state.tormenta_arena,
			)
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
		x, y = self.entrada_cueva_mapa
		zona_cueva = pygame.Rect(x - 32, y - 32, 64, 64)
		if jugador_mapa.colliderect(zona_cueva):
			texto_cueva = (
				"Entra en la cueva"
				if self.game_state.cuevaAbierta
				else "Clic con martillo o E: revisar el muro"
			)
			indicacion = self.fuente.render(
				texto_cueva,
				True,
				(255, 255, 255),
			)
			pantalla.blit(
				indicacion,
				indicacion.get_rect(
					midtop=(pantalla.get_width() // 2, 20)
				),
			)
		for nombre, (x, y) in self.energia_mapa.items():
			zona_interaccion = pygame.Rect(x - 32, y - 32, 64, 64)
			if not jugador_mapa.colliderect(zona_interaccion):
				continue
			if nombre == "Generador":
				texto_indicacion = "E: revisar generador"
			else:
				indice_power = int(nombre.removeprefix("Power")) - 1
				if self.game_state.powers_reparados[indice_power]:
					texto_indicacion = (
						f"E: Línea {indice_power + 1} ya reparada"
					)
				elif self.game_state.powers_pagados[indice_power]:
					texto_indicacion = (
						f"E: reintentar reparación de Línea "
						f"{indice_power + 1}"
					)
				else:
					texto_indicacion = (
						f"E: reparar línea {indice_power + 1} ({self.COSTO_REPARACION_POWER} materiales)"
					)
			indicacion = self.fuente.render(
				texto_indicacion, True, (255, 255, 255)
			)
			pantalla.blit(
				indicacion,
				indicacion.get_rect(
					midtop=(pantalla.get_width() // 2, 20)
				),
			)
			break
		if (
			self.mensaje_antena is not None
			and pygame.time.get_ticks() < self.mensaje_antena_hasta
		):
			lineas = self._envolver_texto_mensaje(
				translate(self.mensaje_antena),
				limites_pantalla.width - 240,
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
		if self.ventana_generador_abierta:
			self._dibujar_ventana_generador(pantalla)
		if self.power_pendiente_confirmacion is not None:
			self._dibujar_confirmacion_power(pantalla)
		self._dibujar_transicion_desmayo(pantalla)
		self._dibujar_transicion_ending(pantalla)
		self._actualizar_cursor_guante()

	def _dibujar_interfaz_estado(self, pantalla):
		jugador_mapa = self.camera.to_map(self.jugador.rectangulo)
		dentro_zona_segura = self._zona_segura_protege_jugador(
			jugador_mapa
		)
		self.interfaz_estado.dibujar(
			pantalla,
			self.game_state,
			mostrar_chatarra=True,
			mostrar_materiales=True,
			dentro_zona_segura=dentro_zona_segura,
		)

	def _tiene_todas_las_estrellas(self):
		return all(
			(
				self.game_state.estrella_centro_datos,
				self.game_state.estrella_expediciones,
				self.game_state.estrella_generador,
				self.game_state.reciclajeDisponible,
				self.game_state.estrella_creditos,
			)
		)

	def _dibujar_transicion_ending(self, pantalla):
		if self.transicion_ending_inicio is None:
			return
		progreso = min(
			1,
			(pygame.time.get_ticks() - self.transicion_ending_inicio)
			/ self.DURACION_FUNDIDO_ENDING,
		)
		fundido = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
		fundido.fill((0, 0, 0, round(255 * progreso)))
		pantalla.blit(fundido, (0, 0))

	def _dibujar_confirmacion_power(self, pantalla):
		capa_sombra = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
		capa_sombra.fill((0, 0, 0, 170))
		pantalla.blit(capa_sombra, (0, 0))

		ancho = min(480, pantalla.get_width() - 40)
		ventana = pygame.Rect(
			(pantalla.get_width() - ancho) // 2,
			(pantalla.get_height() - 160) // 2,
			ancho,
			160,
		)
		pygame.draw.rect(pantalla, (20, 25, 28), ventana)
		pygame.draw.rect(pantalla, (220, 230, 225), ventana, 2)

		indice_power = self.power_pendiente_confirmacion
		if indice_power is None:
			raise RuntimeError("No hay un Power pendiente de confirmación.")
		texto = self.fuente.render(
			f"¿Usar {self.COSTO_REPARACION_POWER} materiales para reparar Línea {indice_power + 1}?",
			True,
			(255, 255, 255),
		)
		pantalla.blit(
			texto,
			texto.get_rect(center=(ventana.centerx, ventana.centery - 12)),
		)
		ayuda = LocalizedFont(None, 22).render(
			"E: confirmar | Esc: cancelar", True, (200, 200, 200)
		)
		pantalla.blit(
			ayuda,
			ayuda.get_rect(center=(ventana.centerx, ventana.centery + 34)),
		)

	def _dibujar_ventana_generador(self, pantalla):
		ancho = min(480, pantalla.get_width() - 40)
		ventana = pygame.Rect(
			(pantalla.get_width() - ancho) // 2,
			(pantalla.get_height() - 180) // 2,
			ancho,
			180,
		)
		pygame.draw.rect(pantalla, (20, 25, 28), ventana)
		pygame.draw.rect(pantalla, (220, 230, 225), ventana, 2)

		titulo = self.fuente.render("GENERADOR", True, (255, 255, 255))
		pantalla.blit(
			titulo,
			titulo.get_rect(midtop=(ventana.centerx, ventana.top + 18)),
		)

		progreso = self._obtener_progreso_energia()
		rect_barra = pygame.Rect(
			ventana.left + 32,
			ventana.top + 70,
			ventana.width - 64,
			28,
		)
		pygame.draw.rect(pantalla, (55, 65, 60), rect_barra)
		if progreso:
			pygame.draw.rect(
				pantalla,
				(45, 205, 90),
				(
					rect_barra.left,
					rect_barra.top,
					round(rect_barra.width * progreso / 100),
					rect_barra.height,
				),
			)

		estado = (
			"Completado"
			if progreso == 100
			else f"Energía: {progreso}%"
		)
		texto_estado = self.fuente.render(estado, True, (255, 255, 255))
		pantalla.blit(
			texto_estado,
			texto_estado.get_rect(midtop=(ventana.centerx, ventana.top + 108)),
		)
		ayuda = LocalizedFont(None, 22).render(
			"Esc: cerrar", True, (200, 200, 200)
		)
		pantalla.blit(
			ayuda,
			ayuda.get_rect(midbottom=(ventana.centerx, ventana.bottom - 8)),
		)

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
				f"DÍA {self.game_state.dia_actual}", True, (255, 255, 255)
			)
			if tiempo_transcurrido >= inicio_fundido_entrada:
				texto_dia.set_alpha(opacidad)
			pantalla.blit(
				texto_dia,
				texto_dia.get_rect(center=pantalla.get_rect().center),
			)
