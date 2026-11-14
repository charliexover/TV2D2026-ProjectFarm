import pygame

from projectFarm.localization import translate


class TextRenderer:
    def __init__(self):
        self.textos_pendientes = []

    def comenzar_frame(self):
        self.textos_pendientes.clear()

    def dibujar_texto(
        self,
        fuente,
        texto,
        antialias,
        color,
        posicion,
        ancla="topleft",
        alpha=255,
    ):
        self.textos_pendientes.append(
            {
                "fuente": fuente,
                "texto": texto,
                "antialias": antialias,
                "color": color,
                "posicion": posicion,
                "ancla": ancla,
                "alpha": alpha,
            }
        )

    def dibujar_pendientes(self, ventana, escala, desplazamiento):
        for datos in self.textos_pendientes:
            fuente = datos["fuente"]
            texto = datos["texto"]

            if hasattr(fuente, "render_scaled"):
                superficie = fuente.render_scaled(
                    texto,
                    escala,
                    datos["antialias"],
                    datos["color"],
                )
            else:
                superficie = fuente.render(
                    translate(texto),
                    datos["antialias"],
                    datos["color"],
                )
                tamano = (
                    max(1, round(superficie.get_width() * escala)),
                    max(1, round(superficie.get_height() * escala)),
                )
                superficie = pygame.transform.smoothscale(
                    superficie,
                    tamano,
                )
            superficie.set_alpha(datos["alpha"])
            x = desplazamiento[0] + round(datos["posicion"][0] * escala)
            y = desplazamiento[1] + round(datos["posicion"][1] * escala)

            rect = superficie.get_rect()
            setattr(rect, datos["ancla"], (x, y))

            ventana.blit(superficie, rect)