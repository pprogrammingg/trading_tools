# web3

Wallet recovery helper and related tools.

## Venv and requirements

Use the **single venv at repo root**; install only this folder's deps so scripts here don't pull in technical_analysis deps:

```bash
cd /path/to/trading_tools
python3 -m venv .venv
.venv/bin/pip install -r web3/requirements.txt
```

- **mnemonic** – BIP-39 wordlist and checksum validation (no downloaded wordlist).
- **bip_utils** – Used to derive SUI Ed25519 public key from mnemonic for matching.

## Recovery (single entry point)

All recovery commands go through **recovery.py** and **run_recovery.sh**.

- **recovery.py** – Python CLI: baseline run, N-uncertain (1–4), or check SUI target.
- **wallet_recovery.py** – Library: BIP-39 expansion, checksum, SUI address derivation and matching.
- **recovery_uncertain_common.py** – Library: N-uncertain logic (combinations, shorten, run recovery).

### Commands

From **web3** directory:

```bash
cd web3

# Baseline: expand guess, validate checksum, match SUI address (uses cache)
./run_recovery.sh [guess.json]

# Same explicitly
./run_recovery.sh run [guess.json]

# 1–4 positions uncertain (shorten those words to 2 letters, expand, match)
./run_recovery.sh uncertain 1 [guess.json]
./run_recovery.sh uncertain 2 [guess.json]
./run_recovery.sh uncertain 3 [guess.json]
./run_recovery.sh uncertain 4 [guess.json]

# Validate SUI target in wallet_recovery.py (0x + 64 hex)
./run_recovery.sh check-target
```

From **repo root** (venv activated):

```bash
python web3/recovery.py [guess.json]
python web3/recovery.py run [guess.json]
python web3/recovery.py uncertain 2 [guess.json]
python web3/recovery.py check-target
```

Default guess file is `recovery_guess.json` if omitted.

### What each command does

1. **run** (or no subcommand) – Read 12 tokens from the guess file. For each token: if valid BIP-39 use it, else use all BIP-39 words with that prefix. Enumerate combinations, keep only those that pass BIP-39 checksum. If `SUI_TARGET_ADDRESS_HEX` is set in wallet_recovery.py, report phrases that derive to that SUI account (address = BLAKE2b(0x00||pubkey)). Results are cached in `recovery_phrase_cache.json` per guess.

2. **uncertain N** – For each set of N positions (1–4), shorten those words to their first 2 letters (so BIP-39 expands to many options), run the same expansion/checksum/SUI match. Priority positions 0, 4, 10 are tried first. N=1 runs all 12 positions; N≥2 stops on first SUI match.

3. **check-target** – Print and validate the SUI target (0x + 64 hex) used by recovery.

### recovery_guess.json

Put your 12 tokens (full words or prefixes) in `words` (space-separated string or list):

```json
{
  "words": "arm blade ignore daughter law day erase hour all junk impulse isolate"
}
```

**Sample that derives to a known SUI key:** `recovery_guess_sui_sample.json`. Use it to see a SUI match:

```bash
./run_recovery.sh recovery_guess_sui_sample.json
```

### Suggested run order (from your notes)

1. **Baseline** – Put your phrase in `recovery_guess.json` (e.g. Armed→arm, Lawsuit→law). Run `./run_recovery.sh` → if 0 valid, one word is wrong.
2. **One uncertain** – `./run_recovery.sh uncertain 1` → try each of 12 positions with 2-letter prefix.
3. **Two uncertain** – `./run_recovery.sh uncertain 2` → pairs (priority 0,4,10 first).
4. **Three uncertain** – `./run_recovery.sh uncertain 3` → triples (priority (0,4,10) first).
5. **Four uncertain** – `./run_recovery.sh uncertain 4` → all 495 4-tuples.

### Output and cache

- Valid phrases and SUI match (yes/no) are printed and appended to **recovery_last_run.txt**.
- Valid phrases per guess are cached in **recovery_phrase_cache.json** so re-runs with the same guess are fast.

## Tests

From **web3** directory:

```bash
cd web3
../.venv/bin/python -m pytest tests/test_wallet_recovery.py tests/test_recovery_uncertain.py -v
```

From **repo root** (venv activated):

```bash
python3 -m pytest web3/tests/test_wallet_recovery.py web3/tests/test_recovery_uncertain.py -v
```

- **test_wallet_recovery.py** – Baseline run on `recovery_guess_sui_sample.json` finds one valid phrase and SUI match.
- **test_recovery_uncertain.py** – For N=1,2,3,4 uncertain (with sample phrase), the matching phrase is still found.
