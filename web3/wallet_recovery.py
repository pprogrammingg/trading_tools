#!/usr/bin/env python3
"""
Wallet recovery helper: given a 12-word recovery phrase with typos or abbreviations,
output all valid BIP-39 candidate combinations (one per line).
Use case: help people find their key when they wrote down partial or wrong words.

Optional: if SUI target (account/address) is set, combos that derive to that SUI
address are reported. We derive pub key from phrase, then SUI address = BLAKE2b(0x00||pubkey).
"""

import hashlib
import itertools
import json
import sys
from datetime import datetime
from pathlib import Path

# SUI account/address to match (0x + 64 hex). Recovery derives pub key from phrase, then
# address from pub key, and compares to this.
SUI_TARGET_ADDRESS_HEX = "0x23f950ce84e13d477be7e01c5dc929c7f076eb2468daae1c7cf19e4e3987fe5a"
# Backward-compat name used in run_recovery_from_words and callers.
SUI_TARGET_PUBKEY_HEX = SUI_TARGET_ADDRESS_HEX

# Append each run's valid phrases + derived pub keys + match status to this file (under script dir).
RECOVERY_LAST_RUN_LOG = "recovery_last_run.txt"
# Cache of valid phrases per guess so we don't recompute; key = " ".join(tokens).
RECOVERY_PHRASE_CACHE = "recovery_phrase_cache.json"

def _sui_derivation_available() -> bool:
    """True if bip_utils is available for SUI key derivation."""
    try:
        from bip_utils import Bip39SeedGenerator, Bip32Slip10Ed25519
        return True
    except ImportError:
        return False


def get_bip39_wordlist():
    """Return the official BIP-39 English wordlist (2048 words) from the mnemonic package."""
    try:
        from mnemonic import Mnemonic
        return Mnemonic("english").wordlist
    except ImportError:
        raise SystemExit(
            "Missing dependency: pip install mnemonic\n"
            "See https://github.com/trezor/python-mnemonic"
        )


def get_mnemonic_validator():
    """Return Mnemonic instance for checksum validation (uses package wordlist, no download)."""
    try:
        from mnemonic import Mnemonic
        return Mnemonic("english")
    except ImportError:
        return None


