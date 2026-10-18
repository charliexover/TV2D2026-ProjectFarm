import json
import os
from pathlib import Path


class SaveSlots:
    CANTIDAD_PARTIDAS = 3
    VERSION = 1

    def __init__(self, carpeta=None):
        self.carpeta = (
            Path(carpeta)
            if carpeta is not None
            else Path.home()
            / "AppData"
            / "Local"
            / "TVJ2D_2026_ProyectoGranja"
            / "partidas"
        )

    def _validar_slot(self, slot):
        if type(slot) is not int or not 0 <= slot < self.CANTIDAD_PARTIDAS:
            raise ValueError(f"Espacio de partida invalido: {slot}")

    def _ruta_slot(self, slot):
        self._validar_slot(slot)
        return self.carpeta / f"partida_{slot + 1}.json"

    def cargar(self, slot):
        ruta = self._ruta_slot(slot)
        if not ruta.exists():
            return None
        with ruta.open("r", encoding="utf-8") as archivo:
            partida = json.load(archivo)
        if (
            not isinstance(partida, dict)
            or partida.get("version") != self.VERSION
            or not isinstance(partida.get("game_state"), dict)
            or not isinstance(partida.get("parcelas"), list)
            or not isinstance(partida.get("chatarra_restante"), list)
            or not isinstance(partida.get("slot_inventario"), int)
        ):
            raise ValueError(f"El archivo de la partida {slot + 1} no es valido.")
        return partida

    def guardar(self, slot, partida):
        ruta = self._ruta_slot(slot)
        self.carpeta.mkdir(parents=True, exist_ok=True)
        ruta_temporal = ruta.with_suffix(".tmp")
        try:
            with ruta_temporal.open("w", encoding="utf-8") as archivo:
                json.dump(partida, archivo, ensure_ascii=False, indent=2)
            os.replace(ruta_temporal, ruta)
        except (OSError, TypeError, ValueError):
            try:
                ruta_temporal.unlink()
            except FileNotFoundError:
                pass
            raise

    def resumenes(self):
        resumenes = []
        for slot in range(self.CANTIDAD_PARTIDAS):
            try:
                partida = self.cargar(slot)
            except (OSError, ValueError) as error:
                resumenes.append({"estado": "error", "error": str(error)})
                continue

            if partida is None:
                resumenes.append({"estado": "vacia"})
                continue

            estado = partida["game_state"]
            resumenes.append(
                {
                    "estado": "guardada",
                    "dia": estado.get("dia_actual", 0),
                    "creditos": estado.get("creditos", 0),
                }
            )
        return resumenes
