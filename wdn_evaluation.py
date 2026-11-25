"""Verdikte als reine Funktionen (Art, Text) und Zahlformate (ohne Streamlit)."""

import wdn_experimente as X
import wdn_masse as M
import wdn_statistik as ST

ENTARTET_AB = 0.95          # Schwelle dieser Seite: ab dieser Rangkorrelation „ordnet fast wie der Gradterm“
ANDERS_UNTER = 0.7          # darunter „ordnet anders“

URTEIL_TEXT = {ST.R_VORN: "R klar vorn", ST.GEGNER_VORN: "Gegner klar vorn", ST.UNKLAR: "kein klarer Unterschied"}


def zahl(x, stellen: int = 2) -> str:
    """Deutsche Schreibweise mit Komma; Minuszeichen als echtes Minus; None als „nicht bestimmbar“."""
    if x is None:
        return "nicht bestimmbar"
    text = f"{abs(x):,.{stellen}f}".replace(",", " ").replace(".", ",")
    return ("−" if x < 0 and float(text.replace(" ", "").replace(",", ".")) != 0 else "") + text


def prozent(anteil, stellen: int = 1) -> str:
    return zahl(None if anteil is None else 100 * anteil, stellen) + (" %" if anteil is not None else "")


def p_text(p: float) -> str:
    return zahl(p, 2)


def urteil(zeile: dict, gegner: str) -> int:
    """R gegen einen Gegner in einer Netz-p-Zelle nach dem Klar-Kriterium."""
    r1, r2 = zeile["rho1"], zeile["rho2"]
    return ST.klar(r1[M.WIDERSTAND], r2[M.WIDERSTAND], r1[gegner], r2[gegner])


def _vergleich(zeile: dict, gegner: str) -> str:
    return f"{zahl(zeile['rho1'][gegner])} (zweite Stichprobe {zahl(zeile['rho2'][gegner])})"


def _gegner_satz(zeile: dict, gegner: str, akkusativ: str, nominativ: str) -> str:
    u = urteil(zeile, gegner)
    worte = {ST.R_VORN: "R klar vorn", ST.GEGNER_VORN: f"{nominativ} klar vorn", ST.UNKLAR: "kein klarer Unterschied"}[u]
    return f"gegen {akkusativ} {_vergleich(zeile, gegner)}: {worte}"


def verdict_ausfall(zeile: dict) -> tuple:
    """Verdikt von Experiment 1. `zeile` hat 'messbar', 'rho1', 'rho2' (je Maß → Rangkorrelation oder None)."""
    if not zeile["messbar"]:
        return ("warning", "**Nicht messbar:** Mindestens 95 % der Paare haben in einer der zwei Wahrheitsstichproben dieselbe Trennwahrscheinlichkeit; "
                           "es gibt keine Rangfolge, die ein Maß treffen könnte.")
    d, g = urteil(zeile, M.DISTANZ), urteil(zeile, M.GRADTERM)
    r = zeile["rho1"][M.WIDERSTAND]
    kopf = f"R erreicht die Rangkorrelation {_vergleich(zeile, M.WIDERSTAND)}. "
    if d == ST.R_VORN and g == ST.R_VORN:
        art, satz = "success", "**R ist klar vor der Distanz und vor dem Gradterm.**"
    elif d == ST.R_VORN:
        art = "info"
        if g == ST.GEGNER_VORN:
            satz = "**R ist klar vor der Distanz, nicht vor den Graden:** der Gradterm ist klar vor R."
        else:
            # kein klarer Unterschied: R kann dabei vor oder hinter dem Gradterm liegen
            satz = "**R ist klar vor der Distanz, nicht klar vor den Graden:** zum Gradterm gibt es keinen klaren Unterschied."
    elif d == ST.GEGNER_VORN:
        art, satz = "warning", "**R liegt klar hinter der kürzesten Distanz.**"
    else:
        art = "info"
        satz = "**Kein klarer Unterschied zwischen R und der Distanz.**"
        dist = zeile["rho1"][M.DISTANZ]
        if r is not None and dist is not None and r < dist and zeile["rho2"][M.WIDERSTAND] < zeile["rho2"][M.DISTANZ]:
            satz += " R liegt in beiden Stichproben dahinter, aber nicht in beiden um mindestens 0,05."
    teile = [_gegner_satz(zeile, M.DISTANZ, "die Distanz", "die Distanz"), _gegner_satz(zeile, M.GRADTERM, "den Gradterm", "der Gradterm"),
             _gegner_satz(zeile, M.MINCUT, "den min cut", "der min cut"), _gegner_satz(zeile, M.STICH200, "die 200er-Stichprobe", "die 200er-Stichprobe")]
    return art, kopf + satz + " Einzeln: " + "; ".join(teile) + ". („Klar“ heißt: in beiden Wahrheitsstichproben dasselbe Vorzeichen und mindestens 0,05 Abstand.)"


