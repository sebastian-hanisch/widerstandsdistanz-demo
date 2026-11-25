"""SplitMix64 blockweise (ohne Streamlit, nur numpy). Kopie des Generators aus dem gemeinsamen Baustein `trz_irrfahrt_sim` der Demo „Trefferzeit“.

`BlockZufall(seed).u64(m)` sind die nächsten m Werte genau der Folge der Klasse `SplitMix64` aus `wdn_rng.py` (Test: `tests/test_zufall.py`): der k-te Wert ist die
Mischung von Zufalls-Seed + k·γ, also lassen sich ganze Blöcke auf einmal rechnen. Netze, Paare und Ausfallmuster sind damit auf jeder Plattform bitgleich.
`abgeleitet(seed, zweck, nummer)` leitet aus dem Zufalls-Seed der Seite getrennte Zufalls-Seeds für verschiedene Zwecke ab.
"""

import numpy as np

from wdn_rng import SplitMix64

GAMMA = np.uint64(0x9E3779B97F4A7C15)
_M1 = np.uint64(0xBF58476D1CE4E5B9)
_M2 = np.uint64(0x94D049BB133111EB)
MASK = (1 << 64) - 1


class BlockZufall:
    """SplitMix64 blockweise: `u64(m)` sind die nächsten m Werte der Folge."""

    def __init__(self, seed: int):
        self.seed = int(seed) & MASK
        self.gezogen = 0

    def u64(self, m: int) -> np.ndarray:
        nummer = np.arange(self.gezogen + 1, self.gezogen + m + 1, dtype=np.uint64)
        self.gezogen += m
        z = nummer * GAMMA + np.full(m, self.seed, dtype=np.uint64)      # uint64-Felder rechnen modulo 2^64
        z = (z ^ (z >> np.uint64(30))) * _M1
        z = (z ^ (z >> np.uint64(27))) * _M2
        return z ^ (z >> np.uint64(31))

    def random(self, m: int) -> np.ndarray:
        """Gleichverteilt in [0, 1) mit 53 Bit."""
        return (self.u64(m) >> np.uint64(11)).astype(np.float64) / float(1 << 53)


# Zwecke, für die aus einem Zufalls-Seed getrennte Zufalls-Seeds abgeleitet werden (feste Nummern, nie umsortieren).
ZWECK_NETZ, ZWECK_PAARE, ZWECK_WAHR1, ZWECK_WAHR2, ZWECK_KLEIN, ZWECK_ANFRAGEN = range(1, 7)


def abgeleitet(seed: int, zweck: int, nummer: int = 0) -> int:
    """Ein 64-Bit-Zufalls-Seed je (Zufalls-Seed, Zweck, laufende Nummer): erste Ausgabe von SplitMix64 an einer je Tripel verschiedenen Stelle."""
    return SplitMix64(int(seed) * 1_000_003 + zweck * 7_919 + nummer * 104_729_017).next_u64()
