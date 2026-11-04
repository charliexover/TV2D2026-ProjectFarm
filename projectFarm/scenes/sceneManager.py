
import os

import pygame

from engine.audio import reproducir_sonido_pc
from engine.ui import Inventario
from projectFarm.scenes.dataCenter_scene import DataCenterScene
from projectFarm.scenes.caveScene import CaveScene
from projectFarm.scenes.expedition_scene import ExpeditionScene
from projectFarm.scenes.ending import EndingScene
from projectFarm.scenes.game_scene import GameScene
from projectFarm.scenes.home_scene import HomeScene
from projectFarm.scenes.options import OptionsMenu
from projectFarm.scenes.recycle_scene import RecycleScene
from projectFarm.scenes.save_slots_scene import SaveSlotsScene
from projectFarm.scenes.skilltree_scene import SkillTreeMenu
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
        self.tipo_musica_actual = None
        self.ruta_musica_exterior = os.path.join(
            os.path.dirname(__file__), "..", "sounds", "OneDayInMars.wav"
        )
        self.ruta_musica_tormenta = os.path.join(
            os.path.dirname(__file__),
            "..",
            "sounds",
            "OneTormentDayInMars.wav",
        )
        self.ruta_musica_titulo = os.path.join(
            os.path.dirname(__file__), "..", "sounds", "MarsAndMeIntro.wav"
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
            self.cambiar_a_cueva,
            al_ending=self.cambiar_a_ending,
        )
        self.cueva = CaveScene(
            self.game_state,
            self.inventario,
            self.salir_de_cueva,
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
        self.menu_habilidades_edificios = SkillTreeMenu()
        self.menu_opciones = OptionsMenu()
        self.solicitar_cierre = False
        self.registrar_escena("granja", self.granja, inicial=False)
        self.registrar_escena("casa", self.casa, inicial=False)
        self.registrar_escena("titulo", self.titulo, inicial=True)
        self.registrar_escena("partidas", self.selector_partidas, inicial=False)
        self.registrar_escena("reciclaje", self.reciclaje, inicial=False)
        self.registrar_escena("dataCenter", self.dataCenter, inicial=False)
        self.registrar_escena("expedicion", self.expedicion, inicial=False)
        self.registrar_escena("cueva", self.cueva, inicial=False)
        self._actualizar_musica(self.escena_actual)

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

        if self.escena_actual is self.granja:
            self.granja.restablecer_cursor()

        self.escena_actual = escena
        self._actualizar_musica(escena)

    def _actualizar_musica(self, escena):
        if escena is self.titulo:
            tipo_musica = "titulo"
            ruta_musica = self.ruta_musica_titulo
        elif escena is self.granja:
            if self.game_state.tormenta_arena:
                tipo_musica = "tormenta"
                ruta_musica = self.ruta_musica_tormenta
            else:
                tipo_musica = "exterior"
                ruta_musica = self.ruta_musica_exterior
        else:
            if self.tipo_musica_actual is not None:
                pygame.mixer.music.pause()
            return

        if self.tipo_musica_actual == tipo_musica:
            pygame.mixer.music.unpause()
            return

        pygame.mixer.music.load(os.path.normpath(ruta_musica))
        pygame.mixer.music.play(-1)
        self.tipo_musica_actual = tipo_musica
        if tipo_musica == "exterior":
            self.musica_exterior_cargada = True

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

    def cambiar_a_cueva(self):
        self.cueva.primera_entrada = True
        self.cambiar_escena("cueva")

    def cambiar_a_ending(self):
        self.ending = EndingScene(
            self.game_state,
            al_volver_titulo=self.cambiar_a_titulo,
        )
        self.registrar_escena("ending", self.ending)
        self.cambiar_escena("ending")

    def salir_de_cueva(self):
        self.granja.primera_entrada = True
        self.granja.puerta_reentrada = "cueva"
        self.granja.ultimo_update_oxigeno = None
        self.cambiar_a_granja()

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
            "correos_programados",
            "nombre_jugador",
            "tipo_mascota",
            "nombre_mascota",
            "tormenta_arena",
            "oxigeno_maximo",
            "creditos_acumulados",
            "oxigenoMaximo1Comprado",
            "oxigenoMaximo2Comprado",
            "oxigenoMaximo3Comprado",
            "progreso_centro_datos",
            "centro_datos_completado",
            "powers_reparados",
            "powers_pagados",
            "estrella_centro_datos",
            "estrella_expediciones",
            "estrella_generador",
            "estrella_creditos",
            "dia_interaccion_pared",
            "cuevaAbierta",
            "mateRecolectado",
            "dia_recoleccion_mate",
            "bono_mate_creditos_otorgado",
            "martilloDisponible",
            "martilloComprado",
            "linternaComprada",
            "descargaDatos1Comprado",
            "descargaDatos2Comprado",
            "mejorRegaderaComprada",
            "mejorExpedicionComprada",
            "radarComprado",
            "trajeAntiTormentaComprado",
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
            "correos_programados": {},
            "nombre_jugador": None,
            "tipo_mascota": None,
            "nombre_mascota": None,
            "tormenta_arena": False,
            "oxigeno_maximo": 100,
            "creditos_acumulados": estado_guardado.get("creditos", 0),
            "oxigenoMaximo1Comprado": False,
            "oxigenoMaximo2Comprado": False,
            "oxigenoMaximo3Comprado": False,
            "progreso_centro_datos": 0,
            "centro_datos_completado": False,
            "powers_reparados": [False] * 6,
            "powers_pagados": [False] * 6,
            "estrella_centro_datos": False,
            "estrella_expediciones": False,
            "estrella_generador": False,
            "estrella_creditos": False,
            "dia_interaccion_pared": None,
            "cuevaAbierta": False,
            "mateRecolectado": False,
            "dia_recoleccion_mate": None,
            "bono_mate_creditos_otorgado": False,
            "martilloDisponible": False,
            "martilloComprado": False,
            "linternaComprada": False,
            "descargaDatos1Comprado": False,
            "descargaDatos2Comprado": False,
            "mejorRegaderaComprada": False,
            "mejorExpedicionComprada": False,
            "radarComprado": False,
            "trajeAntiTormentaComprado": False,
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
                        "dia_interaccion_pared",
                        "dia_recoleccion_mate",
                    )
                    else (str, type(None))
                )
                if type(valor) not in tipos_permitidos:
                    raise ValueError(f"El valor guardado de {nombre} no es valido.")
            elif type(valor) is not type(valor_inicial):
                raise ValueError(f"El valor guardado de {nombre} no es valido.")
        for nombre in (
            "semilla_zanahoria",
            "semilla_papa",
            "semilla_tomate",
            "semilla_repollo",
        ):
            estado_guardado[nombre] = min(
                estado_guardado[nombre], self.inventario.LIMITE_SEMILLAS
            )
        if len(estado_guardado["powers_reparados"]) != 6 or any(
            type(reparado) is not bool
            for reparado in estado_guardado["powers_reparados"]
        ):
            raise ValueError("El estado guardado de los Power no es valido.")
        if len(estado_guardado["powers_pagados"]) != 6 or any(
            type(pagado) is not bool
            for pagado in estado_guardado["powers_pagados"]
        ):
            raise ValueError("El estado de pagos de los Power no es valido.")
        if any(
            reparado and pagado
            for reparado, pagado in zip(
                estado_guardado["powers_reparados"],
                estado_guardado["powers_pagados"],
            )
        ):
            raise ValueError("Un Power reparado no puede tener un pago pendiente.")
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
        if self.game_state.dia_actual == 7:
            self.game_state.tormenta_arena = True
        elif self.game_state.dia_actual > 7:
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

    def _seleccionar_slot_por_clic(self, eventos, limites_pantalla):
        if (
            self.escena_actual not in (
                self.casa,
                self.reciclaje,
                self.dataCenter,
                self.expedicion,
                self.cueva,
            )
        ):
            return False

        for evento in eventos:
            if (
                evento.type == pygame.MOUSEBUTTONDOWN
                and evento.button == 1
                and self.inventario.seleccionar_slot(
                    evento.pos,
                    limites_pantalla.width,
                    limites_pantalla.height,
                )
            ):
                return True
        return False

    def update(self, teclas, limites_pantalla, eventos=()):
        escenas_jugables = (
            self.granja,
            self.casa,
            self.reciclaje,
            self.dataCenter,
            self.expedicion,
            self.cueva,
        )
        if self.escena_actual in escenas_jugables:
            if (
                self.escena_actual is self.granja
                and self.granja.minijuego_power.activo
            ):
                self.granja.update(teclas, limites_pantalla, eventos)
                return

            if (
                self.escena_actual is self.granja
                and self.granja.power_pendiente_confirmacion is not None
            ):
                self.granja.update(teclas, limites_pantalla, eventos)
                return

            if (
                self.escena_actual is self.granja
                and self.granja.ventana_generador_abierta
            ):
                self.granja.update(teclas, limites_pantalla, eventos)
                return

            if self.menu_opciones.abierto:
                self.menu_opciones.procesar_eventos(
                    eventos, limites_pantalla
                )
                self.solicitar_cierre = (
                    self.menu_opciones.solicitar_cierre
                )
                if not self.menu_opciones.abierto:
                    self.granja.pausado = False
                    self.granja.ultimo_update_oxigeno = (
                        pygame.time.get_ticks()
                    )
                return
            if self.escena_actual is self.casa and self.casa.menu_pc is not None:
                self.casa.update(teclas, limites_pantalla, eventos)
                return
            if any(
                evento.type == pygame.KEYDOWN
                and evento.key == pygame.K_ESCAPE
                for evento in eventos
            ):
                self.menu_opciones.abierto = True
                self.menu_opciones.pagina = "principal"
                self.menu_opciones.seleccion = 0
                self.granja.pausado = True
                return

        escenas_interiores = (
            self.casa,
            self.reciclaje,
            self.dataCenter,
            self.expedicion,
            self.cueva,
        )
        if (
            self.escena_actual in escenas_interiores
            and self.escena_actual.interfaz_estado.mostrar_inventario
        ):
            if self._seleccionar_slot_por_clic(
                eventos, limites_pantalla
            ):
                return
            for evento in eventos:
                if (
                    evento.type == pygame.KEYDOWN
                    and pygame.K_1 <= evento.key <= pygame.K_9
                ):
                    self.inventario.slot_seleccionado = (
                        evento.key - pygame.K_1
                    )
                    return
            if any(
                evento.type == pygame.KEYDOWN
                and evento.key == pygame.K_i
                for evento in eventos
            ):
                self.escena_actual.interfaz_estado.mostrar_inventario = False
            return

        if self.escena_actual in escenas_interiores and self.menu_habilidades_edificios.procesar_eventos(
            eventos, limites_pantalla, self.game_state
        ):
            return

        if self._seleccionar_slot_por_clic(eventos, limites_pantalla):
            return

        if self.escena_actual in escenas_interiores:
            for evento in eventos:
                if (
                    evento.type == pygame.KEYDOWN
                    and pygame.K_1 <= evento.key <= pygame.K_9
                ):
                    self.inventario.slot_seleccionado = (
                        evento.key - pygame.K_1
                    )
                    return

        if self.escena_actual in escenas_interiores and any(
            evento.type == pygame.KEYDOWN
            and evento.key == pygame.K_i
            for evento in eventos
        ):
            self.escena_actual.interfaz_estado.mostrar_inventario = True
            reproducir_sonido_pc()
            return

        self.escena_actual.update(teclas, limites_pantalla, eventos)

    def draw(self, pantalla):
        self.escena_actual.draw(pantalla)
        escenas_interiores = (
            self.casa,
            self.reciclaje,
            self.dataCenter,
            self.expedicion,
            self.cueva,
        )
        if (
            self.escena_actual in escenas_interiores
            and self.escena_actual is not self.casa
        ):
            self.inventario.dibujar(pantalla, self.game_state)
        if (
            self.escena_actual in escenas_interiores
            and self.escena_actual.interfaz_estado.mostrar_inventario
        ):
            self.escena_actual.interfaz_estado.dibujar_inventario(
                pantalla, self.game_state
            )
        if self.escena_actual in escenas_interiores:
            self.menu_habilidades_edificios.dibujar(
                pantalla, self.game_state
            )
        self.menu_opciones.dibujar(
            pantalla, self.game_state.nombre_mascota
        )