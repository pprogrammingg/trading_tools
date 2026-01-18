# Sentiment Analysis Integration Guide

## Feasibility: ⚠️ Moderate (with caveats)

### What's Possible:
- ✅ Crawl Twitter/X for stock mentions
- ✅ Analyze sentiment (positive/negative/neutral)
- ✅ Integrate into existing categories
- ✅ Use free tools and APIs

### Challenges:
- ⚠️ Twitter API changes (now X API) - limited free tier
- ⚠️ Rate limits and blocking
- ⚠️ Legal/ToS considerations
- ⚠️ Data quality varies

---

## Option 1: Twitter/X API (Recommended)

### Free Tier (X API Basic):
- **Cost**: $100/month (not free anymore)
- **Rate limits**: 1,500 tweets/month
- **Features**: Official API, reliable, legal

### Free Alternative: snscrape (Unofficial)
- **Cost**: Free
- **How**: Scrapes Twitter without API
- **Limitations**: 
  - Can break if Twitter changes structure
  - Rate limiting issues
  - May violate ToS (use at own risk)

### Implementation:
```python
# Using snscrape (free, unofficial)
import snscrape.modules.twitter as sntwitter
from textblob import TextBlob

def get_twitter_sentiment(ticker, limit=100):
    """Get sentiment from Twitter mentions."""
    query = f"${ticker} OR {ticker} lang:en"
    tweets = []
    
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= limit:
            break
        tweets.append({
            'text': tweet.content,
            'date': tweet.date,
            'likes': tweet.likeCount
        })
    
    # Analyze sentiment
    sentiments = []
    for tweet in tweets:
        blob = TextBlob(tweet['text'])
        sentiments.append(blob.sentiment.polarity)  # -1 to +1
    
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    return {
        'sentiment_score': avg_sentiment,
        'tweet_count': len(tweets),
        'positive_ratio': sum(1 for s in sentiments if s > 0.1) / len(sentiments) if sentiments else 0
    }
```

---

## Option 2: Reddit (Free & More Reliable)

### Why Reddit is Better:
- ✅ Free API (PRAW library)
- ✅ Better quality discussions
- ✅ Less rate limiting
- ✅ More reliable long-term

### Implementation:
```python
import praw
from textblob import TextBlob

def get_reddit_sentiment(ticker, subreddits=['stocks', 'investing', 'StockMarket']):
    """Get sentiment from Reddit posts/comments."""
    reddit = praw.Reddit(
        client_id='your_client_id',
        client_secret='your_client_secret',
        user_agent='TechnicalAnalysisBot/1.0'
    )
    
    all_sentiments = []
    
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        
        # Search for ticker mentions
        for submission in subreddit.search(ticker, limit=50):
            # Analyze title
            title_sentiment = TextBlob(submission.title).sentiment.polarity
            all_sentiments.append(title_sentiment)
            
            # Analyze top comments
            submission.comments.replace_more(limit=0)
            for comment in submission.comments.list()[:10]:
                comment_sentiment = TextBlob(comment.body).sentiment.polarity
                all_sentiments.append(comment_sentiment)
    
    avg_sentiment = sum(all_sentiments) / len(all_sentiments) if all_sentiments else 0
    return {
        'sentiment_score': avg_sentiment,
        'mention_count': len(all_sentiments),
        'source': 'reddit'
    }
```

---

## Option 3: News Headlines (Free)

### Sources:
- **NewsAPI**: 100 requests/day free
- **Alpha Vantage News**: Free with API key
- **RSS Feeds**: Completely free

### Implementation:
```python
import feedparser
from textblob import TextBlob

def get_news_sentiment(ticker):
    """Get sentiment from news headlines."""
    # Google News RSS
    url = f"https://news.google.com/rss/search?q={ticker}+stock&hl=en&gl=US&ceid=US:en"
    feed = feedparser.parse(url)
    
    sentiments = []
    for entry in feed.entries[:20]:
        title = entry.title
        sentiment = TextBlob(title).sentiment.polarity
        sentiments.append(sentiment)
    
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0
    return {
        'sentiment_score': avg_sentiment,
        'headline_count': len(sentiments),
        'source': 'news'
    }
```

---

## Integration with Your System

### 1. Add Sentiment to Results

