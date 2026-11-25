"""Widerstand als Netzmaß - wann sagt er mehr als die zwei Grade? - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Kanten eines Netzes fallen zufällig aus. Wie gut sagt der effektive Widerstand R voraus, welche Knotenpaare dabei getrennt werden, und wie schneidet er gegen
kürzeste Distanz, min cut und die zwei Endgrade ab? Dazu: wann R nur noch die Grade ordnet, welche neue Leitung er wählt und was Reparaturversuche bringen.
Aufbau und Regeln stehen im DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import numpy as np
import streamlit as st

import wdn_ausfall as AF
import wdn_constants as C
import wdn_daten as D
import wdn_evaluation as E
import wdn_experimente as X
import wdn_karte as K
import wdn_masse as M
import wdn_netze as N
import wdn_szenario as S
import wdn_tabellen as T
from wdn_layout import dunkles_design, kopf_css
from wdn_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    merke,
    randomize_seed,
    seed_widget,
    sidebar_presets,
    sync_query_params,
    wert,
)
from wdn_visualization import (
    balken_ausbau,
    balken_rangkorrelation,
    balken_reparatur,
    entartung_streubild,
    streubild,
    verteilung_ausbau,
)

st.set_page_config(page_title="Widerstand als Netzmaß – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _daten():
    return D.laden()


@st.cache_data(show_spinner=False, max_entries=12)
def _netzmasse(familie, n, a, tueren, verbund, seed):
    g = S.baue(familie, n, a, tueren, verbund, seed)
    return g, X.netzmasse(g, seed, S.FAMNR[familie])


@st.cache_data(show_spinner=False, max_entries=36)
def _zelle(familie, n, a, tueren, verbund, seed, p):
    g, nm = _netzmasse(familie, n, a, tueren, verbund, seed)
    p_werte = S.P_DICHT if S.ist_dicht(familie) else S.P_DUENN
    return X.ausfallzelle(g, nm, p, p_werte.index(p), seed, S.FAMNR[familie])


@st.cache_data(show_spinner=False, max_entries=8)
def _entartung(familie, n, seed):
    g = S.baue_entartung(familie, n, seed)
    return X.entartung(g, haelften=familie == S.E_HAELFTEN)


@st.cache_data(show_spinner=False, max_entries=30)
def _ausbau(netz, seed):
    g = S.baue_ausbau(netz, seed)
    return g, X.ausbau(g)


@st.cache_data(show_spinner=False)
def _handnetz_aufhaenger():
    """Exakte Werte am Handnetz bei Ausfallrate 0,15 (eine und zwei Türen)."""
    erg = {}
    for tueren in (1, 2):
        g = N.handnetz(tueren)
        paare = AF.alle_paare(6)
        wahr = AF.exakt(g, paare, 0.15)
        nm = X.netzmasse(g, 0, 0, anzahl=15, extra=False)
        A = N.adjazenz(g)
        werte = dict(nm.werte)
        werte[M.ISOLATION] = M.isolation(A.sum(axis=1), paare[:, 0], paare[:, 1], A[paare[:, 0], paare[:, 1]], 0.15)
        erg[tueren] = {"paare": [tuple(int(x) for x in q) for q in paare], "wahr": wahr, "R": nm.R, "iso": werte[M.ISOLATION], "grad": nm.grad,
                       "zaehlung": {m: X.ordnungszaehlung(werte[m], wahr) for m in (M.WIDERSTAND, M.DISTANZ, M.MINCUT, M.MINCUT_DIST, M.GRADTERM,
                                                                                     M.ISOLATION)}}
    return erg


def z(x, stellen=2):
    return E.zahl(x, stellen)


def tabelle(kopf, zeilen):
    """Markdown-Tabelle (scrollt auf dem Telefon über das Stylesheet unten)."""
    teile = ["| " + " | ".join(kopf) + " |", "|" + "---|" * len(kopf)]
    teile += ["| " + " | ".join(str(c) for c in zeile) + " |" for zeile in zeilen]
    st.markdown("\n".join(teile))


daten = _daten()

# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in wdn_layout.py).
st.html(kopf_css(dunkles_design()))
st.html('<style>[data-testid="stMarkdownContainer"] table { display: block; overflow-x: auto; max-width: 100%; }</style>')
with st.container(key="kopf"):
    st.title("🔌 Widerstand als Netzmaß – wann sagt er mehr als die zwei Grade?")
st.markdown(
    """
Die Demo „Pendelzeit“ zeigt, dass ein Anhang abseits der Strecke die Pendelzeit verlängert und den **effektiven Widerstand R** unverändert lässt, prüft aber
nicht, was R über zwei Orte vorhersagt. Diese Demo stellt R bei zufälligem **Kantenausfall** gegen kürzeste Distanz, **min cut** und die zwei Endgrade (die
**Isolationsnäherung** kennt zusätzlich die Ausfallrate und ob die zwei Orte benachbart sind) und zeigt, auf welchen Netzen R Nichtnachbarn kaum anders
ordnet als die Grade. Sie gehört zur Reihe „Irrfahrten auf Netzen“.

Weiter unten: **❓ Kernfragen**, vier **🔬 Experimente**, **🚧 Wo die Annahmen enden** und die Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und
**📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert der Widerstand als Netzmaß", expanded=True):
    st.markdown(
        """
1. **Ausfall.** Jede Kante fällt unabhängig mit der Ausfallrate p aus. Gesucht ist, mit welcher Wahrscheinlichkeit zwei Orte s und t danach **getrennt** sind.
   Auf dem Handnetz wird das exakt gezählt; auf den größeren Netzen schätzen es zwei unabhängige **Wahrheitsstichproben** mit je 1 600 Ausfallmustern.
2. **Effektiver Widerstand.** Jede Kante ist ein Widerstand von 1 Ohm; R ist der Widerstand zwischen s und t. Viele und kurze Wege machen R klein. R ist die
   Pendelzeit geteilt durch 2m (m Zahl der Kanten, Demo „Pendelzeit“); die Ausfallrate kennt R nicht.
3. **Gegner.** Kürzeste Distanz, min cut (so viele Kanten muss man mindestens wegnehmen, um s und t zu trennen), der **Gradterm** 1/d_s + 1/d_t aus den zwei
   Nachbarzahlen, die Isolationsnäherung und eine eigene kleine Ausfallstichprobe mit 50 oder 200 Proben.
4. **Güte.** Für 300 zufällige Knotenpaare (auf kleineren Netzen alle) misst die **Rangkorrelation** (Spearman), wie gut die Reihenfolge eines Maßes zur
   Reihenfolge der Trennwahrscheinlichkeiten passt (1 = gleiche Reihenfolge, 0 = kein Zusammenhang).
        """
    )
