#!/usr/bin/env python3
"""
Hot Stock Discovery Script
Discovers trending stocks from Reddit discussions and integrates them into the analysis pipeline.
"""

import json
import re
import sys
import os
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import argparse

# Try to import Reddit API (optional)
try:
    import praw
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False
    print("Warning: praw not installed. Install with: pip install praw")

# Try to import sentiment analysis (optional)
try:
    from textblob import TextBlob
    SENTIMENT_AVAILABLE = True
except ImportError:
    SENTIMENT_AVAILABLE = False
    print("Warning: textblob not installed. Install with: pip install textblob")


# Common stock ticker patterns
TICKER_PATTERN = re.compile(r'\$?([A-Z]{1,5})\b')
STOCK_SUBREDDITS = ['stocks', 'investing', 'StockMarket', 'wallstreetbets', 'SecurityAnalysis', 'ValueInvesting']

# Known stock exchanges and patterns
KNOWN_TICKERS = set()  # Will be populated from existing config


def load_existing_symbols():
    """Load all existing symbols from configuration.json 'categories'."""
    try:
        from config_loader import get_symbols_config
        config = get_symbols_config()
    except Exception:
        config = {}
    all_symbols = set()
    for category_symbols in config.values():
        all_symbols.update(category_symbols)
    return all_symbols


def get_reddit_mentions(days_back=90, limit_per_subreddit=100):
    """
    Scrape Reddit for stock mentions.
    
    Args:
        days_back: How many days to look back
        limit_per_subreddit: Max posts per subreddit
        
    Returns:
        Counter of ticker mentions
    """
    if not REDDIT_AVAILABLE:
        print("Error: Reddit API (praw) not available.")
        print("Install with: pip install praw")
        print("Then create Reddit app at: https://www.reddit.com/prefs/apps")
        return Counter()
    
    # Initialize Reddit (use environment variables or config)
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID', ''),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET', ''),
            user_agent='TechnicalAnalysisBot/1.0'
        )
    except Exception as e:
        print(f"Error initializing Reddit: {e}")
        print("Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables")
        return Counter()
    
    cutoff_date = datetime.now() - timedelta(days=days_back)
    ticker_mentions = Counter()
    post_data = defaultdict(list)  # Store post info for each ticker
    
    print(f"Searching Reddit for stock mentions (last {days_back} days)...")
    print(f"Subreddits: {', '.join(STOCK_SUBREDDITS)}")
    
    for subreddit_name in STOCK_SUBREDDITS:
        try:
            subreddit = reddit.subreddit(subreddit_name)
            print(f"\n  Checking r/{subreddit_name}...")
            
            post_count = 0
            for submission in subreddit.hot(limit=limit_per_subreddit):
                # Check if post is recent enough
                post_date = datetime.fromtimestamp(submission.created_utc)
                if post_date < cutoff_date:
                    continue
                
                post_count += 1
                
                # Extract tickers from title
                title_tickers = TICKER_PATTERN.findall(submission.title.upper())
                
                # Extract tickers from selftext (if exists)
                body_tickers = []
                if hasattr(submission, 'selftext') and submission.selftext:
                    body_tickers = TICKER_PATTERN.findall(submission.selftext.upper())
                
                # Combine and count
                all_tickers = title_tickers + body_tickers
                for ticker in all_tickers:
                    # Filter out common false positives
                    if ticker in ['THE', 'FOR', 'AND', 'ARE', 'YOU', 'ALL', 'CAN', 'HAS', 'WAS', 'BUT', 'NOT', 'ITS']:
                        continue
                    if len(ticker) == 1:  # Skip single letters
                        continue
                    
                    ticker_mentions[ticker] += 1
                    post_data[ticker].append({
                        'title': submission.title,
                        'score': submission.score,
                        'date': post_date.strftime('%Y-%m-%d'),
                        'subreddit': subreddit_name
                    })
                
                # Also check top comments
                try:
                    submission.comments.replace_more(limit=0)
                    for comment in submission.comments.list()[:10]:  # Top 10 comments
                        comment_tickers = TICKER_PATTERN.findall(comment.body.upper())
                        for ticker in comment_tickers:
                            if ticker not in ['THE', 'FOR', 'AND', 'ARE', 'YOU', 'ALL', 'CAN', 'HAS', 'WAS', 'BUT', 'NOT', 'ITS']:
                                if len(ticker) > 1:
                                    ticker_mentions[ticker] += 0.5  # Comments weighted less
                except:
                    pass
            
            print(f"    Processed {post_count} recent posts")
            
        except Exception as e:
            print(f"    Error processing r/{subreddit_name}: {e}")
            continue
    
    return ticker_mentions, post_data


def categorize_ticker(ticker, existing_symbols):
    """
    Determine which category a ticker belongs to.
    
    Args:
        ticker: Stock ticker symbol
        existing_symbols: Set of known symbols from config
        
    Returns:
        Category name or None if unknown
    """
    ticker_upper = ticker.upper()
    
    # Known categories based on patterns
    crypto_patterns = ['BTC', 'ETH', 'SOL', 'USD']
    if any(pattern in ticker_upper for pattern in crypto_patterns) or ticker_upper.endswith('-USD'):
        return 'cryptocurrencies'
    
    try:
        from config_loader import get_symbols_config
        config = get_symbols_config()
        for category, symbols in config.items():
            if ticker_upper in [s.upper() for s in symbols]:
                return category
    except Exception:
        pass

    # Default to general stocks
    return 'general_stocks'


