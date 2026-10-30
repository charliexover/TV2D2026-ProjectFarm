
CORREOS = [
    {
        "id": "bienvenida_colonia",
        "dia_llegada": 1,
        "remitente": "Agencia Espacial",
        "asunto": "Bienvenido a Marte, {jugador}",
        "mensaje": (
            "Bienvenido a tu nueva residencia en Marte, "
            "{jugador}.\n"
            "Como fue acordado, tu mision es terminar la construccion "
             "de la base marciana y todos los creditos que generes seran tuyos "
             "hasta un limite de 100mil creditos que equivalen a 500mil dolares."
             "Seguiremos en contacto para informarte de cualquier novedad."
        ),
    },
    {
        "id": "veterinario_mascota",
        "dia_llegada": 1,
        "remitente": "Veterinario Robert Emmil",
        "asunto": "Sobre {mascota}",
        "mensaje": (
            "Buenos días, {jugador}.\n"
            "Le recuerdo que {mascota} necesita un tratamiento urgente."
            "Su enfermedad esta avanzando rapido pero estimo que aun le quedan algunos meses de vida."
            "El tratamiento es costoso de unos 500 mil dolares.\n\n"
            "Espero noticias al respecto, saludos cordiales."
        ),
    },
    {
        "id": "tutorial1",
        "dia_llegada": 1,
        "remitente": "Agencia Espacial",
        "asunto": "Tutorial",
        "mensaje": (
            "Presiona E para interacturar con npcs y objetos.\n"
            "Presiona click izquierdo para usar lo que tengas equipado en tu barra de inventario.\n"
            "En el exterior presiona G para abrir el menu de mejoras. \n"
            "Parcelas al oeste, hay oxigeno limitado no alejarse mucho"
        ),
    },
    {
        "id": "dia_siguiente",
        "dia_llegada": 2,
        "remitente": "Agencia Espacial",
        "asunto": "Venta de cosechas",
        "mensaje": (
            "El precio de venta de las cosechas es el siguiente:\n"
            "Zanahoria: 8 cred \n"
            "Papa: 12 cred \n"
            "Tomate: 18 cred \n"
            "Repollo: 44 cred"
        ),
    },
    {
        "id": "desconocido_1",
        "dia_llegada": 5,
        "remitente": "Desconocido",
        "asunto": "solo",
        "mensaje": (
            "Te vemos.............\n\n"
            "........................Buscamos...\n\n"
            "...................Metal no?...\n\n"
            "....Esperar.."
        ),
    },
    {
        "id": "dia100",
        "dia_llegada": 100,
        "remitente": "Dev",
        "asunto": "100 dias",
        "mensaje": (
            "Gracias por jugar"
        ),
    },
]

def personalizar_texto(texto, game_state):
    reemplazos = {
        "{jugador}": game_state.nombre_jugador or "Colono",
        "{mascota}": game_state.nombre_mascota or "tu mascota",
        "{tipo_mascota}": game_state.tipo_mascota or "mascota",
    }

    for marcador, valor in reemplazos.items():
        texto = texto.replace(marcador, valor)

    return texto


class GestorCorreos:
    def __init__(self, game_state):
        self.game_state = game_state

    def actualizar_dia(self, dia_actual):
        for correo in CORREOS:
            identificador = correo["id"]

            if (
                correo["dia_llegada"] <= dia_actual
                and identificador not in self.game_state.correos_recibidos
            ):
                self.game_state.correos_recibidos.append(identificador)

    def obtener_correos(self):
        correos = []

        for correo in CORREOS:
            if correo["id"] not in self.game_state.correos_recibidos:
                continue

            correo_personalizado = correo.copy()

            correo_personalizado["asunto"] = personalizar_texto(
                correo["asunto"], self.game_state
            )

            correo_personalizado["mensaje"] = personalizar_texto(
                correo["mensaje"], self.game_state
            )

            correo_personalizado["remitente"] = personalizar_texto(
                correo["remitente"], self.game_state
            )

            correos.append(correo_personalizado)

        return correos

    def marcar_leido(self, identificador):
        if identificador not in self.game_state.correos_leidos:
            self.game_state.correos_leidos.append(identificador)

    def esta_leido(self, identificador):
        return identificador in self.game_state.correos_leidos

    def cantidad_no_leidos(self):
        return sum(
            1
            for correo in self.obtener_correos()
            if not self.esta_leido(correo["id"])
        )
