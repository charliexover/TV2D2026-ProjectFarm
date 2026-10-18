
import os

import pygame

from engine.audio import reproducir_sonido_interaccion
from engine.spritesheet import Spritesheet
from engine.ui import InterfazEstado
from projectFarm.entities import Jugador
from projectFarm.farm import CULTIVOS


DIALOGO_RAM = {
    "inicio": {
        "texto": "Bienvenido a tu primer dia kzzzt-- "
        "y esperemos no el ultimo kzzzt-- "
        "en la colonia Marciana. Soy un robot "
        "autonomo de mantenimiento(RAM) preparado "
        "para ayudarte a completar la "
        "construccion de la colonia.",
        "opciones": [
            ("Te llamaré Pepe  ", "charla"),
            ("Cerrar diálogo", None),
        ],
    },
    "charla": {
        "texto": "Esto no es un videojuego terricola donde le pones nombre a los npcs kzzzt-- menos un nombre tan feo kzzzt-- "
        "para empezar el dia de hoy te recomiendo que vayas a la granja y plantes tus primeras semillas de zanahoria.",
        "opciones": [
            ("Volver a saludar", "inicio"),
            ("Cerrar diálogo", None),
        ],
    }
}


class HomeScene:
    def __init__(self, game_state, inventario, al_salir_casa, al_avanzar_dia):
        self.name = "Home Scene"
        self.game_state = game_state
        self.interfaz_estado = InterfazEstado()
        self.jugador = Jugador()
        self.primera_entrada = True
        self.primera_visita = True
        self.al_salir_casa = al_salir_casa
        self.al_avanzar_dia = al_avanzar_dia
        self.tamano_cama = (96, 48)
        self.tamano_salida = (70, 50)
        self.tamano_pc = (50, 70)
        self.cuadrados = [
            pygame.Rect(195, 160, 10, 340),
            pygame.Rect(130, 165, 550, 10),
            pygame.Rect(595, 160, 10, 340),
            pygame.Rect(200, 495, 95, 10),
            pygame.Rect(360, 495, 300, 10),
        ]
        self.colores_cuadrados = [(255, 120, 120), (120, 200, 255), (120, 255, 170), (255, 210, 120), (255, 210, 120)]
        self.fuente = pygame.font.Font(None, 28)
        self.inventario = inventario
        self.fondo = self._cargar_fondo()
        ruta_ram = os.path.join(
            os.path.dirname(__file__), "..", "utils", "RamSprite.json"
        )
        spritesheet_ram = Spritesheet(ruta_ram)
        self.sprites_ram = [
            pygame.transform.scale(sprite, (48, 54))
            for sprite in spritesheet_ram.get_animation_frames("default")
        ]
        self.npc_rectangulo = pygame.Rect(250, 210, 48, 48)
        self.nodo_dialogo_ram = None
        self.opcion_dialogo_ram = 0
        self.sprite_ram_actual = 0
        self.proximo_cambio_sprite_ram = pygame.time.get_ticks() + 350
        self.mensaje_guardado = None
        self.mensaje_guardado_hasta = 0
        
    def _cargar_fondo(self):
        ruta_fondo = os.path.join(
            os.path.dirname(__file__), "..", "assets", "spritesheetInterior1.png"
        )
        try:
            fondo = pygame.image.load(ruta_fondo).convert()
            return pygame.transform.scale(
                fondo,
                (fondo.get_width() * 3, fondo.get_height() * 3),
            )
        except (FileNotFoundError, pygame.error):
            return None

    def obtener_cama(self, limites_pantalla):
        cama = pygame.Rect(0, 0, self.tamano_cama[0], self.tamano_cama[1])
        cama.center = (545,230)
        return cama

    def obtener_area_interaccion_cama(self, limites_pantalla):
        return self.obtener_cama(limites_pantalla).inflate(20, 20)

    def obtener_salida(self, limites_pantalla):
        salida = pygame.Rect(0, 0, *self.tamano_salida)
        salida.center = (330, 520)
        return salida

    def obtener_posicion_entrada(self, limites_pantalla):
        salida = self.obtener_salida(limites_pantalla)
        posicion = self.jugador.rectangulo.copy()
        posicion.midbottom = (salida.centerx, salida.top - 8)
        return posicion

    def obtener_pc(self, limites_pantalla):
        pc = pygame.Rect(0, 0, *self.tamano_pc)
        pc.center = (425, 150)
        return pc

    def envolver_texto_dialogo(self, texto, ancho_maximo):
        lineas = []
        for parrafo in texto.splitlines() or [""]:
            palabras = parrafo.split()
            linea = ""
            for palabra in palabras:
                candidata = f"{linea} {palabra}".strip()
                if linea and self.fuente.size(candidata)[0] > ancho_maximo:
                    lineas.append(linea)
                    linea = palabra
                else:
                    linea = candidata
            lineas.append(linea)
        return lineas

    def obtener_cuadro_dialogo(self, limites_pantalla, texto):
        ancho = limites_pantalla.width - 200
        lineas = self.envolver_texto_dialogo(texto, ancho - 40)
        alto = max(80, len(lineas) * self.fuente.get_linesize() + 24)
        cuadro = pygame.Rect(
            100, limites_pantalla.height - 80 - alto, ancho, alto
        )
        return cuadro, lineas

    def obtener_rectangulos_opciones_dialogo(self, cuadro_dialogo, cantidad):
        alto_opciones = max(42, 30 * cantidad + 16)
        cuadro_opciones = pygame.Rect(
            cuadro_dialogo.right - 230,
            cuadro_dialogo.top - alto_opciones - 8,
            230,
            alto_opciones,
        )
        rectangulos_opciones = [
            pygame.Rect(
                cuadro_opciones.left + 2,
                cuadro_opciones.top + 2 + indice * 30,
                cuadro_opciones.width - 4,
                30,
            )
            for indice in range(cantidad)
        ]
        return cuadro_opciones, rectangulos_opciones

    def vender_zanahorias(self):
        creditos = 0
        for cultivo in CULTIVOS.values():
            atributo_cosecha = cultivo["cosecha"]
            cantidad = getattr(self.game_state, atributo_cosecha)
            creditos += cantidad * cultivo["precio_venta"]
            setattr(self.game_state, atributo_cosecha, 0)
        self.game_state.creditos += creditos

    def update(self, teclas, limites_pantalla, eventos=()):
        ahora = pygame.time.get_ticks()
        if ahora >= self.proximo_cambio_sprite_ram:
            self.sprite_ram_actual = (
                self.sprite_ram_actual + 1
            ) % len(self.sprites_ram)
            self.proximo_cambio_sprite_ram = ahora + 350

        if self.primera_entrada:
            if self.primera_visita:
                self.jugador.rectangulo.center = (
                    limites_pantalla.centerx,
                    limites_pantalla.centery + 30,
                )
                self.primera_visita = False
            else:
                self.jugador.rectangulo = self.obtener_posicion_entrada(
                    limites_pantalla
                )
            self.primera_entrada = False
        if self.nodo_dialogo_ram is None:
            rect_previo = self.jugador.rectangulo.copy()
            self.jugador.actualizar(teclas)
            self.jugador.rectangulo.clamp_ip(limites_pantalla)
            cama = self.obtener_cama(limites_pantalla)
            for cuadrado in [*self.cuadrados, cama, self.npc_rectangulo]:
                if self.jugador.rectangulo.colliderect(cuadrado):
                    self.jugador.rectangulo = rect_previo
                    break
        salida = self.obtener_salida(limites_pantalla)
        if (
            self.nodo_dialogo_ram is None
            and self.jugador.rectangulo.colliderect(salida)
        ):
            self.primera_entrada = True
            self.al_salir_casa()
            return
        area_interaccion_ram = self.npc_rectangulo.inflate(40, 40)
        if (
            self.nodo_dialogo_ram is not None
            and not self.jugador.rectangulo.colliderect(area_interaccion_ram)
        ):
            self.nodo_dialogo_ram = None
        area_interaccion_cama = self.obtener_area_interaccion_cama(
            limites_pantalla
        )
        for evento in eventos:
            if (
                self.nodo_dialogo_ram is not None
                and evento.type == pygame.MOUSEBUTTONDOWN
                and evento.button == 1
            ):
                nodo_dialogo = DIALOGO_RAM[self.nodo_dialogo_ram]
                opciones = nodo_dialogo["opciones"]
                cuadro_dialogo, _ = self.obtener_cuadro_dialogo(
                    limites_pantalla, nodo_dialogo["texto"]
                )
                _, rectangulos_opciones = self.obtener_rectangulos_opciones_dialogo(
                    cuadro_dialogo, len(opciones)
                )
                for indice, rectangulo_opcion in enumerate(rectangulos_opciones):
                    if rectangulo_opcion.collidepoint(evento.pos):
                        _, siguiente_nodo = opciones[indice]
                        self.nodo_dialogo_ram = siguiente_nodo
                        self.opcion_dialogo_ram = 0
                        break
                continue

            if evento.type != pygame.KEYDOWN:
                continue

            if self.nodo_dialogo_ram is not None:
                if evento.key == pygame.K_ESCAPE:
                    self.nodo_dialogo_ram = None
                continue

            if evento.key != pygame.K_e:
                continue
            if self.jugador.rectangulo.colliderect(area_interaccion_ram):
                reproducir_sonido_interaccion()
                self.nodo_dialogo_ram = "inicio"
                self.opcion_dialogo_ram = 0
                self.jugador.sprite = self.jugador.sprites["Idle"]
                self.jugador.moviendose = False
            elif self.jugador.rectangulo.colliderect(area_interaccion_cama):
                reproducir_sonido_interaccion()
                self.mensaje_guardado = self.al_avanzar_dia()
                self.mensaje_guardado_hasta = pygame.time.get_ticks() + 5000
            elif self.jugador.rectangulo.colliderect(
                self.obtener_pc(limites_pantalla)
            ):
                reproducir_sonido_interaccion()
                self.vender_zanahorias()

    def draw(self, pantalla):
        pantalla.fill((0, 0, 0))
        limites_pantalla = pantalla.get_rect()
        if self.fondo is not None:
            pantalla.blit(self.fondo, self.fondo.get_rect(center=limites_pantalla.center))
        else:
            pantalla.fill((99, 60, 58))

        #for i, cuadrado in enumerate(self.cuadrados):
            #pygame.draw.rect(pantalla, self.colores_cuadrados[i], cuadrado)
            #pygame.draw.rect(pantalla, (30, 30, 30), cuadrado, 2)

        self.interfaz_estado.dibujar(pantalla, self.game_state)
        
        salida = self.obtener_salida(limites_pantalla)
        #pygame.draw.rect(pantalla, (120, 255, 120), salida)
        pc = self.obtener_pc(limites_pantalla)
        #pygame.draw.rect(pantalla, (95, 125, 135), pc)
        #pygame.draw.rect(pantalla, (60, 45, 30), pc, 3)

        sprite_ram = self.sprites_ram[self.sprite_ram_actual]
        pantalla.blit(
            sprite_ram,
            sprite_ram.get_rect(center=self.npc_rectangulo.center),
        )
        self.jugador.dibujar(pantalla)
        if self.nodo_dialogo_ram is not None:
            nodo_dialogo = DIALOGO_RAM[self.nodo_dialogo_ram]
            cuadro_dialogo, lineas_dialogo = self.obtener_cuadro_dialogo(
                limites_pantalla, nodo_dialogo["texto"]
            )
            pygame.draw.rect(pantalla, (0, 0, 0), cuadro_dialogo)
            pygame.draw.rect(pantalla, (255, 255, 255), cuadro_dialogo, 2)
            for indice, linea in enumerate(lineas_dialogo):
                texto_dialogo = self.fuente.render(linea, True, (255, 255, 255))
                pantalla.blit(
                    texto_dialogo,
                    (
                        cuadro_dialogo.left + 20,
                        cuadro_dialogo.top + 12
                        + indice * self.fuente.get_linesize(),
                    ),
                )
            opciones = nodo_dialogo["opciones"]
            if opciones:
                cuadro_opciones, rectangulos_opciones = (
                    self.obtener_rectangulos_opciones_dialogo(
                        cuadro_dialogo, len(opciones)
                    )
                )
                pygame.draw.rect(pantalla, (0, 0, 0), cuadro_opciones)
                pygame.draw.rect(pantalla, (255, 255, 255), cuadro_opciones, 2)
                for indice, (texto_opcion, _) in enumerate(opciones):
                    superficie_opcion = self.fuente.render(
                        texto_opcion,
                        True,
                        (255, 255, 255),
                    )
                    fila_opcion = rectangulos_opciones[indice]
                    if fila_opcion.collidepoint(pygame.mouse.get_pos()):
                        pygame.draw.rect(
                            pantalla, (55, 55, 55), fila_opcion
                        )
                    pantalla.blit(
                        superficie_opcion,
                        (
                            fila_opcion.left + 8,
                            fila_opcion.top
                            + (fila_opcion.height - superficie_opcion.get_height())
                            // 2,
                        ),
                    )
        elif self.jugador.rectangulo.colliderect(
            self.npc_rectangulo.inflate(40, 40)
        ):
            indicacion = self.fuente.render(
                "E: hablar con Ram", True, (255, 255, 255)
            )
            pantalla.blit(
                indicacion,
                indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)),
            )
        elif self.jugador.rectangulo.colliderect(
            self.obtener_area_interaccion_cama(limites_pantalla)
        ):
            indicacion = self.fuente.render("E: avanzar dia", True, (255, 255, 255))
            pantalla.blit(indicacion, indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)))
        elif self.jugador.rectangulo.colliderect(salida):
            indicacion = self.fuente.render("Salida automatica", True, (255, 255, 255))
            pantalla.blit(indicacion, indicacion.get_rect(midtop=(pantalla.get_width() // 2, 20)))
        elif self.jugador.rectangulo.colliderect(pc):
            indicacion = self.fuente.render(
                "E: vender cosechas (2 creditos c/u)",
                True,
                (255, 255, 255),
            )
            pantalla.blit(indicacion, indicacion.get_rect(midtop=(pantalla.get_width() // 2, 30)))
        self.inventario.dibujar(pantalla, self.game_state)
        if (
            self.mensaje_guardado is not None
            and pygame.time.get_ticks() < self.mensaje_guardado_hasta
        ):
            color = (
                (255, 180, 140)
                if "no se pudo guardar" in self.mensaje_guardado.lower()
                else (255, 255, 255)
            )
            mensaje = self.fuente.render(self.mensaje_guardado, True, color)
            pantalla.blit(
                mensaje,
                mensaje.get_rect(midtop=(pantalla.get_width() // 2, 52)),
            )