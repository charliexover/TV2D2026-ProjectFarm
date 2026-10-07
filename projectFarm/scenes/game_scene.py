import pygame

from engine.ui import Inventario
from ..entities import Jugador
from ..farm import CULTIVOS, Parcela


class GameScene:
	def __init__(self, game_state, inventario, al_entrar_casa):
		self.game_state = game_state
		self.inventario = inventario
		self.jugador = Jugador()
		self.puerta = pygame.Rect(500, 400, 50, 70)
		self.al_entrar_casa = al_entrar_casa
		self.parcelas = [
			Parcela(300 + columna * 56, 250 + fila * 56)
			for fila in range(3)
			for columna in range(3)
		]
		self.parcela_seleccionada = None
		self.fuente = pygame.font.Font(None, 28)

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

	def avanzar_dia(self):
		for parcela in self.parcelas:
			parcela.avanzar_dia(self.game_state.dia_actual)
		self.game_state.dia_actual += 1
		self.game_state.resistencia = 100

	def update(self, teclas, limites_pantalla, eventos=()):
		self.jugador.actualizar(teclas)
		self.jugador.rectangulo.clamp_ip(limites_pantalla)

		self.parcela_seleccionada = self.obtener_parcela_jugador(self.jugador)

		for evento in eventos:
			if (
				evento.type == pygame.KEYDOWN
				and evento.key == pygame.K_e
				and self.jugador.rectangulo.colliderect(self.puerta)
			):
				self.al_entrar_casa()
				return
			if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
				continue
			if self.inventario.seleccionar_slot(
				evento.pos, limites_pantalla.width, limites_pantalla.height
			):
				continue
			parcela_clickeada = self.obtener_parcela_jugador(
				self.jugador, evento.pos
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
		pantalla.fill((99, 60, 58))
		for parcela in self.parcelas:
			parcela.dibujar(pantalla)
		pygame.draw.rect(pantalla, (125, 76, 42), self.puerta)
		pygame.draw.rect(pantalla, (60, 45, 30), self.puerta, 3)
		pygame.draw.circle(pantalla, (235, 196, 85), (self.puerta.right - 10, self.puerta.centery), 3)
		self.jugador.dibujar(pantalla)
		if self.jugador.rectangulo.colliderect(self.puerta):
			texto_puerta = self.fuente.render("E: entrar a la casa", True, (255, 255, 255))
			pantalla.blit(texto_puerta, (self.puerta.x - 35, self.puerta.y - 28))
		texto_dia = self.fuente.render(f"Dia = {self.game_state.dia_actual}", True, (30, 30, 30))
		pantalla.blit(texto_dia, (10, 10))
		etapa = (
			self.parcela_seleccionada.obtener_etapa()
			if self.parcela_seleccionada is not None
			else "-"
		)
		if self.parcela_seleccionada is not None and etapa == self.parcela_seleccionada.planta:
			etapa = CULTIVOS[etapa]["nombre"]
		texto_etapa = self.fuente.render(f"Etapa = {etapa}", True, (30, 30, 30))
		pantalla.blit(texto_etapa, (10, 38))
		texto_semilla = self.fuente.render(f"Semillas = {self.game_state.semilla_zanahoria}", True, (30, 30, 30))
		pantalla.blit(texto_semilla, (10, 66))
		if self.parcela_seleccionada is not None and self.parcela_seleccionada.planta is not None:
			regada = self.parcela_seleccionada.dia_regado == self.game_state.dia_actual
			texto_riego = self.fuente.render(f"Regada hoy = {'si' if regada else 'no'}", True, (30, 30, 30))
			pantalla.blit(texto_riego, (10, 94))
		texto_zanahorias = self.fuente.render(f"Zanahorias cosechadas = {self.game_state.zanahorias_cosechadas}", True, (30, 30, 30))
		pantalla.blit(texto_zanahorias, (10, 122))
		texto_resistencia = self.fuente.render(f"Resistencia = {self.game_state.resistencia}", True, (30, 30, 30))
		pantalla.blit(texto_resistencia, (10, 150))
		texto_creditos = self.fuente.render(f"Creditos = {self.game_state.creditos}", True, (30, 30, 30))
		pantalla.blit(texto_creditos, (10, 178))
		self.inventario.dibujar(pantalla, self.game_state.semilla_zanahoria)
