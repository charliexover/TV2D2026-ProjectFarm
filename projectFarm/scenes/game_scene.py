import pygame

from ..entities import Jugador
from ..farm import Parcela


class GameScene:
	def __init__(self):
		self.jugador = Jugador()
		self.parcelas = [
			Parcela(300 + columna * 56, 250 + fila * 56)
			for fila in range(3)
			for columna in range(3)
		]
		self.parcela_seleccionada = None
		self.semilla = 1
		self.dia_actual = 0
		self.tecla_n_presionada = False
		self.tecla_e_presionada = False
		self.fuente = pygame.font.Font(None, 28)

	def obtener_parcela_jugador(self, jugador):
		return next(
			(
				parcela
				for parcela in self.parcelas
				if jugador.rectangulo.colliderect(parcela.rectangulo)
			),
			None,
		)

	def update(self, teclas, limites_pantalla):
		self.jugador.actualizar(teclas)
		self.jugador.rectangulo.clamp_ip(limites_pantalla)
		n_presionada = teclas[pygame.K_n]
		if n_presionada and not self.tecla_n_presionada:
			for parcela in self.parcelas:
				parcela.avanzar_dia(self.dia_actual)
			self.dia_actual += 1
		self.tecla_n_presionada = n_presionada

		self.parcela_seleccionada = self.obtener_parcela_jugador(self.jugador)

		e_presionada = teclas[pygame.K_e]
		if e_presionada and not self.tecla_e_presionada:
			if self.parcela_seleccionada is not None:
				if self.parcela_seleccionada.planta is None and self.semilla > 0:
					self.parcela_seleccionada.plantar("zanahoria")
					self.semilla -= 1
				elif self.parcela_seleccionada.obtener_etapa() == "cosechable":
					self.parcela_seleccionada.cosechar()
				elif self.parcela_seleccionada.planta is not None:
					self.parcela_seleccionada.regar(self.dia_actual)
		self.tecla_e_presionada = e_presionada

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
		texto_etapa = self.fuente.render(f"Etapa = {etapa}", True, (30, 30, 30))
		pantalla.blit(texto_etapa, (10, 38))
		texto_semilla = self.fuente.render(f"Semillas = {self.semilla}", True, (30, 30, 30))
		pantalla.blit(texto_semilla, (10, 66))
		if self.parcela_seleccionada is not None and self.parcela_seleccionada.planta is not None:
			regada = self.parcela_seleccionada.dia_regado == self.dia_actual
			texto_riego = self.fuente.render(f"Regada hoy = {'si' if regada else 'no'}", True, (30, 30, 30))
			pantalla.blit(texto_riego, (10, 94))