def discover_hot_stocks(min_mentions=5, days_back=90, use_reddit=True):
    """
    Discover hot stocks from Reddit.
    
    Args:
        min_mentions: Minimum mentions to include
        days_back: Days to look back
        use_reddit: Whether to use Reddit API
        
    Returns:
        Dictionary of {ticker: {'mentions': count, 'category': str, 'posts': list}}
    """
    existing_symbols = load_existing_symbols()
    
    if use_reddit and REDDIT_AVAILABLE:
        try:
            ticker_mentions, post_data = get_reddit_mentions(days_back=days_back)
        except Exception as e:
            print(f"Error accessing Reddit: {e}")
            print("Falling back to manual input mode...")
            return get_manual_input_stocks()
    else:
        # Fallback: return empty or use mock data for testing
        print("Reddit not available. Using manual input mode...")
        return get_manual_input_stocks()


def get_manual_input_stocks():
    """
    Allow manual input of hot stocks when Reddit is unavailable.
    """
    print("\n" + "=" * 60)
    print("Manual Stock Input Mode")
    print("=" * 60)
    print("Enter stock tickers to add (one per line, or comma-separated)")
    print("Press Enter twice when done, or type 'skip' to skip")
    print()
    
    stocks = {}
    while True:
        try:
            user_input = input("Enter ticker(s): ").strip()
            if not user_input or user_input.lower() == 'skip':
                break
            
            # Parse comma-separated or space-separated
            tickers = re.split(r'[,\s]+', user_input.upper())
            
            for ticker in tickers:
                ticker = ticker.strip().replace('$', '')
                if not ticker or len(ticker) < 2:
                    continue
                
                existing_symbols = load_existing_symbols()
                if ticker in existing_symbols:
                    print(f"  {ticker} already in config, skipping...")
                    continue
                
                category = categorize_ticker(ticker, existing_symbols)
                stocks[ticker] = {
                    'mentions': 1,  # Manual entry
                    'category': category,
                    'posts': [{'title': 'Manually added', 'date': datetime.now().strftime('%Y-%m-%d'), 'subreddit': 'manual'}]
                }
                print(f"  ✓ Added {ticker} to {category}")
        
        except (EOFError, KeyboardInterrupt):
            break
    
    return stocks
    
    # Filter and categorize
    hot_stocks = {}
    for ticker, count in ticker_mentions.most_common():
        if count < min_mentions:
            continue
        
        # Skip if already in config
        if ticker in existing_symbols:
            continue
        
        category = categorize_ticker(ticker, existing_symbols)
        hot_stocks[ticker] = {
            'mentions': int(count),
            'category': category,
            'posts': post_data.get(ticker, [])[:5]  # Top 5 posts
        }
    
    return hot_stocks


def update_symbols_config(hot_stocks, dry_run=False):
    """Update configuration.json 'categories' with discovered stocks."""
    try:
        from config_loader import get_symbols_config, update_categories
        config = get_symbols_config()
    except Exception:
        config = {}
    if "general_stocks" not in config:
        config["general_stocks"] = []
    added_count = 0
    for ticker, data in hot_stocks.items():
        category = data["category"]
        if category not in config:
            config[category] = []
        if ticker not in config[category]:
            config[category].append(ticker)
            added_count += 1
            print(f"  ✓ Added {ticker} to {category} ({data['mentions']} mentions)")

    if not dry_run and added_count > 0:
        try:
            from config_loader import update_categories
            update_categories(config)
            print(f"\n✓ Updated configuration.json categories with {added_count} new stock(s)")
        except Exception as e:
            print(f"\nWarning: could not update configuration.json: {e}")
    elif dry_run:
        print(f"\n[DRY RUN] Would add {added_count} new stock(s)")
    return config


def main():
    parser = argparse.ArgumentParser(description='Discover hot stocks from Reddit')
    parser.add_argument('--min-mentions', type=int, default=5,
                       help='Minimum mentions to include (default: 5)')
    parser.add_argument('--days', type=int, default=90,
                       help='Days to look back (default: 90)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be added without updating config')
    parser.add_argument('--no-reddit', action='store_true',
                       help='Skip Reddit scraping (for testing)')
    parser.add_argument('--run-analysis', action='store_true',
                       help='Run full analysis after discovering stocks')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Hot Stock Discovery")
    print("=" * 60)
    
    # Discover hot stocks
    hot_stocks = discover_hot_stocks(
        min_mentions=args.min_mentions,
        days_back=args.days,
        use_reddit=not args.no_reddit
    )
    
    if not hot_stocks:
        print("\nNo new hot stocks found (or Reddit not configured).")
        return
    
    print(f"\n{'=' * 60}")
    print(f"Found {len(hot_stocks)} hot stock(s):")
    print(f"{'=' * 60}")
    
    # Sort by mentions
    sorted_stocks = sorted(hot_stocks.items(), key=lambda x: x[1]['mentions'], reverse=True)
    
    for ticker, data in sorted_stocks:
        print(f"\n{ticker}:")
        print(f"  Mentions: {data['mentions']}")
        print(f"  Category: {data['category']}")
        if data['posts']:
            print(f"  Sample posts:")
            for post in data['posts'][:2]:
                print(f"    - [{post['date']}] {post['title'][:60]}... (r/{post['subreddit']})")
    
    # Update config
    print(f"\n{'=' * 60}")
    print("Updating symbols configuration...")
    print(f"{'=' * 60}")
    
    config = update_symbols_config(hot_stocks, dry_run=args.dry_run)
    
    # Run analysis if requested
    if args.run_analysis and not args.dry_run:
        print(f"\n{'=' * 60}")
        print("Running full analysis pipeline...")
        print(f"{'=' * 60}")
        
        import subprocess
        result = subprocess.run(['bash', 'run_full_analysis.sh'], cwd=Path(__file__).parent)
        if result.returncode == 0:
            print("\n✓ Analysis complete! Visualizations are open in your browser.")
        else:
            print("\n✗ Analysis failed. Check errors above.")


if __name__ == "__main__":
    import os
    main()
