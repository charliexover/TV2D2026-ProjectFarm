import pygame


class Inventario:
	SLOT_MANO = 0
	SLOT_REGADERA = 1
	SLOT_SEMILLA_ZANAHORIA = 5

	def __init__(self, cantidad_casillas=9, tamano_casilla=48, separacion=5, separacion_grupo=12, margen_inferior=16):
		self.cantidad_casillas = cantidad_casillas
		self.tamano_casilla = tamano_casilla
		self.separacion = separacion
		self.separacion_grupo = separacion_grupo
		self.margen_inferior = margen_inferior
		self.fuente_item = pygame.font.Font(None, 22)
		self.fuente_cantidad = pygame.font.Font(None, 18)
		self.slot_seleccionado = 0

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

	def dibujar_mano(self, pantalla, x, y):
		color_mano = (225, 184, 143)
		borde_mano = (112, 79, 56)
		dedos = [
			pygame.Rect(x + 16, y + 13, 6, 18),
			pygame.Rect(x + 21, y + 9, 6, 22),
			pygame.Rect(x + 26, y + 12, 6, 19),
			pygame.Rect(x + 31, y + 18, 6, 13),
		]
		for dedo in dedos:
			pygame.draw.rect(pantalla, color_mano, dedo, border_radius=3)
			pygame.draw.rect(pantalla, borde_mano, dedo, 1, border_radius=3)

		palma = pygame.Rect(x + 15, y + 23, 22, 16)
		pygame.draw.ellipse(pantalla, color_mano, palma)
		pygame.draw.ellipse(pantalla, borde_mano, palma, 1)
		pulgar = [(x + 17, y + 26), (x + 12, y + 22), (x + 9, y + 25), (x + 16, y + 35), (x + 21, y + 32)]
		pygame.draw.polygon(pantalla, color_mano, pulgar)
		pygame.draw.polygon(pantalla, borde_mano, pulgar, 1)

	def dibujar(self, pantalla, cantidad_semillas_zanahoria=0):
		casillas = self.obtener_rectangulos(pantalla.get_width(), pantalla.get_height())
		for indice, casilla in enumerate(casillas):
			x, y = casilla.topleft
			if indice == self.slot_seleccionado:
				self.dibujar_fondo_seleccionado(pantalla, casilla)
				pygame.draw.rect(pantalla, (112, 79, 29), casilla, 3)
			else:
				pygame.draw.rect(pantalla, (232, 232, 215), casilla)
				pygame.draw.rect(pantalla, (60, 65, 48), casilla, 2)

			if indice == self.SLOT_MANO:
				self.dibujar_mano(pantalla, x, y)
			elif indice == self.SLOT_SEMILLA_ZANAHORIA and cantidad_semillas_zanahoria > 0:
				icono = self.fuente_item.render("Za", True, (45, 55, 36))
				icono_rect = icono.get_rect(center=(casilla.centerx, casilla.centery - 4))
				pantalla.blit(icono, icono_rect)
				cantidad = self.fuente_cantidad.render(
					str(cantidad_semillas_zanahoria), True, (25, 25, 20)
				)
				cantidad_rect = cantidad.get_rect(
					bottomright=(casilla.right - 3, casilla.bottom - 2)
				)
				pantalla.blit(cantidad, cantidad_rect)
			elif indice == self.SLOT_REGADERA:
				color_regadera = (83, 145, 153)
				borde_regadera = (45, 75, 78)
				cuerpo = pygame.Rect(x + 15, y + 20, 18, 15)
				pygame.draw.rect(pantalla, color_regadera, cuerpo)
				pygame.draw.rect(pantalla, borde_regadera, cuerpo, 2)
				pygame.draw.lines(
					pantalla,
					borde_regadera,
					False,
					[(x + 15, y + 22), (x + 10, y + 22), (x + 10, y + 32), (x + 15, y + 32)],
					2,
				)
				pico = [(x + 31, y + 23), (x + 39, y + 16), (x + 42, y + 18), (x + 33, y + 28)]
				pygame.draw.polygon(pantalla, color_regadera, pico)
				pygame.draw.polygon(pantalla, borde_regadera, pico, 2)
				pygame.draw.circle(pantalla, borde_regadera, (x + 41, y + 16), 3, 2)