st.markdown(
    "Zum Gradterm: Addiert man H(u,v) ≈ 2m/d_v und H(v,u) ≈ 2m/d_u und teilt durch 2m, steht der Gradterm 1/d_u + 1/d_v da: dieselbe Näherung wie in der "
    "Demo „Trefferzeit“. Ob R mehr sagt als diese zwei Zahlen, hängt am Netz."
)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("🧩 Experiment 1: Netz und Ausfall")
    st.selectbox("Netzfamilie", S.FAMILIEN, key="netz", format_func=S.FAMILIE_TEXT.get, help="Hallen sind fest gebaut; die übrigen Netze zieht der Zufalls-Seed.")
    netz = st.session_state["netz"]
    if netz == S.HALLEN:
        seed_widget("a")
        st.slider("Hallenseite a", *bounds("a"), key="a", help="Jede Halle ist ein Gitter a×a, zusammen 2a² Knoten (72 bis 200).")
        merke("a")
        seed_widget("tueren")
        st.selectbox("Türfamilie", S.TUEREN, key="tueren", format_func=S.TUEREN_TEXT.get,
                     help="k Türen in gleichmäßig verteilten Zeilen. Eine eigene Netzfamilie je k, keine Ergänzung der einen Tür.")
        merke("tueren")
    elif netz == S.VERBUND:
        seed_widget("verbund")
        st.selectbox("Verbund", tuple(S.VERBUND_VARIANTEN), key="verbund", format_func=S.VERBUND_TEXT.get)
        merke("verbund")
    else:
        seed_widget("n")
        st.slider("Zahl der Knoten n", *bounds("n"), key="n", step=C.N_STEP, help="Vor dem Beschränken auf die größte zusammenhängende Komponente.")
        merke("n")
    if S.ist_dicht(netz):
        seed_widget("pd")
        st.radio("Ausfallrate p", S.P_DICHT, key="pd", format_func=E.p_text, horizontal=True, help="Jede Kante fällt unabhängig mit dieser Wahrscheinlichkeit aus.")
        merke("pd")
    else:
        seed_widget("p")
        st.radio("Ausfallrate p", S.P_DUENN, key="p", format_func=E.p_text, horizontal=True, help="Jede Kante fällt unabhängig mit dieser Wahrscheinlichkeit aus.")
        merke("p")
    st.number_input("Zufalls-Seed", *bounds("seed"), key="seed", step=1,
                    help="Wählt die Knotenpaare, die Ausfallproben und (außer bei den Hallen) das Netz; auch für die Netze der Experimente 2 und 3.")
    st.button("🎲 Neuen Zufalls-Seed ziehen", width="stretch", on_click=randomize_seed)

    st.header("📉 Experiment 2: Entartung")
    st.selectbox("Netz (Entartung)", S.ENTARTUNG, key="e_netz", format_func=S.E_TEXT.get)
    st.radio("Größe (Entartung)", S.E_GROESSEN, key="e_n", horizontal=True,
             format_func=lambda n: f"{n:,}".replace(",", " "), help="Bei den Hallen heißt das Seite a = 10, 16 oder 22 (200, 512, 968 Knoten).")

    st.header("🔧 Experiment 3: neue Leitung")
    st.selectbox("Netz (Ausbau)", S.X_NETZE, key="x_netz", format_func=S.X_TEXT.get, help="Netze mit höchstens 81 Knoten; alle fehlenden Kanten werden exakt bewertet.")
    _, ab_vorschau = _ausbau(st.session_state["x_netz"], int(st.session_state["seed"]))
    regeln = [r for r in X.REGELN if ab_vorschau.anteil[r] is not None]
    if st.session_state["x_regel"] not in regeln:
        st.session_state["x_regel"] = X.MAX_R
    st.session_state["x_regel"] = st.session_state["x_regel"]
    st.selectbox("Regel", regeln, key="x_regel", format_func=C.REGEL_TEXT.get,
                 help="Welche Regel die neue Leitung wählt. Die Fiedler-Regel fehlt auf Netzen mit doppeltem zweitem Eigenwert.")

    st.header("🩹 Experiment 4: Reparatur")
    st.selectbox("Dichtes Netz (Reparatur)", T.REP_FAELLE, key="r_netz", format_func=T.REP_TEXT.get, help="Vorgerechnet mit 1 000 Knoten.")

aktuell = {key: wert(key) for key in ("netz", "a", "tueren", "verbund", "n", "p", "pd", "seed", "e_netz", "e_n", "x_netz", "x_regel", "r_netz")}
sync_query_params(aktuell)
seed = int(aktuell["seed"])
netz = aktuell["netz"]
p = float(aktuell["pd"] if S.ist_dicht(netz) else aktuell["p"])
# Nur die Einstellungen, die das gewählte Netz beeinflussen, gehen in den Zwischenspeicher ein.
schluessel = (netz, int(aktuell["n"]) if netz not in (S.HALLEN, S.VERBUND) else 0, int(aktuell["a"]) if netz == S.HALLEN else 0,
              int(aktuell["tueren"]) if netz == S.HALLEN else 0, aktuell["verbund"] if netz == S.VERBUND else "", seed)

with st.spinner("Ziehe Ausfallmuster und rechne die Maße (bis zu wenige Sekunden) …"):
    g, nm = _netzmasse(*schluessel)
    zelle = _zelle(*schluessel, p)
zeile = X.zeile(zelle)

if netz == S.HALLEN:
    tueren_n = S.anzahl_tueren(int(aktuell["a"]), int(aktuell["tueren"]))
    netz_name = f"zwei Hallen {aktuell['a']}×{aktuell['a']} mit {tueren_n} {'Tür' if tueren_n == 1 else 'verteilten Türen'}"
    gruppe = {1: "hallen1", 2: "hallen2", 4: "hallen4", 0: "hallen_a"}[int(aktuell["tueren"])]
else:
    netz_name = S.VERBUND_TEXT[aktuell["verbund"]] if netz == S.VERBUND else S.FAMILIE_KURZ[netz]
    gruppe = netz
netz_info = f"{netz_name}: {g.n} Knoten, {len(g.kanten)} Kanten, mittlerer Grad {z(2 * len(g.kanten) / g.n, 1)}"

with st.spinner("Rechne Entartung (bei 1 000 Knoten wenige Sekunden) …"):
    ent = _entartung(aktuell["e_netz"], int(aktuell["e_n"]), seed)
g_aus, aus = _ausbau(aktuell["x_netz"], seed)
regel = aktuell["x_regel"]

# --- Kernfragen ------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfragen")
st.caption(f"Live auf den gewählten Netzen (Experiment 1: {netz_info}; Ausfallrate {E.p_text(p)}, {len(nm.paare)} Knotenpaare). Voraussetzungen überall: "
           "ungewichtete Netze, Kanten fallen unabhängig und gleich wahrscheinlich aus, Zielgröße nur die Trennung eines Paars. Die vorgerechneten Zählungen "
           "gelten für Hallen mit a = 6, 8, 10, den Verbund und für die übrigen Familien mit 150 Knoten vor der größten Komponente.")
