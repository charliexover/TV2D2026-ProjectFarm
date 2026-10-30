import os

import pygame
import math

class Inventario:
	SLOT_MANO = 0
	SLOT_REGADERA = 1
	SLOT_SEMILLA_ZANAHORIA = 5
	SLOTS_SEMILLAS = {
		SLOT_SEMILLA_ZANAHORIA: 1,
		6: 2,
		7: 3,
		8: 4,
	}
	DESBLOQUEOS_SEMILLAS = {
		2: "semillaPapaDesbloqueada",
		3: "semillaTomateDesbloqueada",
		4: "semillaRepolloDesbloqueada",
	}

	def __init__(self, cantidad_casillas=9, tamano_casilla=45, separacion=5, separacion_grupo=12, margen_inferior=0):
		self.cantidad_casillas = cantidad_casillas
		self.tamano_casilla = tamano_casilla
		self.separacion = separacion
		self.separacion_grupo = separacion_grupo
		self.margen_inferior = margen_inferior
		self.fuente_cantidad = pygame.font.Font(None, 18)
		self.slot_seleccionado = 0
		ruta_fondo_inventario = os.path.join(
			os.path.dirname(__file__),
			"..",
			"projectFarm",
			"assets",
			"Inventory.png",
		)
		fondo_inventario = pygame.image.load(
			os.path.normpath(ruta_fondo_inventario)
		).convert_alpha()
		recorte_fondo = fondo_inventario.get_bounding_rect()
		self.fondo_inventario = fondo_inventario.subsurface(recorte_fondo).copy()
		ruta_mano = os.path.join(
			os.path.dirname(__file__), "..", "projectFarm", "assets", "handIcon.png"
		)
		self.sprite_mano = pygame.transform.scale(
			pygame.image.load(ruta_mano).convert_alpha(), (40, 40)
		)
		ruta_mano_reforzada = os.path.join(
			os.path.dirname(__file__),
			"..",
			"projectFarm",
			"assets",
			"handIcon2.png",
		)
		self.sprite_mano_reforzada = pygame.transform.scale(
			pygame.image.load(ruta_mano_reforzada).convert_alpha(), (40, 40)
		)
		ruta_assets = os.path.normpath(
			os.path.join(os.path.dirname(__file__), "..", "projectFarm", "assets")
		)
		self.sprites_semillas = {
			1: self._cargar_sprite_inventario(
				ruta_assets, "zanahoriaPack.png"
			),
			2: self._cargar_sprite_inventario(ruta_assets, "papaPack.png"),
			3: self._cargar_sprite_inventario(ruta_assets, "tomatePack.png"),
			4: self._cargar_sprite_inventario(
				ruta_assets, "repolloPack.png"
			),
		}
		self.sprite_regadera = self._cargar_sprite_inventario(
			ruta_assets, "regadera.png"
		)

	@staticmethod
	def _cargar_sprite_inventario(ruta_assets, nombre_archivo):
		ruta_sprite = os.path.join(ruta_assets, nombre_archivo)
		sprite = pygame.image.load(ruta_sprite).convert_alpha()
		return pygame.transform.scale(sprite, (36, 36))

	def obtener_rectangulos(self, ancho_pantalla, alto_pantalla):
		cortes = [corte for corte in (1, 5) if corte < self.cantidad_casillas]
		ancho_total = (
			self.cantidad_casillas * self.tamano_casilla
			+ (self.cantidad_casillas - 1) * self.separacion
			+ len(cortes) * self.separacion_grupo
		)
		inicio_x = (ancho_pantalla - ancho_total) // 2
		y = alto_pantalla - self.tamano_casilla - self.margen_inferior
		return [
			pygame.Rect(
				inicio_x
				+ indice * (self.tamano_casilla + self.separacion)
				+ sum(self.separacion_grupo for corte in cortes if indice >= corte),
				y,
				self.tamano_casilla,
				self.tamano_casilla,
			)
			for indice in range(self.cantidad_casillas)
		]

	def seleccionar_slot(self, posicion, ancho_pantalla, alto_pantalla):
		for indice, casilla in enumerate(
			self.obtener_rectangulos(ancho_pantalla, alto_pantalla)
		):
			if casilla.collidepoint(posicion):
				self.slot_seleccionado = indice
				return True
		return False

	def dibujar_fondo_seleccionado(self, pantalla, casilla):
		color_superior = (250, 229, 159)
		color_inferior = (218, 181, 91)
		for desplazamiento in range(casilla.height):
			progreso = desplazamiento / max(casilla.height - 1, 1)
			color = tuple(
				round(superior + (inferior - superior) * progreso)
				for superior, inferior in zip(color_superior, color_inferior)
			)
			pygame.draw.line(
				pantalla,
				color,
				(casilla.left, casilla.top + desplazamiento),
				(casilla.right - 1, casilla.top + desplazamiento),
			)

	def dibujar(self, pantalla, game_state):
		casillas = self.obtener_rectangulos(pantalla.get_width(), pantalla.get_height())
		if casillas:
			contenedor_casillas = casillas[0].unionall(casillas[1:])
			fondo_rect = contenedor_casillas.inflate(24, 16)
			fondo = pygame.transform.scale(
				self.fondo_inventario, fondo_rect.size
			)
			pantalla.blit(fondo, fondo_rect)

		for indice, casilla in enumerate(casillas):
			if indice == self.slot_seleccionado:
				self.dibujar_fondo_seleccionado(pantalla, casilla)
				pygame.draw.rect(pantalla, (112, 79, 29), casilla, 3)
			else:
				pygame.draw.rect(pantalla, (232, 232, 215), casilla)
				pygame.draw.rect(pantalla, (60, 65, 48), casilla, 2)

			if indice == self.SLOT_MANO:
				sprite_mano = (
					self.sprite_mano_reforzada
					if game_state.guanteReforzado
					else self.sprite_mano
				)
				pantalla.blit(
					sprite_mano,
					sprite_mano.get_rect(center=casilla.center),
				)
			elif indice in self.SLOTS_SEMILLAS:
				tipo_cultivo = self.SLOTS_SEMILLAS[indice]
				semilla = (
					"semilla_zanahoria",
					"semilla_papa",
					"semilla_tomate",
					"semilla_repollo",
				)[tipo_cultivo - 1]
				cantidad_semillas = getattr(game_state, semilla)
				desbloqueo = self.DESBLOQUEOS_SEMILLAS.get(tipo_cultivo)
				if (
					cantidad_semillas <= 0
					and desbloqueo is None
				):
					continue
				if desbloqueo is not None and not getattr(
					game_state, desbloqueo
				):
					continue
				sprite_semilla = self.sprites_semillas[tipo_cultivo]
				pantalla.blit(
					sprite_semilla,
					sprite_semilla.get_rect(center=casilla.center),
				)
				cantidad = self.fuente_cantidad.render(
					str(cantidad_semillas), True, (255, 255, 255)
				)
				cantidad_rect = cantidad.get_rect(
					topright=(casilla.right - 2, casilla.top + 1)
				)
				sombra_cantidad = self.fuente_cantidad.render(
					str(cantidad_semillas), True, (25, 25, 20)
				)
				pantalla.blit(
					sombra_cantidad,
					cantidad_rect.move(1, 1),
				)
				pantalla.blit(cantidad, cantidad_rect)
			elif indice == self.SLOT_REGADERA:
				pantalla.blit(
					self.sprite_regadera,
					self.sprite_regadera.get_rect(center=casilla.center),
				)


