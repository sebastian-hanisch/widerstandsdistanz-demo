"""Plotly-Abbildungen der Experimente (ohne Streamlit). Alle Achsen sind gesperrt; Zahlen mit Dezimalkomma."""

import numpy as np
import plotly.graph_objects as go

import wdn_constants as C
import wdn_masse as M

SEPARATOREN = ", "      # Dezimalkomma, Tausender mit Leerzeichen


def _fest(fig: go.Figure, hoehe: int, **layout) -> go.Figure:
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    fig.update_layout(height=hoehe, margin=dict(l=10, r=10, t=30, b=10), dragmode=False, separators=SEPARATOREN, **layout)
    return fig


def streubild(x, y, xtitel: str) -> go.Figure:
    """Ein Punkt je Knotenpaar: Vorhersager gegen Trennwahrscheinlichkeit (Wahrheitsstichprobe 1)."""
    fig = go.Figure(go.Scatter(x=np.round(np.asarray(x, dtype=float), 6), y=np.round(y, 5), mode="markers", marker=dict(size=6, color=C.FARBE_R, opacity=0.55),
                               hovertemplate="%{x}<br>getrennt in %{y:.1%} der Proben<extra></extra>"))
    fig.update_xaxes(title_text=xtitel)
    fig.update_yaxes(title_text="Anteil getrennt", tickformat=".0%", rangemode="tozero")
    return _fest(fig, 330)


def balken_rangkorrelation(zeile: dict) -> go.Figure:
    """Balken je Maß aus den zwei Wahrheitsstichproben; die kleinen Stichproben als waagrechte Linien (gegen Stichprobe 1)."""
    namen = [C.MASS_KURZ[m] for m in C.BALKEN_MASSE]
    fig = go.Figure()
    for schluessel, titel, farbe in (("rho1", "Wahrheit 1", C.FARBE_R), ("rho2", "Wahrheit 2", C.FARBE_GEGNER)):
        werte = [zeile[schluessel][m] for m in C.BALKEN_MASSE]
        fig.add_trace(go.Bar(x=namen, y=[None if v is None else round(v, 4) for v in werte], name=titel, marker_color=farbe,
                             hovertemplate="%{x}: %{y:.2f}<extra>" + titel + "</extra>"))
    for proben, mass in ((50, M.STICH50), (200, M.STICH200)):
        v = zeile["rho1"][mass]
        if v is not None:
            fig.add_trace(go.Scatter(x=namen, y=[round(v, 4)] * len(namen), mode="lines", line=dict(color=C.FARBE_STICH[proben], width=2, dash="dash"),
                                     name=f"Stichprobe {proben}", hovertemplate=f"Stichprobe {proben}: %{{y:.2f}}<extra></extra>"))
    fig.update_yaxes(title_text="Rangkorrelation", range=[min(0.0, _minimum(zeile) - 0.05), 1.05])
    return _fest(fig, 360, barmode="group", legend=dict(orientation="h", y=-0.3, x=0))


def _minimum(zeile: dict) -> float:
    werte = [v for key in ("rho1", "rho2") for m, v in zeile[key].items() if m in C.BALKEN_MASSE + (M.STICH50, M.STICH200) and v is not None]
    return min(werte) if werte else 0.0


def entartung_streubild(e, schritt: int) -> go.Figure:
    """R gegen den Gradterm auf den Nichtnachbarpaaren (jedes `schritt`-te); bei zwei Hälften nach „innen/quer“ gefärbt."""
    wahl = np.arange(0, len(e.R), schritt)
    fig = go.Figure()
    if e.quer is None:
        gruppen = [("Nichtnachbarpaare", wahl, C.FARBE_INNEN)]
    else:
        gruppen = [("innerhalb einer Hälfte", wahl[~e.quer[wahl]], C.FARBE_INNEN), ("quer über die Hälften", wahl[e.quer[wahl]], C.FARBE_QUER)]
    for name, idx, farbe in gruppen:
        fig.add_trace(go.Scattergl(x=np.round(e.gt[idx], 5), y=np.round(e.R[idx], 5), mode="markers", name=name,
                                   marker=dict(size=4, color=farbe, opacity=0.5), hovertemplate="Gradterm %{x:.3f}, R %{y:.3f}<extra></extra>"))
    lo, hi = float(e.gt[wahl].min()), float(e.gt[wahl].max())
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", line=dict(color="rgba(80,80,80,0.8)", width=1.5, dash="dot"), name="R = Gradterm",
                             hoverinfo="skip"))
    fig.update_xaxes(title_text="Gradterm 1/d_u + 1/d_v")
    fig.update_yaxes(title_text="effektiver Widerstand R")
    return _fest(fig, 380, legend=dict(orientation="h", y=-0.25, x=0))


def balken_ausbau(anteile: dict, gewaehlt: str) -> go.Figure:
    regeln = [r for r, v in anteile.items() if v is not None]
    farben = [C.FARBE_WAHL if r == gewaehlt else C.FARBE_R if r == "max_r" else C.FARBE_GEGNER for r in regeln]
    fig = go.Figure(go.Bar(y=[C.REGEL_KURZ[r] for r in regeln], x=[round(anteile[r], 4) for r in regeln], orientation="h", marker_color=farben,
                           hovertemplate="%{y}: %{x:.1%}<extra></extra>"))
    fig.update_xaxes(title_text="erreichte / beste Senkung", tickformat=".0%", range=[0, 1.05])
    fig.update_yaxes(autorange="reversed")
    return _fest(fig, 300)


def verteilung_ausbau(zeilen: list, regeln) -> go.Figure:
    """Verteilung des erreichten Anteils je Regel über die vorgerechneten Netze einer Familie."""
    fig = go.Figure()
    for r in regeln:
        werte = [round(z["anteil"][r], 4) for z in zeilen if z["anteil"][r] is not None]
        if werte:
            fig.add_trace(go.Box(y=werte, name=C.REGEL_KURZ[r], marker_color=C.FARBE_R if r == "max_r" else C.FARBE_GEGNER, boxpoints="all",
                                 pointpos=0, jitter=0.4, marker=dict(size=3), showlegend=False))
    fig.update_yaxes(title_text="erreichte / beste Senkung", tickformat=".0%", range=[0, 1.05])
    return _fest(fig, 340)


def balken_reparatur(fall: dict, masse) -> go.Figure:
    namen = [C.MASS_KURZ[m] for m in masse]
    farben = [C.FARBE_R if m == M.VERSTAERKT else C.FARBE_WAHL if m == M.DISTANZ else C.FARBE_GEGNER for m in masse]
    fig = go.Figure(go.Bar(y=namen, x=[round(fall["mittel"][m], 4) for m in masse], orientation="h", marker_color=farben,
                           hovertemplate="%{y}: %{x:.2f}<extra></extra>"))
    titel = "P@10 (räumlich nächste)" if fall["guete"] == "p10" else "AUC „gleiche Gruppe“"
    fig.update_xaxes(title_text=titel, range=[0, 1.05])
    fig.update_yaxes(autorange="reversed")
    return _fest(fig, 380)
