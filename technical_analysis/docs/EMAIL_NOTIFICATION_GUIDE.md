# Email Notification & Scheduling Guide

## Free Options for Weekly Email Reports

### Option 1: Local + Free Email Service (Recommended for Few Subscribers)

**Setup:**
- Run script locally on your machine
- Use cron (macOS/Linux) or Task Scheduler (Windows) for weekly scheduling
- Send emails via free email service

**Email Services (Free Tiers):**
1. **SendGrid** (Best for small scale)
   - 100 emails/day free forever
   - Easy API integration
   - Good for <10 subscribers
   - Sign up: https://sendgrid.com

2. **Brevo (formerly Sendinblue)**
   - 300 emails/day free
   - Good API, templates
   - Sign up: https://www.brevo.com

3. **Mailjet**
   - 6,000 emails/month free
   - Good for more subscribers
   - Sign up: https://www.mailjet.com

4. **Gmail SMTP** (Simplest)
   - 500 emails/day limit
   - Requires app password
   - Free but less reliable

**Pros:**
- ✅ Completely free
- ✅ Full control
- ✅ No hosting costs

**Cons:**
- ❌ Your computer must be on
- ❌ Requires stable internet
- ❌ Manual setup

---

### Option 2: GitHub Actions (Best Free Cloud Option)

**Setup:**
- Store code in GitHub (public or private)
- Use GitHub Actions for scheduling
- Send emails via free service

**How it works:**
- GitHub Actions runs on schedule (cron syntax)
- Executes your Python script
- Sends emails via API

**Pros:**
- ✅ Completely free
- ✅ Runs in cloud (no local machine needed)
- ✅ Automatic execution
- ✅ Version control built-in

**Cons:**
- ❌ Requires GitHub account
- ❌ Code must be in repository
- ❌ 2,000 minutes/month free (plenty for weekly job)

**Example GitHub Actions workflow:**
```yaml
# .github/workflows/weekly-report.yml
name: Weekly Technical Analysis Report
on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  send-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: python technical_analysis.py
      - run: python send_email_report.py
        env:
          SENDGRID_API_KEY: ${{ secrets.SENDGRID_API_KEY }}
          EMAIL_RECIPIENTS: ${{ secrets.EMAIL_RECIPIENTS }}
```

---

### Option 3: PythonAnywhere (Free Tier)

**Setup:**
- Host script on PythonAnywhere
- Use scheduled tasks (free tier: 1 task)
- Send emails via free service

**Pros:**
- ✅ Free tier available
- ✅ Runs in cloud
- ✅ Easy Python setup

**Cons:**
- ❌ Limited to 1 scheduled task
- ❌ Free tier has restrictions
- ❌ Requires account setup

---

### Option 4: Railway / Render (Free Tier)

**Setup:**
- Deploy script as service
- Use cron jobs
- Send emails via API

**Pros:**
- ✅ Free tier available
- ✅ Cloud hosting
- ✅ Automatic deployment

**Cons:**
- ❌ Free tier has limits
- ❌ May require credit card
- ❌ More complex setup

---

## Recommended Solution: GitHub Actions + SendGrid

**Why this combination:**
1. **GitHub Actions**: Free, reliable, runs automatically
2. **SendGrid**: 100 emails/day free (plenty for weekly reports)
3. **No hosting costs**: Everything runs in cloud
4. **Easy setup**: Just add workflow file

**Steps:**
1. Create GitHub repository (can be private)
2. Add your technical analysis code
3. Create email sending script
4. Add GitHub Actions workflow
5. Configure SendGrid API key as secret
6. Add subscriber emails as secret

---

## Implementation Example

### Email Sending Script (`send_email_report.py`)

```python
import os
import json
from pathlib import Path
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from datetime import datetime

def send_weekly_report():
    """Send weekly technical analysis report via email."""
    
    # Load results
    results_dir = Path("result_scores")
    categories = [
        "cryptocurrencies", "faang_hot_stocks", "quantum",
        "miner_hpc", "precious_metals", "index_etfs", "tech_stocks"
    ]
    
    # Generate HTML report
    html_content = generate_html_report(categories, results_dir)
    
    # Get recipients from environment variable
    recipients = os.getenv("EMAIL_RECIPIENTS", "").split(",")
    
    # Send via SendGrid
    sg = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
    
    for recipient in recipients:
        message = Mail(
            from_email="your-email@example.com",
            to_emails=recipient.strip(),
            subject=f"Weekly Technical Analysis Report - {datetime.now().strftime('%Y-%m-%d')}",
            html_content=html_content
        )
        sg.send(message)
        print(f"Sent report to {recipient}")

def generate_html_report(categories, results_dir):
    """Generate HTML email content from results."""
    # Read visualization HTML files or generate summary
    # Return formatted HTML
    pass

if __name__ == "__main__":
    send_weekly_report()
```

---

## Cost Comparison

| Option | Email Service | Hosting | Total Cost |
|--------|--------------|---------|------------|
| Local + SendGrid | Free (100/day) | Free (your PC) | **$0** |
| GitHub Actions + SendGrid | Free (100/day) | Free (GitHub) | **$0** |
| PythonAnywhere + SendGrid | Free (100/day) | Free tier | **$0** |
| Railway + SendGrid | Free (100/day) | Free tier* | **$0** |

*May require credit card for verification

---

## Recommendation

**For few subscribers (<10):**
- **GitHub Actions + SendGrid** (best free cloud option)
- Or **Local + SendGrid** (if your machine is always on)

**Setup time:** ~30 minutes
**Monthly cost:** $0
**Reliability:** High (GitHub Actions) or Medium (Local)

---

## Next Steps

1. Choose email service (SendGrid recommended)
2. Choose hosting (GitHub Actions recommended)
3. Create email sending script
4. Set up scheduling
5. Test with your email first
6. Add subscribers

Would you like me to create the email sending script and GitHub Actions workflow for you?