gruppen_zellen = D.zellen(daten, gruppe=gruppe)
st.markdown("**1. Sagt R mehr über das Zerreißen als die kürzeste Distanz?**")
art, text = E.kernfrage_distanz(zeile, D.zaehlung(gruppen_zellen, M.DISTANZ), C.GRUPPEN_TEXT[gruppe])
getattr(st, art)(text)
st.markdown("**2. Und mehr als die zwei Grade an den Enden?**")
art, text = E.kernfrage_grade(zeile, D.zaehlung(gruppen_zellen, M.GRADTERM), C.GRUPPEN_TEXT[gruppe])
getattr(st, art)(text)
st.markdown("**3. Ab wann ordnet R nur noch die Grade?**")
art, text = E.verdict_entartung(ent.n, ent.mittlerer_grad, ent.rho, ent.abweichung)
getattr(st, art)(f"Netz aus Experiment 2 ({S.E_TEXT[aktuell['e_netz']]}): " + text)
st.markdown("**4. Wählt R die bessere neue Leitung?**")
art, text = E.verdict_ausbau(aus.anteil, regel, C.REGEL_KURZ[regel])
getattr(st, art)(f"Netz aus Experiment 3 ({S.X_TEXT[aktuell['x_netz']]}): " + text)

st.markdown("---")

# --- Experiment 1 ------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Wer sieht den Ausfall kommen?")
st.markdown("**Zwei Paare mit denselben Graden** (Handnetz „zwei Hallen“ mit einer Tür 2–3, Ausfallrate 0,15, exakt über alle 2⁷ Ausfallmuster):")
hand = _handnetz_aufhaenger()
eins = hand[1]
links, rechts = st.columns([1, 1.3])
with links:
    st.plotly_chart(K.karte(N.handnetz(1), hoehe=230, beschriftung=True), width="stretch", key="hand_karte")
with rechts:
    i01, i04 = eins["paare"].index((0, 1)), eins["paare"].index((0, 4))
    tabelle(["Paar", "Grade", "Gradterm", "ein Ende ohne Kante", "P(getrennt)", "R"],
            [["(0,1)", "2, 2", "1", z(eins["iso"][i01], 3), E.prozent(eins["wahr"][i01]), "2/3"],
             ["(0,4)", "2, 2", "1", z(eins["iso"][i04], 3), E.prozent(eins["wahr"][i04]), "7/3"]])
    st.markdown("Gradterm und Grade sind gleich, R ist 3,5-mal so groß, und (0,4) wird viel öfter getrennt. Dass ein Ende ohne Kante dasteht "
                "(die Isolationsnäherung), ist für beide Paare fast gleich wahrscheinlich.")
with st.expander("Alle 15 Paare des Handnetzes: wie oft ordnet ein Maß zwei Paare richtig?"):
    namen = [M.WIDERSTAND, M.DISTANZ, M.MINCUT, M.MINCUT_DIST, M.GRADTERM, M.ISOLATION]
    tabelle(["Maß (Handnetz, p = 0,15)", "eine Tür: richtig / falsch / gleich bewertet", "zwei Türen: richtig / falsch / gleich bewertet"],
            [[C.MASS_TEXT[m], " / ".join(str(v) for v in hand[1]["zaehlung"][m]), " / ".join(str(v) for v in hand[2]["zaehlung"][m])] for m in namen])
    i04z = hand[2]["paare"].index((0, 4))
    st.markdown(f"Gezählt werden alle Vergleiche zweier Paare mit verschiedener Trennwahrscheinlichkeit. Mit der zweiten Tür 5–0 sinkt P(0–4 getrennt) auf "
                f"{E.prozent(hand[2]['wahr'][i04z])}. Dass R hier jeden Vergleich richtig ordnet, ist eine Eigenschaft dieses Netzes, kein Satz: das Beispiel "
                "„Leitung gegen drei Wege“ weiter unten zeigt ein Gegenbeispiel.")

st.markdown(f"**Gewähltes Netz: {netz_info}; Ausfallrate {E.p_text(p)}.** Je Wahrheitsstichprobe 1 600 Ausfallmuster, {len(nm.paare)} Knotenpaare.")
if len(g.kanten) <= 700:
    with st.expander("Karte des gewählten Netzes"):
        st.plotly_chart(K.karte(g, hoehe=360), width="stretch", key="netz_karte")
st.radio("Vorhersager im Streubild", C.STREU_MASSE, key="streu_mass", format_func=C.MASS_KURZ.get, horizontal=True)
mass = st.session_state["streu_mass"]
S_, T_ = nm.paare[:, 0], nm.paare[:, 1]
x_werte = {M.WIDERSTAND: nm.R, M.DISTANZ: nm.D, M.MINCUT: -nm.werte[M.MINCUT], M.GRADTERM: nm.werte[M.GRADTERM], M.ISOLATION: zelle.isolation,
           M.STICH200: zelle.klein[200]}[mass]
spalte1, spalte2 = st.columns(2)
with spalte1:
    st.plotly_chart(streubild(x_werte, zelle.y1, C.MASS_TEXT[mass] + (" (Zahl der Kanten)" if mass == M.MINCUT else "")), width="stretch", key="streu_chart")
    st.caption("Ein Punkt je Knotenpaar; senkrecht der Anteil der Ausfallmuster (Wahrheitsstichprobe 1), in denen das Paar getrennt ist."
               + (" Beim min cut heißt größer: seltener getrennt." if mass == M.MINCUT else ""))
with spalte2:
    if zelle.messbar:
        st.plotly_chart(balken_rangkorrelation(zeile), width="stretch", key="balken_chart")
        st.caption("Rangkorrelation je Maß gegen zwei unabhängige Wahrheitsstichproben; gestrichelt die eigenen Stichproben mit 50 und 200 Proben (gegen "
                   "Stichprobe 1). Größere Werte = bessere Reihenfolge.")
    else:
        st.info("Auf diesem Netz bei dieser Ausfallrate haben mindestens 95 % der Paare dieselbe Trennwahrscheinlichkeit: keine Rangkorrelation.")
duenn = D.zellen(daten, block=("hallen", "kontrast"))
st.metric("Wiederholbarkeit: Hälfte gegen Hälfte (Stichprobe 1)", z(zelle.haelften))
st.caption("Rangkorrelation der geraden gegen die ungeraden Proben derselben Stichprobe. Das ist **keine Obergrenze**: in den vorgerechneten dünnen Netzen lag "
           f"der min cut in {D.ueber_wiederholbarkeit(duenn, M.MINCUT)} von {len(duenn)} Zellen darüber.")
art, text = E.verdict_ausfall(zeile)
getattr(st, art)(text)

st.markdown("**Was jeder Gegner weiß**")
tabelle(["Maß", "weiß", "weiß nicht", "Aufwand"], [
    ["kürzeste Distanz", "den kürzesten Weg", "Ersatzwege, p", "Breitensuche"],
    ["min cut (auch: dann Distanz)", "Zahl kantendisjunkter Wege (und kürzeste Länge)", "alle Weglängen, p", "ein Maximalfluss je Paar"],
    ["Gradterm 1/d_s + 1/d_t", "zwei Grade", "alles dazwischen, p", "zwei Zahlen"],
    ["Isolationsnäherung", "zwei Grade, Nachbarschaft von s und t und p", "alles dazwischen", "drei Zahlen und p"],
    ["effektiver Widerstand R", "alle Wege und ihre Längen", "p", "ein Gleichungssystem"],
    ["eigene Stichprobe (50 oder 200)", "Netz und p", "nur Zufallsfehler", "50 oder 200 Komponentensuchen für alle Paare"],
    ["Wahrheit (1 600 Proben)", "Netz und p", "kleinerer Zufallsfehler", "wer sie rechnen kann, braucht keinen Stellvertreter"],
])

