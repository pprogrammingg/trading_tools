# GitHub Actions Email Setup Guide

## Quick Setup (5 minutes)

### Step 1: Create SendGrid Account (Free)

1. Go to https://sendgrid.com
2. Sign up for free account (100 emails/day free)
3. Verify your email
4. Go to Settings → API Keys
5. Create new API key (name it "GitHub Actions")
6. Copy the API key (you'll need it in Step 3)

### Step 2: Add GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret** and add these:

#### Required Secrets:

**SENDGRID_API_KEY**
- Value: Your SendGrid API key from Step 1

**SENDGRID_FROM_EMAIL**
- Value: Your verified SendGrid email (e.g., `your-email@example.com`)
- Note: Must be verified in SendGrid

**EMAIL_SUBSCRIBERS**
- Value: `chemipoo@hotmail.com,sobh.bekhair@outlook.com`
- Format: Comma-separated list (no spaces)

### Step 3: Verify Setup

1. Go to **Actions** tab in your GitHub repository
2. Click **Weekly Technical Analysis Report** workflow
3. Click **Run workflow** button (top right)
4. Select branch (usually `main` or `master`)
5. Click **Run workflow**

The workflow will:
- Generate fresh data
- Create visualizations
- Send emails to subscribers

### Step 4: Test Email

After first run, check:
- ✅ GitHub Actions shows "green checkmark" (success)
- ✅ Subscribers receive email
- ✅ Email contains HTML report

---

## Manual Trigger

You can trigger the workflow manually anytime:

1. Go to **Actions** tab
2. Click **Weekly Technical Analysis Report**
3. Click **Run workflow** button
4. Select branch and click **Run workflow**

---

## Schedule

The workflow runs automatically:
- **Every Sunday at 5:00 PM UTC**
- You can also trigger manually anytime

---

## Troubleshooting

### Email not sending?

1. Check SendGrid API key is correct
2. Verify FROM_EMAIL is verified in SendGrid
3. Check GitHub Actions logs for errors
4. Ensure EMAIL_SUBSCRIBERS is set correctly

### Workflow failing?

1. Check **Actions** tab for error messages
2. Verify all secrets are set correctly
3. Check Python dependencies are in requirements.txt

### Need to change subscribers?

1. Go to **Settings** → **Secrets** → **Actions**
2. Edit **EMAIL_SUBSCRIBERS** secret
3. Update the comma-separated list
4. Save changes

---

## Alternative: Use SMTP (Gmail)

If you prefer Gmail instead of SendGrid:

1. Enable 2-factor authentication on Gmail
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Add these secrets instead:

**SMTP_SERVER**: `smtp.gmail.com`
**SMTP_PORT**: `587`
**SMTP_USER**: `your-email@gmail.com`
**SMTP_PASSWORD**: `your-app-password`
**SMTP_FROM_EMAIL**: `your-email@gmail.com`

The script will automatically use SMTP if SendGrid is not configured.

---

## Current Subscribers

- chemipoo@hotmail.com
- sobh.bekhair@outlook.com

To add/remove subscribers, edit the **EMAIL_SUBSCRIBERS** secret in GitHub.
