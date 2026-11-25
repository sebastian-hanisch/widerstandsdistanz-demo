"""Der Blockgenerator liefert genau die SplitMix64-Folge; abgeleitete Zufalls-Seeds sind verschieden und fest."""

import numpy as np
import pytest

from wdn_rng import SplitMix64
from wdn_zufall import BlockZufall, abgeleitet


@pytest.mark.parametrize("seed", [0, 1, 7000, 2**63, 2**64 - 1])
def test_blockgenerator_ist_splitmix64(seed):
    skalar = SplitMix64(seed)
    block = BlockZufall(seed)
    werte = np.concatenate([block.u64(3), block.u64(1), block.u64(0), block.u64(40)])
    assert [int(x) for x in werte] == [skalar.next_u64() for _ in range(44)]


def test_random_wie_skalar():
    skalar, block = SplitMix64(77), BlockZufall(77)
    assert block.random(20).tolist() == [skalar.random() for _ in range(20)]


def test_abgeleitete_seeds_verschieden_und_reproduzierbar():
    seeds = {abgeleitet(s, z, k) for s in range(7000, 7010) for z in range(1, 7) for k in range(0, 40)}
    assert len(seeds) == 10 * 6 * 40
    assert abgeleitet(7000, 1, 3) == abgeleitet(7000, 1, 3)
