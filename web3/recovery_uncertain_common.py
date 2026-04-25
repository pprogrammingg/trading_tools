"""
Shared logic for N-uncertain-word recovery: load words, build position combinations,
run recovery for each combination, log and report matches.
Used by recovery_uncertain_one.py, recovery_uncertain_two.py, recovery_uncertain_three.py, recovery_uncertain_four.py.
"""
import itertools
import json
import sys
from pathlib import Path

from wallet_recovery import (
    RECOVERY_LAST_RUN_LOG,
    RECOVERY_PHRASE_CACHE,
    SUI_TARGET_PUBKEY_HEX,
    run_recovery_from_words,
    sui_public_key_from_mnemonic,
    sui_address_from_pubkey_hex,
    _sui_derivation_available,
)

# Priority positions from notes (Armed→0, Lawsuit→4, Impulse→10). Try these first when N uncertain.
PRIORITY_POSITIONS = (0, 4, 10)


def load_words(path: Path) -> list[str]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    raw = data.get("words")
    if isinstance(raw, str):
        return raw.strip().split()
    if isinstance(raw, list):
        return [w.strip() for w in raw]
    raise ValueError("JSON must have 'words' as string or list")


def shorten_for_expansion(word: str, min_prefix_len: int = 2) -> str:
    """Shorten word to a prefix so BIP-39 expansion gives more candidates."""
    w = word.lower()
    if len(w) <= min_prefix_len:
        return w[0:1] if len(w) >= 1 else w
    return w[:min_prefix_len]


def ordered_combinations(
    n: int,
    num_positions: int = 12,
    priority_tuples: list[tuple[int, ...]] | None = None,
) -> list[tuple[int, ...]]:
    """
    All n-element combinations of range(num_positions), with priority tuples first.
    For n=1: (0), (1), ... (11); for n=2: (i,j) with i<j; etc.
    """
    all_combos = list(itertools.combinations(range(num_positions), n))
    if not priority_tuples:
        return all_combos
    priority_set = set(priority_tuples)
    ordered = [c for c in priority_tuples if c in all_combos]
    ordered += [c for c in all_combos if c not in priority_set]
    return ordered


def default_priority_tuples(n: int) -> list[tuple[int, ...]]:
    """Default priority: subsets of PRIORITY_POSITIONS (0, 4, 10) when they form valid n-combinations."""
    if n == 1:
        return [(i,) for i in PRIORITY_POSITIONS]
    if n == 2:
        return [(0, 4), (0, 10), (4, 10)]
    if n == 3:
        return [(0, 4, 10)]
    if n == 4:
        return [(0, 1, 4, 10), (0, 4, 10, 11)]
    return []


def apply_uncertain(words: list[str], positions: tuple[int, ...]) -> list[str]:
    """Return a copy of words with the given positions shortened for expansion."""
    modified = list(words)
    for pos in positions:
        modified[pos] = shorten_for_expansion(words[pos])
    return modified


def run_uncertain(
    words: list[str],
    n: int,
    target_hex: str,
    cache_path: Path,
    log_path: Path,
    *,
    priority_tuples: list[tuple[int, ...]] | None = None,
    stop_on_first_match: bool = True,
    log_prefix: str = "uncertain",
) -> str | None:
    """
    Run recovery for each N-position combination. Shorten those positions to 2 letters and expand.
    Returns the first phrase that matched the target SUI account, or None.
    """
    if priority_tuples is None:
        priority_tuples = default_priority_tuples(n)
    combinations = ordered_combinations(n, len(words), priority_tuples)
    matched_phrase: str | None = None

    for positions in combinations:
        modified = apply_uncertain(words, positions)
        try:
            valid_phrases, sui_matches, _ = run_recovery_from_words(
                modified, target_hex, cache_path=cache_path
            )
        except ValueError as e:
            print(f"# Positions {positions}: {e}", file=sys.stderr)
            continue

        num_valid = len(valid_phrases)
        if num_valid == 0:
            print(f"# Positions {positions}: 0 valid", file=sys.stderr)
            continue

        sui_match_set = set(sui_matches)
        if sui_matches and matched_phrase is None:
            matched_phrase = sui_matches[0]

        prefixes_str = ",".join(repr(modified[p]) for p in positions)
        print(f"# Positions {positions} (prefixes {prefixes_str}): {num_valid} valid", file=sys.stderr)
        with open(log_path, "a", encoding="utf-8") as log:
            log.write(f"\n--- {log_prefix}_n={n} positions={positions} ---\n")
            log.write(f"target_sui_address={target_hex}\n")
            for phrase in valid_phrases:
                derived_pub = sui_public_key_from_mnemonic(phrase) if _sui_derivation_available() else None
                derived_addr = sui_address_from_pubkey_hex(derived_pub) if derived_pub else "n/a"
                matched = "yes" if phrase in sui_match_set else "no"
                log.write(f"phrase: {phrase}\n  derived_sui_address: {derived_addr}\n  sui_account_matched: {matched}\n")
                print(f"combination : {phrase} gave valid priv key , resulting in SUI address {derived_addr} , SUI account matched {matched}")
            log.write(f"valid_count: {num_valid}\n")

        if matched_phrase and stop_on_first_match:
            break

    return matched_phrase


def main_uncertain(
    n: int,
    guess_file: str = "recovery_guess.json",
    script_dir: Path | None = None,
) -> str | None:
    """
    CLI entry: load guess from file, run N-uncertain recovery, print summary.
    Returns matched phrase or None. Exits with 1 if no valid phrase found (n=1 only).
    """
    script_dir = script_dir or Path(__file__).resolve().parent
    guess_path = (script_dir / guess_file).resolve() if not Path(guess_file).is_absolute() else Path(guess_file).resolve()

    if not guess_path.exists():
        print(f"Error: {guess_path} not found.", file=sys.stderr)
        sys.exit(1)

    words = load_words(guess_path)
    if len(words) != 12:
        print(f"Error: expected 12 words, got {len(words)}.", file=sys.stderr)
        sys.exit(1)

    target_hex = SUI_TARGET_PUBKEY_HEX
    cache_path = script_dir / RECOVERY_PHRASE_CACHE
    log_path = script_dir / RECOVERY_LAST_RUN_LOG

    print(f"# {n} position(s) uncertain (first 2 letters each). Target SUI account (address):", target_hex, file=sys.stderr)
    priority_tuples = default_priority_tuples(n)
    if priority_tuples:
        print(f"# Priority (from notes): {priority_tuples}", file=sys.stderr)
    total = len(ordered_combinations(n, 12, priority_tuples))
    print(f"# Total combinations: {total}", file=sys.stderr)
    print(file=sys.stderr)

    # n=1: run all 12 positions to collect every valid phrase; n>=2: stop on first match
    matched_phrase = run_uncertain(
        words, n, target_hex, cache_path, log_path,
        priority_tuples=priority_tuples,
        stop_on_first_match=(n != 1),
        log_prefix=f"{n}_uncertain",
    )

    print(file=sys.stderr)
    print(f"# Run complete. Target SUI account (address): {target_hex}", file=sys.stderr)
    if matched_phrase:
        print(f"# MATCH FOUND: {matched_phrase}", file=sys.stderr)
    else:
        print(f"# No combination had SUI account matched yes.", file=sys.stderr)
        if n == 1:
            print("# No valid phrase found for any uncertain position. Try shortening more letters or check the phrase.", file=sys.stderr)
            sys.exit(1)

    return matched_phrase
