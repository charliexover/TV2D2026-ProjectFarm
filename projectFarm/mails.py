
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
             "de la base marciana. Al terminarla se te acreditara en tu cuenta personal"
             " 500mil dolares."
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
        "asunto": "Tutorial 1",
        "mensaje": (
            "En tu pocesion tienes una regadera y semillas.\n"
            "Sal fuera y ve al oeste donde veras un campo donde plantarlas.\n"
            "El oxigeno es limitado asi que se recomienda no merodear mucho."
        ),
    },
    {
        "id": "dia_siguiente",
        "dia_llegada": 2,
        "remitente": "Agencia Espacial",
        "asunto": "Tutorial 2",
        "mensaje": (
            "Presiona la tecla G para abrir el menu de mejoras.\n"
            "Si quieres ver la cantidad de recursos que tienes presiona Tab.\n"
        ),
    },
    {
        "id": "mision_estrellas",
        "dia_llegada": 3,
        "remitente": "Agencia Espacial",
        "asunto": "Estrellas",
        "mensaje": (
            "Cada mision que cumplas agregará estrellas a la interfaz \n"
            "superior derecha. Al conseguir las 5 podrás irte al este \n"
            "donde te espera un cohete que te llevará a la Tierra. "
        ),
    },
    {
        "id": "centroDatos_completado",
        "dia_llegada": None,
        "requisito_objetivo": "estrella_centro_datos",
        "remitente": "Agencia Espacial",
        "asunto": "Centro de Datos Completado",
        "mensaje": (
            "Buen trabajo {jugador}.\n"
            "Has completado el centro de datos exitosamente. \n"
            "Te has ganado tu estrella del merito sigue asi."
        ),
    },
    {
        "id": "expediciones_completado",
        "dia_llegada": None,
        "requisito_objetivo": "estrella_expediciones",
        "remitente": "Agencia Espacial",
        "asunto": "Expediciones Completadas",
        "mensaje": (
            "Buen trabajo {jugador}.\n"
            "Has completado todas las expediciones. \n"
            "Te has ganado tu estrella del merito sigue asi."
        ),
    },
    {
        "id": "reciclaje_completado",
        "dia_llegada": None,
        "requisito_objetivo": "reciclajeDisponible",
        "remitente": "Agencia Espacial",
        "asunto": "Reciclaje Completado",
        "mensaje": (
            "Buen trabajo {jugador}.\n"
            "Has construido el centro de reciclaje. \n"
            "Te has ganado tu estrella del merito sigue asi."
        ),
    },
    {
        "id": "generador_completado",
        "dia_llegada": None,
        "requisito_objetivo": "estrella_generador",
        "remitente": "Agencia Espacial",
        "asunto": "Generador Completado",
        "mensaje": (
            "Buen trabajo {jugador}.\n"
            "Has reparado el generador de la base. \n"
            "Te has ganado tu estrella del merito sigue asi."
        ),
    },
    {
        "id": "creditos_completado",
        "dia_llegada": None,
        "requisito_objetivo": "estrella_creditos",
        "remitente": "Agencia Espacial",
        "asunto": "Créditos Completados",
        "mensaje": (
            "Buen trabajo {jugador}.\n"
            "Has conseguido una suma total de 100mil créditos. \n"
            "Te has ganado tu estrella del merito sigue asi."
        ),
    },
    {
        "id": "mascota_estado1",
        "dia_llegada": 5,
        "remitente": "Señor Smith",
        "asunto": " {mascota} ",
        "mensaje": (
            "Buenos dias o noches nosé como será ahi arriba. \n"
            "{mascota} esta de buen humor hoy, pasaron una noticia sobre usted \n"
            "en la tele y creo que eso le hizo levantar el animo. \n"
            "Saludos cordiales."
        ),
    },
    {
        "id": "mascota_estado2",
        "dia_llegada": 15,
        "remitente": "Señor Smith",
        "asunto": " {mascota} ",
        "mensaje": (
            "Buenos dias o noches nosé como será ahi arriba. \n"
            "El otro dia compré un muñeco de astronauta en una tienda y se lo di a {mascota} \n" 
            "No se despega de el muñeco y lo abraza todo el tiempo. \n"
            "Saludos cordiales." 
        ),
    },
    {
        "id": "mate_encontrado",
        "dia_llegada": None,
        "requisito_objetivo": "mateRecolectado",
        "dia_referencia": "dia_recoleccion_mate",
        "remitente": "Desconocido",
        "asunto": " El mate ",
        "mensaje": (
            "Hola {jugador}.\n"
            "Perdi ese mate en mi primera expedicion no entiendo como "
            "pudo haber terminado dentro de una cueva. \n"
            "Que la agencia no se entere de esto por favor, que te parece "
            "un incentivo asi estaras mas cerca de esos 100mil creditos. Mira tu monitor de recursos :)" 
        ),
    },
    {
        "id": "tormenta_advertencia",
        "dia_llegada": 7,
        "remitente": "Agencia Espacial",
        "asunto": " Advertencia de Tormenta ",
        "mensaje": (
            "Se ha detectado una tormenta de arena en la zona. \n"
            "Se recomienda no estar mucho tiempo afuera. \n"
            "Investigaremos una forma de que pueda protegerse. \n"
            "Por el momento tenga mucho cuidado" 
        ),
    },
    {
        "id": "tormenta_advertencia2",
        "dia_llegada": 14,
        "remitente": "Agencia Espacial",
        "asunto": " Investigacion completada ",
        "mensaje": (
            "Tiene a su disposición un nuevo traje anti-tormenta. \n"
            "Abra el menu de mejoras y desbloquee el traje. \n"
            "Esperemos que le sea útil."
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
            if identificador in self.game_state.correos_recibidos:
                continue

            requisito_objetivo = correo.get("requisito_objetivo")
            if requisito_objetivo is not None:
                dia_programado = self.game_state.correos_programados.get(
                    identificador
                )
                if (
                    dia_programado is None
                    and getattr(self.game_state, requisito_objetivo)
                ):
                    dia_referencia = correo.get("dia_referencia")
                    dia_base = (
                        getattr(self.game_state, dia_referencia, None)
                        if dia_referencia is not None
                        else None
                    )
                    dia_programado = (
                        dia_base + 1
                        if dia_base is not None
                        else dia_actual + 1
                    )
                    self.game_state.correos_programados[identificador] = (
                        dia_programado
                    )

                if dia_programado is not None and dia_programado <= dia_actual:
                    self.game_state.correos_recibidos.append(identificador)
                    del self.game_state.correos_programados[identificador]
            elif correo["dia_llegada"] <= dia_actual:
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
