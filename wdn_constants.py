"""Konstanten: Regler-Grenzen, Beschriftungen, Farben und Presets."""

import wdn_experimente as X
import wdn_masse as M
import wdn_szenario as S
import wdn_tabellen as T

SEED_MAX = 999_999
DEFAULT_SEED = T.TAB_SEED
A_MIN, A_MAX, DEFAULT_A = 6, 10, 8                 # zwei Hallen: 72 bis 200 Knoten; 300 Maximalflüsse und eine Inverse unter 1 s
N_MIN, N_MAX, N_STEP, DEFAULT_N = 80, 200, 10, 150  # Kontrast- und dichte Netze
DEFAULT_TUEREN, DEFAULT_VERBUND = 1, "3x3x4"
P_LEITUNG_MIN, P_LEITUNG_MAX, P_LEITUNG_STD = 0.01, 0.60, 0.15
STREUPUNKTE_MAX = 3000                             # Punkte im Streubild der Entartung (jeder k-te)

MASS_TEXT = {
    M.DISTANZ: "kürzeste Distanz", M.WIDERSTAND: "effektiver Widerstand R", M.MINCUT: "min cut", M.MINCUT_DIST: "min cut, dann Distanz",
    M.GRADTERM: "Gradterm 1/d_s + 1/d_t", M.ISOLATION: "Isolationsnäherung", M.STICH50: "eigene Stichprobe, 50 Proben",
    M.STICH200: "eigene Stichprobe, 200 Proben", M.VERSTAERKT: "verstärkte Widerstandsdistanz", M.MINUS_LPLUS: "−L⁺",
    M.KOSINUS: "Kosinusform von L⁺", M.PPR: "PPR/Grad (Sprung 0,15)", M.ADAMIC: "Adamic-Adar", M.DIST_WEGE: "Distanz, dann Wegezahl",
    "ppr_voreinstellung": "PPR/Grad (Sprung 0,15)", "ppr_abgestimmt": "PPR/Grad (abgestimmt)",
}
MASS_KURZ = {
    M.DISTANZ: "Distanz", M.WIDERSTAND: "R", M.MINCUT: "min cut", M.MINCUT_DIST: "min cut, Dist.", M.GRADTERM: "Gradterm",
    M.ISOLATION: "Isolation", M.STICH50: "Stichpr. 50", M.STICH200: "Stichpr. 200", M.VERSTAERKT: "verstärkt", M.MINUS_LPLUS: "−L⁺",
    M.KOSINUS: "Kosinus L⁺", M.PPR: "PPR/Grad", M.ADAMIC: "Adamic-Adar", M.DIST_WEGE: "Dist., Wege", "ppr_voreinstellung": "PPR 0,15",
    "ppr_abgestimmt": "PPR abgest.",
}
STREU_MASSE = (M.WIDERSTAND, M.DISTANZ, M.MINCUT, M.GRADTERM, M.ISOLATION, M.STICH200)
BALKEN_MASSE = (M.DISTANZ, M.MINCUT, M.MINCUT_DIST, M.GRADTERM, M.ISOLATION, M.WIDERSTAND)
GRUPPEN_TEXT = {
    "hallen1": "zwei Hallen, 1 Tür", "hallen2": "zwei Hallen, 2 verteilte Türen", "hallen4": "zwei Hallen, 4 verteilte Türen",
    "hallen_a": "zwei Hallen, a verteilte Türen", "verbund": "Hallenverbund", **{f: S.FAMILIE_KURZ[f] for f in S.KONTRAST + S.DICHT},
}

REGEL_TEXT = {
    X.ZUFAELLIG: "zufällige fehlende Kante (Erwartung)", X.MAX_R: "größtes R", X.MAX_GRADTERM: "größter Gradterm (kleinste Grade)",
    X.MAX_DISTANZ: "größte Distanz (Mittel über Gleichstände)", X.DIST_GRAD: "größte Distanz, dann Gradterm",
    X.FIEDLER: "Fiedler: größte Differenz im zweiten Eigenvektor", X.MAX_ZAEHLER: "größter Zähler (biharmonisch)",
}
REGEL_KURZ = {X.ZUFAELLIG: "zufällig", X.MAX_R: "größtes R", X.MAX_GRADTERM: "Gradterm", X.MAX_DISTANZ: "Distanz", X.DIST_GRAD: "Dist., Gradterm",
              X.FIEDLER: "Fiedler", X.MAX_ZAEHLER: "Zähler"}

FARBE_R = "#2F6B65"
FARBE_GEGNER = "#9aa5b1"
FARBE_STICH = {50: "#c77d2e", 200: "#7b4fa3"}
FARBE_INNEN, FARBE_QUER = "#4c78a8", "#d1495b"
FARBE_WAHL, FARBE_BESTE = "#e69f00", "#d1495b"


def _preset(**abweichung) -> dict:
    basis = {"netz": S.HALLEN, "a": DEFAULT_A, "tueren": DEFAULT_TUEREN, "verbund": DEFAULT_VERBUND, "n": DEFAULT_N, "p": 0.15, "pd": 0.7,
             "seed": DEFAULT_SEED, "e_netz": S.E_HALLEN1, "e_n": 500, "x_netz": S.X_HALLEN1, "x_regel": X.MAX_R, "r_netz": "torus3d"}
    basis.update(abweichung)
    return basis


PRESETS = {
    "Zwei Hallen, eine Tür": _preset(),
    "Vier verteilte Türen: Grade vorn": _preset(tueren=4, e_netz=S.E_HALLENA, x_netz=S.X_HALLEN2),
    "Straßenähnlich": _preset(netz=S.STRASSE, x_netz="xstrasse"),
    "Netz mit Knotenpunkten": _preset(netz=S.KNOTEN, e_netz=S.E_ER8, x_netz="xknoten"),
    "Dichtes Netz": _preset(netz=S.ER20, e_netz=S.E_ERWURZEL, r_netz="gruppen20"),
    "Besen": _preset(x_netz=S.X_BESEN),
}
PRESET_HELP = {
    "Zwei Hallen, eine Tür": "Zwei Gitterhallen 8×8 mit einer Tür, Ausfallrate 15 %: R ordnet die Ausfälle klar besser als Distanz und Gradterm.",
    "Vier verteilte Türen: Grade vorn": "Dieselben Hallen, vier verteilte Türen: hier liegen die zwei Endgrade klar vor R.",
    "Straßenähnlich": "Ausgedünnte Delaunay-Triangulierung mit 150 Knoten und mittlerem Grad 2,8 (ein Modellnetz, kein Straßennetz): R liegt klar vor der "
                      "Distanz, min cut und eine 200er-Stichprobe liegen hier klar vor R.",
    "Netz mit Knotenpunkten": "Anschluss nach dem Grad, 150 Knoten: R liegt klar vor Distanz und min cut, aber nicht vor den Graden.",
    "Dichtes Netz": "Zufallsnetz mit 150 Knoten und mittlerem Grad 20, Ausfallrate 70 %: R und Gradterm treffen den Ausfall ohne klaren Unterschied.",
    "Besen": "Stellt Experiment 3 auf den Besen, einen Baum mit 5 Knoten, an dem sich Ausbauregeln unterscheiden; Experiment 1 bleibt auf den zwei Hallen.",
}
