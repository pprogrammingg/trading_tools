#!/usr/bin/env python3
"""
Single entry point for wallet recovery:

  recovery.py [guess.json]           # baseline: expand guess, validate checksum, match SUI address
  recovery.py run [guess.json]       # same
  recovery.py uncertain 1 [guess.json]   # 1 position uncertain (try all 12)
  recovery.py uncertain 2 [guess.json]   # 2 positions uncertain (pairs)
  recovery.py uncertain 3 [guess.json]   # 3 positions uncertain (triples)
  recovery.py uncertain 4 [guess.json]   # 4 positions uncertain
  recovery.py check-target            # validate SUI target in wallet_recovery.py
"""
import sys
from pathlib import Path


def _script_dir() -> Path:
    return Path(__file__).resolve().parent


def cmd_check_target() -> None:
    """Validate SUI target (0x + 64 hex)."""
    from wallet_recovery import SUI_TARGET_ADDRESS_HEX

    target = SUI_TARGET_ADDRESS_HEX
    print("Target value in wallet_recovery.py (SUI account/address):")
    print(f"  {target}")
    print()

    if not target or not target.startswith("0x"):
        print("ERROR: Target must start with 0x")
        sys.exit(1)
    rest = target[2:].lower()
    if len(rest) != 64:
        print(f"ERROR: Expected 64 hex chars after 0x, got {len(rest)}")
        sys.exit(1)
    if not all(c in "0123456789abcdef" for c in rest):
        print("ERROR: Target contains non-hex characters")
        sys.exit(1)
    print("Format: OK (0x + 64 hex = 32-byte SUI address)")
    print("Recovery derives address from each phrase and compares to this target.")


def cmd_run(guess_file: str) -> None:
    """Baseline recovery: expand guess, validate checksum, match SUI address."""
    from wallet_recovery import main as wallet_main

    # wallet_recovery.main() reads sys.argv for guess file; we need to set it
    script_dir = _script_dir()
    guess_path = (script_dir / guess_file).resolve() if not Path(guess_file).is_absolute() else Path(guess_file).resolve()
    if not guess_path.exists():
        print(f"Error: {guess_path} not found.", file=sys.stderr)
        sys.exit(1)
    # Temporarily override argv so wallet_recovery.main() sees the path
    old_argv = sys.argv
    sys.argv = [old_argv[0], str(guess_path)]
    try:
        wallet_main()
    finally:
        sys.argv = old_argv


def cmd_uncertain(n: int, guess_file: str) -> None:
    """N positions uncertain (shorten to 2 letters, expand, match SUI address)."""
    from recovery_uncertain_common import main_uncertain

    result = main_uncertain(n, guess_file=guess_file, script_dir=_script_dir())
    if result is None and n == 1:
        sys.exit(1)


def _parse_args(argv: list[str]) -> tuple[str, list[str]]:
    """Return (command, remaining_args). Command: 'run' | 'uncertain' | 'check-target'. """
    args = [a for a in argv if not a.startswith("-")]
    if not args:
        return "run", ["recovery_guess.json"]
    first = args[0].lower()
    if first == "run":
        return "run", args[1:] or ["recovery_guess.json"]
    if first == "check-target":
        return "check-target", args[1:]
    if first == "uncertain":
        if len(args) < 2:
            print("Usage: recovery.py uncertain <1|2|3|4> [guess.json]", file=sys.stderr)
            sys.exit(1)
        try:
            n = int(args[1])
            if n not in (1, 2, 3, 4):
                raise ValueError("N must be 1, 2, 3, or 4")
        except ValueError as e:
            print(f"recovery.py uncertain: {e}", file=sys.stderr)
            sys.exit(1)
        guess = args[2] if len(args) > 2 else "recovery_guess.json"
        return "uncertain", [n, guess]
    # First arg is guess file (default command: run)
    return "run", args


def main() -> None:
    argv = sys.argv[1:]
    cmd, rest = _parse_args(argv)

    if cmd == "check-target":
        cmd_check_target()
        return
    if cmd == "run":
        cmd_run(rest[0] if rest else "recovery_guess.json")
        return
    if cmd == "uncertain":
        n, guess = rest[0], rest[1]
        cmd_uncertain(n, guess)
        return


if __name__ == "__main__":
    main()