def verdict_entartung(n: int, grad: float, rho, abweichung: float) -> tuple:
    """Verdikt von Experiment 2: Rangfolge und Wertfehler getrennt."""
    if rho is None:
        return ("warning", f"In diesem Netz ({n} Knoten, mittlerer Grad {zahl(grad, 1)}) haben alle Nichtnachbarpaare denselben R-Wert oder denselben Gradterm; "
                           "eine Rangkorrelation ist nicht bestimmbar.")
    if rho >= ENTARTET_AB:
        art, kopf = "warning", "**R ordnet die Nichtnachbarn hier fast wie die zwei Endgrade** (Schwelle dieser Seite: ab 0,95)."
    elif rho < ANDERS_UNTER:
        art, kopf = "success", "**R ordnet die Nichtnachbarn hier anders als die zwei Endgrade** (Schwelle dieser Seite: unter 0,70)."
    else:
        art, kopf = "info", "**R und die zwei Endgrade ordnen die Nichtnachbarn hier ähnlich, aber nicht fast gleich** (zwischen den Schwellen 0,70 und 0,95)."
    return art, (f"{kopf} In diesem Netz ({n} Knoten, mittlerer Grad {zahl(grad, 1)}) ist die Rangkorrelation von R mit dem Gradterm 1/d_u + 1/d_v über die "
                 f"Nichtnachbarn {zahl(rho, 3)}; der Wert von R weicht im Median um {prozent(abweichung)} vom Gradterm ab. Das sagt noch nichts darüber, wie "
                 "gut R den Ausfall vorhersagt (Experiment 1).")


def verdict_ausbau(anteile: dict, regel: str, name_regel: str) -> tuple:
    """Verdikt von Experiment 3 an den erreichten Anteilen (Regel → Anteil oder None)."""
    r, dist, grad = anteile[X.MAX_R], anteile[X.MAX_DISTANZ], anteile[X.MAX_GRADTERM]
    andere = [v for k, v in anteile.items() if k not in (X.MAX_R, X.ZUFAELLIG) and v is not None]
    besser = [v for v in andere if v > r + 1e-9]
    if r >= 1 - 1e-9:
        art, zusatz = "success", "„Größtes R“ trifft hier eine beste Kante."
    elif not besser:
        art, zusatz = "success", "Keine der anderen Regeln ist hier besser als „größtes R“."
    else:
        art, zusatz = "info", f"{len(besser)} andere Regel{'n sind' if len(besser) != 1 else ' ist'} hier besser als „größtes R“."
    text = (f"Hier erreicht „größtes R“ {prozent(r)} der besten Senkung, die Distanzregel {prozent(dist)}, der Gradterm {prozent(grad)}. {zusatz}")
    if regel not in (X.MAX_R, X.MAX_DISTANZ, X.MAX_GRADTERM):
        text += f" Die gewählte Regel „{name_regel}“ erreicht {prozent(anteile[regel])}."
    return art, text


def verdict_reparatur(fall: dict) -> tuple:
    """Verdikt von Experiment 4 aus den vorgerechneten Güten eines Falls."""
    m = fall["mittel"]
    verst, dist = m[M.VERSTAERKT], m[M.DISTANZ]
    zaehl = max((M.ADAMIC, M.DIST_WEGE), key=lambda k: m[k])
    name = {M.ADAMIC: "Adamic-Adar", M.DIST_WEGE: "Distanz, dann Wegezahl"}[zaehl]
    mass = "P@10" if fall["guete"] == "p10" else "AUC"
    if verst > dist + 1e-9:
        art, lage = "success", "sie liegt über der Distanz"
    elif verst < dist - 1e-9:
        art, lage = "warning", "sie liegt unter der Distanz"
    else:
        art, lage = "info", "sie liegt gleichauf mit der Distanz"
    stelle = "über" if verst > m[zaehl] + 1e-9 else "unter" if verst < m[zaehl] - 1e-9 else "gleichauf mit"
    return art, (f"Auf diesem Netz erreicht die verstärkte Widerstandsdistanz {mass} {zahl(verst)} (Distanz: {zahl(dist)}, beste Zählregel „{name}“: "
                 f"{zahl(m[zaehl])}); {lage} und {stelle} der Zählregel. R ohne Korrektur: {zahl(m[M.WIDERSTAND])}.")


