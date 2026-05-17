# 📦 Listing Manager - AI-Powered Multi-Platform Sales Tool

**For non-technical users** - Simple dashboard to manage products across eBay, Poshmark, and Mercari automatically.

---

## Quick Start (5 Minutes)

### Step 1: Install Dependencies

Open terminal and run:

```bash
cd ~/listing-manager
pip install -r requirements.txt
```

This installs all required packages (FastAPI for dashboard, requests for APIs, watchdog for folder monitoring).

---

### Step 2: Start LM Studio

Before running the app, you need AI model access:

1. Download [LM Studio](https://lmstudio.ai) (free)
2. Open LM Studio and load a vision model:
   - Click "Download Model"
   - Search for: `llava-next-nearest-34b` or `qwen2.5-vl-7b-instruct`
   - Download one of these models
3. Go to "Server" tab (left sidebar)
4. Load the model you downloaded
5. Click **"Start Server"** (green button at bottom)
6. Make sure it says "Server running on http://localhost:1234/v1"

---

### Step 3: Configure for Your System

Open `config/settings.yaml` and check these settings:

```yaml
ai_parser:
  lmstudio_url: "http://localhost:1234/v1"  # This is correct if LM Studio on same machine
  
models:
  primary: "llava-next-nearest-34b"  # Use the exact model name you loaded in LM Studio
  fast: "qwen2.5-vl-7b-instruct"

platforms:
  ebay:
    enabled: true
    auto_relist_days: 30
    
  poshmark:
    enabled: true
    auto_relist_days: 30
    
  mercari:
    enabled: true
    auto_relist_days: 60
```

**Important:** The model name must match EXACTLY what you see in LM Studio's model list.

---

### Step 4: Run the Dashboard

From terminal (in `~/listing-manager` folder):

```bash
python main.py dashboard
```

Or just run normally first to test:

```bash
python main.py monitor
```

Then open your browser to: **http://localhost:8000**

---

## How to Use Daily

### Adding New Products (Simplest Way)

1. Create folder structure:
   ```
   ~/listing-manager/inventory/input/
   ```

2. Drop product photos into the `input` folder
   
3. The system automatically:
   - Scans for new images every few seconds
   - Analyzes each photo with AI (title, price, condition)
   - Flags items needing review
   - Moves processed items to `processed/` folder

4. Check the dashboard at **http://localhost:8000** to see results

---

### Manual Single Product Scan

From terminal:

```bash
python main.py scan /path/to/product/photo.jpg
```

You'll see extracted details and can approve/reject before posting.

---

## Features Explained

### 🤖 AI Product Analysis
- Extracts title, price, condition from photos
- Confidence score shows how certain the AI is (flag items below 75%)
- Uses your local LM Studio model - no cloud costs

### 🔄 Auto-Sync Across Platforms
When you sell an item on eBay:
1. System marks it as sold
2. Automatically removes listing from Poshmark & Mercari  
3. Schedules relist after X days for fresh visibility boost

### ⏰ Smart Relisting
- eBay listings expire every 30 days → auto-relist with new ID
- Boosts search ranking without manual work
- Configurable per platform in `settings.yaml`

---

## Troubleshooting

### "AI analysis failed" errors
- Make sure LM Studio server is running (green status bar)
- Check model name matches exactly what's loaded in LM Studio
- Try a different model if one fails consistently

### Platform connection issues
- The current version uses simulation mode (no actual API calls yet)
- To enable real posting: get OAuth/API credentials from each platform
- Update `config/settings.yaml` with your keys when ready

### Dashboard won't start on port 8000
- Another service might be using that port
- Edit `settings.yaml` and change dashboard port to something else (e.g., 8080)

---

## Moving to New Machine Later

This system is designed for easy migration:

1. Copy the entire `~/listing-manager/` folder
2. Install dependencies on new machine
3. Run LM Studio with same models
4. Update `lmstudio_url` in config if server IP changes
5. Done! All settings preserved

---

## Support & Questions

- Check `logs/app.log` for detailed error messages
- Review `config/settings.yaml` to adjust timing, model choices
- Items below confidence threshold go to manual review queue

**Happy selling!** 🚀
