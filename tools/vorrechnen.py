"""Rechnet die gespeicherten Tabellen der Demo neu und schreibt daten/vorgerechnet.json.

Aufruf (im Demo-Ordner): python tools/vorrechnen.py [ausfall] [entartung] [ausbau] [reparatur]   (ohne Angabe alles, einzeln ergänzbar)
Alle Zufalls-Seeds stehen in `wdn_tabellen.py`. Gemessen mit OMP_NUM_THREADS=1: zusammen wenige Minuten."""

import json
import sys
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))

import numpy as np  # noqa: E402

import wdn_szenario as S  # noqa: E402
import wdn_tabellen as T  # noqa: E402

ZIEL = WURZEL / "daten" / "vorgerechnet.json"


def ausfall() -> dict:
    zeilen = []
    for block in ("hallen", "kontrast", "dicht"):
        for gruppe in T.gruppen_block(block):
            start = time.time()
            for inst in T.instanzen(gruppe):
                zeilen += [dict(z, block=block) for z in T.ausfall_zeilen(gruppe, inst)]
            print(f"  Ausfall {gruppe}: {time.time() - start:.1f} s", flush=True)
    return {"zeilen": zeilen}


def entartung() -> dict:
    zeilen = []
    for familie in S.ENTARTUNG:
        for n in S.E_GROESSEN:
            start = time.time()
            zeilen.append(T.entartung_zeile(familie, n))
            print(f"  Entartung {familie} {n}: {time.time() - start:.1f} s", flush=True)
    return {"zeilen": zeilen, "hallen_a": T.entartung_hallen_a()}


def ausbau() -> dict:
    zeilen, pruefung = [], 0.0
    for netz in S.X_NETZE:
        anzahl = T.NETZE_AUSBAU if netz in S.X_ZUFALL else 1
        for i in range(anzahl):
            zeilen.append(T.ausbau_zeile(netz, T.TAB_SEED + i))
        pruefung = max(pruefung, T.ausbau_pruefung(netz, T.TAB_SEED))
        print(f"  Ausbau {netz}", flush=True)
    dicht = [T.ausbau_dicht_zeile(f, i) for f in T.DICHT_AUSBAU for i in range(T.NETZE_AUSBAU_DICHT)]
    return {"zeilen": zeilen, "dicht": dicht, "pruefung_max_relativ": float(pruefung)}


def reparatur() -> dict:
    faelle = {}
    for fall in T.REP_FAELLE:
        start = time.time()
        gitter = np.zeros(len(T.REP_SPRUNGGITTER))
        for seed in T.REP_ABSTIMM_SEEDS:
            g, wahr = T.rep_netz(fall, seed)
            import wdn_experimente as X

            b = X.reparatur_bausteine(g)
            anfragen = T.rep_anfragen(fall, seed)
            gitter += [T.rep_ppr(b, fall, wahr, anfragen, s) for s in T.REP_SPRUNGGITTER]
        gitter /= len(T.REP_ABSTIMM_SEEDS)
        gewaehlt = T.REP_SPRUNGGITTER[int(np.argmax(gitter))]
        netze = [T.rep_netzwerte(fall, seed, {"voreinstellung": 0.15, "abgestimmt": gewaehlt}) for seed in T.REP_BEWERT_SEEDS]
        mittel = {m: round(float(np.mean([x["guete"][m] for x in netze])), 6) for m in netze[0]["guete"]}
        spanne = {m: [round(min(x["guete"][m] for x in netze), 6), round(max(x["guete"][m] for x in netze), 6)] for m in netze[0]["guete"]}
        bezug = {k: round(float(np.mean([x["bezug"][k] for x in netze])), 6) for k in netze[0]["bezug"]}
        faelle[fall] = {"guete": T.rep_guete(fall), "netze": len(netze), "m_mittel": int(np.mean([x["m"] for x in netze])), "mittel": mittel,
                        "spanne": spanne, "bezug": bezug, "sprung_abgestimmt": gewaehlt,
                        "sprung_gitter": [round(float(v), 6) for v in gitter],
                        "sprung_am_rand": bool(gewaehlt in (T.REP_SPRUNGGITTER[0], T.REP_SPRUNGGITTER[-1]))}
        print(f"  Reparatur {fall}: {time.time() - start:.1f} s, Sprung {gewaehlt}", flush=True)
    return {"faelle": faelle}


TEILE = {"ausfall": ausfall, "entartung": entartung, "ausbau": ausbau, "reparatur": reparatur}


def main():
    wahl = sys.argv[1:] or list(TEILE)
    ZIEL.parent.mkdir(exist_ok=True)
    daten = json.loads(ZIEL.read_text(encoding="utf-8")) if ZIEL.exists() else {}
    start = time.time()
    for teil in wahl:
        t = time.time()
        daten[teil] = TEILE[teil]()
        ZIEL.write_text(json.dumps(daten, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
        print(f"{teil}: {time.time() - t:.1f} s", flush=True)
    print(f"geschrieben: {ZIEL} ({time.time() - start:.1f} s)")


if __name__ == "__main__":
    main()
