# Reddit App Setup - Step by Step

## Creating Your Reddit App

When creating a Reddit app for script use, here's exactly what to fill in:

### Step-by-Step Instructions

1. **Go to**: https://www.reddit.com/prefs/apps
2. **Scroll down** and click the **"create another app..."** button
3. **Fill in the form**:

```
Name: TechnicalAnalysisBot
     ↑ (or any name you want - this is just for your reference)

Type: [script] ← Select "script" from dropdown
     ↑ (This is important! Must be "script" type)

Description: Stock analysis bot
            ↑ (Optional - can be anything or leave blank)

About URL: (leave blank)
         ↑ (Not used for scripts - can be empty)

Redirect URI: http://localhost:8080
            ↑ (Required field but not used for scripts - use any URL)
```

4. **Click "create app"**

### What You'll See After Creation

After creating the app, you'll see a box with your app details:

```
┌─────────────────────────────────────┐
│  TechnicalAnalysisBot               │
│  (script)                           │
│                                     │
│  client_id: abc123xyz456            │ ← This is your CLIENT_ID
│                                     │
│  secret: [edit]                    │ ← Click "edit" to see CLIENT_SECRET
└─────────────────────────────────────┘
```

### Getting Your Credentials

1. **client_id**: 
   - It's the string shown directly under your app name
   - Looks like: `abc123xyz456` or `random_characters`
   - Copy this exactly

2. **client_secret**:
   - Click the **"edit"** button next to "secret"
   - The secret will be revealed
   - Copy this exactly (it's longer, like: `abc123xyz456_secret_key_here`)

### Important Notes

- **Redirect URI**: For script type apps, this is required but **not actually used**. You can put:
  - `http://localhost:8080` (recommended)
  - `http://localhost`
  - `http://127.0.0.1:8080`
  - Any URL - it doesn't matter for scripts

- **About URL**: Can be left blank for script apps

- **Type**: Must be **"script"** - don't use "web app" or "installed app"

### Setting Environment Variables

After you have your credentials:

**macOS/Linux:**
```bash
export REDDIT_CLIENT_ID="your_client_id_here"
export REDDIT_CLIENT_SECRET="your_client_secret_here"
```

**Windows (Command Prompt):**
```cmd
set REDDIT_CLIENT_ID=your_client_id_here
set REDDIT_CLIENT_SECRET=your_client_secret_here
```

**Windows (PowerShell):**
```powershell
$env:REDDIT_CLIENT_ID="your_client_id_here"
$env:REDDIT_CLIENT_SECRET="your_client_secret_here"
```

### Testing

After setting environment variables, test with:

```bash
python discover_hot_stocks.py --dry-run
```

If it works, you'll see it connecting to Reddit and searching for stocks!
