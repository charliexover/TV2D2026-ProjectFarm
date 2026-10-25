HITOS_ROVER = [
    {
        "id": "tierra_50",
        "atributo": "muestras_tierra",
        "cantidad": 50,
        "creditos": 200,
    },
    {
        "id": "tierra_150",
        "atributo": "muestras_tierra",
        "cantidad": 150,
        "creditos": 500,
    },
    {
        "id": "tierra_400",
        "atributo": "muestras_tierra",
        "cantidad": 400,
        "creditos": 1500,
    },
    {
        "id": "atmosfera_100",
        "atributo": "muestras_atmosfera",
        "cantidad": 100,
        "creditos": 250,
    },
    {
        "id": "atmosfera_350",
        "atributo": "muestras_atmosfera",
        "cantidad": 350,
        "creditos": 500,
    },
    {
        "id": "atmosfera_500",
        "atributo": "muestras_atmosfera",
        "cantidad": 500,
        "creditos": 2000,
    },
    {
        "id": "minerales_100",
        "atributo": "minerales_recogidos",
        "cantidad": 100,
        "creditos": 350,
    },
    {
        "id": "minerales_250",
        "atributo": "minerales_recogidos",
        "cantidad": 250,
        "creditos": 800,
    },
    {
        "id": "minerales_500",
        "atributo": "minerales_recogidos",
        "cantidad": 500,
        "creditos": 2000,
    },
]


class SistemaRecompensas:

    def reclamar_recompensas_rover(self, game_state):
        creditos_ganados = 0
        hitos_completados = []

        for hito in HITOS_ROVER:
            identificador = hito["id"]
            atributo = hito["atributo"]

            cantidad_actual = getattr(game_state, atributo)

            if (
                cantidad_actual >= hito["cantidad"]
                and identificador
                not in game_state.hitos_rover_reclamados
            ):
                recompensa = hito["creditos"]

                game_state.creditos += recompensa
                creditos_ganados += recompensa

                game_state.hitos_rover_reclamados.append(
                    identificador
                )
                hitos_completados.append(hito)

        return creditos_ganados, hitos_completados