def verdict_reparatur_ausfall(zeile: dict, netz_name: str) -> tuple:
    """Zweiter Satz von Experiment 4: dieselben Maße beim Ausfall auf dem in Experiment 1 gezeigten Netz."""
    if not zeile["messbar"]:
        return "info", f"Beim Ausfall auf dem in Experiment 1 gezeigten Netz ({netz_name}) ist die Zielgröße nicht messbar."
    v, r = zeile["rho1"][M.VERSTAERKT], zeile["rho1"][M.WIDERSTAND]
    return "info", (f"Beim Ausfall auf dem in Experiment 1 gezeigten Netz ({netz_name}) liegt die verstärkte Widerstandsdistanz bei {zahl(v)} gegen R mit "
                    f"{zahl(r)} (Rangkorrelation mit der Trennwahrscheinlichkeit, Stichprobe 1).")


def verdict_leitung(p: float, p_leitung: float, p_wege: float) -> tuple:
    """Eine Leitung (R = 1) gegen drei Wege der Länge 4 (R = 4/3)."""
    werte = f"Bei Ausfallrate {p_text(p)}: eine Leitung (R = 1) ist mit {prozent(p_leitung, 2)} getrennt, die drei Wege (R = 4/3) mit {prozent(p_wege, 2)}."
    if p_wege < p_leitung - 1e-12:
        return "info", werte + " **Das Netz mit dem größeren R wird seltener getrennt.**"
    if p_wege > p_leitung + 1e-12:
        return "info", werte + " **Das Netz mit dem größeren R wird häufiger getrennt.**"
    return "info", werte + " Beide werden gleich oft getrennt."


def kernfrage_distanz(zeile: dict, zaehl: dict, gruppe_name: str) -> tuple:
    """Kernfrage 1: R gegen die Distanz, aktuelle Zelle und vorgerechnete Familie."""
    familie = f"In den vorgerechneten Zellen „{gruppe_name}“ lag R in {zaehl['r_vorn']} von {zaehl['messbar']} messbaren Netz-p-Zellen vor der Distanz."
    if not zeile["messbar"]:
        return "warning", "Auf dem gewählten Netz ist die Frage nicht messbar. " + familie
    u = urteil(zeile, M.DISTANZ)
    art = {ST.R_VORN: "success", ST.GEGNER_VORN: "warning", ST.UNKLAR: "info"}[u]
    return art, (f"Auf dem gewählten Netz: {URTEIL_TEXT[u] if u != ST.GEGNER_VORN else 'Distanz klar vorn'} (R {zahl(zeile['rho1'][M.WIDERSTAND])}, "
                 f"Distanz {zahl(zeile['rho1'][M.DISTANZ])}). " + familie)


def kernfrage_grade(zeile: dict, zaehl: dict, gruppe_name: str) -> tuple:
    """Kernfrage 2: R gegen die zwei Endgrade."""
    familie = (f"In den vorgerechneten Zellen „{gruppe_name}“ lag R in {zaehl['r_vorn']} von {zaehl['messbar']} messbaren Netz-p-Zellen vor dem Gradterm; "
               f"klar vorn war R in {zaehl['klar_r']}, der Gradterm in {zaehl['klar_gegner']}.")
    if not zeile["messbar"]:
        return "warning", "Auf dem gewählten Netz ist die Frage nicht messbar. " + familie
    u = urteil(zeile, M.GRADTERM)
    art = {ST.R_VORN: "success", ST.GEGNER_VORN: "warning", ST.UNKLAR: "info"}[u]
    return art, (f"Auf dem gewählten Netz: {URTEIL_TEXT[u] if u != ST.GEGNER_VORN else 'Gradterm klar vorn'} (R {zahl(zeile['rho1'][M.WIDERSTAND])}, "
                 f"Gradterm {zahl(zeile['rho1'][M.GRADTERM])}). " + familie)
