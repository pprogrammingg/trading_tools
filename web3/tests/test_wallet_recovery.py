"""
Test wallet_recovery on known valid inputs: recovery_guess_sui_sample.json contains
a valid 12-word BIP-39 phrase that derives to a known SUI public key. We assert the
script finds exactly one valid phrase and that it matches that SUI key.
"""
import sys
from pathlib import Path

import pytest

# Run from web3/ or repo root; ensure web3 is on path
SCRIPT_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from wallet_recovery import run_recovery, sui_public_key_from_mnemonic, sui_address_from_pubkey_hex

# Known valid 12-word phrase and its SUI Ed25519 public key (path m/44'/784'/0'/0'/0')
SUI_SAMPLE_PHRASE = "skull slide rain ocean way replace limb glide produce earn check cattle"
SUI_SAMPLE_PUBKEY_HEX = "0xcb3776e6889bc5fd5552a2c5dbabe0f7babb668ee74015356b86d0b22e10286a"
# Recovery compares SUI address to target; address = BLAKE2b(0x00||pubkey)
SUI_SAMPLE_ADDRESS_HEX = sui_address_from_pubkey_hex(SUI_SAMPLE_PUBKEY_HEX)
SUI_SAMPLE_JSON = SCRIPT_DIR / "recovery_guess_sui_sample.json"


def test_sui_sample_file_exists():
    assert SUI_SAMPLE_JSON.exists(), f"Missing {SUI_SAMPLE_JSON}"


def test_run_recovery_sui_sample_one_valid_phrase():
    """With the SUI sample (all valid words), we get exactly one valid BIP-39 phrase."""
    valid_phrases, sui_matches = run_recovery(SUI_SAMPLE_JSON, target_pubkey_hex=SUI_SAMPLE_ADDRESS_HEX)
    assert len(valid_phrases) == 1, f"Expected 1 valid phrase, got {len(valid_phrases)}"
    assert valid_phrases[0] == SUI_SAMPLE_PHRASE


def test_run_recovery_sui_sample_matches_known_pubkey():
    """The single valid phrase from the SUI sample derives to the known SUI address (and pub key)."""
    valid_phrases, sui_matches = run_recovery(SUI_SAMPLE_JSON, target_pubkey_hex=SUI_SAMPLE_ADDRESS_HEX)
    assert len(sui_matches) == 1, f"Expected 1 SUI match, got {len(sui_matches)}"
    assert sui_matches[0] == SUI_SAMPLE_PHRASE
    derived_pub = sui_public_key_from_mnemonic(SUI_SAMPLE_PHRASE)
    assert derived_pub is not None
    assert derived_pub.lower() == SUI_SAMPLE_PUBKEY_HEX.lower()
    assert sui_address_from_pubkey_hex(derived_pub).lower() == SUI_SAMPLE_ADDRESS_HEX.lower()
