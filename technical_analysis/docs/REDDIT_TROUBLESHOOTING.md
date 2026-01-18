# Reddit App Creation Troubleshooting

## Error 500 When Creating App

If you're getting a 500 error when creating a Reddit app, try these solutions:

### Solution 1: Wait and Retry
- Reddit servers sometimes have issues
- Wait 5-10 minutes and try again
- Try during off-peak hours (not peak US times)

### Solution 2: Use Different Browser
- Try Chrome, Firefox, or Safari
- Clear browser cache
- Try incognito/private mode

### Solution 3: Verify Reddit Account
- Make sure you're logged into Reddit
- Verify your email if required
- Check account isn't restricted

### Solution 4: Try Alternative Method
If Reddit keeps failing, we can use a fallback approach (see below)

---

## Alternative: Use Mock Data for Testing

If Reddit API setup is problematic, you can test the script with mock data first:

```bash
# Test without Reddit (uses mock data)
python discover_hot_stocks.py --no-reddit --dry-run
```

This will show you how the script works without needing Reddit credentials.

---

## Alternative: Manual Stock Addition

Instead of scraping Reddit, you can manually add hot stocks:

1. Edit `symbols_config.json`
2. Add stocks to appropriate categories
3. Run the analysis pipeline

This is simpler and doesn't require Reddit setup.

---

## If Reddit Still Doesn't Work

We can modify the script to use:
- News headlines (RSS feeds - completely free, no API needed)
- Manual input
- CSV file import

Let me know if you want to try one of these alternatives!