class InterfazEstado:
	def __init__(self):
		self.tiempo_animacion_danger = 0
		self.escala_danger = 1.0
		self.mostrar_inventario = False
		ruta_reloj = os.path.join(
			os.path.dirname(__file__), "..", "projectFarm", "assets", "reloj.png"
		)
		self.sprite_reloj = pygame.transform.scale(
			pygame.image.load(ruta_reloj).convert_alpha(), (24, 24)
		)
		self.fuente = pygame.font.Font(None, 28)

		ruta_zanahoria = os.path.join(
					os.path.dirname(__file__), "..", "projectFarm", "assets", "zanahoriaIcon.png"
				)
		self.sprite_zanahoria = pygame.transform.scale(
			pygame.image.load(ruta_zanahoria).convert_alpha(), (24, 24)
		)
		self.sprites_cosechas = {
			"papas_cosechadas": self._cargar_icono_cosecha("PapaIcon.png"),
			"tomates_cosechadas": self._cargar_icono_cosecha("TomateIcon.png"),
			"repollos_cosechadas": self._cargar_icono_cosecha("RepolloIcon.png"),
		}
		ruta_creditos = os.path.join(
			os.path.dirname(__file__), "..", "projectFarm", "assets", "creditosIcon.png"
		)
		self.sprite_creditos = pygame.transform.scale(
			pygame.image.load(ruta_creditos).convert_alpha(), (24, 24)
		)
		ruta_materiales = os.path.join(
			os.path.dirname(__file__), "..", "projectFarm", "assets", "materialesIcon.png"
		)
		self.sprite_materiales = pygame.transform.scale(
			pygame.image.load(ruta_materiales).convert_alpha(), (24, 24)
		)
		ruta_chatarra = os.path.join(
			os.path.dirname(__file__), "..", "projectFarm", "assets", "chatarraIcon.png"
		)
		self.sprite_chatarra = pygame.transform.scale(
			pygame.image.load(ruta_chatarra).convert_alpha(), (24, 24)
		)
		ruta_oxigeno = os.path.join(
			os.path.dirname(__file__), "..", "projectFarm", "assets", "oxigenoIcon.png"
		)
		self.sprite_oxigeno = pygame.transform.scale(
			pygame.image.load(ruta_oxigeno).convert_alpha(), (24, 24)
		)
		ruta_hud_oxigeno = os.path.join(
			os.path.dirname(__file__),
			"..",
			"projectFarm",
			"assets",
			"hudOxigeno.png",
		)

		self.sprite_hud_oxigeno = pygame.transform.scale(
			pygame.image.load(ruta_hud_oxigeno).convert_alpha(),
			(135, 135),
		)

		ruta_safe = os.path.join(
			os.path.dirname(__file__),
			"..",
			"projectFarm",
			"assets",
			"statusSafe.png",
		)

		ruta_danger = os.path.join(
			os.path.dirname(__file__),
			"..",
			"projectFarm",
			"assets",
			"statusDanger.png",
		)

		self.sprite_safe = pygame.transform.scale_by(
			pygame.image.load(ruta_safe).convert_alpha(),
			3,
		)

		self.sprite_danger = pygame.transform.scale_by(
			pygame.image.load(ruta_danger).convert_alpha(),
			3,
		)

		ruta_fondo = os.path.join(
			os.path.dirname(__file__),
			"..",
			"projectFarm",
			"assets",
			"inventoryHud.png",
		)

		self.sprite_fondo_inventario = pygame.transform.scale(
			pygame.image.load(ruta_fondo).convert_alpha(),
			(320, 310),
		)

	def _cargar_icono_cosecha(self, nombre_archivo):
				ruta_icono = os.path.join(
					os.path.dirname(__file__), "..", "projectFarm", "assets", nombre_archivo
				)
				return pygame.transform.scale(
					pygame.image.load(ruta_icono).convert_alpha(), (24, 24)
				)	

	def dibujar_inventario(self, pantalla, game_state):
		ancho = 320
		alto = 310

		ventana = pygame.Rect(
			(pantalla.get_width() - ancho) // 2,
			(pantalla.get_height() - alto) // 2,
			ancho,
			alto,
		)

		pantalla.blit(
			self.sprite_fondo_inventario,
			ventana.topleft,
		)

		titulo = self.fuente.render(
			"RECURSOS",
			True,
			(255, 255, 255),
		)
		pantalla.blit(titulo, (ventana.x + 20, ventana.y + 12))

		recursos = [
			(
				self.sprite_zanahoria,
				"Zanahorias",
				game_state.zanahorias_cosechadas,
			),
			(
				self.sprites_cosechas["papas_cosechadas"],
				"Papas",
				game_state.papas_cosechadas,
			),
			(
				self.sprites_cosechas["tomates_cosechadas"],
				"Tomates",
				game_state.tomates_cosechadas,
			),
			(
				self.sprites_cosechas["repollos_cosechadas"],
				"Repollos",
				game_state.repollos_cosechadas,
			),
			(
				self.sprite_materiales,
				"Materiales",
				game_state.materiales,
			),
			(
				self.sprite_chatarra,
				"Chatarra",
				game_state.chatarra,
			),
		]

		y = ventana.y + 48

		for icono, nombre, cantidad in recursos:
			pantalla.blit(icono, (ventana.x + 20, y))

			texto = self.fuente.render(
				f"{nombre}: {cantidad}",
				True,
				(255, 255, 255),
			)
			pantalla.blit(texto, (ventana.x + 55, y + 2))

			y += 40

		# Instrucción para cerrar
		ayuda = pygame.font.Font(None, 22).render(
			"I: cerrar",
			True,
			(200, 200, 200),
		)
		pantalla.blit(
			ayuda,
			ayuda.get_rect(
				midbottom=(ventana.centerx, ventana.bottom - 8)
			),
		)

	def dibujar(
		self,
		pantalla,
		game_state,
		mostrar_chatarra=False,
		mostrar_procesamiento=False,
		mostrar_materiales=False,
		y_inicial=46,
		dentro_zona_segura=True,
	):
		lineas = []
		# Panel del HUD: día, oxígeno y créditos
		escala = 3
		posicion_x = pantalla.get_width() - self.sprite_hud_oxigeno.get_width() - 10
		posicion_y = 10

		rect_hud = self.sprite_hud_oxigeno.get_rect(
			topleft=(posicion_x, posicion_y)
		)

		# Dibujar primero el panel de fondo
		pantalla.blit(self.sprite_hud_oxigeno, rect_hud)

		# Día actual
		texto_dia = self.fuente.render(
			str(game_state.dia_actual),
			True,
			(255, 255, 255),
		)
		pantalla.blit(
			texto_dia,
			(posicion_x + 40, posicion_y + 20),
		)

		# Barra de oxígeno
		ancho_barra = 37 * escala
		alto_barra = 5 * escala

		rect_barra = pygame.Rect(
			posicion_x + 4 * escala,
			posicion_y + 15 * escala,
			ancho_barra,
			alto_barra,
		)

		# Fondo de la barra
		pygame.draw.rect(
			pantalla,
			(35, 43, 48),
			rect_barra,
		)

		# Porcentaje de oxígeno restante según el máximo actual
		oxigeno_maximo = max(1, game_state.oxigeno_maximo)

		porcentaje_oxigeno = max(
			0,
			min(1, game_state.oxigeno / oxigeno_maximo),
		)

		ancho_relleno = round(
			ancho_barra * porcentaje_oxigeno,
		)

		color_oxigeno = (
			(75, 200, 245)
			if dentro_zona_segura
			else (245, 105, 70)
		)

		if ancho_relleno > 0:
			pygame.draw.rect(
				pantalla,
				color_oxigeno,
				(
					rect_barra.x,
					rect_barra.y,
					ancho_relleno,
					alto_barra,
				),
			)

		# Indicador de zona segura, debajo de los créditos
		if dentro_zona_segura:
			sprite_estado = self.sprite_safe
			escala_estado = 1.0
		else:
			sprite_estado = self.sprite_danger

			tiempo = pygame.time.get_ticks() / 250
			escala_estado = 1.0 + 0.08 * (
				(1 + math.sin(tiempo)) / 2
			)

		ancho = max(1, int(sprite_estado.get_width() * escala_estado))
		alto = max(1, int(sprite_estado.get_height() * escala_estado))

		sprite_animado = pygame.transform.scale(
			sprite_estado,
			(ancho, alto),
		)

		# Centrar el indicador debajo de los créditos
		centro_x = posicion_x + self.sprite_hud_oxigeno.get_width() // 2
		posicion_indicador_y = posicion_y + 95 + 5

		rect_estado = sprite_animado.get_rect(
			midtop=(centro_x, posicion_indicador_y)
		)

		pantalla.blit(sprite_animado, rect_estado)

		# Créditos
		pantalla.blit(
			self.sprite_creditos,
			(posicion_x + 6, posicion_y + 65),
		)

		texto_creditos = self.fuente.render(
			str(game_state.creditos),
			True,
			(255, 255, 255),
		)

		pantalla.blit(
			texto_creditos,
			(posicion_x + 30, posicion_y + 70),
		)

		""" y = y_inicial
		pantalla.blit(self.sprite_zanahoria, (10, y))
		cantidad_zanahorias = self.fuente.render(
			str(game_state.zanahorias_cosechadas), True, (255, 255, 255)
		)
		pantalla.blit(cantidad_zanahorias, (42, y + 6))
		y += 34

		for atributo, sprite in self.sprites_cosechas.items():
			pantalla.blit(sprite, (10, y))
			cantidad = self.fuente.render(
				str(getattr(game_state, atributo)), True, (255, 255, 255)
			)
			pantalla.blit(cantidad, (42, y + 6))
			y += 34

		

		if mostrar_chatarra:
			pantalla.blit(self.sprite_chatarra, (10, y))
			cantidad_chatarra = self.fuente.render(
				str(game_state.chatarra), True, (255, 255, 255)
			)
			pantalla.blit(cantidad_chatarra, (42, y + 5))
			y += 34
		
		if mostrar_materiales:
			pantalla.blit(self.sprite_materiales, (10, y))
			cantidad_materiales = self.fuente.render(
				str(game_state.materiales), True, (255, 255, 255)
			)
			pantalla.blit(cantidad_materiales, (42, y + 5))
 """	

		if self.mostrar_inventario:
			self.dibujar_inventario(pantalla, game_state)
