"""Karte eines Netzes als Plotly-Figur (ohne Streamlit).

Grundlage: Kopie des gemeinsamen Bausteins `pzt_karte` der Demo „Pendelzeit“ (kopieren, nicht importieren), ohne Ströme, dafür mit mehreren zusätzlichen Kanten
in eigenen Farben (gewählte und beste neue Leitung).

Jeder Knotenpunkt hat seine Nummer in `customdata`. Beschriftungen sind Annotationen, und alle Punkte behalten die volle Deckkraft. Achsen sind gesperrt."""

import plotly.graph_objects as go

import wdn_netze as N

FARBE_KANTE = "rgba(130,130,130,0.55)"
FARBE_KNOTEN = "#9aa5b1"


def _linien(g: N.Netz, kanten):
    xs, ys = [], []
    for a, b in kanten:
        xs += [g.pos[a][0], g.pos[b][0], None]
        ys += [g.pos[a][1], g.pos[b][1], None]
    return xs, ys


BOEGEN = (0.16, -0.16)        # Ausbuchtung neuer Leitungen (Anteil ihrer Länge), je Linie zur anderen Seite: so verdecken sie weder Netzkanten noch einander


def _bogen(g: N.Netz, kante, anteil: float, schritte: int = 24):
    """Punkte eines flachen Bogens (quadratische Bézierkurve) zwischen den Enden der Kante."""
    (x0, y0), (x1, y1) = g.pos[kante[0]], g.pos[kante[1]]
    mx, my = (x0 + x1) / 2 - anteil * 2 * (y1 - y0), (y0 + y1) / 2 + anteil * 2 * (x1 - x0)
    ts = [i / schritte for i in range(schritte + 1)]
    return ([(1 - t) ** 2 * x0 + 2 * t * (1 - t) * mx + t * t * x1 for t in ts], [(1 - t) ** 2 * y0 + 2 * t * (1 - t) * my + t * t * y1 for t in ts])


def knotengroesse(n: int) -> int:
    if n <= 10:
        return 28
    if n <= 40:
        return 18
    if n <= 100:
        return 11
    return 7 if n <= 250 else 4


def karte(g: N.Netz, neue_kanten=(), hoehe: int = 340, beschriftung: bool = None) -> go.Figure:
    """Karte des Netzes. `neue_kanten`: Folge von (Kante, Farbe, Strichart, Name für die Legende)."""
    fig = go.Figure()
    breite = 0.7 if len(g.kanten) > 150 else 1.5
    xs, ys = _linien(g, g.kanten)
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=FARBE_KANTE, width=breite), hoverinfo="skip", showlegend=False))
    for nummer, (kante, farbe, strich, name) in enumerate(neue_kanten):
        xs, ys = _bogen(g, kante, BOEGEN[nummer % len(BOEGEN)])
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=farbe, width=4, dash=strich), hoverinfo="skip", showlegend=True, name=name))
    groesse = knotengroesse(g.n)
    fig.add_trace(go.Scatter(x=[p[0] for p in g.pos], y=[p[1] for p in g.pos], mode="markers",
                             marker=dict(size=groesse, color=FARBE_KNOTEN, line=dict(width=1, color="rgba(60,60,60,0.7)")),
                             customdata=list(range(g.n)), text=list(g.knoten), hovertemplate="%{text}<extra></extra>", showlegend=False))
    if beschriftung is None:
        beschriftung = g.n <= 12
    if beschriftung:
        for i in range(g.n):
            fig.add_annotation(x=g.pos[i][0], y=g.pos[i][1], text=g.knoten[i], showarrow=False, font=dict(size=13, color="#111111"),
                               bgcolor="rgba(255,255,255,0.75)")
    xs_alle = [p[0] for p in g.pos]
    ys_alle = [p[1] for p in g.pos]
    spanne = max(max(xs_alle) - min(xs_alle), max(ys_alle) - min(ys_alle), 1e-9)
    rand = 0.08 * spanne + (0.2 if g.n <= 12 else 0.0)
    # zwei unsichtbare Eckpunkte erzwingen den Rand; gleicher Maßstab über scaleanchor nur mit automatischem Bereich
    fig.add_trace(go.Scatter(x=[min(xs_alle) - rand, max(xs_alle) + rand], y=[min(ys_alle) - rand, max(ys_alle) + rand], mode="markers",
                             marker=dict(size=1, opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, fixedrange=True)
    fig.update_yaxes(visible=False, fixedrange=True, scaleanchor="x", scaleratio=1)
    fig.update_layout(height=hoehe, margin=dict(l=5, r=5, t=26, b=5), dragmode=False, plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      showlegend=bool(neue_kanten), legend=dict(orientation="h", y=-0.02, x=0, yanchor="top"))
    return fig
