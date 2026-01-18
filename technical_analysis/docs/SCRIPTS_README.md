# Scripts Overview

This document describes all scripts in the technical analysis system and how to use them.

## Main Scripts

### 1. `run_full_analysis.sh` - Complete Pipeline
**Purpose**: Runs the entire pipeline: data refresh → score calculation → visualization → open browser

**Usage**:
```bash
./run_full_analysis.sh                    # Run all categories with default settings
./run_full_analysis.sh --refresh          # Force refresh all data
./run_full_analysis.sh --calculate-potential  # Include relative potential calculation
./run_full_analysis.sh --category faang_hot_stocks  # Process only one category
./run_full_analysis.sh --refresh --calculate-potential  # Combine flags
```

**What it does**:
1. Finds Python executable (venv/bin/python, env/bin/python, or python3)
2. Runs `technical_analysis.py` to download/refresh data and calculate scores
3. Runs `visualize_scores.py` to generate HTML visualizations
4. Opens all visualizations in browser using `open_visualizations.sh`

**Features**:
- Automatic Python path detection
- Error handling with `set -e`
- Passes all command-line arguments to `technical_analysis.py`
- Validates each step before proceeding

---

### 2. `run_visualization.sh` - Visualization Only
**Purpose**: Generates visualizations from existing result files and opens them

**Usage**:
```bash
./run_visualization.sh
```

**What it does**:
1. Finds Python executable
2. Runs `visualize_scores.py` to generate HTML from existing `result_scores/*.json` files
3. Opens all visualizations in browser

**When to use**:
- When you already have result files and just want to regenerate/update visualizations
- Faster than full analysis (no data download/calculation)

---

### 3. `open_visualizations.sh` - Open Existing Visualizations
**Purpose**: Opens all existing HTML visualizations in browser

**Usage**:
```bash
./open_visualizations.sh
```

**What it does**:
1. Checks if `visualizations_output/` directory exists
2. Finds all HTML files (excluding test files)
3. Opens each file in the default browser

**Features**:
- Skips test files automatically
- Validates that files exist before opening
- Works on macOS (uses `open` command)

---

## Python Scripts

### 4. `technical_analysis.py` - Data & Score Calculation
**Purpose**: Downloads data, calculates technical indicators, and computes scores

**Usage**:
```bash
python technical_analysis.py                              # All categories, default settings
python technical_analysis.py --refresh                    # Force refresh all data
python technical_analysis.py --calculate-potential        # Include relative potential
python technical_analysis.py --category faang_hot_stocks  # Single category
python technical_analysis.py --refresh --category quantum  # Combine options
```

**Command-line arguments**:
- `--category CATEGORY`: Process only specific category
- `--config PATH`: Path to symbols config (default: `symbols_config.json`)
- `--calculate-potential`: Calculate relative potential (slower, ~30-45% more time)
- `--refresh`: Force refresh all data (ignore cache)

**Output**: Creates `result_scores/{category}_results.json` files

---

### 5. `visualize_scores.py` - HTML Generation
**Purpose**: Generates HTML visualizations from result JSON files

**Usage**:
```bash
python visualize_scores.py
```

**What it does**:
1. Finds all `result_scores/*_results.json` files
2. For each file, generates an HTML table with color-coded scores
3. Saves to `visualizations_output/{category}_scores.html`

**Output**: Creates HTML files in `visualizations_output/` directory

---

## Workflow Examples

### Full Refresh and Analysis
```bash
# Refresh all data, calculate scores, generate visualizations, open browser
./run_full_analysis.sh --refresh
```

### Quick Visualization Update
```bash
# Just regenerate HTML from existing results
./run_visualization.sh
```

### Single Category Analysis
```bash
# Analyze only FAANG stocks
./run_full_analysis.sh --category faang_hot_stocks
```

### View Existing Visualizations
```bash
# Open already-generated HTML files
./open_visualizations.sh
```

---

## Script Improvements Made

### Shell Script Robustness
1. **Python Path Detection**: Automatically finds Python in venv/env or system
2. **Error Handling**: Uses `set -e` to exit on errors
3. **Path Validation**: Checks directories exist before operations
4. **Command Validation**: Verifies commands are available before use

### Fixed Issues
1. **Indentation**: Fixed formatting issues in `open_visualizations.sh`
2. **Test File Filtering**: Properly excludes test files from opening
3. **Argument Passing**: All arguments properly passed through scripts
4. **Exit Codes**: Proper error codes for failure cases

---

## Directory Structure

```
technical_analysis/
├── run_full_analysis.sh      # Main pipeline script
├── run_visualization.sh      # Visualization-only script
├── open_visualizations.sh    # Browser opening script
├── technical_analysis.py     # Data & score calculation
├── visualize_scores.py       # HTML generation
├── symbols_config.json       # Symbol configuration
├── result_scores/            # JSON result files
├── visualizations_output/    # HTML visualization files
└── data_cache/               # Cached data files
```

---

## Troubleshooting

### "Python not found"
- Ensure Python 3 is installed
- Or create a virtual environment: `python3 -m venv venv`

### "Visualizations not opening"
- On macOS, ensure `open` command is available
- Check that HTML files exist in `visualizations_output/`

### "No result files found"
- Run `technical_analysis.py` first to generate result files
- Or use `./run_full_analysis.sh` to run the full pipeline

### Shell Issues
- All scripts now use robust path detection
- Scripts are executable (chmod +x)
- Use `bash script.sh` if direct execution fails
