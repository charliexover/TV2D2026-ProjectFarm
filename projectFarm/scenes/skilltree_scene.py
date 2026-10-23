import os
import xml.etree.ElementTree as ET

import pygame

from engine.spritesheet import Spritesheet


class SkillTreeMenu:
	ESCALA = 3
	ESCALA_HOVER = 1.25
	COMPRAS_NODOS = {
		"Parcela1": {
			"estado": "parcela1Comprada",
			"costo": 0,
			"nombre": "Parcela 1",
		},
		"Parcela2": {
			"estado": "parcela2Comprada",
			"costo": 100,
			"nombre": "Parcela 2",
		},
		"Parcela3": {
			"estado": "parcela3Comprada",
			"costo": 150,
			"nombre": "Parcela 3",
		},
		"GuantesReforzados": {
			"estado": "guanteReforzado",
			"costo": 50,
			"nombre": "Guantes Reforzados",
		},
		"TanqueOxigeno1": {
			"estado": "tanqueOxigenoEsteComprado",
			"costo": 50,
			"nombre": "Tanque de Oxígeno Este",
		},
		"TanqueOxigeno2": {
			"estado": "tanqueOxigenoOesteComprado",
			"costo": 100,
			"nombre": "Tanque de Oxígeno Oeste",
			"requiere": "tanqueOxigenoEsteComprado",
			"requisito_nombre": "el Tanque de Oxígeno Este",
		},
		"TanqueOxigeno3": {
			"estado": "tanqueOxigenoNorteComprado",
			"costo": 150,
			"nombre": "Tanque de Oxígeno Norte",
			"requiere": "tanqueOxigenoOesteComprado",
			"requisito_nombre": "el Tanque de Oxígeno Oeste",
		},
		"CentroDatos": {
			"estado": "centroDatosComprado",
			"costo": 200,
			"materiales": 50,
			"nombre": "Centro de Datos",
		},
		"Expediciones": {
			"estado": "expedicionesComprado",
			"costo": 300,
			"materiales": 100,
			"nombre": "Centro de Expediciones",
		},
		"Reciclaje": {
			"estado": "reciclajeComprado",
			"costo": 100,
			"nombre": "Centro de Reciclaje",
		},
		"SemillaPapa": {
			"estado": "semillaPapaDesbloqueada",
			"costo": 25,
			"nombre": "semilla de papa",
		},
		"SemillaTomate": {
			"estado": "semillaTomateDesbloqueada",
			"costo": 60,
			"nombre": "semilla de tomate",
			"requiere": "semillaPapaDesbloqueada",
			"requisito_nombre": "la semilla de papa",
		},
		"SemillaRepollo": {
			"estado": "semillaRepolloDesbloqueada",
			"costo": 120,
			"nombre": "semilla de repollo",
			"requiere": "semillaTomateDesbloqueada",
			"requisito_nombre": "la semilla de tomate",
		},
	}
	SPRITES_NODOS = {
		"Parcela": "Parcela_OFF",
		"GuantesReforzados": "GuantesReforzados_OFF",
		"TanqueOxigeno": "TanqueOxigeno_OFF",
		"CentroDatos": "CentroDatos_OFF",
		"Expediciones": "Expediciones_OFF",
		"Reciclaje": "Reciclaje_OFF",
		"Semilla": "Semillas_OFF",
		"CintaReciclaje": "CintaReciclaje_OFF",
		"DescargaDatos": "DescargaDatos_OFF",
		"OxigenoMaximo": "OxigenoMaximo_OFF",
	}

	def __init__(self):
		self.abierto = False
		self.dialogo = None
		self.fuente_dialogo = pygame.font.Font(None, 28)
		self.fuente_boton = pygame.font.Font(None, 26)
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
		compra = self.COMPRAS_NODOS[nombre_nodo]
		costo = f"{compra['costo']} créditos"
		if compra.get("materiales", 0):
			costo += f" y {compra['materiales']} materiales"
		self.dialogo = {
			"tipo": "confirmacion",
			"nodo": nombre_nodo,
			"texto": f"Desbloquear {compra['nombre']} cuesta {costo}. "
			"¿Quieres comprarlo?",
		}

	def mostrar_mensaje(self, texto):
		self.dialogo = {"tipo": "mensaje", "texto": texto}

	def _resolver_opcion(self, etiqueta, game_state):
		if self.dialogo["tipo"] == "confirmacion" and etiqueta == "Sí":
			compra = self.COMPRAS_NODOS[self.dialogo["nodo"]]
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
		self.dialogo = None

	def procesar_eventos(self, eventos, limites_pantalla, game_state):
		for evento in eventos:
			if evento.type == pygame.KEYDOWN and evento.key == pygame.K_g:
				if self.dialogo is None:
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
						or not rect_nodo.collidepoint(evento.pos)
					):
						continue
					compra = self.COMPRAS_NODOS[nombre_compra]
					if getattr(game_state, compra["estado"]):
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
			for nombre, sprite_off, sprite_on, (x, y) in self.nodos:
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