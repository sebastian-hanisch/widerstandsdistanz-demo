"""Die festgeschriebene Instanzmenge der vorgerechneten Tabellen und wie eine Tabellenzeile entsteht (ohne Streamlit).

`tools/vorrechnen.py` rechnet damit `daten/vorgerechnet.json`; `tests/test_claims.py` rechnet Stichproben daraus neu. Alle Zufalls-Seeds stehen hier.
"""

import numpy as np

import wdn_experimente as X
import wdn_masse as M
import wdn_netze as N
import wdn_statistik as ST
import wdn_szenario as S
from wdn_zufall import ZWECK_ANFRAGEN, abgeleitet

TAB_SEED = 7000                                   # erster Zufalls-Seed der Netze; zugleich Voreinstellung der Seite
HALLEN_A = S.A_FAMILIE                            # 6, 8, 10
NETZE_KONTRAST = 10                               # Netze je Kontrastfamilie (Zufalls-Seeds TAB_SEED … TAB_SEED + 9)
NETZE_DICHT = 6
N_TABELLE = 150

# Gruppen der Ausfalltabelle: Schlüssel → Liste von (Familie, n, a, Türen, Verbund-Variante, Zufalls-Seed)
HALLEN_GRUPPEN = ("hallen1", "hallen2", "hallen4", "hallen_a", "verbund")


def instanzen(gruppe: str) -> list:
    if gruppe in ("hallen1", "hallen2", "hallen4", "hallen_a"):
        tueren = {"hallen1": 1, "hallen2": 2, "hallen4": 4, "hallen_a": 0}[gruppe]
        return [(S.HALLEN, 0, a, tueren, "", TAB_SEED) for a in HALLEN_A]
    if gruppe == "verbund":
        return [(S.VERBUND, 0, 0, 0, v, TAB_SEED) for v in S.VERBUND_VARIANTEN]
    anzahl = NETZE_DICHT if gruppe in S.DICHT else NETZE_KONTRAST
    return [(gruppe, N_TABELLE, 0, 0, "", TAB_SEED + i) for i in range(anzahl)]


def gruppen_block(block: str) -> tuple:
    return {"hallen": HALLEN_GRUPPEN, "kontrast": S.KONTRAST, "dicht": S.DICHT}[block]


def p_werte(gruppe: str) -> tuple:
    return S.P_DICHT if gruppe in S.DICHT else S.P_DUENN


def netz_instanz(inst) -> N.Netz:
    familie, n, a, tueren, verbund, seed = inst
    return S.baue(familie, n, a, tueren, verbund, seed)


def _rund(d: dict) -> dict:
    return {k: None if v is None else round(float(v), 6) for k, v in d.items()}


def ausfall_zeilen(gruppe: str, inst) -> list:
    """Alle p-Zeilen eines Netzes der Ausfalltabelle."""
    familie, n, a, tueren, verbund, seed = inst
    g = netz_instanz(inst)
    nm = X.netzmasse(g, seed, S.FAMNR[familie])
    zeilen = []
    for i, p in enumerate(p_werte(gruppe)):
        z = X.ausfallzelle(g, nm, p, i, seed, S.FAMNR[familie])
        zeilen.append({"gruppe": gruppe, "n": g.n, "m": len(g.kanten), "a": a, "variante": verbund, "seed": seed, "p": p, "messbar": z.messbar,
                       "rho1": _rund(z.rho1), "rho2": _rund(z.rho2), "haelften": None if z.haelften is None else round(z.haelften, 6)})
    return zeilen


# --- Entartung ------------------------------------------------------------------------------------------------------------------------

NETZE_ENTARTUNG = 5                               # je Zelle der Zufallsfamilien; Hallen sind fest gebaut (ein Netz)


