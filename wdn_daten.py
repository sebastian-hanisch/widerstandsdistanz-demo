"""Laden der vorgerechneten Zahlen (daten/vorgerechnet.json, erzeugt von tools/vorrechnen.py) und ihre Zusammenfassungen (ohne Streamlit).

Zählweise: gezählt werden Netz-p-Zellen mit messbarer Zielgröße. „R vorn“ = höhere Rangkorrelation in Wahrheitsstichprobe 1; ein konstanter Gegner (keine
Rangkorrelation bestimmbar) zählt wie 0. „klar“ = nach dem Kriterium `wdn_statistik.klar` in beiden Wahrheitsstichproben.
"""

import json
from pathlib import Path

import numpy as np

import wdn_masse as M
import wdn_statistik as ST

PFAD = Path(__file__).resolve().parent / "daten" / "vorgerechnet.json"


def laden() -> dict:
    return json.loads(PFAD.read_text(encoding="utf-8"))


def _wert(x):
    return 0.0 if x is None else x


def zellen(daten: dict, gruppe=None, p=None, block=None) -> list:
    return [z for z in daten["ausfall"]["zeilen"] if (gruppe is None or z["gruppe"] == gruppe) and (p is None or z["p"] == p)
            and (block is None or z["block"] in ((block,) if isinstance(block, str) else block))]


def mittel(zz: list, mass: str):
    """Mittlere Rangkorrelation (Stichprobe 1) über die messbaren Zellen, in denen das Maß nicht konstant ist; None, wenn keine bleibt."""
    werte = [z["rho1"][mass] for z in zz if z["messbar"] and z["rho1"][mass] is not None]
    return float(np.mean(werte)) if werte else None


def zaehlung(zz: list, gegner: str) -> dict:
    """{'messbar', 'r_vorn', 'gegner_vorn', 'klar_r', 'klar_gegner', 'zellen'} für R gegen einen Gegner."""
    ok = [z for z in zz if z["messbar"]]
    urteile = [ST.klar(z["rho1"][M.WIDERSTAND], z["rho2"][M.WIDERSTAND], z["rho1"][gegner], z["rho2"][gegner]) for z in ok]
    return {"zellen": len(zz), "messbar": len(ok),
            "r_vorn": sum(_wert(z["rho1"][M.WIDERSTAND]) > _wert(z["rho1"][gegner]) for z in ok),
            "gegner_vorn": sum(_wert(z["rho1"][gegner]) > _wert(z["rho1"][M.WIDERSTAND]) for z in ok),
            "klar_r": sum(u == ST.R_VORN for u in urteile), "klar_gegner": sum(u == ST.GEGNER_VORN for u in urteile)}


def ueber_wiederholbarkeit(zz: list, mass: str) -> int:
    """Zahl der messbaren Zellen, in denen das Maß über „Hälfte gegen Hälfte“ liegt (das ist darum keine Obergrenze)."""
    return sum(z["messbar"] and z["haelften"] is not None and _wert(z["rho1"][mass]) > z["haelften"] for z in zz)


def nicht_messbar(zz: list) -> tuple:
    return sum(not z["messbar"] for z in zz), len(zz)


def entartung_zeile(daten: dict, familie: str, groesse: int) -> dict:
    return next(z for z in daten["entartung"]["zeilen"] if z["familie"] == familie and z["groesse"] == groesse)


def ausbau_zeilen(daten: dict, netz: str) -> list:
    return [z for z in daten["ausbau"]["zeilen"] if z["netz"] == netz]


def ausbau_median(zz: list, regel: str):
    werte = [z["anteil"][regel] for z in zz if z["anteil"][regel] is not None]
    return float(np.median(werte)) if werte else None


def ausbau_vergleich(zz: list, gegner: str) -> tuple:
    """(besser, gleich, schlechter) von „größtes R“ gegen eine Regel, je Netz (Netze, auf denen die Regel nicht bestimmbar ist, zählen nicht)."""
    paare = [(z["anteil"]["max_r"], z["anteil"][gegner]) for z in zz if z["anteil"][gegner] is not None]
    besser = sum(a > b + 1e-9 for a, b in paare)
    schlechter = sum(a < b - 1e-9 for a, b in paare)
    return besser, len(paare) - besser - schlechter, schlechter


def dicht_ausbau(daten: dict) -> dict:
    """Je dichter Familie: Median der Rangkorrelation R gegen Gradterm, des Gradterm-Anteils und der besten Senkung; besser/gleich/schlechter."""
    erg = {}
    for fam in sorted({z["familie"] for z in daten["ausbau"]["dicht"]}):
        zz = [z for z in daten["ausbau"]["dicht"] if z["familie"] == fam]
        besser, gleich, schlechter = ausbau_vergleich(zz, "max_gradterm")
        erg[fam] = {"netze": len(zz), "rho": float(np.median([z["rho"] for z in zz])),
                    "gradterm": float(np.median([z["anteil"]["max_gradterm"] for z in zz])),
                    "senkung": float(np.median([z["beste_senkung_anteil"] for z in zz])), "besser": besser, "gleich": gleich, "schlechter": schlechter}
    return erg


def dicht_ohne_engpass(daten: dict, familie: str, p: float) -> dict:
    zz = zellen(daten, gruppe=familie, p=p)
    return {m: mittel(zz, m) for m in (M.DISTANZ, M.WIDERSTAND, M.GRADTERM, M.ISOLATION)}
