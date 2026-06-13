# Technical analysis

- `python technical_analysis.py` — Score all categories from cache.
- `python technical_analysis.py --category KEY` — One category; KEY from configuration.
- `python technical_analysis.py --refresh` — Re-download data; ignore cache.
- `python visualize_scores.py` — Build HTML from `result_scores` JSON.
- `python visualize_scores.py --index-only` — Rebuild landing; skip category files.
- `bash scripts/run_full_analysis.sh` — Run analysis, then all visualizations.