st.markdown("**Leitung gegen drei Wege: R kennt die Ausfallrate nicht.** Eine Leitung (R = 1) gegen drei sonst getrennte Wege der Länge 4 (R = 4/3).")
p_leit = st.slider("Ausfallrate im Beispiel", C.P_LEITUNG_MIN, C.P_LEITUNG_MAX, C.P_LEITUNG_STD, 0.01, key="p_leitung", format="%.2f")
l1, l2 = st.columns(2)
with l1:
    st.plotly_chart(K.karte(N.leitung(), hoehe=170), width="stretch", key="leitung_karte")
with l2:
    st.plotly_chart(K.karte(N.drei_wege(), hoehe=170, beschriftung=False), width="stretch", key="drei_karte")
art, text = E.verdict_leitung(p_leit, AF.p_leitung(p_leit), AF.p_drei_wege(p_leit))
getattr(st, art)(text)
st.markdown("Bei p = 0,15 hat das Netz mit dem **größeren** R die **kleinere** Trennwahrscheinlichkeit, bei p = 0,30 die größere. Kein Maß, das p nicht kennt, "
            "kann diese zwei Paare bei beiden Ausfallraten richtig ordnen.")

n4 = D.zellen(daten, gruppe="hallen4")
na = D.zellen(daten, gruppe="hallen_a")
na_zaehl = D.zaehlung(na, M.GRADTERM)
rho_a = {e["a"]: e["rho"] for e in daten["entartung"]["hallen_a"]}
st.markdown("**Ehrlicher Gegenfall: viele verteilte Türen.**")
st.warning(
    f"In der Familie „k gleichmäßig verteilte Türen“ (zwei Hallen, a = 6, 8, 10) ordnen zwei Gradzahlen den Ausfall bei k = 4 (p = 0,05 und 0,15) und bei "
    f"k = a (alle drei p) im Familienmittel besser als R: bei 4 Türen und p = 0,15 Gradterm {z(D.mittel([c for c in n4 if c['p'] == 0.15], M.GRADTERM))} gegen "
    f"R {z(D.mittel([c for c in n4 if c['p'] == 0.15], M.WIDERSTAND))}. Bei k = a war der Gradterm in {na_zaehl['klar_gegner']} von {na_zaehl['messbar']} "
    f"Netz-p-Zellen klar vorn; in {na_zaehl['r_vorn']} lag R knapp vorn (nicht klar). R ist dort nicht entartet: seine Rangkorrelation mit dem Gradterm über "
    f"die Nichtnachbarn ist {z(rho_a[6])}, {z(rho_a[8])} und {z(rho_a[10])} (a = 6, 8, 10). Ob R die Grade nachahmt und ob R den Ausfall gut vorhersagt, sind "
    "zwei verschiedene Fragen (Experiment 2)."
)

with st.expander("Alle vorgerechneten Netz-p-Zellen (feste Netze und Zufalls-Seeds)"):
    st.markdown(
        "Zwei Hallen und Hallenverbund (fest gebaut, je ein Netz je Größe; der Zufalls-Seed wählt nur Paare und Proben), sechs Kontrastfamilien mit je 10 "
        "Netzen (150 Knoten vor der größten Komponente), vier dichte Familien mit je 6 Netzen; je Netz und p 300 Paare. Mittlere Rangkorrelation gegen "
        "Wahrheitsstichprobe 1; Isolation = Isolationsnäherung."
    )
    spalten = (M.DISTANZ, M.WIDERSTAND, M.MINCUT, M.MINCUT_DIST, M.GRADTERM, M.ISOLATION, M.STICH200)
    zeilen_t = []
    alle_gruppen = [x for b in ("hallen", "kontrast", "dicht") for x in T.gruppen_block(b)]
    for gr in alle_gruppen:
        for pw in T.p_werte(gr):
            zz = D.zellen(daten, gruppe=gr, p=pw)
            offen, gesamt = D.nicht_messbar(zz)
            if offen == gesamt:
                zeilen_t.append([C.GRUPPEN_TEXT[gr], E.p_text(pw), f"nicht messbar ({offen}/{gesamt})"] + ["–"] * (len(spalten) - 1))
            else:
                name = C.GRUPPEN_TEXT[gr] + (f" ({gesamt - offen}/{gesamt} messbar)" if offen else "")
                zeilen_t.append([name, E.p_text(pw)] + [z(D.mittel(zz, m)) for m in spalten])
    tabelle(["Netz", "p"] + [C.MASS_KURZ[m] for m in spalten], zeilen_t)
    st.markdown("**R vorn, gezählt je Familie** (Zahl der messbaren Netz-p-Zellen mit höherer Rangkorrelation von R):")
    gegner = (M.DISTANZ, M.GRADTERM, M.ISOLATION, M.MINCUT, M.MINCUT_DIST, M.STICH200)
    zeilen_t = []
    for gr in alle_gruppen:
        zz = D.zellen(daten, gruppe=gr)
        zeilen_t.append([C.GRUPPEN_TEXT[gr]] + [f"{D.zaehlung(zz, m)['r_vorn']}/{D.zaehlung(zz, m)['messbar']}" for m in gegner])
    tabelle(["Netz"] + [C.MASS_KURZ[m] for m in gegner], zeilen_t)
    vs_mc, vs_st, vs_gt = D.zaehlung(duenn, M.MINCUT), D.zaehlung(duenn, M.STICH200), D.zaehlung(duenn, M.GRADTERM)
    st.markdown(
        f"Über alle {len(duenn)} dünnen Zellen (Hallen, Verbund, Kontrastfamilien): R vor der Distanz in {D.zaehlung(duenn, M.DISTANZ)['r_vorn']}; keines der "
        f"Maße ist durchgehend das beste. Der min cut lag in {vs_mc['gegner_vorn']} Zellen vor R, die eigene 200er-Stichprobe in {vs_st['gegner_vorn']}. Nach "
        f"dem Klar-Kriterium gegen den Gradterm: R {vs_gt['klar_r']}-mal klar vorn, der Gradterm {vs_gt['klar_gegner']}-mal."
    )

st.markdown("---")

