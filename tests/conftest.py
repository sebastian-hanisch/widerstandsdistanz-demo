"""Gemeinsame Fixtures und die exakten Referenz-Rechenwege der Tests (Brüche, eigene Gauß-Elimination, eigene Komponentensuche).

Die Referenz rechnet bewusst anders als die Demo: R aus dem geerdeten Laplace in Brüchen und aus der Zählung von Spannbäumen (Matrix-Baum-Satz),
P(getrennt) durch Aufzählung aller Ausfallmuster mit eigener Vereinigungssuche, min cut durch Aufzählung aller Knotenmengen."""

import itertools
import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import wdn_netze as N  # noqa: E402


@pytest.fixture
def hand():
    """Handnetz „zwei Hallen“ mit einer Tür 2–3 (7 Kanten)."""
    return N.handnetz(1)


@pytest.fixture
def hand2():
    """Mit zweiter Tür 5–0 (8 Kanten)."""
    return N.handnetz(2)


@pytest.fixture
def besen():
    return N.besen()


def loese_brueche(M, b):
    n = len(b)
    M = [[Fraction(x) for x in z] + [Fraction(y)] for z, y in zip(M, b)]
    for c in range(n):
        p = next(r for r in range(c, n) if M[r][c] != 0)
        M[c], M[p] = M[p], M[c]
        for r in range(n):
            if r != c and M[r][c] != 0:
                f = M[r][c] / M[c][c]
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return [M[i][n] / M[i][i] for i in range(n)]


def laplace_brueche(n, kanten):
    L = [[Fraction(0)] * n for _ in range(n)]
    for a, b in kanten:
        L[a][a] += 1
        L[b][b] += 1
        L[a][b] -= 1
        L[b][a] -= 1
    return L


def widerstand_geerdet(n, kanten, s, t):
    """R(s,t): Strom 1 bei s, t geerdet; die Spannung an s ist R."""
    L = laplace_brueche(n, kanten)
    rest = [x for x in range(n) if x != t]
    M = [[L[x][y] for y in rest] for x in rest]
    phi = loese_brueche(M, [int(x == s) for x in rest])
    return phi[rest.index(s)]


def determinante(M):
    M = [[Fraction(x) for x in z] for z in M]
    n, det = len(M), Fraction(1)
    for c in range(n):
        p = next((r for r in range(c, n) if M[r][c] != 0), None)
        if p is None:
            return Fraction(0)
        if p != c:
            M[c], M[p] = M[p], M[c]
            det = -det
        det *= M[c][c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return det


def widerstand_spannbaeume(n, kanten, s, t):
    """R(s,t) = det(L ohne s und t) / det(L ohne s)."""
    L = laplace_brueche(n, kanten)

    def ohne(weg):
        rest = [x for x in range(n) if x not in weg]
        return [[L[x][y] for y in rest] for x in rest]

    return determinante(ohne({s, t})) / determinante(ohne({s}))


def wurzeln(n, kanten):
    eltern = list(range(n))

    def f(x):
        while eltern[x] != x:
            x = eltern[x]
        return x

    for a, b in kanten:
        eltern[f(a)] = f(b)
    return [f(i) for i in range(n)]


def p_getrennt_brueche(n, kanten, p, paare):
    """Exakt über alle 2^m Ausfallmuster."""
    m = len(kanten)
    erg = [Fraction(0)] * len(paare)
    for maske in range(1 << m):
        da = [kanten[i] for i in range(m) if (maske >> i) & 1]
        gewicht = (1 - p) ** len(da) * p ** (m - len(da))
        k = wurzeln(n, da)
        for j, (s, t) in enumerate(paare):
            if k[s] != k[t]:
                erg[j] += gewicht
    return erg


def p_isoliert_brueche(n, kanten, p, paare):
    """Wahrscheinlichkeit, dass s oder t keine Kante mehr hat, durch Aufzählung aller Ausfallmuster (ohne Formel)."""
    m = len(kanten)
    erg = [Fraction(0)] * len(paare)
    for maske in range(1 << m):
        da = [kanten[i] for i in range(m) if (maske >> i) & 1]
        gewicht = (1 - p) ** len(da) * p ** (m - len(da))
        belegt = {x for k in da for x in k}
        for j, (s, t) in enumerate(paare):
            if s not in belegt or t not in belegt:
                erg[j] += gewicht
    return erg


def min_cut_aufzaehlung(n, kanten, s, t):
    """Kleinster Rand einer Knotenmenge, die s enthält und t nicht."""
    beste = len(kanten)
    uebrige = [x for x in range(n) if x not in (s, t)]
    for k in range(len(uebrige) + 1):
        for teil in itertools.combinations(uebrige, k):
            menge = {s, *teil}
            beste = min(beste, sum((a in menge) != (b in menge) for a, b in kanten))
    return beste


def zufallsnetz_klein(n, m, seed):
    """Zusammenhängendes Netz mit n Knoten und m Kanten: zufälliger Baum plus weitere Kanten (eigener Zufall, nicht aus der Demo)."""
    import random

    rng = random.Random(seed)
    kanten = {(rng.randrange(i), i) for i in range(1, n)}
    frei = [(a, b) for a in range(n) for b in range(a + 1, n) if (a, b) not in kanten]
    rng.shuffle(frei)
    kanten |= set(frei[: max(0, min(m, n * (n - 1) // 2) - len(kanten))])
    return N.netz(f"Test {seed}", n, sorted(kanten))
