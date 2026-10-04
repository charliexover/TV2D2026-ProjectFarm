import pygame

from engine.ui import Inventario
from ..entities import Jugador
from ..farm import CULTIVOS, Parcela


class GameScene:
	def __init__(self):
		self.jugador = Jugador()
		self.parcelas = [
			Parcela(300 + columna * 56, 250 + fila * 56)
			for fila in range(3)
			for columna in range(3)
		]
		self.parcela_seleccionada = None
		self.semilla = 9
		self.dia_actual = 0
		self.zanahorias_cosechadas = 0
		self.resistencia = 100
		self.tecla_n_presionada = False
		self.fuente = pygame.font.Font(None, 28)
		self.inventario = Inventario()

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

	def update(self, teclas, limites_pantalla, eventos=()):
		self.jugador.actualizar(teclas)
		self.jugador.rectangulo.clamp_ip(limites_pantalla)
		n_presionada = teclas[pygame.K_n]
		if n_presionada and not self.tecla_n_presionada:
			for parcela in self.parcelas:
				parcela.avanzar_dia(self.dia_actual)
			self.dia_actual += 1
			self.resistencia = 100
		self.tecla_n_presionada = n_presionada

		self.parcela_seleccionada = self.obtener_parcela_jugador(self.jugador)

		for evento in eventos:
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

			if parcela_clickeada.obtener_etapa() == "cosechable":
				if self.inventario.slot_seleccionado == Inventario.SLOT_MANO:
					parcela_clickeada.cosechar()
					self.zanahorias_cosechadas += 1
					self.resistencia -= 15
			elif self.inventario.slot_seleccionado == Inventario.SLOT_SEMILLA_ZANAHORIA:
				if parcela_clickeada.planta is None and self.semilla > 0:
					parcela_clickeada.plantar(1)
					self.semilla -= 1
					self.resistencia -= 10
			elif self.inventario.slot_seleccionado == Inventario.SLOT_REGADERA:
				if (
					parcela_clickeada.planta is not None
					and parcela_clickeada.dia_regado != self.dia_actual
				):
					parcela_clickeada.regar(self.dia_actual)
					self.resistencia -= 5

	def draw(self, pantalla):
		pantalla.fill((245, 245, 230))
		for parcela in self.parcelas:
			parcela.dibujar(pantalla)
		self.jugador.dibujar(pantalla)
		texto_dia = self.fuente.render(f"Dia = {self.dia_actual}", True, (30, 30, 30))
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
		texto_semilla = self.fuente.render(f"Semillas = {self.semilla}", True, (30, 30, 30))
		pantalla.blit(texto_semilla, (10, 66))
		if self.parcela_seleccionada is not None and self.parcela_seleccionada.planta is not None:
			regada = self.parcela_seleccionada.dia_regado == self.dia_actual
			texto_riego = self.fuente.render(f"Regada hoy = {'si' if regada else 'no'}", True, (30, 30, 30))
			pantalla.blit(texto_riego, (10, 94))
		texto_zanahorias = self.fuente.render(f"Zanahorias cosechadas = {self.zanahorias_cosechadas}", True, (30, 30, 30))
		pantalla.blit(texto_zanahorias, (10, 122))
		texto_resistencia = self.fuente.render(f"Resistencia = {self.resistencia}", True, (30, 30, 30))
		pantalla.blit(texto_resistencia, (10, 150))
		self.inventario.dibujar(pantalla, self.semilla)