def load_guess(path: Path) -> list[str]:
    """Load recovery guess from JSON. Supports 'words' as string or list."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    raw = data.get("words")
    if isinstance(raw, str):
        return raw.strip().split()
    if isinstance(raw, list):
        return [w.strip() for w in raw]
    raise ValueError("recovery_guess.json must have 'words' as string or list")


def candidates_for(word: str, wordlist: set) -> list[str]:
    """
    For a single word from the user's guess:
    - If it's a valid BIP-39 word, return [word].
    - Otherwise return all BIP-39 words that start with this string (prefix match).
    """
    if word in wordlist:
        return [word]
    prefix = word.lower()
    return [w for w in wordlist if w.startswith(prefix)]


def sui_public_key_from_mnemonic(phrase: str) -> str | None:
    """
    Derive SUI Ed25519 public key (0x + 64 hex) from BIP-39 mnemonic using path m/44'/784'/0'/0'/0'.
    Uses bip_utils (SLIP-0010 Ed25519) when available. Returns None if derivation fails.
    """
    # Use bip_utils: BIP-39 seed -> SLIP-0010 Ed25519 path m/44'/784'/0'/0'/0'
    try:
        from bip_utils import Bip39SeedGenerator, Bip32Slip10Ed25519
        seed = Bip39SeedGenerator(phrase).Generate()
        bip32_ctx = Bip32Slip10Ed25519.FromSeed(seed)
        derived = bip32_ctx.DerivePath("m/44'/784'/0'/0'/0'")
        pub_key = bytes(derived.PublicKey().RawCompressed())
        # Ed25519: RawCompressed can be 33 bytes (prefix + 32); SUI uses raw 32-byte key
        if len(pub_key) == 33:
            pub_key = pub_key[1:33]
        return "0x" + pub_key.hex()
    except Exception:
        return None


def sui_address_from_pubkey_hex(pubkey_hex: str) -> str:
    """SUI Ed25519 account/address = BLAKE2b(0x00 || pubkey_32_bytes)."""
    raw = (pubkey_hex or "").strip().lower()
    if raw.startswith("0x"):
        raw = raw[2:]
    if len(raw) != 64 or not all(c in "0123456789abcdef" for c in raw):
        raise ValueError("Expected 64 hex chars (32-byte pub key)")
    data = bytes.fromhex(raw)
    h = hashlib.blake2b(b"\x00" + data, digest_size=32)
    return "0x" + h.hexdigest()


def run_recovery(guess_path: Path, target_pubkey_hex: str | None = SUI_TARGET_PUBKEY_HEX) -> tuple[list[str], list[str]]:
    """
    Load guess file, expand candidates, validate BIP-39 checksum, optionally match SUI pubkey.
    Returns (valid_phrases, sui_matches) for testing or reuse. No cache (for deterministic tests).
    """
    words = load_guess(guess_path)
    valid_phrases, sui_matches, _ = run_recovery_from_words(words, target_pubkey_hex)
    return valid_phrases, sui_matches


def _load_phrase_cache(cache_path: Path) -> dict:
    """Load cache file; supports legacy single-key format and multi-key format."""
    if not cache_path.exists():
        return {}
    try:
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    # Legacy: {"guess_key": "...", "valid_phrases": [...], "cached_at": "..."}
    if isinstance(cache.get("valid_phrases"), list) and "guess_key" in cache:
        key = cache["guess_key"]
        return {key: {"valid_phrases": cache["valid_phrases"], "cached_at": cache.get("cached_at", "")}}
    # Multi-key: {"key1": {"valid_phrases": [...], "cached_at": "..."}, ...}
    if isinstance(cache, dict):
        return {k: v for k, v in cache.items() if isinstance(v, dict) and isinstance(v.get("valid_phrases"), list)}
    return {}


def _save_phrase_cache(cache_path: Path, cache: dict) -> None:
    """Write multi-key cache to file."""
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=0)
    except OSError:
        pass


def run_recovery_from_words(
    words: list[str],
    target_pubkey_hex: str | None = SUI_TARGET_PUBKEY_HEX,
    cache_path: Path | None = None,
) -> tuple[list[str], list[str]]:
    """
    Same as run_recovery but takes a list of 12 tokens (no file). For automation.
    If cache_path is set, valid phrases for this guess are read/written to that file (multi-key by " ".join(words)).
    """
    guess_key = " ".join(words)
    check_sui = target_pubkey_hex and target_pubkey_hex.startswith("0x") and len(target_pubkey_hex) == 66
    valid_phrases: list[str] = []
    used_cache = False

    if cache_path:
        cache = _load_phrase_cache(cache_path)
        if guess_key in cache and isinstance(cache[guess_key].get("valid_phrases"), list):
            valid_phrases = cache[guess_key]["valid_phrases"]
            used_cache = True

    if not valid_phrases:
        wordlist = get_bip39_wordlist()
        wordlist_set = set(wordlist)
        mnemonic_validator = get_mnemonic_validator()
        candidate_lists = []
        for w in words:
            cands = candidates_for(w, wordlist_set)
            if not cands:
                raise ValueError(f"No BIP-39 candidate for word: {w!r}")
            candidate_lists.append(cands)
        for combo in itertools.product(*candidate_lists):
            phrase = " ".join(combo)
            if mnemonic_validator and not mnemonic_validator.check(phrase):
                continue
            valid_phrases.append(phrase)
        if cache_path:
            cache = _load_phrase_cache(cache_path)
            cache[guess_key] = {"valid_phrases": valid_phrases, "cached_at": datetime.now().isoformat()}
            _save_phrase_cache(cache_path, cache)

    sui_matches = []
    if check_sui and _sui_derivation_available():
        for phrase in valid_phrases:
            pub_hex = sui_public_key_from_mnemonic(phrase)
            if pub_hex:
                try:
                    if sui_address_from_pubkey_hex(pub_hex).lower() == target_pubkey_hex.lower():
                        sui_matches.append(phrase)
                except Exception:
                    pass
    return valid_phrases, sui_matches, used_cache


def main():
    script_dir = Path(__file__).resolve().parent
    guess_file = sys.argv[1] if len(sys.argv) > 1 else "recovery_guess.json"
    guess_path = (script_dir / guess_file).resolve() if not Path(guess_file).is_absolute() else Path(guess_file).resolve()

    if not guess_path.exists():
        print(f"Error: {guess_path} not found.", file=sys.stderr)
        sys.exit(1)

    wordlist = get_bip39_wordlist()
    wordlist_set = set(wordlist)
    mnemonic_validator = get_mnemonic_validator()
    if not mnemonic_validator:
        print("Warning: mnemonic package required for checksum validation.", file=sys.stderr)

    words = load_guess(guess_path)
    if len(words) != 12:
        print(f"Warning: expected 12 words, got {len(words)}.", file=sys.stderr)

    candidate_lists = []
    for i, w in enumerate(words):
        cands = candidates_for(w, wordlist_set)
        if not cands:
            print(
                f"Error: no BIP-39 candidate for position {i+1} '{w}'.",
                file=sys.stderr,
            )
            sys.exit(1)
        candidate_lists.append(cands)

    total = 1
    for c in candidate_lists:
        total *= len(c)
    print(f"# Total candidate combinations (before checksum): {total}", file=sys.stderr)

    check_sui = SUI_TARGET_PUBKEY_HEX and SUI_TARGET_PUBKEY_HEX.startswith("0x") and len(SUI_TARGET_PUBKEY_HEX) == 66
    if check_sui:
        print(f"# SUI target (account/address): {SUI_TARGET_PUBKEY_HEX}", file=sys.stderr)

    cache_path = script_dir / RECOVERY_PHRASE_CACHE
    valid_phrases, sui_matches, used_cache = run_recovery_from_words(
        words, SUI_TARGET_PUBKEY_HEX, cache_path=cache_path
    )
    if used_cache:
        print(f"# Using cached valid phrases ({len(valid_phrases)} from {cache_path})", file=sys.stderr)
    elif valid_phrases:
        print(f"# Cached {len(valid_phrases)} valid phrases to {cache_path}", file=sys.stderr)

    valid_count = len(valid_phrases)
    sui_match_set = set(sui_matches)
    target_hex = SUI_TARGET_PUBKEY_HEX if check_sui else None

    # Append to last-run log: each valid phrase, derived SUI address, and whether it matched target account.
    log_path = script_dir / RECOVERY_LAST_RUN_LOG
    with open(log_path, "a", encoding="utf-8") as log:
        log.write(f"\n--- {datetime.now().isoformat()} ---\n")
        log.write(f"guess_file={guess_path.name} target_sui_address={target_hex or 'none'}\n")
        for phrase in valid_phrases:
            derived_pub = sui_public_key_from_mnemonic(phrase) if _sui_derivation_available() else None
            derived_addr = sui_address_from_pubkey_hex(derived_pub) if derived_pub else "n/a"
            matched = "yes" if (target_hex and phrase in sui_match_set) else "no"
            log.write(f"phrase: {phrase}\n")
            log.write(f"  derived_sui_address: {derived_addr}\n")
            log.write(f"  sui_account_matched: {matched}\n")
        log.write(f"valid_count: {valid_count}\n")
    print(f"# Appended run to {log_path}", file=sys.stderr)

    for phrase in valid_phrases:
        derived_pub = sui_public_key_from_mnemonic(phrase) if _sui_derivation_available() else None
        derived_addr = sui_address_from_pubkey_hex(derived_pub) if derived_pub else "n/a"
        matched = "yes" if (target_hex and phrase in sui_match_set) else "no"
        print(f"combination : {phrase} gave valid priv key , resulting in SUI address {derived_addr} , SUI account matched {matched}")

    print(f"# Valid BIP-39 phrases (checksum passed): {valid_count}", file=sys.stderr)
    if check_sui and sui_matches:
        for phrase in sui_matches:
            print(f"# SUI MATCH (recovery phrase for target account): {phrase}", file=sys.stderr)
    elif check_sui:
        if _sui_derivation_available():
            print("# No phrase matched SUI target account (address).", file=sys.stderr)
        else:
            print("# No phrase matched SUI target account (install bip_utils for SUI key check).", file=sys.stderr)


if __name__ == "__main__":
    main()