# --- Experiment 2 ------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 2: Ab wann nur noch zwei Grade?")
st.markdown(
    "Auf manchen großen, gut verbundenen Netzen nähert sich R dem Gradterm 1/d_u + 1/d_v. Hier wird das auf **allen Nichtnachbarpaaren** gemessen, getrennt "
    "als **Rangfolge** (Rangkorrelation) und als **Wertfehler** (Median von |R − Gradterm| / R)."
)
schritt = max(1, ent.paare // C.STREUPUNKTE_MAX)
st.plotly_chart(entartung_streubild(ent, schritt), width="stretch", key="entartung_chart")
st.caption(f"{S.E_TEXT[aktuell['e_netz']]}: {ent.n} Knoten, mittlerer Grad {z(ent.mittlerer_grad, 1)}, {z(ent.paare, 0)} Nichtnachbarpaare, im Bild jedes "
           f"{schritt}. Paar. Die gepunktete Linie ist R = Gradterm.")
m1, m2 = st.columns(2)
m1.metric("Rangkorrelation R gegen Gradterm", z(ent.rho, 3))
m2.metric("Median |R − Gradterm| / R", E.prozent(ent.abweichung))
if ent.quer is not None:
    h1, h2 = st.columns(2)
    h1.metric("Wertfehler innerhalb einer Hälfte", E.prozent(ent.abweichung_innen))
    h2.metric("Wertfehler quer über die Hälften", E.prozent(ent.abweichung_quer))
art, text = E.verdict_entartung(ent.n, ent.mittlerer_grad, ent.rho, ent.abweichung)
getattr(st, art)(text)

with st.expander("Vorgerechnet: Rangfolge und Wertfehler über die Größe"):
    zeilen_t = []
    for fam in S.ENTARTUNG:
        for n_ in S.E_GROESSEN:
            w = D.entartung_zeile(daten, fam, n_)
            spanne = "" if w["netze"] == 1 else f" ({z(w['rho_min'], 3)} bis {z(w['rho_max'], 3)})"
            groesse = ", ".join(str(v) for v in w["n"])
            zeilen_t.append([S.E_TEXT[fam], groesse, str(w["netze"]), z(w["grad"], 1), z(w["rho"], 3) + spanne, E.prozent(w["abweichung"])])
    tabelle(["Netz", "Knoten", "Netze", "mittlerer Grad", "Rangkorrelation (Median, Spanne)", "Wertfehler (Median)"], zeilen_t)
    p10 = [D.entartung_zeile(daten, S.E_PUNKT10, n_) for n_ in S.E_GROESSEN]
    st.markdown(f"Beim Punktnetz mit festem Grad 10 streuen die fünf Netze je Größe stark (Spanne über alle Größen {z(min(w['rho_min'] for w in p10))} bis "
                f"{z(max(w['rho_max'] for w in p10))}); ein einzelnes Netz wäre hier kein Befund.")

ohne_eng = {fam: {pw: D.dicht_ohne_engpass(daten, fam, pw) for pw in (0.7, 0.85)} for fam in (S.ER20, S.KNOTEN10, S.PUNKT5D)}
gt_vorsprung = [w[M.GRADTERM] - w[M.WIDERSTAND] for fam in ohne_eng.values() for w in fam.values()]
offen = sum(D.nicht_messbar(D.zellen(daten, gruppe=f, p=0.15))[0] for f in ohne_eng)
dh = {pw: {m: D.mittel(D.zellen(daten, gruppe=S.DHAELFTEN, p=pw), m) for m in (M.DISTANZ, M.WIDERSTAND, M.MINCUT, M.GRADTERM)} for pw in S.P_DICHT}
st.markdown(
    f"**Was das beim Ausfall heißt (vorgerechnet, 150 Knoten, mittlerer Grad etwa 20, je 6 Netze).** Auf den drei dichten Familien ohne Engpass "
    f"(Zufallsnetz, Netz mit Knotenpunkten, Punktnetz 5D) ordnet die Isolationsnäherung bei p = 0,7 und 0,85 in allen sechs Familienmitteln mindestens so gut "
    f"wie R; auch der Gradterm ohne p liegt dort in {sum(v >= 0 for v in gt_vorsprung)} von 6 Familienmitteln knapp vor R (um höchstens "
    f"{z(max(gt_vorsprung), 3)}). Bei p = 0,15 war die Trennung dort in {offen} von 18 Netzen nicht messbar. „R schlägt die Distanz“ heißt dort vor allem: die Grade schlagen die Distanz. Anders auf den "
    f"dichten Hälften mit 3 Querverbindungen: bei p = 0,7 / 0,85 R {z(dh[0.7][M.WIDERSTAND])} / {z(dh[0.85][M.WIDERSTAND])} gegen Gradterm "
    f"{z(dh[0.7][M.GRADTERM])} / {z(dh[0.85][M.GRADTERM])}; bei p = 0,15 liegt R ({z(dh[0.15][M.WIDERSTAND])}) hinter Distanz "
    f"({z(dh[0.15][M.DISTANZ])}) und min cut ({z(dh[0.15][M.MINCUT])})."
)
st.info(
    "**Fehlende Kanten suchen?** Entartet R, heißt „nahe in R“ vor allem: kleine Summe der Kehrgrade. Wer dort fehlende Kanten sucht, nimmt R nicht roh. "
    "Das Vorhersagen fehlender Kanten selbst behandelt die Demo [Link-Vorhersage](https://sebastianhanisch-link-prediction-demo.streamlit.app/)."
)

st.markdown("---")

# --- Experiment 3 ------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 3: Welche Leitung bauen?")
st.markdown(
    "Eine neue Kante soll das Netz möglichst gut verbinden. Ziel hier: die **Summe aller Paarwiderstände** möglichst klein machen (der **Kirchhoff-Index** KI). "
    "Für jede fehlende Kante u–v lässt sich die Senkung exakt ausrechnen:"
)
st.markdown(
    r"""
$$
\Delta KI_{uv} = \frac{n \, \lVert L^{+}(e_u - e_v) \rVert^2}{1 + R_{uv}}
$$
"""
)
st.markdown("R steht im **Nenner**; der Zähler ist die quadrierte biharmonische Distanz. „Die Kante mit dem größten R bauen“ ist darum eine Daumenregel, "
            "keine Rechenvorschrift. Alle fehlenden Kanten werden mit einer Inversion und einem Matrixprodukt bewertet.")
beste = int(np.flatnonzero(aus.senkung >= aus.senkung.max() * (1 - 1e-9))[0])
gewaehlt = None if aus.wahl[regel] is None else aus.wahl[regel]
kanten = [((int(aus.U[beste]), int(aus.V[beste])), C.FARBE_BESTE, "dot", "eine beste Kante")]
if regel != X.ZUFAELLIG:
    j = int(gewaehlt[0])
    kanten.append(((int(aus.U[j]), int(aus.V[j])), C.FARBE_WAHL, "dash", f"gewählt: {C.REGEL_KURZ[regel]}"))
st.plotly_chart(K.karte(g_aus, neue_kanten=kanten, hoehe=380), width="stretch", key="ausbau_karte")


def kantenname(i):
    return f"{g_aus.knoten[int(aus.U[i])]} – {g_aus.knoten[int(aus.V[i])]}"


zeilen_t = []
for r in X.REGELN:
    if aus.anteil[r] is None:
        zeilen_t.append([C.REGEL_TEXT[r], "nicht bestimmbar (zweiter Eigenwert doppelt)", "–", "–"])
    elif r == X.ZUFAELLIG:
        zeilen_t.append([C.REGEL_TEXT[r], "jede fehlende Kante gleich wahrscheinlich", str(len(aus.U)), E.prozent(aus.anteil[r])])
    else:
        w = aus.wahl[r]
        zeilen_t.append([C.REGEL_TEXT[r], kantenname(w[0]) + (" u. a." if len(w) > 1 else ""), str(len(w)), E.prozent(aus.anteil[r])])
e1, e2 = st.columns([1.2, 1])
with e1:
    tabelle(["Regel", "gewählte Kante", "gleichrangige Kanten", "erreichte / beste Senkung"], zeilen_t)
    st.caption(f"{len(aus.U)} fehlende Kanten; KI vorher {z(aus.ki, 1)}, beste Senkung {z(float(aus.senkung.max()), 2)} (eine beste Kante: {kantenname(beste)}). "
               "Wählt eine Regel mehrere gleichrangige Kanten, zählt ihr Mittel.")
with e2:
    st.plotly_chart(balken_ausbau(aus.anteil, regel), width="stretch", key="ausbau_balken")
art, text = E.verdict_ausbau(aus.anteil, regel, C.REGEL_KURZ[regel])
getattr(st, art)(text)

if aktuell["x_netz"] in S.X_ZUFALL:
    zz = D.ausbau_zeilen(daten, aktuell["x_netz"])
    st.markdown(f"**Über {len(zz)} Netze dieser Familie** (vorgerechnet, feste Zufalls-Seeds):")
    st.plotly_chart(verteilung_ausbau(zz, X.REGELN), width="stretch", key="ausbau_verteilung")
    teile = []
    for geg in (X.MAX_GRADTERM, X.MAX_DISTANZ, X.DIST_GRAD, X.FIEDLER):
        b, gl, s_ = D.ausbau_vergleich(zz, geg)
        teile.append(f"gegen {C.REGEL_KURZ[geg]}: {b} / {gl} / {s_}")
    st.caption("„Größtes R“ besser / gleich / schlechter, je Netz: " + "; ".join(teile) + ".")
alle = [w for w in daten["ausbau"]["zeilen"] if w["netz"] in S.X_ZUFALL]
vg = D.ausbau_vergleich(alle, X.MAX_GRADTERM)
st.markdown(
    f"**Über alle {len(alle)} Netze der sechs Zufallsfamilien** ist „größtes R“ gegen den Gradterm je Netz in {vg[0]} besser, in {vg[1]} gleich und in "
    f"{vg[2]} schlechter; das ist eine Aussage über diesen Netzsatz, kein Satz. **Keine Regel gewinnt überall.** Median über diese {len(alle)} Netze: "
    + ", ".join(f"{C.REGEL_KURZ[r]} {E.prozent(D.ausbau_median(alle, r), 0)}" for r in (X.FIEDLER, X.MAX_ZAEHLER, X.MAX_R, X.MAX_DISTANZ, X.DIST_GRAD,
                                                                                       X.MAX_GRADTERM, X.ZUFAELLIG)) + "."
)
dicht = D.dicht_ausbau(daten)
st.caption(
    f"Dicht (150 Knoten, mittlerer Grad etwa 20, je 20 Netze der drei Familien ohne Engpass): R ordnet die fehlenden Kanten fast wie der Gradterm "
    f"(Rangkorrelation im Median {z(min(v['rho'] for v in dicht.values()), 3)} bis {z(max(v['rho'] for v in dicht.values()), 3)}), der Gradterm erreicht im "
    f"Median {E.prozent(min(v['gradterm'] for v in dicht.values()), 0)} bis {E.prozent(max(v['gradterm'] for v in dicht.values()), 0)} der besten Senkung, und "
    f"die beste Kante senkt den KI nur um {E.prozent(min(v['senkung'] for v in dicht.values()), 2)} bis "
    f"{E.prozent(max(v['senkung'] for v in dicht.values()), 2)} (Median). „Größtes R“ ist je Netz in {min(v['besser'] for v in dicht.values())} bis "
    f"{max(v['besser'] for v in dicht.values())} von 20 besser als der Gradterm, sonst gleich."
)
with st.expander("Von Hand: Handnetz und Besen"):
    st.markdown(
        "**Handnetz mit einer Tür** (KI = 21): die vier fehlenden Kanten mit R = 7/3 senken den KI um 83/10, die vier mit R = 5/3 um 13/2. Größtes R, "
        "größter Gradterm und größter Zähler wählen dieselben vier: **das Handnetz trennt die Regeln nicht.**\n\n"
        "Deshalb der **Besen** (Weg 2–3–4, dazu die Blätter 0 und 1 an Knoten 2; ein Baum, also ist der KI die Summe aller Abstände = 18). Die drei Kanten "
        "zwischen den Blättern haben denselben Gradterm 2. R trennt sie (2, 3, 3) und wählt die besten, (0,4) und (1,4), mit Senkung 13/2; die Kante (0,1) "
        "senkt nur um 10/3. Die Gradterm-Regel erreicht im Mittel ihrer drei gleichrangigen Kanten 98/117 der besten Senkung."
    )

st.markdown("---")

# --- Experiment 4 ------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 4: Reparaturversuche")
st.markdown(
    "Wenn R auf einem dichten Netz nur noch die Grade ordnet, lässt sich die Entartung abziehen? Hier die Probe auf **dichten Netzen mit bekannter Wahrheit** "
    "(vorgerechnet, 1 000 Knoten, 150 Anfrageknoten, Mittel über 3 Netze): bei Punkten auf einem Torus sind die richtigen Nachbarn die 10 räumlich nächsten "
    "(Maß P@10 = Anteil davon unter den 10 nächsten nach dem Netzmaß), bei 5 gepflanzten Gruppen zählt, ob das Netzmaß Knoten derselben Gruppe näher stellt "
    "(AUC)."
)
fall = daten["reparatur"]["faelle"][aktuell["r_netz"]]
REP_ANZEIGE = (M.DISTANZ, M.WIDERSTAND, M.VERSTAERKT, M.MINUS_LPLUS, M.KOSINUS, "ppr_voreinstellung", "ppr_abgestimmt", M.ADAMIC, M.DIST_WEGE)
st.plotly_chart(balken_reparatur(fall, REP_ANZEIGE), width="stretch", key="reparatur_chart")
rand = " (am Rand des Abstimmgitters 0,001 bis 0,9; die Güte ändert sich dort kaum noch)" if fall["sprung_am_rand"] else ""
st.caption(f"{T.REP_TEXT[aktuell['r_netz']]}, im Mittel {z(fall['m_mittel'], 0)} Kanten. Abgestimmte Sprungwahrscheinlichkeit von PPR/Grad "
           f"{z(fall['sprung_abgestimmt'], 3)}{rand}, gewählt auf eigenen Abstimm-Netzen. Rangkorrelation mit dem Gradterm über die Nichtnachbarn: R "
           f"{z(fall['bezug']['rho_r_gradterm'])}, verstärkt {z(fall['bezug']['rho_verst_gradterm'])}.")
st.markdown(
    """
* **verstärkte Widerstandsdistanz** (amplified commute distance): R − 1/d_s − 1/d_t + 2·a_st / (d_s·d_t), also R ohne den Gradanteil, mit einem Korrekturterm für
  Nachbarn (a_st = 1, sonst 0).
* **−L⁺:** der Eintrag der Pseudoinversen L⁺ des Laplace mit umgekehrtem Vorzeichen; ein großer Eintrag in L⁺ heißt „nah“.
* **Kosinusform von L⁺:** L⁺_st / √(L⁺_ss · L⁺_tt), zentriert und normiert (im Konferenzbeitrag von von Luxburg, Radl und Hein als Korrektur nach Brand
  beschrieben).
* **PPR/Grad:** Irrfahrt mit zufälligem Neustart (in jedem Schritt mit der Sprungwahrscheinlichkeit zurück zum Start); Aufenthaltsanteil am Ziel geteilt durch
  dessen Grad, über beide Richtungen addiert. Das Verfahren (personalisiertes PageRank) erklärt die Demo „Lokaler Schnitt“ der Reihe.
* **Adamic-Adar:** zählt gemeinsame Nachbarn, jeden mit 1 / ln seines Grades gewichtet.
* **Distanz, dann Wegezahl:** reine Zählregel ohne Gleichungssystem: erst die Distanz, bei Gleichstand die Zahl der kürzesten Wege (bei Nachbarn die Zahl der
  nicht gemeinsamen Nachbarn).
* Wald-Distanz, biharmonische Distanz und p-Widerstand sind weitere Vorschläge; sie sind hier nicht gemessen.
"""
)
art, text = E.verdict_reparatur(fall)
getattr(st, art)(text)
art, text = E.verdict_reparatur_ausfall(zeile, netz_name)
getattr(st, art)(text)
if zelle.messbar:
    reparatur_masse = (M.WIDERSTAND,) + X.REPARATUR_BEIM_AUSFALL
    tabelle(["Maß beim Ausfall (Netz aus Experiment 1)", "Rangkorrelation"], [[C.MASS_TEXT[m], z(zeile["rho1"][m])] for m in reparatur_masse])
vs = D.zaehlung(duenn, M.VERSTAERKT)
dicht_zellen = D.zellen(daten, block="dicht")
vsd = D.zaehlung(dicht_zellen, M.VERSTAERKT)
faelle = daten["reparatur"]["faelle"]
vorsprung = [faelle[k]["mittel"][M.DIST_WEGE] - faelle[k]["mittel"][M.VERSTAERKT] for k in ("torus3d", "torus5d", "torus2d")]
st.markdown(
    f"**Zusammengefasst (vorgerechnet):** Auf den drei dichten Punktnetzen holt die verstärkte Widerstandsdistanz die räumlich nahen Knoten zurück; die "
    f"Zählregel „Distanz, dann Wegezahl“ liegt dort {z(min(vorsprung))} bis {z(max(vorsprung))} davor. Bei den 5 Gruppen mit mittlerem Grad 20 holt sie "
    f"nichts zurück: {z(faelle['gruppen20']['mittel'][M.VERSTAERKT])} liegt unter der Distanz ({z(faelle['gruppen20']['mittel'][M.DISTANZ])}); −L⁺, Kosinusform "
    f"und PPR/Grad sind dort besser. Bei Grad 80 liegt sie vorn. **Beim Ausfall verliert die Reparatur Information:** in den vorgerechneten dünnen Zellen lag R in "
    f"{vs['r_vorn']} von {vs['messbar']} vor ihr, in den dichten in {vsd['r_vorn']} von {vsd['messbar']} messbaren; in den übrigen lag sie nirgends vor R."
)

st.markdown("---")

# --- Grenzen ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
tabelle(["Annahme", "Was passiert, wenn sie nicht gilt", "Stand"], [
    ["Kanten fallen **unabhängig** und gleich wahrscheinlich aus", "Bei gemeinsamen Ursachen (Sturm, Baustellenzug) zählen Wege nicht mehr unabhängig",
     "nicht gemessen"],
    ["Netze **ungewichtet**", "Mit Leitungswerten verschiebt sich R, und die Gradterme ändern sich", "nicht gemessen"],
    ["Zielgröße **P(getrennt)** eines Paars", "Umwege, längere Wege oder Durchsatz sind andere Größen", "nicht gemessen"],
    ["**Modellnetze** mit 72 bis 225 Knoten (Ausfall)", "Echte Straßen-, Strom- oder Datennetze können sich anders verhalten", "nicht gemessen"],
    ["dichte Netze nur mit 150 Knoten (Ausfall)", "Andere Größen und Grade können andere Ergebnisse geben", "nicht gemessen"],
])
st.markdown(
    "**Wie die Reihe weitergeht.** Diese Demo ordnet Knotenpaare und findet, dass R auf dichten Netzen ohne Engpass Nichtnachbarn fast wie die zwei Endgrade "
    "ordnet. Die Demo „Ausdünnen“ stellt eine andere Aufgabe (Kanten zufällig ziehen und umgewichten): An den wenigen Engpasskanten folgt R nicht den Graden, "
    "und beim Ziehen nach R blieb in den gemessenen Netzen ab c = 2 (q = c·n·ln n Züge) jede Ziehung zusammenhängend; wo die Bauart es zulässt, leisten das "
    "auch einfachere Regeln (bei genau einer Tür die Brückensuche, auf dichten Netzen mit vielen Dreiecken das Zählen gemeinsamer Nachbarn), während bei c = 2 "
    "auf den gemessenen dreiecksfreien Hälften ein Teil der gleichverteilten Ziehungen zerfiel und keine nach R (bei je K30,30 mit drei Querverbindungen "
    "deutlich; mit sechs und auf den zufällig verdrahteten Hälften nur wenige). Verglichen sind nur die dort gezeigten Regeln; dass es auf dreiecksfreien Netzen "
    "ohne R nicht geht, ist damit nicht gezeigt. Gemessen ist das in der Demo „Ausdünnen“, nicht hier."
)
st.markdown(
    "**Bezug zum Operations Research.** Das Werkzeug Circuitscape nutzt den Widerstand im Naturschutz, um die Vernetzung von Landschaften zu bewerten "
    "(Übersicht: Dickson u. a., *Conservation Biology* 33, 2019; hier nach Zusammenfassung und Schlussteil); die Autoren nennen selbst Fälle, in denen einfachere "
    "Modelle besser sein können. Zum besten einzelnen Eingriff in ein Verkehrsnetz gibt es ein Ergebnis über effektive Widerstände (Cianfanelli, Como, "
    "Ozdaglar, Parise; hier nur nach der Zusammenfassung: affine Fahrzeitfunktionen, unveränderte genutzte Wege im Gleichgewicht)."
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(
        """
**Annahmen.** Ungerichtete, ungewichtete, einfache Netze; R nur auf zusammenhängenden Netzen (bei den Netzen mit Zufall zählt die größte zusammenhängende
Komponente, nie wird neu gezogen, bis ein Netz zusammenhängt). Kanten fallen unabhängig mit gleicher Wahrscheinlichkeit aus.

**Grenzen.** Die Wahrheit ist außer auf dem Handnetz und bei der Leitung gegen drei Wege eine Stichprobe (1 600 Muster); die Rangkorrelation gilt für die
gezogenen 300 Paare. Die vorgerechneten Familien haben je 3 (Hallen, Verbund), 10 (Kontrast) bzw. 6 (dicht) Netze; die Hallen sind je Größe ein festes Netz.
Entartung bei Hallen: ein Netz je Größe; bei den Zufallsfamilien 5 Netze. Reparaturversuche: je 3 Netze mit 1 000 Knoten, abgestimmt ist nur die
Sprungwahrscheinlichkeit von PPR/Grad. Es sind Messungen an Modellnetzen, keine Aussage über echte Straßennetze.

**Bekannte Probleme und Unsicherheiten.** Auf den Gittern mit Löchern hängt die Richtung zwischen R und Gradterm vom Netz und von p ab; für p ≤ 0,15 behauptet
diese Demo dort keine Richtung. Auf dem Zufallsnetz mit mittlerem Grad 4 liegen R und Gradterm nah beieinander. Eigene Stichproben sind bei seltenen Trennungen
wenig wiederholbar. Stärkere Schätzer, die kantendisjunkte kürzeste Wege mit p verrechnen, sind nicht als Gegner dabei. Die Literaturstellen sind nicht alle
vollständig gelesen (Stand bei den Quellen angegeben).
        """
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Gegeben ist ein zusammenhängendes, ungerichtetes, ungewichtetes Netz mit $n$ Knoten und $m$ Kanten, jede Kante mit dem Widerstand 1, und eine
Ausfallrate $p$. Gesucht ist für Knotenpaare $s, t$ die Wahrscheinlichkeit $P_{st}(p)$, dass sie getrennt sind, wenn jede Kante unabhängig mit
Wahrscheinlichkeit $p$ ausfällt.

| Symbol | Bedeutung |
|---|---|
| $d_s$ | Nachbarzahl (Grad) von $s$ |
| $a_{st}$ | 1, wenn $s$ und $t$ Nachbarn sind, sonst 0 |
| $L = D - A$ | Laplace-Matrix |
| $L^{+}$ | Pseudoinverse von $L$ |
| $e_s$ | Einheitsvektor von $s$ |
| $R_{st}$ | effektiver Widerstand |
| $KI$ | Kirchhoff-Index, Summe aller $R_{st}$ |

**Pseudoinverse** (nur für zusammenhängende Netze, $J$ = Matrix aus Einsen):

$$
L^{+} = \left(L + \tfrac1n J\right)^{-1} - \tfrac1n J
$$

**Effektiver Widerstand:**

$$
R_{st} = (e_s - e_t)^\top L^{+} (e_s - e_t)
$$

Er ist $C_{st}/(2m)$ mit der Pendelzeit $C_{st}$.

**Gradterm:**

$$
g_{st} = \frac1{d_s} + \frac1{d_t}
$$

Für Nichtnachbarn gilt $R_{st} \ge g_{st}$ (alle übrigen Knoten kurzschließen; Rayleigh-Monotonie), für alle Paare $R_{st} \ge g_{st}/2$ (Lovász 1993,
Korollar 3.3). Für Nachbarn gilt $R_{st} \ge g_{st}$ nicht allgemein.

**Isolationsnäherung** (genau die Wahrscheinlichkeit, dass $s$ oder $t$ keine Kante mehr hat):

$$
\begin{aligned} I_{st}(p) ={} & p^{d_s} + p^{d_t} \\ & - p^{d_s + d_t - a_{st}} \end{aligned}
$$

**Leitung gegen drei Wege** der Länge 4:

$$
P_{\text{Leitung}} = p
$$

$$
P_{\text{Wege}} = \bigl(1 - (1-p)^4\bigr)^3
$$

**Neue Kante** $uv$ (Sherman-Morrison), mit $z = e_u - e_v$:

$$
L^{+}_{\text{neu}} = L^{+} - \frac{L^{+} z z^\top L^{+}}{1 + R_{uv}}
$$

Daraus, mit $KI = n \cdot \mathrm{Spur}(L^{+})$:

$$
\Delta KI = \frac{n \, \lVert L^{+} z \rVert^2}{1 + R_{uv}}
$$

**Verstärkte Widerstandsdistanz** (Diagonale 0):

$$
\begin{aligned} V_{st} ={} & R_{st} - \frac1{d_s} - \frac1{d_t} \\ & + \frac{2 a_{st}}{d_s d_t} \end{aligned}
$$

**Rangkorrelation.** Spearman: Pearson-Korrelation der Ränge, Gleichstände mit mittlerem Rang; Werte vorher auf 9 Stellen gerundet, die Isolationsnäherung
vorher logarithmiert. Ist eine Seite konstant, gibt es keinen Wert. Klar ist ein Abstand $R$ − Gegner, wenn er in beiden Wahrheitsstichproben dasselbe
Vorzeichen hat und mindestens 0,05 beträgt.

**Literatur.** von Luxburg, Radl, Hein: *Hitting and Commute Times in Large Random Neighborhood Graphs*, Journal of Machine Learning Research 15
(2014): R nähert sich dem Gradterm, wenn der Mindestgrad mit der Netzgröße wächst und kein starker Engpass besteht; Gitter und Netze mit konstantem
Mindestgrad sind dort nicht abgedeckt (gelesen: Abschnitte 1 bis 5 und 6.1). Dieselben: *Getting lost in space* (NIPS 2010), Abschnitt 4: verstärkte
Widerstandsdistanz (dort für die Pendeldistanz). L. Lovász: *Random Walks on Graphs: A Survey* (1993; in Teilen gelesen), Korollar 3.3. Pendelzeit $= 2mR$:
D. Levin, Y. Peres, E. Wilmer, *Markov Chains and Mixing Times*, 2. Auflage, Proposition 10.7.
        """
    )

st.markdown(
    "Verwandte Demos: [Zufällige Spannbäume](https://sebastianhanisch-random-spanning-tree-demo.streamlit.app/) (R je vorhandener Kante, Zuverlässigkeit "
    "des ganzen Netzes), [Gomory-Hu-Baum](https://sebastianhanisch-gomory-hu-demo.streamlit.app/) und "
    "[Satz von Menger](https://sebastianhanisch-menger-demo.streamlit.app/) (min cut), [Importance Sampling](https://sebastianhanisch-importance-sampling-demo.streamlit.app/) "
    "(seltene Trennungen richtig schätzen), [Zusammenhang verstärken](https://sebastianhanisch-zusammenhang-verstaerken-demo.streamlit.app/) (neue Kanten für "
    "garantierten Zusammenhang), [Netzhärtung](https://sebastianhanisch-haertung-demo.streamlit.app/) (dort ist R ein anderes Maß: der Robustheitsindex) und "
    "[Zentralität](https://sebastianhanisch-centrality-demo.streamlit.app/)."
)

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Irrfahrten auf Netzen: Trefferzeit bis Schnitt](https://sebastianhanisch.net/konzepte-irrfahrten.html)."
)
