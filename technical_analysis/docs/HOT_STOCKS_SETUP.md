# Hot Stock Discovery Setup

## Quick Start

### 1. Install Dependencies

```bash
pip install praw textblob
```

### 2. Create Reddit App (Free)

1. Go to https://www.reddit.com/prefs/apps
2. Click **"create another app..."** button at the bottom
3. Fill in the form:
   - **Name**: `TechnicalAnalysisBot` (or any name you want)
   - **Type**: Select **"script"** (important!)
   - **Description**: `Stock analysis bot` (optional, can be anything)
   - **About URL**: Leave blank or put `http://localhost` (not used for scripts)
   - **Redirect URI**: `http://localhost:8080` (required but not used for scripts - can be any URL)
4. Click **"create app"**
5. After creation, you'll see:
   - **client_id**: The string under your app name (looks like random characters)
   - **client_secret**: The "secret" field (click "edit" to reveal it if hidden)
   
**Note**: For script type apps, the redirect URI is required but not actually used. You can use any URL like `http://localhost:8080` or `http://localhost` - it doesn't matter.

### 3. Set Environment Variables

**macOS/Linux:**
```bash
export REDDIT_CLIENT_ID="your_client_id_here"
export REDDIT_CLIENT_SECRET="your_client_secret_here"
```

**Windows:**
```cmd
set REDDIT_CLIENT_ID=your_client_id_here
set REDDIT_CLIENT_SECRET=your_client_secret_here
```

**Or create `.env` file** (add to .gitignore):
```
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
```

### 4. Run Discovery

```bash
# Discover hot stocks (dry run - shows what would be added)
python discover_hot_stocks.py --dry-run

# Discover and update config
python discover_hot_stocks.py

# Discover, update, and run full analysis
python discover_hot_stocks.py --run-analysis

# Customize: minimum 10 mentions, last 60 days
python discover_hot_stocks.py --min-mentions 10 --days 60
```

## How It Works

1. **Scrapes Reddit** subreddits:
   - r/stocks
   - r/investing
   - r/StockMarket
   - r/wallstreetbets
   - r/SecurityAnalysis
   - r/ValueInvesting

2. **Extracts ticker mentions** from:
   - Post titles
   - Post bodies
   - Top comments

3. **Counts mentions** over last 90 days (configurable)

4. **Categorizes stocks**:
   - Checks existing categories
   - Crypto patterns (BTC, ETH, SOL, -USD)
   - Defaults to "general_stocks"

5. **Updates symbols_config.json** with new stocks

6. **Optionally runs full analysis** pipeline

## Options

```bash
--min-mentions N    Minimum mentions to include (default: 5)
--days N           Days to look back (default: 90)
--dry-run          Show what would be added without updating
--no-reddit        Skip Reddit (for testing)
--run-analysis     Run full analysis after discovery
```

## Example Output

```
============================================================
Hot Stock Discovery
============================================================
Searching Reddit for stock mentions (last 90 days)...
Subreddits: stocks, investing, StockMarket, wallstreetbets

  Checking r/stocks...
    Processed 45 recent posts
  Checking r/investing...
    Processed 38 recent posts
...

============================================================
Found 3 hot stock(s):
============================================================

NVDA:
  Mentions: 127
  Category: faang_hot_stocks
  Sample posts:
    - [2024-01-15] NVDA is going to the moon! (r/wallstreetbets)
    - [2024-01-14] Why I'm bullish on NVDA (r/stocks)

PLTR:
  Mentions: 23
  Category: general_stocks
  Sample posts:
    - [2024-01-12] PLTR earnings discussion (r/stocks)

============================================================
Updating symbols configuration...
============================================================
  ✓ Added PLTR to general_stocks (23 mentions)

✓ Updated symbols_config.json with 1 new stock(s)
```

## Integration with Pipeline

After discovery, stocks are automatically added to `symbols_config.json`. The existing pipeline will pick them up:

```bash
# Run full analysis (includes newly discovered stocks)
./run_full_analysis.sh
```

## Troubleshooting

### "Reddit API not available"
- Install: `pip install praw`
- Set environment variables: `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET`

### "No new hot stocks found"
- Lower `--min-mentions` threshold
- Increase `--days` to look back further
- Check Reddit API credentials

### Rate Limiting
- Reddit API has rate limits (60 requests/minute)
- Script handles this automatically
- If issues persist, reduce `--days` or wait between runs

## Notes

- **Free**: Reddit API is completely free
- **Legal**: Using official Reddit API (PRAW) is allowed
- **Reliable**: More stable than Twitter scraping
- **Quality**: Reddit discussions are often more thoughtful than Twitter

## Next Steps

1. Run discovery weekly to find new hot stocks
2. Review discovered stocks before running analysis
3. Manually adjust categories if needed
4. Integrate into GitHub Actions workflow for automatic discovery
