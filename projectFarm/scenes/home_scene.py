
import pygame

from projectFarm.entities import Jugador


class HomeScene:
    def __init__(self, game_state, inventario, al_salir_casa, al_avanzar_dia):
        self.name = "Home Scene"
        self.game_state = game_state
        self.jugador = Jugador()
        self.al_salir_casa = al_salir_casa
        self.al_avanzar_dia = al_avanzar_dia
        self.tamano_cama = (50, 70)
        self.tamano_salida = (70, 50)
        self.tamano_maquina = (70, 70)
        self.fuente = pygame.font.Font(None, 28)
        self.inventario = inventario

    def obtener_cama(self, limites_pantalla):
        cama = pygame.Rect(0, 0, self.tamano_cama[0], self.tamano_cama[1])
        cama.center = limites_pantalla.center
        return cama

    def obtener_salida(self, limites_pantalla):
        salida = pygame.Rect(0, 0, *self.tamano_salida)
        salida.midbottom = (limites_pantalla.centerx, limites_pantalla.bottom - 70)
        return salida

    def obtener_maquina(self, limites_pantalla):
        maquina = pygame.Rect(0, 0, *self.tamano_maquina)
        maquina.topright = (limites_pantalla.right - 30, limites_pantalla.top + 100)
        return maquina

    def vender_zanahorias(self):
        zanahorias = self.game_state.zanahorias_cosechadas
        self.game_state.creditos += zanahorias * 2
        self.game_state.zanahorias_cosechadas = 0

    def update(self, teclas, limites_pantalla, eventos=()):
        self.jugador.actualizar(teclas)
        self.jugador.rectangulo.clamp_ip(limites_pantalla)
        for evento in eventos:
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_e:
                if self.jugador.rectangulo.colliderect(
                    self.obtener_cama(limites_pantalla)
                ):
                    self.al_avanzar_dia()
                elif self.jugador.rectangulo.colliderect(
                    self.obtener_salida(limites_pantalla)
                ):
                    self.al_salir_casa()
                    return
                elif self.jugador.rectangulo.colliderect(
                    self.obtener_maquina(limites_pantalla)
                ):
                    self.vender_zanahorias()

    def draw(self, pantalla):
        pantalla.fill((99, 60, 58))
        limites_pantalla = pantalla.get_rect()
        cama = self.obtener_cama(limites_pantalla)
        pygame.draw.rect(pantalla, (170, 120, 82), cama)
        pygame.draw.rect(pantalla, (60, 45, 30), cama, 3)

        texto_dia = self.fuente.render(f"Dia = {self.game_state.dia_actual}", True, (30, 30, 30))
        pantalla.blit(texto_dia, (10, 10))
        texto_zanahorias = self.fuente.render(f"Zanahorias cosechadas = {self.game_state.zanahorias_cosechadas}", True, (30, 30, 30))
        pantalla.blit(texto_zanahorias, (10, 122))
        texto_resistencia = self.fuente.render(f"Resistencia = {self.game_state.resistencia}", True, (30, 30, 30))
        pantalla.blit(texto_resistencia, (10, 150))
        texto_creditos = self.fuente.render(f"Creditos = {self.game_state.creditos}", True, (30, 30, 30))
        pantalla.blit(texto_creditos, (10, 178))
        
        etiqueta = self.fuente.render("Cama", True, (255, 255, 255))
        pantalla.blit(etiqueta, etiqueta.get_rect(center=cama.center))
        salida = self.obtener_salida(limites_pantalla)
        pygame.draw.rect(pantalla, (125, 76, 42), salida)
        pygame.draw.rect(pantalla, (60, 45, 30), salida, 3)
        etiqueta_salida = self.fuente.render("Salida", True, (255, 255, 255))
        pantalla.blit(etiqueta_salida, etiqueta_salida.get_rect(center=salida.center))

        maquina = self.obtener_maquina(limites_pantalla)
        pygame.draw.rect(pantalla, (95, 125, 135), maquina)
        pygame.draw.rect(pantalla, (60, 45, 30), maquina, 3)
        etiqueta_maquina = self.fuente.render("Maquina", True, (255, 255, 255))
        pantalla.blit(
            etiqueta_maquina,
            etiqueta_maquina.get_rect(center=maquina.center),
        )

        self.jugador.dibujar(pantalla)
        if self.jugador.rectangulo.colliderect(cama):
            indicacion = self.fuente.render("E: avanzar dia", True, (255, 255, 255))
            pantalla.blit(indicacion, indicacion.get_rect(midtop=(pantalla.get_width() // 2, 30)))
        elif self.jugador.rectangulo.colliderect(salida):
            indicacion = self.fuente.render("E: salir de la casa", True, (255, 255, 255))
            pantalla.blit(indicacion, indicacion.get_rect(midtop=(pantalla.get_width() // 2, 30)))
        elif self.jugador.rectangulo.colliderect(maquina):
            indicacion = self.fuente.render(
                "E: vender zanahorias (2 creditos c/u)",
                True,
                (255, 255, 255),
            )
            pantalla.blit(indicacion, indicacion.get_rect(midtop=(pantalla.get_width() // 2, 30)))
        self.inventario.dibujar(pantalla, self.game_state.semilla_zanahoria)