def entartung_zeile(familie: str, n: int) -> dict:
    anzahl = 1 if familie in S.E_HALLEN else NETZE_ENTARTUNG
    werte = []
    for i in range(anzahl):
        g = S.baue_entartung(familie, n, TAB_SEED + i)
        e = X.entartung(g, haelften=familie == S.E_HAELFTEN)
        werte.append((g.n, e.mittlerer_grad, e.rho, e.abweichung, e.abweichung_innen, e.abweichung_quer))
    spalte = lambda k: [w[k] for w in werte]
    mitte = lambda k: None if any(v is None for v in spalte(k)) else round(float(np.median(spalte(k))), 6)
    return {"familie": familie, "groesse": n, "netze": anzahl, "n": sorted(set(spalte(0))), "grad": mitte(1), "rho": mitte(2),
            "rho_min": round(min(spalte(2)), 6), "rho_max": round(max(spalte(2)), 6), "abweichung": mitte(3), "innen": mitte(4), "quer": mitte(5)}


def entartung_hallen_a() -> list:
    """Rangkorrelation R gegen Gradterm auf den Hallen mit a verteilten Türen für die Hallenseiten der Ausfalltabelle."""
    erg = []
    for a in HALLEN_A:
        e = X.entartung(N.k_tueren(a, a))
        erg.append({"a": a, "rho": round(e.rho, 6)})
    return erg


# --- Netzausbau ------------------------------------------------------------------------------------------------------------------------

NETZE_AUSBAU = 40
NETZE_AUSBAU_DICHT = 20
DICHT_AUSBAU = (S.ER20, S.KNOTEN10, S.PUNKT5D)


def ausbau_zeile(netz: str, seed: int) -> dict:
    g = S.baue_ausbau(netz, seed)
    erg = X.ausbau(g)
    return {"netz": netz, "seed": seed, "n": g.n, "anteil": _rund(erg.anteil)}


