import pygame

from engine.audio import establecer_volumen_efectos


class OptionsMenu:
	OPCIONES_PRINCIPALES = ("Opciones", "Salir del juego")
	PAGINAS_OPCIONES = ("Sonido", "Controles")
	OPCIONES_SALIDA = ("Sí, salir", "No, volver")
	CONTROLES = (
		"W, A, S, D: mover al personaje",
		"Shift: alternar entre caminar y correr",
		"E: interactuar con objetos y edificios",
		"I: mostrar u ocultar el inventario",
		"G: abrir el árbol de habilidades",
		"R: mostrar u ocultar el radar (si está desbloqueado)",
		"Clic izquierdo: seleccionar objetos, parcelas y opciones",
		"Clic en una casilla: seleccionar un objeto del inventario",
		"ESC: abrir o cerrar este menú",
	)

	def __init__(self):
		self.abierto = False
		self.pagina = "principal"
		self.seleccion = 0
		self.volumen_musica = 10
		self.volumen_efectos = 10
		self.solicitar_cierre = False
		self.fuente_titulo = pygame.font.Font(None, 42)
		self.fuente = pygame.font.Font(None, 30)
		self.fuente_pequena = pygame.font.Font(None, 24)
		self._aplicar_volumen()

	def _aplicar_volumen(self):
		pygame.mixer.music.set_volume(self.volumen_musica / 10)
		establecer_volumen_efectos(self.volumen_efectos / 10)

	def _rectangulo_panel(self, pantalla):
		if isinstance(pantalla, pygame.Rect):
			ancho_pantalla, alto_pantalla = pantalla.size
			centro = pantalla.center
		else:
			ancho_pantalla, alto_pantalla = pantalla.get_size()
			centro = pantalla.get_rect().center
		panel = pygame.Rect(
			0,
			0,
			min(560, ancho_pantalla - 32),
			min(470, alto_pantalla - 32),
		)
		panel.center = centro
		return panel

	def _rectangulos_principales(self, panel):
		ancho = min(300, panel.width - 48)
		return [
			pygame.Rect(
				panel.centerx - ancho // 2,
				panel.centery - 25 + indice * 64,
				ancho,
				48,
			)
			for indice in range(len(self.OPCIONES_PRINCIPALES))
		]

	def _rectangulos_confirmacion_salida(self, panel):
		ancho = min(300, panel.width - 48)
		return [
			pygame.Rect(
				panel.centerx - ancho // 2,
				panel.centery + 24 + indice * 58,
				ancho,
				42,
			)
			for indice in range(len(self.OPCIONES_SALIDA))
		]

	def _rectangulos_paginas(self, panel):
		ancho = min(300, panel.width - 48)
		return [
			pygame.Rect(
				panel.centerx - ancho // 2,
				panel.centery - 48 + indice * 64,
				ancho,
				48,
			)
			for indice in range(len(self.PAGINAS_OPCIONES))
		]

	def _rectangulos_volumen(self, panel):
		return [
			(
				pygame.Rect(panel.centerx - 76, panel.centery - 53 + i * 92, 40, 40),
				pygame.Rect(panel.centerx + 36, panel.centery - 53 + i * 92, 40, 40),
			)
			for i in range(2)
		]

	def _ajustar_volumen(self, indice, incremento):
		if indice == 0:
			self.volumen_musica = max(
				0, min(10, self.volumen_musica + incremento)
			)
		else:
			self.volumen_efectos = max(
				0, min(10, self.volumen_efectos + incremento)
			)
		self._aplicar_volumen()

	def procesar_eventos(self, eventos, limites_pantalla):
		for evento in eventos:
			if evento.type == pygame.KEYDOWN:
				if evento.key == pygame.K_ESCAPE:
					if self.pagina != "principal":
						self.pagina = "principal"
						self.seleccion = 0
					else:
						self.abierto = False
					return True

				if evento.key in (pygame.K_UP, pygame.K_w):
					self.seleccion = max(0, self.seleccion - 1)
					return True
				if evento.key in (pygame.K_DOWN, pygame.K_s):
					limite = (
						1
						if self.pagina in (
							"principal",
							"opciones",
							"sonido",
							"confirmar_salir",
						)
						else 0
					)
					self.seleccion = min(limite, self.seleccion + 1)
					return True
				if evento.key in (pygame.K_LEFT, pygame.K_RIGHT):
					if self.pagina == "sonido":
						self._ajustar_volumen(
							self.seleccion,
							1 if evento.key == pygame.K_RIGHT else -1,
						)
					return True
				if evento.key in (pygame.K_RETURN, pygame.K_SPACE):
					self._activar_seleccion()
					return True

			if (
				evento.type == pygame.MOUSEBUTTONDOWN
				and evento.button == 1
			):
				if self.pagina == "principal":
					for indice, rectangulo in enumerate(
						self._rectangulos_principales(limites_pantalla)
					):
						if rectangulo.collidepoint(evento.pos):
							self.seleccion = indice
							self._activar_seleccion()
							return True
				elif self.pagina == "confirmar_salir":
					for indice, rectangulo in enumerate(
						self._rectangulos_confirmacion_salida(
							self._rectangulo_panel(limites_pantalla)
						)
					):
						if rectangulo.collidepoint(evento.pos):
							self.seleccion = indice
							self._activar_seleccion()
							return True
				elif self.pagina == "opciones":
					for indice, rectangulo in enumerate(
						self._rectangulos_paginas(limites_pantalla)
					):
						if rectangulo.collidepoint(evento.pos):
							self.seleccion = indice
							self._activar_seleccion()
							return True
				elif self.pagina == "sonido":
					for indice, rectangulos in enumerate(
						self._rectangulos_volumen(limites_pantalla)
					):
						if rectangulos[0].union(rectangulos[1]).inflate(
							0, 20
						).collidepoint(evento.pos):
							self.seleccion = indice
							if rectangulos[0].collidepoint(evento.pos):
								self._ajustar_volumen(indice, -1)
							elif rectangulos[1].collidepoint(evento.pos):
								self._ajustar_volumen(indice, 1)
							return True
				panel = self._rectangulo_panel(limites_pantalla)
				if self._boton_volver(panel).collidepoint(evento.pos):
					self.pagina = (
						"principal"
						if self.pagina == "opciones"
						else "opciones"
					)
					self.seleccion = 0
					return True

			if evento.type == pygame.MOUSEMOTION:
				if self.pagina in ("principal", "confirmar_salir"):
					rectangulos = self._rectangulos_principales(
						limites_pantalla
					)
					if self.pagina == "confirmar_salir":
						rectangulos = self._rectangulos_confirmacion_salida(
							self._rectangulo_panel(limites_pantalla)
						)
					self._actualizar_hover(
						evento.pos, rectangulos
					)
				elif self.pagina == "opciones":
					self._actualizar_hover(
						evento.pos,
						self._rectangulos_paginas(limites_pantalla),
					)
				elif self.pagina == "sonido":
					for indice, rectangulos in enumerate(
						self._rectangulos_volumen(limites_pantalla)
					):
						if rectangulos[0].union(
							rectangulos[1]
						).inflate(0, 20).collidepoint(evento.pos):
							self.seleccion = indice
							break
		return True

	def _actualizar_hover(self, posicion, rectangulos):
		for indice, rectangulo in enumerate(rectangulos):
			if rectangulo.collidepoint(posicion):
				self.seleccion = indice
				return

	def _activar_seleccion(self):
		if self.pagina == "principal":
			if self.seleccion == 0:
				self.pagina = "opciones"
				self.seleccion = 0
			else:
				self.pagina = "confirmar_salir"
				self.seleccion = 0
		elif self.pagina == "confirmar_salir":
			if self.seleccion == 0:
				self.solicitar_cierre = True
			else:
				self.pagina = "principal"
				self.seleccion = 0
		elif self.pagina == "opciones":
			self.pagina = (
				"sonido" if self.seleccion == 0 else "controles"
			)
			self.seleccion = 0

	def _boton_volver(self, panel):
		return pygame.Rect(panel.left + 20, panel.bottom - 58, 130, 40)

	def dibujar(self, pantalla, nombre_mascota=""):
		if not self.abierto:
			return

		sombra = pygame.Surface(pantalla.get_size(), pygame.SRCALPHA)
		sombra.fill((0, 0, 0, 170))
		pantalla.blit(sombra, (0, 0))
		panel = self._rectangulo_panel(pantalla)

		titulo = (
			"¿Salir del juego?"
			if self.pagina == "confirmar_salir"
			else {
				"principal": "Pausa",
				"opciones": "Opciones",
				"sonido": "Sonido",
				"controles": "Controles",
			}[self.pagina]
		)
		texto_titulo = self.fuente_titulo.render(
			titulo, True, (255, 255, 255)
		)
		pantalla.blit(
			texto_titulo,
			texto_titulo.get_rect(midtop=(panel.centerx, panel.top + 24)),
		)

		if self.pagina == "principal":
			self._dibujar_botones(
				pantalla,
				self.OPCIONES_PRINCIPALES,
				self._rectangulos_principales(panel),
			)
		elif self.pagina == "confirmar_salir":
			nombre = (nombre_mascota or "").strip() or "Tu mascota"
			mensaje = (
				f"{nombre} te está esperando ansioso a que regreses "
				"a la Tierra."
			)
			self._dibujar_texto_en_lineas(
				pantalla,
				mensaje,
				panel.centerx,
				panel.top + 105,
				panel.width - 56,
			)
			self._dibujar_botones(
				pantalla,
				self.OPCIONES_SALIDA,
				self._rectangulos_confirmacion_salida(panel),
			)
		elif self.pagina == "opciones":
			self._dibujar_botones(
				pantalla,
				self.PAGINAS_OPCIONES,
				self._rectangulos_paginas(panel),
			)
			self._dibujar_boton_volver(pantalla, panel)
		elif self.pagina == "sonido":
			self._dibujar_volumen(pantalla, panel)
			self._dibujar_boton_volver(pantalla, panel)
		else:
			self._dibujar_controles(pantalla, panel)
			self._dibujar_boton_volver(pantalla, panel)

	def _dibujar_botones(self, pantalla, etiquetas, rectangulos):
		for indice, (etiqueta, rectangulo) in enumerate(
			zip(etiquetas, rectangulos)
		):
			texto = self.fuente.render(etiqueta, True, (255, 255, 255))
			texto_rect = texto.get_rect(center=rectangulo.center)
			pantalla.blit(texto, texto_rect)
			if indice == self.seleccion:
				pygame.draw.line(
					pantalla,
					(255, 255, 255),
					(texto_rect.left, texto_rect.bottom + 3),
					(texto_rect.right, texto_rect.bottom + 3),
					1,
				)

	def _dibujar_volumen(self, pantalla, panel):
		rectangulos = self._rectangulos_volumen(panel)
		etiquetas = (
			("Música", self.volumen_musica),
			("Efectos de sonido", self.volumen_efectos),
		)
		for indice, (rectangulos_flecha, (etiqueta, nivel)) in enumerate(
			zip(rectangulos, etiquetas)
		):
			flecha_izquierda, flecha_derecha = rectangulos_flecha
			texto = self.fuente_pequena.render(
				etiqueta, True, (255, 255, 255)
			)
			pantalla.blit(
				texto,
				texto.get_rect(
					midleft=(panel.left + 24, flecha_izquierda.centery)
				),
			)
			self._dibujar_flecha(
				pantalla,
				flecha_izquierda,
				"‹",
				indice == self.seleccion,
			)
			self._dibujar_flecha(
				pantalla,
				flecha_derecha,
				"›",
				indice == self.seleccion,
			)
			valor = self.fuente_pequena.render(
				f"{nivel}/10", True, (255, 255, 255)
			)
			pantalla.blit(
				valor,
				valor.get_rect(
					center=(
						(flecha_izquierda.centerx + flecha_derecha.centerx) // 2,
						flecha_izquierda.centery,
					)
				),
			)

	def _dibujar_flecha(self, pantalla, rectangulo, texto, seleccionada):
		superficie = self.fuente.render(texto, True, (255, 255, 255))
		rect_texto = superficie.get_rect(center=rectangulo.center)
		pantalla.blit(superficie, rect_texto)
		if seleccionada:
			pygame.draw.line(
				pantalla,
				(255, 255, 255),
				(rect_texto.left, rect_texto.bottom + 2),
				(rect_texto.right, rect_texto.bottom + 2),
				1,
			)

	def _dibujar_controles(self, pantalla, panel):
		espacio = 32
		inicio_y = panel.top + 94
		for indice, control in enumerate(self.CONTROLES):
			texto = self.fuente_pequena.render(
				control, True, (255, 255, 255)
			)
			pantalla.blit(
				texto,
				texto.get_rect(
					midtop=(panel.centerx, inicio_y + indice * espacio)
				),
			)

	def _dibujar_texto_en_lineas(
		self, pantalla, texto, centro_x, inicio_y, ancho_maximo
	):
		lineas = []
		linea = ""
		for palabra in texto.split():
			candidata = f"{linea} {palabra}".strip()
			if (
				linea
				and self.fuente_pequena.size(candidata)[0] > ancho_maximo
			):
				lineas.append(linea)
				linea = palabra
			else:
				linea = candidata
		if linea:
			lineas.append(linea)

		for indice, texto_linea in enumerate(lineas):
			superficie = self.fuente_pequena.render(
				texto_linea, True, (255, 255, 255)
			)
			pantalla.blit(
				superficie,
				superficie.get_rect(
					midtop=(
						centro_x,
						inicio_y + indice * self.fuente_pequena.get_linesize(),
					)
				),
			)

	def _dibujar_boton_volver(self, pantalla, panel):
		rectangulo = self._boton_volver(panel)
		texto = self.fuente_pequena.render(
			"Volver", True, (255, 255, 255)
		)
		texto_rect = texto.get_rect(center=rectangulo.center)
		pantalla.blit(texto, texto_rect)
		if self.pagina in ("opciones", "controles", "sonido"):
			pygame.draw.line(
				pantalla,
				(255, 255, 255),
				(texto_rect.left, texto_rect.bottom + 3),
				(texto_rect.right, texto_rect.bottom + 3),
				1,
			)