Modify `technical_analysis.py` to include sentiment:

```python
def process_category(category_name: str, symbols: list, ...):
    # ... existing code ...
    
    for symbol in symbols:
        # ... existing analysis ...
        
        # Add sentiment analysis
        sentiment = get_sentiment_for_symbol(symbol, category_name)
        results[symbol]['sentiment'] = sentiment
        
        # ... rest of processing ...
```

### 2. Add Sentiment to Scoring

```python
def compute_indicators_with_score(df, category: str = None, sentiment: dict = None):
    # ... existing scoring ...
    
    # Add sentiment to score
    if sentiment:
        sentiment_score = sentiment.get('sentiment_score', 0)
        if sentiment_score > 0.3:  # Positive sentiment
            result["score"] += 0.5
            result["score_breakdown"]["positive_sentiment"] = 0.5
        elif sentiment_score < -0.3:  # Negative sentiment
            result["score"] -= 0.5
            result["score_breakdown"]["negative_sentiment"] = -0.5
```

### 3. Update Visualization

Add sentiment column to HTML tables showing:
- Sentiment score (-1 to +1)
- Source (Twitter/Reddit/News)
- Number of mentions

---

## Recommended Approach

### Phase 1: Start with Reddit (Easiest)
1. **Setup**: Create Reddit app (free)
2. **Implement**: Reddit sentiment scraper
3. **Test**: Run on a few symbols
4. **Integrate**: Add to scoring system

### Phase 2: Add News Headlines
1. **Setup**: NewsAPI or RSS feeds
2. **Implement**: News sentiment analyzer
3. **Combine**: Weight Reddit + News sentiment

### Phase 3: Twitter (If Needed)
1. **Evaluate**: Check if Reddit/News sufficient
2. **Consider**: snscrape (unofficial, free) or X API (paid)
3. **Implement**: Only if needed

---

## Free Tools & Libraries

### Sentiment Analysis:
- **TextBlob**: Free, simple, good for basic sentiment
- **VADER**: Free, optimized for social media
- **Transformers (Hugging Face)**: Free, more advanced

### Data Sources:
- **Reddit (PRAW)**: Free API
- **NewsAPI**: 100 requests/day free
- **RSS Feeds**: Completely free
- **snscrape**: Free Twitter scraping (unofficial)

### Installation:
```bash
pip install textblob vaderSentiment praw feedparser snscrape
```

---

## Legal & Ethical Considerations

### Twitter/X:
- ⚠️ Scraping may violate ToS
- ⚠️ Rate limiting can cause blocks
- ⚠️ API changes can break scrapers
- ✅ Official API is legal but paid

### Reddit:
- ✅ Official API (PRAW) is allowed
- ✅ Rate limits are reasonable
- ✅ More stable long-term

### News:
- ✅ RSS feeds are public
- ✅ NewsAPI has free tier
- ✅ Generally safe and legal

---

## Implementation Example

### File Structure:
```
technical_analysis/
├── sentiment_analysis.py      # Sentiment scraping functions
├── technical_analysis.py     # Modified to include sentiment
└── symbols_config.json        # Add Twitter handles if needed
```

### Quick Start:
1. Install: `pip install textblob vaderSentiment praw feedparser`
2. Create Reddit app: https://www.reddit.com/prefs/apps
3. Add sentiment module
4. Integrate into main script
5. Test on one category first

---

## Cost Summary

| Source | Cost | Reliability | Setup Time |
|--------|------|--------------|------------|
| Reddit API | Free | High | 15 min |
| NewsAPI | Free (100/day) | High | 10 min |
| RSS Feeds | Free | Medium | 5 min |
| Twitter (snscrape) | Free | Low | 20 min |
| X API | $100/mo | High | 10 min |

---

## Recommendation

**Start with Reddit + News Headlines:**
- ✅ Both free
- ✅ Reliable and legal
- ✅ Good quality data
- ✅ Easy to implement
- ✅ Sufficient for sentiment analysis

**Skip Twitter initially:**
- ⚠️ More complex
- ⚠️ Legal gray area (scraping)
- ⚠️ Paid API ($100/mo)
- ✅ Can add later if needed

Would you like me to create the sentiment analysis module and integrate it into your system?
