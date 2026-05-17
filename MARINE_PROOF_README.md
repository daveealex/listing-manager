# 📦 Listings Manager - Marine Proof Edition

**Simple AI-powered product listing for eBay, Poshmark & Mercari**

Designed for **non-technical users** - everything works in your browser!

---

## 🚀 Quick Start (2 Minutes)

### Step 1: Launch the App

**On Windows:** Double-click `Start_Listings_Manager.bat`

**On Linux/Mac:** Run `./start.sh` or `python run.py`

A browser window will open automatically to **http://localhost:8000**

### Step 2: Configure AI Server (First Time Only)

1. Click **"⚙️ Configure AI Settings"** on the dashboard
2. Enter your LM Studio server URL:
   - If AI model is on **this computer**: `http://localhost:1234/v1`
   - If AI model is on **another machine** (like AMD server): `http://192.168.1.137:1234/v1`
3. Click outside the box to save automatically

### Step 3: Start Uploading Products!

Choose one of two modes:

| Mode | When to Use | How |
|------|-------------|-----|
| **Single File Upload** | Quick, manual uploads | Drag & drop photos or click to browse |
| **Folder Monitor** | Daily bulk processing | Select a folder → new items auto-process |

---

## 📊 Understanding the Dashboard

### Processing Queue Status

| Icon | Meaning | Action Needed |
|------|---------|---------------|
| 📥 Pending | File uploaded, waiting for AI analysis | Wait... |
| 🤖 Analyzing... | AI is processing your photo | Wait... |
| ✅ Done | Analysis successful, ready to post | Click ✓ Post |
| ⚠️ Needs Review | Low confidence or flagged content | Review AI's guess |

### Confidence Scores

- **85%+** = Very reliable, safe to auto-post
- **70-84%** = Good, but review recommended  
- **Below 70%** = AI is unsure, manual entry advised

---

## ⚙️ Settings Explained

### LM Studio Server URL
Where your AI model lives:
- `http://localhost:1234/v1` = Model on same computer (fastest)
- `http://[IP]:1234/v1` = Model on another machine (like AMD server)

### Primary Model Name
The exact name of the vision model loaded in LM Studio. Common options:
- `llama3-llava-next-8b` - Fast, good for most items
- `bakllava` - Alternative if llama3 doesn't work
- Check your LM Studio model list to find the exact name

### Confidence Threshold (0.0-1.0)
How strict should AI be before flagging for review?
- **0.75** = Recommended balance of speed & accuracy
- **Lower** = More auto-posting but higher error risk
- **Higher** = More reviews needed but safer

---

## 🌐 Platform Posting (Future Feature)

Currently the app analyzes products and prepares listings. For actual posting to marketplaces:

1. Get API credentials from eBay/Poshmark/Mercari
2. Update `platforms/*.py` files with OAuth tokens
3. Enable "Auto-Post" in settings (coming soon!)

---

## 📁 File Organization

The app creates these folders automatically:

```
listing-manager/
├── inventory/
│   ├── uploaded/      # Files you drop here get processed
│   └── processed/     # Successfully analyzed items
├── logs/              # Activity logs for troubleshooting
└── run.py             # Launch file (double-click this!)
```

---

## 🐛 Troubleshooting

### "Dashboard won't start"
- Make sure Python is installed: `python --version`
- Install dependencies: `pip install -r requirements.txt`
- Port 8000 might be in use → change port in `run.py`

### "AI analysis keeps failing"
- Check LM Studio server is running (green status bar)
- Verify model name matches exactly what's loaded in LM Studio
- Try a different vision model if problems persist

### "Can't connect to AI server"
- If using remote machine, ensure firewall allows port 1234
- Test connection: `curl http://[IP]:1234/v1/models`
- Check IP address is correct (ask your network admin)

---

## 💡 Tips for Best Results

1. **Good lighting** - Well-lit photos help AI extract accurate details
2. **Clear focus** - Blurry images reduce confidence scores
3. **Show all angles** - Upload multiple photos per item if possible
4. **Include labels/tags** - Brand names, sizes visible in photos improve accuracy

---

## 📞 Support

For questions or issues:
- Check `logs/app.log` for detailed error messages
- Review the AI analysis results before posting to ensure accuracy
- Start with low-value items to test the workflow

---

**Made with ❤️ for non-technical users who just want to sell their stuff!**
