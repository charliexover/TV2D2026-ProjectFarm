
import os

import pygame

from engine.ui import Inventario
from projectFarm.scenes.dataCenter_scene import DataCenterScene
from projectFarm.scenes.expedition_scene import ExpeditionScene
from projectFarm.scenes.game_scene import GameScene
from projectFarm.scenes.home_scene import HomeScene
from projectFarm.scenes.recycle_scene import RecycleScene
from projectFarm.scenes.save_slots_scene import SaveSlotsScene
from projectFarm.scenes.title_scene import TitleScene
from projectFarm.game_state import GameState
from projectFarm.farm import CULTIVOS
from projectFarm.save_slots import SaveSlots
from projectFarm.scraps import Chatarra
import random


class SceneManager:
    def __init__(self):
        self.escenas = {}
        self.escena_actual = None
        self.musica_exterior_cargada = False
        self.ruta_musica_exterior = os.path.join(
            os.path.dirname(__file__), "..", "assets", "MarsSong.wav"
        )
        self.game_state = GameState()
        self.inventario = Inventario()
        self.save_slots = SaveSlots()
        self.partida_activa = None
        self.granja = GameScene(
            self.game_state,
            self.inventario,
            self.cambiar_a_casa,
            self.cambiar_a_reciclaje,
            self.cambiar_a_data_center,
            self.cambiar_a_expedicion,
            self.procesar_desmayo,
            self.completar_desmayo,
        )
        self.casa = HomeScene(
            self.game_state,
            self.inventario,
            self.cambiar_a_granja,
            self.avanzar_dia_y_guardar,
        )
        self.casa.gestor_correos.actualizar_dia(self.game_state.dia_actual)
        self.reciclaje = RecycleScene(self.game_state, self.inventario, self.cambiar_a_granja)  
        self.titulo = TitleScene(self.mostrar_selector_partidas)
        self.selector_partidas = SaveSlotsScene(
            self.save_slots,
            self.iniciar_partida,
            self.cambiar_a_titulo,
        )
        self.dataCenter = DataCenterScene(self.game_state, self.inventario, self.cambiar_a_granja)  
        self.expedicion = ExpeditionScene(
            self.game_state, self.inventario, self.cambiar_a_granja
        )
        self.registrar_escena("granja", self.granja, inicial=False)
        self.registrar_escena("casa", self.casa, inicial=False)
        self.registrar_escena("titulo", self.titulo, inicial=True)
        self.registrar_escena("partidas", self.selector_partidas, inicial=False)
        self.registrar_escena("reciclaje", self.reciclaje, inicial=False)
        self.registrar_escena("dataCenter", self.dataCenter, inicial=False)
        self.registrar_escena("expedicion", self.expedicion, inicial=False)

    def registrar_escena(self, nombre, escena, inicial=False):
        if nombre in self.escenas:
            raise ValueError(f"Ya existe una escena registrada con el nombre: {nombre}")

        self.escenas[nombre] = escena
        if inicial or self.escena_actual is None:
            self.escena_actual = escena

    def cambiar_escena(self, nombre):
        try:
            escena = self.escenas[nombre]
        except KeyError:
            raise KeyError(f"No hay una escena registrada con el nombre: {nombre}") from None

        if escena is self.escena_actual:
            return

        self.escena_actual = escena
        if escena is self.granja:
            if not self.musica_exterior_cargada:
                pygame.mixer.music.load(
                    os.path.normpath(self.ruta_musica_exterior)
                )
                pygame.mixer.music.play(-1)
                self.musica_exterior_cargada = True
            else:
                pygame.mixer.music.unpause()
        elif self.musica_exterior_cargada:
            pygame.mixer.music.pause()

    def cambiar_a_granja(self):
        self.cambiar_escena("granja")

    def cambiar_a_casa(self):
        self.cambiar_escena("casa")

    def cambiar_a_reciclaje(self):
        self.cambiar_escena("reciclaje")

    def cambiar_a_data_center(self):
        self.cambiar_escena("dataCenter")

    def cambiar_a_expedicion(self):
        self.cambiar_escena("expedicion")

    def procesar_desmayo(self):
        self.game_state.creditos //= 2
        return self.avanzar_dia_y_guardar()

    def completar_desmayo(self, mensaje_guardado):
        self.granja.primera_entrada = True
        self.granja.puerta_reentrada = "casa"
        self.granja.ultimo_update_oxigeno = None
        self.granja.segundos_acumulados_oxigeno = 0
        self.casa.primera_entrada = True
        self.casa.primera_visita = False
        self.casa.mensaje_desmayo = (
            "Por desmayarte, la agencia te descontó el 50% "
            "de los créditos que poseías."
        )
        self.casa.mensaje_desmayo_hasta = pygame.time.get_ticks() + 8000
        self.casa.mensaje_guardado = mensaje_guardado
        self.casa.mensaje_guardado_hasta = pygame.time.get_ticks() + 5000
        self.cambiar_a_casa()
        
    def cambiar_a_titulo(self):
        self.cambiar_escena("titulo")

    def mostrar_selector_partidas(self):
        self.selector_partidas.mensaje = None
        self.cambiar_escena("partidas")

    def iniciar_partida(
        self,
        slot,
        nombre_jugador=None,
        tipo_mascota=None,
        nombre_mascota=None,
    ):
        partida = self.save_slots.cargar(slot)

        if partida is None:
            self._reiniciar_progreso()

            self.game_state.nombre_jugador = nombre_jugador
            self.game_state.tipo_mascota = tipo_mascota
            self.game_state.nombre_mascota = nombre_mascota
        else:
            self._cargar_progreso(partida)

        self.casa.gestor_correos.actualizar_dia(
            self.game_state.dia_actual
        )

        self.partida_activa = slot
        self.casa.primera_entrada = True
        self.casa.primera_visita = True
        self.casa.nodo_dialogo_ram = None
        self.casa.mensaje_guardado = None
        self.casa.mensaje_desmayo = None
        self.casa.mensaje_desmayo_hasta = 0
        self.granja.primera_entrada = True
        self.granja.puerta_reentrada = "casa"
        self.granja.ultimo_update_oxigeno = None
        self.granja.mensaje_antena = None
        self.granja.minijuego_antena.activo = False
        self.reciclaje.primera_entrada = True
        self.reciclaje.primera_visita = True
        self.dataCenter.primera_entrada = True
        self.dataCenter.primera_visita = True
        self.cambiar_a_casa()

    def _reiniciar_progreso(self):
        self.game_state.__dict__.clear()
        self.game_state.__dict__.update(vars(GameState()))
        self.inventario.slot_seleccionado = 0
        for parcela in self.granja.parcelas:
            parcela.planta = None
            parcela.dias_crecimiento = 0
            parcela.dia_regado = None
            parcela.dia_maduro = None
            parcela.seca = False
        self.granja.segundos_acumulados_oxigeno = 0
        self.granja.ultimo_update_oxigeno = None
        self.granja.mensaje_antena = None
        self.granja.minijuego_antena.activo = False
        self.granja._generar_chatarra()

    def _cargar_progreso(self, partida):
        estado_guardado = partida["game_state"]
        estado_nuevo = GameState()
        claves_estado = set(vars(estado_nuevo))
        claves_opcionales = {
            "parcela1Comprada",
            "parcela1Disponible",
            "parcela2Comprada",
            "parcela2Disponible",
            "parcela3Comprada",
            "parcela3Disponible",
            "semillaPapaDesbloqueada",
            "semillaTomateDesbloqueada",
            "semillaRepolloDesbloqueada",
            "centroDatosComprado",
            "centroDatosDisponible",
            "reciclajeComprado",
            "reciclajeDisponible",
            "expedicionesComprado",
            "expedicionesDisponible",
            "muestras_tierra",
            "muestras_atmosfera",
            "minerales_recogidos",
            "expedicion_activa",
            "dia_finalizacion_expedicion",
            "resultado_ultima_expedicion",
            "dia_uso_tanque_oeste",
            "dia_uso_tanque_norte",
            "dia_uso_tanque_este",
            "correos_recibidos",
            "correos_leidos",
            "nombre_jugador",
            "tipo_mascota",
            "nombre_mascota",
            "tormenta_arena",
            "oxigeno_maximo",
            "oxigenoMaximo1Comprado",
            "oxigenoMaximo2Comprado",
            "oxigenoMaximo3Comprado",
            "progreso_centro_datos",
            "centro_datos_completado",
            "descargaDatos1Comprado",
            "descargaDatos2Comprado",
        }
        valores_opcionales_por_defecto = {
            "parcela1Comprada": True,
            "parcela1Disponible": True,
            "parcela2Comprada": False,
            "parcela2Disponible": False,
            "parcela3Comprada": False,
            "parcela3Disponible": False,
            "semillaPapaDesbloqueada": False,
            "semillaTomateDesbloqueada": False,
            "semillaRepolloDesbloqueada": False,
            "centroDatosComprado": False,
            "centroDatosDisponible": False,
            "reciclajeComprado": False,
            "reciclajeDisponible": False,
            "expedicionesComprado": False,
            "expedicionesDisponible": False,
            "muestras_tierra": 0,
            "muestras_atmosfera": 0,
            "minerales_recogidos": 0,
            "expedicion_activa": None,
            "dia_finalizacion_expedicion": None,
            "resultado_ultima_expedicion": "",
            "correos_recibidos": [],
            "correos_leidos": [],
            "nombre_jugador": None,
            "tipo_mascota": None,
            "nombre_mascota": None,
            "tormenta_arena": False,
            "oxigeno_maximo": 100,
            "oxigenoMaximo1Comprado": False,
            "oxigenoMaximo2Comprado": False,
            "oxigenoMaximo3Comprado": False,
            "progreso_centro_datos": 0,
            "centro_datos_completado": False,
            "descargaDatos1Comprado": False,
            "descargaDatos2Comprado": False,
        }
        # Campos antiguos que ya no se utilizan desde que se eliminaron
        # los tanques de oxígeno del mapa.
        campos_obsoletos = {
            "dia_uso_tanque_oeste",
            "dia_uso_tanque_norte",
            "dia_uso_tanque_este",
            "tanqueOxigenoEsteComprado",
            "tanqueOxigenoOesteComprado",
            "tanqueOxigenoNorteComprado",
            "tanqueOxigenoEsteDisponible",
            "tanqueOxigenoOesteDisponible",
            "tanqueOxigenoNorteDisponible",
        }

        # Ignoramos esos campos al validar partidas antiguas.
        claves_guardadas = set(estado_guardado) - campos_obsoletos

        if (
            claves_guardadas - claves_estado
            or claves_estado - claves_guardadas - claves_opcionales
        ):
            raise ValueError("El estado guardado no coincide con esta version.")

        # Quitamos los atributos obsoletos antes de restaurar el estado.
        estado_guardado = {
            nombre: valor
            for nombre, valor in estado_guardado.items()
            if nombre not in campos_obsoletos
        }
        estado_guardado = estado_guardado.copy()
        for nombre, valor in valores_opcionales_por_defecto.items():
            estado_guardado.setdefault(nombre, valor)
        for nombre in ("semilla_papa", "semilla_tomate", "semilla_repollo"):
            nombre_desbloqueo = {
                "semilla_papa": "semillaPapaDesbloqueada",
                "semilla_tomate": "semillaTomateDesbloqueada",
                "semilla_repollo": "semillaRepolloDesbloqueada",
            }[nombre]
            if nombre not in partida["game_state"]:
                continue
            cantidad = partida["game_state"][nombre]
            if type(cantidad) is int and cantidad > 0:
                estado_guardado[nombre_desbloqueo] = True
        for nombre, valor_inicial in vars(estado_nuevo).items():
            valor = estado_guardado[nombre]
            if valor_inicial is None:
                tipos_permitidos = (
                    (int, type(None))
                    if nombre
                    in (
                        "dia_inicio_procesamiento",
                        "dia_mision_antena",
                        "dia_finalizacion_expedicion",
                    )
                    else (str, type(None))
                )
                if type(valor) not in tipos_permitidos:
                    raise ValueError(f"El valor guardado de {nombre} no es valido.")
            elif type(valor) is not type(valor_inicial):
                raise ValueError(f"El valor guardado de {nombre} no es valido.")
        if estado_guardado["expedicion_activa"] not in (
            None,
            *self.expedicion.EXPEDICIONES,
        ):
            raise ValueError("El destino de expedicion guardado no es valido.")
        if (estado_guardado["expedicion_activa"] is None) != (
            estado_guardado["dia_finalizacion_expedicion"] is None
        ):
            raise ValueError("El estado de la expedicion guardada no es valido.")

        datos_parcelas = partida["parcelas"]
        cantidad_parcelas_iniciales = len(
            self.granja.parcelas_por_nodo["Parcela1"]
        )

        if not isinstance(datos_parcelas, list):
            raise ValueError("Los datos de parcelas guardados no son validos.")

        # Las partidas antiguas podían tener las 3 parcelas.
        # Conservamos únicamente los datos de Parcela1.
        if len(datos_parcelas) not in (
            cantidad_parcelas_iniciales,
            cantidad_parcelas_iniciales * 3,
        ):
            raise ValueError("La cantidad de parcelas guardadas no es valida.")

        if len(datos_parcelas) == cantidad_parcelas_iniciales * 3:
            datos_parcelas = datos_parcelas[:cantidad_parcelas_iniciales]
        slot_inventario = partida["slot_inventario"]
        if (
            type(slot_inventario) is not int
            or not 0 <= slot_inventario < self.inventario.cantidad_casillas
        ):
            raise ValueError("El espacio de inventario guardado no es valido.")

        for datos in datos_parcelas:
            claves_parcela = {"planta", "dias_crecimiento", "dia_regado"}
            claves_opcionales = {"dia_maduro", "seca"}
            if (
                not isinstance(datos, dict)
                or not claves_parcela <= set(datos)
                or not set(datos) - claves_parcela <= claves_opcionales
            ):
                raise ValueError("Los datos de una parcela no son validos.")
            planta = datos.get("planta")
            dias_crecimiento = datos.get("dias_crecimiento")
            dia_regado = datos.get("dia_regado")
            dia_maduro = datos.get("dia_maduro")
            seca = datos.get("seca", False)
            if planta is not None and (
                type(planta) is not int or planta not in CULTIVOS
            ):
                raise ValueError("Una parcela contiene un cultivo desconocido.")
            if type(dias_crecimiento) is not int or dias_crecimiento < 0:
                raise ValueError("El crecimiento guardado no es valido.")
            if dia_regado is not None and type(dia_regado) is not int:
                raise ValueError("El riego guardado no es valido.")
            if dia_maduro is not None and (
                type(dia_maduro) is not int or dia_maduro < 0 or planta != 3
            ):
                raise ValueError("El dia de maduracion guardado no es valido.")
            if type(seca) is not bool or (seca and planta is None):
                raise ValueError("El estado de sequia guardado no es valido.")

        
        posiciones_chatarra = partida["chatarra_restante"]
        for posicion in posiciones_chatarra:
            if (
                not isinstance(posicion, list)
                or len(posicion) != 2
                or any(type(coordenada) is not int for coordenada in posicion)
            ):
                raise ValueError("Las posiciones de chatarra guardadas no son validas.")
        segundos = partida.get("segundos_acumulados_oxigeno", 0)
        if type(segundos) not in (int, float) or segundos < 0:
            raise ValueError("El temporizador de oxigeno guardado no es valido.")

        self.game_state.__dict__.clear()
        self.game_state.__dict__.update(estado_guardado)
        for parcela, datos in zip(
            self.granja.parcelas_por_nodo["Parcela1"],
            datos_parcelas,
        ):
            parcela.planta = datos["planta"]
            parcela.dias_crecimiento = datos["dias_crecimiento"]
            parcela.dia_regado = datos["dia_regado"]
            parcela.dia_maduro = datos.get("dia_maduro")
            parcela.seca = datos.get("seca", False)
            if (
                parcela.planta == 3
                and parcela.dia_maduro is None
                and parcela.dias_crecimiento
                >= CULTIVOS[parcela.planta]["dias_crecimiento"]
            ):
                parcela.dia_maduro = self.game_state.dia_actual
        self.inventario.slot_seleccionado = slot_inventario
        self.granja.segundos_acumulados_oxigeno = segundos
        self.granja.chatarra = [
            Chatarra(x, y) for x, y in posiciones_chatarra
        ]
        self.granja.posiciones_chatarra_mapa = [
            tuple(posicion) for posicion in posiciones_chatarra
        ]

    def avanzar_dia_y_guardar(self):
        self.granja.avanzar_dia()
        if self.game_state.dia_actual >= 7:
            self.game_state.tormenta_arena = random.random() < 0.35
        else:
            self.game_state.tormenta_arena = False
        self.expedicion.procesar_fin_dia()
        self.casa.gestor_correos.actualizar_dia(self.game_state.dia_actual)
        if self.partida_activa is None:
            return "Dia avanzado, pero no hay espacio activo para guardar."

        partida = {
            "version": self.save_slots.VERSION,
            "game_state": vars(self.game_state).copy(),
            "parcelas": [
                {
                    "planta": parcela.planta,
                    "dias_crecimiento": parcela.dias_crecimiento,
                    "dia_regado": parcela.dia_regado,
                    "dia_maduro": parcela.dia_maduro,
                    "seca": parcela.seca,
                }
                for parcela in self.granja.parcelas
            ],
            "chatarra_restante": [
                [x, y] for x, y in self.granja.posiciones_chatarra_mapa
            ],
            "slot_inventario": self.inventario.slot_seleccionado,
            "segundos_acumulados_oxigeno": (
                self.granja.segundos_acumulados_oxigeno
            ),
        }
        try:
            self.save_slots.guardar(self.partida_activa, partida)
        except (OSError, TypeError, ValueError) as error:
            return f"Dia avanzado, pero no se pudo guardar: {error}"
        return f"Partida {self.partida_activa + 1} guardada."

    def update(self, teclas, limites_pantalla, eventos=()):
        self.escena_actual.update(teclas, limites_pantalla, eventos)

    def draw(self, pantalla):
        self.escena_actual.draw(pantalla)