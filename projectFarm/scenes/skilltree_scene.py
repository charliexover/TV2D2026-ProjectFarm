import os
import xml.etree.ElementTree as ET

import pygame

from engine.audio import reproducir_sonido_pc
from engine.spritesheet import Spritesheet
from projectFarm.farm import CULTIVOS


class SkillTreeMenu:
	ESCALA = 3
	ESCALA_HOVER = 1.25
	COMPRAS_NODOS = {
		"GuantesReforzados": {
			"estado": "guanteReforzado",
			"costo": 50,
			"nombre": "Guantes Reforzados",
			"descripcion": "Permite recoger chatarra del suelo.",
		},
		"OxigenoMaximo1": {
			"estado": "oxigenoMaximo1Comprado",
			"costo": 100,
			"aumento": 50,
			"nombre": "Oxígeno Máximo I",
			"descripcion": "Aumenta el oxígeno máximo en 50.",
		},
		"OxigenoMaximo2": {
			"estado": "oxigenoMaximo2Comprado",
			"costo": 150,
			"aumento": 50,
			"nombre": "Oxígeno Máximo II",
			"descripcion": "Aumenta el oxígeno máximo en 50.",
			"requiere": "oxigenoMaximo1Comprado",
			"requisito_nombre": "la mejora de Oxígeno Máximo I",
		},
		"OxigenoMaximo3": {
			"estado": "oxigenoMaximo3Comprado",
			"costo": 250,
			"aumento": 50,
			"nombre": "Oxígeno Máximo III",
			"descripcion": "Aumenta el oxígeno máximo en 50.",
			"requiere": "oxigenoMaximo2Comprado",
			"requisito_nombre": "la mejora de Oxígeno Máximo II",
		},
		"CentroDatos": {
			"estado": "centroDatosComprado",
			"costo": 100,
			"materiales": 50,
			"nombre": "Centro de Datos",
			"descripcion": "Desbloquea el Centro de Datos para enviar datos de antenas.",
		},
		"DescargaDatos1": {
			"estado": "descargaDatos1Comprado",
			"costo": 150,
			"nombre": "Descarga de Datos I",
			"descripcion": "Suma 3 al progreso al enviar datos de antena.",
			"requiere": "centroDatosComprado",
			"requisito_nombre": "el Centro de Datos",
		},
		"DescargaDatos2": {
			"estado": "descargaDatos2Comprado",
			"costo": 150,
			"nombre": "Descarga de Datos II",
			"descripcion": "Suma 4 al progreso al enviar datos de antena.",
			"requiere": "descargaDatos1Comprado",
			"requisito_nombre": "la mejora de Descarga de Datos I",
		},
		"Expediciones": {
			"estado": "expedicionesComprado",
			"costo": 100,
			"materiales": 50,
			"nombre": "Centro de Expediciones",
			"descripcion": "Desbloquea las expediciones con el Rover.",
		},
		"Reciclaje": {
			"estado": "reciclajeComprado",
			"costo": 100,
			"nombre": "Centro de Reciclaje",
			"descripcion": "Desbloquea el Centro de Reciclaje.",
		},
		"SemillaPapa": {
			"estado": "semillaPapaDesbloqueada",
			"costo": 25,
			"cultivo": 2,
			"nombre": "semilla de papa",
			"descripcion": "Desbloquea el cultivo de papas.",
		},
		"SemillaTomate": {
			"estado": "semillaTomateDesbloqueada",
			"costo": 100,
			"cultivo": 3,
			"nombre": "semilla de tomate",
			"descripcion": "Desbloquea el cultivo de tomates.",
			"requiere": "semillaPapaDesbloqueada",
			"requisito_nombre": "la semilla de papa",
		},
		"SemillaRepollo": {
			"estado": "semillaRepolloDesbloqueada",
			"costo": 150,
			"cultivo": 4,
			"nombre": "semilla de repollo",
			"descripcion": "Desbloquea el cultivo de repollos.",
			"requiere": "semillaTomateDesbloqueada",
			"requisito_nombre": "la semilla de tomate",
		},
		"MejorRegadera": {
			"estado": "mejorRegaderaComprada",
			"costo": 300,
			"nombre": "Mejor Regadera",
			"descripcion": "Riega hasta 9 parcelas alrededor de la seleccionada.",
		},
		"MejorExpedicion": {
			"estado": "mejorExpedicionComprada",
			"costo": 250,
			"nombre": "Mejor Expedición",
			"descripcion": "Reduce a la mitad la duración de nuevas expediciones.",
			"requiere": "expedicionesComprado",
			"requisito_nombre": "el Centro de Expediciones",
		},
		"Radar": {
			"estado": "radarComprado",
			"costo": 100,
			"nombre": "Radar",
			"descripcion": "Permite usar el radar para localizar puntos de interés.",
		},
		"TrajeAntiTormenta": {
			"estado": "trajeAntiTormentaComprado",
			"costo": 500,
			"nombre": "Traje Anti-Tormenta",
			"descripcion": "Protege la zona segura y normaliza el oxígeno durante tormentas.",
			"dia_requerido": 14,
		},
		"Martillo": {
			"estado": "martilloComprado",
			"costo": 500,
			"nombre": "Martillo",
			"descripcion": "Permite romper muros no muy solidos.",
			"disponible": "martilloDisponible",
			"estrellas_requeridas": 1,
		},
		"Linterna": {
			"estado": "linternaComprada",
			"costo": 500,
			"nombre": "Linterna",
			"descripcion": "Una linterna para explorar lugares oscuros.",
			"estrellas_requeridas": 2,
		},
	}
	SPRITES_NODOS = {
		"GuantesReforzados": "GuantesReforzados_OFF",
		"CentroDatos": "CentroDatos_OFF",
		"Expediciones": "Expediciones_OFF",
		"Reciclaje": "Reciclaje_OFF",
		"MejorRegadera": "MejorRegadera_OFF",
		"MejorExpedicion": "MejorExpedicion_OFF",
		"Radar": "Radar_OFF",
		"TrajeAntiTormenta": "TrajeAntiTormenta_OFF",
		"Semilla": "Semillas_OFF",
		"CintaReciclaje": "CintaReciclaje_OFF",
		"DescargaDatos": "DescargaDatos_OFF",
		"OxigenoMaximo": "OxigenoMaximo_OFF",
		"Martillo": "Creditos_OFF",
		"Linterna": "Creditos_OFF",
	}

	def __init__(self):
		self.abierto = False
		self.dialogo = None
		self.fuente_dialogo = pygame.font.Font(None, 28)
		self.fuente_boton = pygame.font.Font(None, 26)
		self.fuente_tooltip = pygame.font.Font(None, 22)
		ruta_scenes = os.path.dirname(__file__)
		ruta_assets = os.path.normpath(
			os.path.join(ruta_scenes, "..", "assets")
		)
		ruta_fondo = os.path.join(ruta_assets, "SkillTree.png")
		self.fondo = pygame.image.load(ruta_fondo).convert_alpha()
		self.fondo = pygame.transform.scale(
			self.fondo,
			(
				self.fondo.get_width() * self.ESCALA,
				self.fondo.get_height() * self.ESCALA,
			),
		)
		ruta_spritesheet = os.path.normpath(
			os.path.join(
				ruta_scenes, "..", "utils", "SkillSpritesheet.json"
			)
		)
		spritesheet = Spritesheet(ruta_spritesheet)
		raiz_mapa = ET.parse(
			os.path.join(ruta_assets, "SkillTreeScene.tmx")
		).getroot()
		capa_nodos = raiz_mapa.find("./objectgroup[@name='Nodos']")
		if capa_nodos is None:
			raise ValueError("No se encontro la capa 'Nodos' del arbol.")

		self.nodos = []
		for objeto in capa_nodos.findall("object"):
			nombre = objeto.attrib["name"]
			nombre_sprite = next(
				(
					sprite
					for prefijo, sprite in self.SPRITES_NODOS.items()
					if nombre.startswith(prefijo)
				),
				None,
			)
			if nombre_sprite is None:
				raise ValueError(
					f"No hay un sprite configurado para el nodo '{nombre}'."
				)

			sprite_off = spritesheet.get_sprite(nombre_sprite)
			sprite_on = spritesheet.get_sprite(
				nombre_sprite.replace("_OFF", "_ON")
			)
			self.nodos.append(
				(
					nombre,
					self._escalar_sprite(sprite_off),
					self._escalar_sprite(sprite_on),
					(
						round(float(objeto.attrib["x"]) * self.ESCALA),
						round(float(objeto.attrib["y"]) * self.ESCALA),
					),
				)
			)

	@staticmethod
	def _escalar_sprite(sprite):
		return pygame.transform.scale(
			sprite,
			(
				sprite.get_width() * SkillTreeMenu.ESCALA,
				sprite.get_height() * SkillTreeMenu.ESCALA,
			),
		)

	def _rectangulo_dialogo(self, limites_pantalla):
		return pygame.Rect(0, 0, 480, 190).move(
			limites_pantalla.centerx - 240,
			limites_pantalla.centery - 95,
		)

	def _rectangulos_opciones(self, rect_dialogo):
		if self.dialogo["tipo"] == "confirmacion":
			etiquetas = ("Sí", "No")
		else:
			etiquetas = ("Aceptar",)
		ancho_boton = 120
		alto_boton = 38
		espacio = 16
		ancho_total = len(etiquetas) * ancho_boton + (
			len(etiquetas) - 1
		) * espacio
		x = rect_dialogo.centerx - ancho_total // 2
		y = rect_dialogo.bottom - alto_boton - 18
		return [
			(etiqueta, pygame.Rect(
				x + indice * (ancho_boton + espacio),
				y,
				ancho_boton,
				alto_boton,
			))
			for indice, etiqueta in enumerate(etiquetas)
		]

	def _abrir_confirmacion_compra(self, nombre_nodo):
		self.dialogo = {
			"tipo": "confirmacion",
			"nodo": nombre_nodo,
			"texto": "¿Quieres comprarlo?",
		}

	def mostrar_mensaje(self, texto):
		self.dialogo = {"tipo": "mensaje", "texto": texto}

	def _texto_hover_nodo(self, nombre_nodo, game_state):
		compra = self.COMPRAS_NODOS[nombre_nodo]
		lineas = [compra["nombre"]]
		lineas.append(compra["descripcion"])
		cultivo_id = compra.get("cultivo")
		if cultivo_id is not None:
			cultivo = CULTIVOS[cultivo_id]
			lineas.append(
				f"Tiempo de crecimiento: "
				f"{cultivo['dias_crecimiento']} dias"
			)
			lineas.append(
				f"Precio de venta: {cultivo['precio_venta']} créditos"
			)
		costo = f"Costo: {compra['costo']} créditos"
		if compra.get("materiales", 0):
			costo += f" y {compra['materiales']} materiales"
		lineas.append(costo)

		if getattr(game_state, compra["estado"]):
			lineas.append("Ya comprada")
		elif compra.get("estrellas_requeridas", 0) > self._contar_estrellas(
			game_state
		):
			lineas.append(
				"Requiere al menos "
				f"{compra['estrellas_requeridas']} estrellas encendidas"
			)
		elif compra.get("requiere") and not getattr(
			game_state, compra["requiere"]
		):
			lineas.append(
				f"Requiere {compra['requisito_nombre']}"
			)
		return lineas

	@staticmethod
	def _contar_estrellas(game_state):
		return sum(
			(
				game_state.estrella_centro_datos,
				game_state.estrella_expediciones,
				game_state.estrella_generador,
				game_state.reciclajeDisponible,
				game_state.estrella_creditos,
			)
		)

	@staticmethod
	def _nodo_visible(nombre_nodo, game_state):
		compra = SkillTreeMenu.COMPRAS_NODOS.get(nombre_nodo)
		if compra is None:
			return True
		disponible = compra.get("disponible")
		return (
			game_state.dia_actual >= compra.get("dia_requerido", 1)
			and (disponible is None or getattr(game_state, disponible))
		)

	def _cumple_requisitos_estrellas(self, nombre_nodo, game_state):
		cantidad_requerida = self.COMPRAS_NODOS[nombre_nodo].get(
			"estrellas_requeridas", 0
		)
		return self._contar_estrellas(game_state) >= cantidad_requerida

	def _dibujar_tooltip(self, pantalla, nombre_nodo, posicion, game_state):
		lineas_sin_ajustar = self._texto_hover_nodo(
			nombre_nodo, game_state
		)
		ancho_maximo = min(420, pantalla.get_width() - 32)
		lineas = []
		for texto in lineas_sin_ajustar:
			renglon = ""
			for palabra in texto.split():
				candidato = f"{renglon} {palabra}".strip()
				if (
					renglon
					and self.fuente_tooltip.size(candidato)[0]
					> ancho_maximo
				):
					lineas.append(renglon)
					renglon = palabra
				else:
					renglon = candidato
			if renglon:
				lineas.append(renglon)
		anchura_texto = max(
			self.fuente_tooltip.size(linea)[0] for linea in lineas
		)
		ancho = anchura_texto + 24
		alto = len(lineas) * 25 + 16
		rect_tooltip = pygame.Rect(
			posicion[0] + 18,
			posicion[1] + 18,
			ancho,
			alto,
		)
		rect_tooltip.right = min(
			rect_tooltip.right, pantalla.get_width() - 8
		)
		rect_tooltip.bottom = min(
			rect_tooltip.bottom, pantalla.get_height() - 8
		)
		rect_tooltip.left = max(rect_tooltip.left, 8)
		rect_tooltip.top = max(rect_tooltip.top, 8)
		pygame.draw.rect(pantalla, (12, 14, 24), rect_tooltip)
		pygame.draw.rect(pantalla, (235, 235, 245), rect_tooltip, 1)

		for indice, texto in enumerate(lineas):
			superficie = self.fuente_tooltip.render(
				texto, True, (255, 255, 255)
			)
			pantalla.blit(
				superficie,
				(rect_tooltip.left + 12, rect_tooltip.top + 8 + indice * 25),
			)

	def _dibujar_conexiones(self, pantalla, rect_fondo, game_state):
		posiciones = {
			nombre: (rect_fondo.left + x, rect_fondo.top + y)
			for nombre, _, _, (x, y) in self.nodos
		}
		nodos_por_estado = {
			compra["estado"]: nombre
			for nombre, compra in self.COMPRAS_NODOS.items()
		}
		for nombre, compra in self.COMPRAS_NODOS.items():
			estado_requerido = compra.get("requiere")
			nombre_anterior = nodos_por_estado.get(estado_requerido)
			if nombre_anterior is None:
				continue
			if not self._nodo_visible(nombre, game_state):
				continue
			pygame.draw.line(
				pantalla,
				(255, 255, 255),
				posiciones[nombre_anterior],
				posiciones[nombre],
				3,
			)

	def _resolver_opcion(self, etiqueta, game_state):
		if self.dialogo["tipo"] == "confirmacion" and etiqueta == "Sí":
			nombre_nodo = self.dialogo["nodo"]
			compra = self.COMPRAS_NODOS[nombre_nodo]
			if not self._nodo_visible(nombre_nodo, game_state):
				self.mostrar_mensaje(
					f"{compra['nombre']} todavía no está disponible."
				)
				return
			if not self._cumple_requisitos_estrellas(nombre_nodo, game_state):
				self.mostrar_mensaje(
					f"Necesitas al menos "
					f"{compra['estrellas_requeridas']} estrellas encendidas "
					f"para comprar {compra['nombre']}."
				)
				return
			costo_materiales = compra.get("materiales", 0)
			if (
				game_state.creditos < compra["costo"]
				or game_state.materiales < costo_materiales
			):
				self.mostrar_mensaje(
					f"No tienes suficientes recursos para desbloquear "
					f"{compra['nombre']}."
				)
				return
			game_state.creditos -= compra["costo"]
			game_state.materiales -= costo_materiales
			setattr(game_state, compra["estado"], True)
			if "aumento" in compra:
				game_state.oxigeno_maximo += compra["aumento"]
				game_state.oxigeno = min(
					game_state.oxigeno + compra["aumento"],
					game_state.oxigeno_maximo,
				)
		self.dialogo = None

	def procesar_eventos(self, eventos, limites_pantalla, game_state):
		for evento in eventos:
			if evento.type == pygame.KEYDOWN and evento.key == pygame.K_g:
				if self.dialogo is None:
					if not self.abierto:
						reproducir_sonido_pc()
					self.abierto = not self.abierto
				return True

			if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
				if self.dialogo is not None:
					self.dialogo = None
					return True
				if self.abierto:
					self.abierto = False
					return True

			if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
				continue

			if self.dialogo is not None:
				rect_dialogo = self._rectangulo_dialogo(limites_pantalla)
				for etiqueta, rectangulo in self._rectangulos_opciones(
					rect_dialogo
				):
					if rectangulo.collidepoint(evento.pos):
						reproducir_sonido_pc()
						self._resolver_opcion(etiqueta, game_state)
						break
				return True

			if self.abierto:
				rect_fondo = self.fondo.get_rect(
					center=limites_pantalla.center
				)
				for nombre, sprite_off, _, posicion in self.nodos:
					rect_nodo = sprite_off.get_rect(
						center=(
							rect_fondo.left + posicion[0],
							rect_fondo.top + posicion[1],
						)
					).inflate(8, 8)
					nombre_compra = next(
						(
							nombre_nodo
							for nombre_nodo in self.COMPRAS_NODOS
							if nombre == nombre_nodo
						),
						None,
					)
					if (
						nombre_compra is None
						or not self._nodo_visible(nombre_compra, game_state)
						or not rect_nodo.collidepoint(evento.pos)
					):
						continue
					reproducir_sonido_pc()
					compra = self.COMPRAS_NODOS[nombre_compra]
					if getattr(game_state, compra["estado"]):
						return True
					if not self._cumple_requisitos_estrellas(
						nombre_compra, game_state
					):
						self.mostrar_mensaje(
							f"Necesitas al menos "
							f"{compra['estrellas_requeridas']} estrellas "
							f"encendidas para comprar {compra['nombre']}."
						)
						return True
					requisito = compra.get("requiere")
					if requisito is not None and not getattr(
						game_state, requisito
					):
						self.mostrar_mensaje(
							f"Primero debes desbloquear "
							f"{compra['requisito_nombre']}."
						)
						return True
					self._abrir_confirmacion_compra(nombre_compra)
					return True

		return self.abierto or self.dialogo is not None

	def dibujar(self, pantalla, game_state):
		if not self.abierto and self.dialogo is None:
			return

		capa_sombra = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
		capa_sombra.fill((0, 0, 0, 150))
		pantalla.blit(capa_sombra, (0, 0))
		if self.abierto:
			rect_fondo = self.fondo.get_rect(
				center=pantalla.get_rect().center
			)
			pantalla.blit(self.fondo, rect_fondo)
			self._dibujar_conexiones(
				pantalla, rect_fondo, game_state
			)
			nodo_hover = None
			posicion_mouse = pygame.mouse.get_pos()
			for nombre, sprite_off, sprite_on, (x, y) in self.nodos:
				if not self._nodo_visible(nombre, game_state):
					continue
				compra = self.COMPRAS_NODOS.get(nombre)
				sprite = (
					sprite_on
					if compra is not None
					and getattr(game_state, compra["estado"])
					else sprite_off
				)
				rect_nodo = sprite.get_rect(
					center=(rect_fondo.left + x, rect_fondo.top + y)
				)
				if (
					self.dialogo is None
					and compra is not None
					and rect_nodo.inflate(8, 8).collidepoint(
						posicion_mouse
					)
				):
					nodo_hover = nombre
				if (
					self.dialogo is None
					and rect_nodo.collidepoint(pygame.mouse.get_pos())
				):
					sprite = pygame.transform.scale(
						sprite,
						(
							round(sprite.get_width() * self.ESCALA_HOVER),
							round(sprite.get_height() * self.ESCALA_HOVER),
						),
					)
				pantalla.blit(
					sprite,
					sprite.get_rect(
						center=(rect_fondo.left + x, rect_fondo.top + y)
					),
				)
			if nodo_hover is not None:
				self._dibujar_tooltip(
					pantalla, nodo_hover, posicion_mouse, game_state
				)

		if self.dialogo is None:
			return

		rect_dialogo = self._rectangulo_dialogo(pantalla.get_rect())
		pygame.draw.rect(pantalla, (12, 14, 24), rect_dialogo)
		pygame.draw.rect(pantalla, (235, 235, 245), rect_dialogo, 2)
		lineas = self.dialogo["texto"].split()
		renglones = []
		renglon = ""
		for palabra in lineas:
			candidato = f"{renglon} {palabra}".strip()
			if renglon and self.fuente_dialogo.size(candidato)[0] > 430:
				renglones.append(renglon)
				renglon = palabra
			else:
				renglon = candidato
		if renglon:
			renglones.append(renglon)
		for indice, texto in enumerate(renglones):
			superficie = self.fuente_dialogo.render(
				texto, True, (255, 255, 255)
			)
			pantalla.blit(
				superficie,
				(
					rect_dialogo.centerx - superficie.get_width() // 2,
					rect_dialogo.top + 35 + indice * 32,
				),
			)
		for etiqueta, rectangulo in self._rectangulos_opciones(rect_dialogo):
			pygame.draw.rect(pantalla, (45, 54, 75), rectangulo)
			pygame.draw.rect(pantalla, (235, 235, 245), rectangulo, 1)
			superficie = self.fuente_boton.render(
				etiqueta, True, (255, 255, 255)
			)
			pantalla.blit(
				superficie,
				superficie.get_rect(center=rectangulo.center),
			)