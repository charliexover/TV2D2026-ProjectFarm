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


class GameScene:
	SEGUNDOS_POR_PUNTO_OXIGENO = 0.2

	def __init__(
		self,
		game_state,
		inventario,
		al_entrar_casa,
		al_entrar_reciclaje,
		al_entrar_data_center,
	):
		self.game_state = game_state
		self.inventario = inventario
		self.interfaz_estado = InterfazEstado()
		self.jugador = Jugador()
		self.primera_entrada = True
		self.puerta_reentrada = "casa"
		self.fondo = self._cargar_fondo()
		self.camera = Camera()
		self.origen_mapa = (0, 0)
		self.al_entrar_casa = al_entrar_casa
		self.al_entrar_reciclaje = al_entrar_reciclaje
		self.al_entrar_data_center = al_entrar_data_center
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
		capa_antenas = mapa.get_layer_by_name("Antenas")
		self.antenas_mapa = {
			objeto.name: (round(objeto.x * 3), round(objeto.y * 3))
			for objeto in capa_antenas
		}
		capa_parcelas = mapa.get_layer_by_name("Parcelas")
		objeto_parcela = next(
			objeto for objeto in capa_parcelas if objeto.name == "Parcela1"
		)
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
		self.puerta_datos_mapa = (
			round(objeto_puerta_datos.x * 3),
			round(objeto_puerta_datos.y * 3),
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
		self.game_state.oxigeno = 100
		self.segundos_acumulados_oxigeno = 0
		self.ultimo_update_oxigeno = None
		self._generar_chatarra()

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

	def update(self, teclas, limites_pantalla, eventos=()):
		if self.minijuego_antena.activo:
			if self.minijuego_antena.actualizar(eventos):
				self.game_state.antena_encontrada = True
				self._mostrar_mensaje_antena(
					f"Datos de Antena "
					f"{self.game_state.antena_objetivo} descargados."
				)
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
					else puerta_casa
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
			) or self._colisiona_con_chatarra(self.jugador.rectangulo):
				self.jugador.rectangulo.y = rect_previo.y

		if rect_destino.x != rect_previo.x:
			self.jugador.rectangulo.x = rect_destino.x
			if any(
				self.camera.to_map(self.jugador.rectangulo).colliderect(colision)
				for colision in self.colisiones_mapa
			) or self._colisiona_con_chatarra(self.jugador.rectangulo):
				self.jugador.rectangulo.x = rect_previo.x

		jugador_en_movimiento = (
			self.jugador.rectangulo.topleft != rect_previo.topleft
		)
		self._actualizar_oxigeno_exterior(jugador_en_movimiento)

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
		if self.jugador.rectangulo.collidepoint(puerta_reciclaje):
			self.primera_entrada = True
			self.puerta_reentrada = "reciclaje"
			self.ultimo_update_oxigeno = None
			self.al_entrar_reciclaje()
			return
		if self.jugador.rectangulo.collidepoint(puerta_datos):
			self.primera_entrada = True
			self.puerta_reentrada = "dataCenter"
			self.ultimo_update_oxigeno = None
			self.al_entrar_data_center()
			return

		self.parcela_seleccionada = self.obtener_parcela_jugador(self.jugador)
		
		self._interactuar_con_antenas(eventos)

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
			pieza.dibujar(
				pantalla, self.sprite_chatarra, self.camera.screen_offset
			)
		
		
		desplazamiento_mundo = self.camera.screen_offset
		self.jugador.dibujar(pantalla, desplazamiento_mundo)
		
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
