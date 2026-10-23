import os

import pygame


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

	def _cargar_icono_cosecha(self, nombre_archivo):
		ruta_icono = os.path.join(
			os.path.dirname(__file__), "..", "projectFarm", "assets", nombre_archivo
		)
		return pygame.transform.scale(
			pygame.image.load(ruta_icono).convert_alpha(), (24, 24)
		)

	def dibujar(
		self,
		pantalla,
		game_state,
		mostrar_chatarra=False,
		mostrar_procesamiento=False,
		mostrar_materiales=False,
		y_inicial=46,
	):
		lineas = []
		pantalla.blit(self.sprite_reloj, (10, 10))
		texto_dia = self.fuente.render(
			str(game_state.dia_actual), True, (255, 255, 255)
		)
		pantalla.blit(texto_dia, (42, 20))

		y = y_inicial
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

		pantalla.blit(self.sprite_oxigeno, (10, y))
		cantidad_oxigeno = self.fuente.render(
			str(game_state.oxigeno), True, (255, 255, 255)
		)
		pantalla.blit(cantidad_oxigeno, (42, y + 5))
		y += 34

		pantalla.blit(self.sprite_creditos, (10, y))
		cantidad_creditos = self.fuente.render(
			str(game_state.creditos), True, (255, 255, 255)
		)
		pantalla.blit(cantidad_creditos, (42, y + 5))
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

		for texto, posicion_y in lineas:
			superficie = self.fuente.render(texto, True, (255, 255, 255))
			pantalla.blit(superficie, (10, posicion_y))
