"""
Test N-uncertain-word recovery: for a known valid phrase (SUI sample), making 1, 2, 3, or 4
positions uncertain (shortened to 2 letters) should still find the phrase that matches the target.
"""
import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from wallet_recovery import sui_address_from_pubkey_hex

from recovery_uncertain_common import (
    apply_uncertain,
    load_words,
    ordered_combinations,
    run_uncertain,
    shorten_for_expansion,
)

# Same as test_wallet_recovery: known phrase and its SUI address
SUI_SAMPLE_PHRASE = "skull slide rain ocean way replace limb glide produce earn check cattle"
SUI_SAMPLE_PUBKEY_HEX = "0xcb3776e6889bc5fd5552a2c5dbabe0f7babb668ee74015356b86d0b22e10286a"
SUI_SAMPLE_ADDRESS_HEX = sui_address_from_pubkey_hex(SUI_SAMPLE_PUBKEY_HEX)
SUI_SAMPLE_JSON = SCRIPT_DIR / "recovery_guess_sui_sample.json"


@pytest.fixture
def sample_words():
    """Load the 12 words from the SUI sample (exact phrase)."""
    assert SUI_SAMPLE_JSON.exists()
    return load_words(SUI_SAMPLE_JSON)


@pytest.fixture
def temp_dirs(tmp_path):
    """Use a temp dir for cache and log so tests don't touch real cache."""
    cache_path = tmp_path / "recovery_phrase_cache.json"
    log_path = tmp_path / "recovery_last_run.txt"
    return cache_path, log_path


@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_uncertain_n_finds_sample_phrase(sample_words, temp_dirs, n):
    """With the SUI sample phrase, N-uncertain (shorten N positions to 2 letters) finds the matching phrase."""
    cache_path, log_path = temp_dirs
    matched = run_uncertain(
        sample_words,
        n,
        SUI_SAMPLE_ADDRESS_HEX,
        cache_path,
        log_path,
        priority_tuples=None,  # use default priority
        stop_on_first_match=True,
        log_prefix="test",
    )
    assert matched is not None, f"N={n} uncertain should find a match for sample phrase"
    assert matched == SUI_SAMPLE_PHRASE, f"N={n} uncertain should return the exact sample phrase"


def test_ordered_combinations():
    """ordered_combinations(n) returns correct count and priority first."""
    # n=1: 12 single positions
    c1 = ordered_combinations(1, 12, [(0,), (4,), (10,)])
    assert len(c1) == 12
    assert c1[:3] == [(0,), (4,), (10,)]
    # n=2: C(12,2)=66 pairs
    c2 = ordered_combinations(2, 12, [(0, 4), (0, 10), (4, 10)])
    assert len(c2) == 66
    assert c2[:3] == [(0, 4), (0, 10), (4, 10)]
    # n=4: C(12,4)=495
    c4 = ordered_combinations(4, 12)
    assert len(c4) == 495


def test_apply_uncertain_and_shorten():
    """apply_uncertain shortens the given positions; shorten_for_expansion uses 2-char prefix."""
    words = ["skull", "slide", "rain"] + ["x"] * 9
    shortened = apply_uncertain(words, (0, 2))
    assert shortened[0] == "sk"
    assert shortened[1] == "slide"
    assert shortened[2] == "ra"
    assert shorten_for_expansion("skull") == "sk"
    assert shorten_for_expansion("way") == "wa"
