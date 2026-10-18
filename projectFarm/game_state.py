class GameState:
    def __init__(self):
        self.semilla_zanahoria = 9
        self.semilla_papa = 9
        self.semilla_tomate = 9
        self.semilla_repollo = 9
        self.dia_actual = 0
        self.zanahorias_cosechadas = 0
        self.papas_cosechadas = 0
        self.tomates_cosechadas = 0
        self.repollos_cosechadas = 0
        self.oxigeno = 100
        self.creditos = 0
        self.chatarra = 0
        self.materiales = 0
        self.chatarra_en_proceso = 0
        self.estado_procesamiento = "inactivo"
        self.dia_inicio_procesamiento = None
        self.guanteReforzado = False
        self.dia_mision_antena = None
        self.antena_objetivo = None
        self.antena_encontrada = False
        self.datos_antena_enviados = False