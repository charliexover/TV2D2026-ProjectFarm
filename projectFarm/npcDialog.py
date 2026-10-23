import pygame


DIALOGOS_NPC = {
    "Ram": {
        "Bienvenida": {
            "texto": "Bienvenido a tu primer dia en la colonia Marciana." ,
            "opciones": [
                ("Siguiente  ", "Bienvenida1"),
            ],
        },
        "Bienvenida1": {
            "texto": "Soy un robot autonomo de mantenimiento(RAM) preparado "
            "para ayudarte a completar la construccion de la colonia.",
            "opciones": [
                ("Siguiente", "Bienvenida2"),
            ],
        },
        "Bienvenida2": {
            "texto": "Entre tus pertenencias ya se encuentran algunas semillas de zanahoria, "
            "te recomiendo que las plantes en la granja y las riegues para que crezcan. ",
            "opciones": [
                ("Siguiente  ", "Bienvenida3"),
            ],
        },
        "Bienvenida3": {
            "texto": "Saliendo de aqui a mano derecha bip bop--- izquierda si esto fuera un videojuego terricola con vista cenital bipbop---"
            "encontraras el modulo de plantacion y RECUERDA!!!",
            "opciones": [
                ("Siguiente", "Bienvenida4"),
            ],
        },
        "Bienvenida4": {
            "texto": "tienes un tanque de oxigeno limitado, asi que no te alejes demasiado de la colonia. ",
            "opciones": [
                ("Finalizar", None),
            ],
        }

    },
}


class DialogoNPC:
    def __init__(self, dialogos, fuente):
        self.dialogos = dialogos
        self.fuente = fuente
        self.nodo_actual = None

    @property
    def activo(self):
        return self.nodo_actual is not None

    def iniciar(self, nodo=None):
        self.nodo_actual = (
            nodo if nodo is not None else next(iter(self.dialogos))
        )

    def cerrar(self):
        self.nodo_actual = None

    def envolver_texto(self, texto, ancho_maximo):
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

    def _obtener_cuadro_dialogo(self, limites_pantalla, texto):
        ancho = limites_pantalla.width - 200
        lineas = self.envolver_texto(texto, ancho - 40)
        alto = max(80, len(lineas) * self.fuente.get_linesize() + 24)
        cuadro = pygame.Rect(
            100, limites_pantalla.height - 80 - alto, ancho, alto
        )
        return cuadro, lineas

    def _obtener_rectangulos_opciones(self, cuadro_dialogo, cantidad):
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

    def procesar_click(self, posicion, limites_pantalla):
        if not self.activo:
            return

        nodo_dialogo = self.dialogos[self.nodo_actual]
        opciones = nodo_dialogo["opciones"]
        cuadro_dialogo, _ = self._obtener_cuadro_dialogo(
            limites_pantalla, nodo_dialogo["texto"]
        )
        _, rectangulos_opciones = self._obtener_rectangulos_opciones(
            cuadro_dialogo, len(opciones)
        )
        for indice, rectangulo_opcion in enumerate(rectangulos_opciones):
            if rectangulo_opcion.collidepoint(posicion):
                _, self.nodo_actual = opciones[indice]
                break

    def dibujar(self, pantalla):
        if not self.activo:
            return

        limites_pantalla = pantalla.get_rect()
        nodo_dialogo = self.dialogos[self.nodo_actual]
        cuadro_dialogo, lineas_dialogo = self._obtener_cuadro_dialogo(
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
        if not opciones:
            return

        cuadro_opciones, rectangulos_opciones = (
            self._obtener_rectangulos_opciones(cuadro_dialogo, len(opciones))
        )
        pygame.draw.rect(pantalla, (0, 0, 0), cuadro_opciones)
        pygame.draw.rect(pantalla, (255, 255, 255), cuadro_opciones, 2)
        for indice, (texto_opcion, _) in enumerate(opciones):
            superficie_opcion = self.fuente.render(
                texto_opcion, True, (255, 255, 255)
            )
            fila_opcion = rectangulos_opciones[indice]
            if fila_opcion.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(pantalla, (55, 55, 55), fila_opcion)
            pantalla.blit(
                superficie_opcion,
                (
                    fila_opcion.left + 8,
                    fila_opcion.top
                    + (fila_opcion.height - superficie_opcion.get_height())
                    // 2,
                ),
            )