def ausbau_pruefung(netz: str, seed: int) -> float:
    """Größte relative Abweichung der Formel gegen die Neuberechnung des Kirchhoff-Index an drei neuen Kanten."""
    import wdn_widerstand as W

    g = S.baue_ausbau(netz, seed)
    erg = X.ausbau(g)
    abw = 0.0
    for j in (0, len(erg.U) // 2, len(erg.U) - 1):
        h = N.mit_kante(g, int(erg.U[j]), int(erg.V[j]))
        neu = W.kirchhoff_index(W.pseudoinverse(h))
        abw = max(abw, abs((erg.ki - neu) - erg.senkung[j]) / erg.ki)
    return abw


def ausbau_dicht_zeile(familie: str, i: int) -> dict:
    g = S.baue(familie, N_TABELLE, 0, 0, "", TAB_SEED + i)
    erg = X.ausbau(g)
    rho = ST.rangkorrelation(erg.R, erg.gradterm)
    return {"familie": familie, "seed": TAB_SEED + i, "rho": round(rho, 6), "beste_senkung_anteil": round(float(erg.senkung.max() / erg.ki), 8),
            "anteil": _rund(erg.anteil)}


# --- Reparaturversuche -----------------------------------------------------------------------------------------------------------------

REP_N = 1000
REP_ANFRAGEN = 150
REP_SPRUNGGITTER = (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.15, 0.25, 0.35, 0.5, 0.65, 0.8, 0.9)
REP_ABSTIMM_SEEDS = (9100, 9101)                  # nur zum Wählen der Sprungwahrscheinlichkeit
REP_BEWERT_SEEDS = (TAB_SEED, TAB_SEED + 1, TAB_SEED + 2)
REP_FAELLE = ("torus3d", "torus5d", "torus2d", "gruppen20", "gruppen80")
REP_TEXT = {"torus3d": "Punktnetz auf dem 3D-Torus, mittlerer Grad 63", "torus5d": "Punktnetz auf dem 5D-Torus, mittlerer Grad 28",
            "torus2d": "Punktnetz auf dem 2D-Torus, mittlerer Grad 63", "gruppen20": "5 gepflanzte Gruppen, mittlerer Grad 20",
            "gruppen80": "5 gepflanzte Gruppen, mittlerer Grad 80"}
REP_PARAMETER = {"torus3d": ("torus", 3, 63), "torus5d": ("torus", 5, 28), "torus2d": ("torus", 2, 63), "gruppen20": ("gruppen", 5, 20),
                 "gruppen80": ("gruppen", 5, 80)}


def rep_guete(fall: str) -> str:
    return "p10" if REP_PARAMETER[fall][0] == "torus" else "auc"


def rep_netz(fall: str, seed: int):
    """(Netz, Wahrheit): beim Torus die Punktabstände, bei den Gruppen die Gruppe je Knoten. Abbruch, falls das Netz nicht zusammenhängt."""
    art, dim, grad = REP_PARAMETER[fall]
    netzseed = abgeleitet(seed, ZWECK_ANFRAGEN, 1000 + REP_FAELLE.index(fall))
    if art == "torus":
        g, D = N.punktnetz_mit_abstaenden(REP_N, grad, dim, netzseed, torus=True)
        wahr = D
    else:
        g, wahr = N.gruppennetz(REP_N, dim, grad, 0.6, netzseed)
    if not N.ist_zusammenhaengend(g):
        raise ValueError(f"Reparaturnetz {fall}, Zufalls-Seed {seed} hängt nicht zusammen")
    return g, wahr


def rep_anfragen(fall: str, seed: int) -> list:
    from wdn_rng import SplitMix64

    rng = SplitMix64(abgeleitet(seed, ZWECK_ANFRAGEN, REP_FAELLE.index(fall)))
    wahl = []
    while len(wahl) < REP_ANFRAGEN:
        q = rng.below(REP_N)
        if q not in wahl:
            wahl.append(q)
    return wahl


def rep_wahrheit(fall: str, wahr, i: int, andere: np.ndarray) -> np.ndarray:
    if REP_PARAMETER[fall][0] == "torus":
        naechste = andere[np.argsort(wahr[i, andere], kind="stable")[:10]]
        return np.isin(andere, naechste)
    return wahr[andere] == wahr[i]


def rep_ppr(b: X.Reparaturnetz, fall: str, wahr, anfragen, sprung: float) -> float:
    """Güte von PPR/Grad bei einer Sprungwahrscheinlichkeit."""
    ppr = M.ppr_grad_matrix(b.A, sprung)
    guete = rep_guete(fall)
    n = len(b.A)
    werte = []
    for i in anfragen:
        andere = np.delete(np.arange(n), i)
        werte.append(X.bewerte(-np.round(ppr[i, andere], 13), rep_wahrheit(fall, wahr, i, andere), guete))
    return float(np.mean(werte))


def rep_netzwerte(fall: str, seed: int, spruenge: dict) -> dict:
    """Güte je Maß auf einem Bewertungsnetz; `spruenge`: Name → Sprungwahrscheinlichkeit für PPR/Grad (Voreinstellung und abgestimmt)."""
    g, wahr = rep_netz(fall, seed)
    b = X.reparatur_bausteine(g)
    anfragen = rep_anfragen(fall, seed)
    guete = rep_guete(fall)
    ppr = {name: M.ppr_grad_matrix(b.A, s) for name, s in spruenge.items()}
    erg = {}
    for i in anfragen:
        andere = np.delete(np.arange(g.n), i)
        w = rep_wahrheit(fall, wahr, i, andere)
        schluessel = X.zeilenschluessel(b, ppr["voreinstellung"], i, andere)
        for name in spruenge:
            schluessel[f"ppr_{name}"] = -np.round(ppr[name][i, andere], 13)
        del schluessel[M.PPR]
        for m, v in schluessel.items():
            erg.setdefault(m, []).append(X.bewerte(v, w, guete))
    I, J = np.nonzero(np.triu(1 - b.A, 1))
    schritt = max(1, len(I) // 120_000)
    I, J = I[::schritt], J[::schritt]
    bezug = {"rho_r_gradterm": ST.rangkorrelation(b.R[I, J], b.gt[I, J]), "rho_verst_gradterm": ST.rangkorrelation(b.verst[I, J], b.gt[I, J]),
             "abweichung_r_gradterm": float(np.median(np.abs(b.R[I, J] - b.gt[I, J]) / b.R[I, J]))}
    return {"n": g.n, "m": len(g.kanten), "guete": {m: float(np.mean(v)) for m, v in erg.items()}, "bezug": bezug}
