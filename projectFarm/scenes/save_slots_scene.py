import pygame

from projectFarm.save_slots import SaveSlots


class SaveSlotsScene:
    def __init__(self, save_slots, al_seleccionar, al_volver):
        self.save_slots = save_slots
        self.al_seleccionar = al_seleccionar
        self.al_volver = al_volver
        self.fuente_titulo = pygame.font.Font(None, 48)
        self.fuente = pygame.font.Font(None, 32)
        self.fuente_detalle = pygame.font.Font(None, 24)
        self.mensaje = None
        self.boton_volver = pygame.Rect(20, 20, 130, 42)

    def obtener_rectangulos(self, limites_pantalla):
        ancho = min(560, limites_pantalla.width - 40)
        alto = 82
        separacion = 14
        inicio_y = (limites_pantalla.height - (3 * alto + 2 * separacion)) // 2
        return [
            pygame.Rect(
                (limites_pantalla.width - ancho) // 2,
                inicio_y + slot * (alto + separacion),
                ancho,
                alto,
            )
            for slot in range(SaveSlots.CANTIDAD_PARTIDAS)
        ]

    def seleccionar(self, slot):
        try:
            self.al_seleccionar(slot)
        except (OSError, ValueError) as error:
            self.mensaje = f"No se pudo abrir la partida: {error}"

    def update(self, teclas, limites_pantalla, eventos=()):
        rectangulos = self.obtener_rectangulos(limites_pantalla)
        for evento in eventos:
            if evento.type == pygame.KEYDOWN:
                if pygame.K_1 <= evento.key <= pygame.K_3:
                    self.seleccionar(evento.key - pygame.K_1)
                    return
            if evento.type != pygame.MOUSEBUTTONDOWN or evento.button != 1:
                continue
            if self.boton_volver.collidepoint(evento.pos):
                self.al_volver()
                return
            for slot, rectangulo in enumerate(rectangulos):
                if rectangulo.collidepoint(evento.pos):
                    self.seleccionar(slot)
                    return

    def draw(self, pantalla):
        pantalla.fill((54, 48, 43))
        limites = pantalla.get_rect()
        pygame.draw.rect(pantalla, (35, 35, 35), self.boton_volver)
        pygame.draw.rect(pantalla, (220, 220, 220), self.boton_volver, 2)
        texto_volver = self.fuente_detalle.render("Volver", True, (255, 255, 255))
        pantalla.blit(
            texto_volver, texto_volver.get_rect(center=self.boton_volver.center)
        )
        titulo = self.fuente_titulo.render(
            "Selecciona una partida", True, (255, 255, 255)
        )
        pantalla.blit(titulo, titulo.get_rect(midtop=(limites.centerx, 45)))

        resumenes = self.save_slots.resumenes()
        for indice, (rectangulo, resumen) in enumerate(
            zip(self.obtener_rectangulos(limites), resumenes), start=1
        ):
            pygame.draw.rect(pantalla, (35, 35, 35), rectangulo)
            pygame.draw.rect(pantalla, (220, 220, 220), rectangulo, 2)
            titulo_slot = self.fuente.render(
                f"Partida {indice}", True, (255, 255, 255)
            )
            pantalla.blit(titulo_slot, (rectangulo.left + 16, rectangulo.top + 10))

            if resumen["estado"] == "vacia":
                detalle = "Espacio vacio - iniciar partida nueva"
            elif resumen["estado"] == "guardada":
                detalle = (
                    f"Continuar - Dia {resumen['dia']} | "
                    f"Creditos: {resumen['creditos']}"
                )
            else:
                detalle = "Archivo de guardado no disponible"
            superficie_detalle = self.fuente_detalle.render(
                detalle, True, (220, 220, 220)
            )
            pantalla.blit(
                superficie_detalle,
                (rectangulo.left + 16, rectangulo.top + 48),
            )

        indicacion = self.fuente_detalle.render(
            "Haz clic en un espacio o pulsa 1, 2 o 3.",
            True,
            (230, 230, 230),
        )
        pantalla.blit(
            indicacion,
            indicacion.get_rect(midbottom=(limites.centerx, limites.bottom - 24)),
        )
        if self.mensaje:
            mensaje = self.fuente_detalle.render(
                self.mensaje, True, (255, 170, 130)
            )
            pantalla.blit(
                mensaje,
                mensaje.get_rect(midbottom=(limites.centerx, limites.bottom - 52)),
            )
