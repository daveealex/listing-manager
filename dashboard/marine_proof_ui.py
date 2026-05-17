"""
Enhanced Dashboard for Tracey - Marine Proof Edition
FINAL VERSION WITH PROPER STATIC FILE MOUNTING
"""

import logging
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import shutil
from pathlib import Path
import asyncio
import random

logger = logging.getLogger(__name__)

app = FastAPI(title="Listing Manager - Marine Proof Dashboard", version="1.0")


# Mount static files BEFORE defining routes (must be done at startup)
static_dir = Path("./dashboard/static").resolve()
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

logger.info(f"Static files mounted from: {static_dir}")


# Settings state (loaded from config)
settings_state = {
    "ai_parser": {
        "lmstudio_url": "http://localhost:1234/v1",
        "primary_model": "llama3-llava-next-8b",
        "confidence_threshold": 0.75
    },
    "platforms": {
        "ebay": {"enabled": True},
        "poshmark": {"enabled": True},
        "mercari": {"enabled": True}
    }
}

# Processing queue (in-memory for UI)
processing_queue: List[Dict] = []


def get_dashboard_html(total_files: int, analyzed: int, flagged: int):
    """Return the dashboard HTML"""
    
    # Extract settings from global state for template
    lmstudio_url = settings_state['ai_parser']['lmstudio_url']
    primary_model = settings_state['ai_parser']['primary_model']
    confidence_threshold = settings_state['ai_parser']['confidence_threshold']
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Listings Manager - Marine Proof</title>
    <style>
        :root {{--primary:#2563eb;--success:#16a34a;--warning:#ca8a04;--danger:#dc2626}}
        * {{box-sizing:border-box;margin:0;padding:0;font-family:sans-serif}}
        body {{background:#f8fafc;color:#1e293b}}
        .container {{max-width:1200px;margin:0 auto;padding:2rem}}
        header {{background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;padding:2rem;border-radius:12px;margin-bottom:2rem}}
        h1 {{font-size:1.75rem;margin:.5rem 0}}
        .stats-grid {{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;margin-bottom:2rem}}
        .stat-card {{background:#fff;padding:1.5rem;border-radius:8px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
        .stat-value {{font-size:2rem;font-weight:700;color:#2563eb}}
        .stat-label {{color:#64748b}}
        .section {{background:#fff;padding:1.5rem;border-radius:8px;margin-bottom:1rem;box-shadow:0 1px 3px rgba(0,0,0,.1)}}
        h2 {{font-size:1.25rem;margin-bottom:1rem;border-bottom:1px solid #e2e8f0;padding-bottom:.5rem}}
        .btn {{background:#2563eb;color:#fff;padding:.75rem 1.5rem;border-radius:6px;font-weight:500;cursor:pointer;border:none;margin-right:.5rem}}
        .btn:hover {{background:#1d4ed8}}
        .btn-success {{background:#16a34a}}.btn-success:hover {{background:#15803d}}
        .btn-warning {{background:#ca8a04}}.btn-warning:hover {{background:#a16207}}
        .upload-zone {{border:2px dashed #e2e8f0;border-radius:8px;padding:3rem;text-align:center;cursor:pointer;background:#fafafa;margin-bottom:1rem}}
        .upload-zone:hover {{border-color:#2563eb;background:#eff6ff}}
        .status-badge {{display:inline-block;padding:.25rem .75rem;border-radius:999px;font-size:.85rem}}
        .status-pending {{background:#fef3c7;color:#92400e}}
        .status-analyzing {{background:#dbeafe;color:#1e40af;animation:pulse 2s infinite}}
        .status-analyzed {{background:#dcfce7;color:#166534}}
        .status-flagged {{background:#fee2e2;color:#991b1b}}
        @keyframes pulse {{0%,100%{{opacity:1}}50%{{opacity:.7}}}}
        .settings-panel {{display:none;margin-top:1rem}}.settings-panel.show {{display:block}}
        label {{display:block;font-weight:500;margin-bottom:.5rem}}
        input[type="text"],input[type="number"] {{width:100%;padding:.75rem;border:1px solid #e2e8f0;border-radius:6px}}
        .queue-table {{width:100%;border-collapse:collapse}}
        .queue-table th,.queue-table td {{padding:.75rem;text-align:left;border-bottom:1px solid #e2e8f0}}
        .queue-table th {{background:#f8fafc;font-weight:600}}
    </style>
</head>
<body>
<div class="container">
<header><h1>📦 Listings Manager - Marine Proof Edition</h1><p style="opacity:.9;margin:.5rem 0">Simple AI-powered product listing for eBay, Poshmark & Mercari</p></header>

<div class="stats-grid">
    <div class="stat-card"><div class="stat-value">{total_files}</div><div class="stat-label">Files Loaded</div></div>
    <div class="stat-card"><div class="stat-value">{analyzed}</div><div class="stat-label">Analyzed</div></div>
    <div class="stat-card"><div class="stat-value">{flagged}</div><div class="stat-label">Need Review</div></div>
</div>

<div class="section">
    <h2>📤 Upload Products</h2>
    <button type="button" onclick="showUploadMode('single')" id="btn-single" class="btn btn-success">Single File Upload</button>
    <button type="button" onclick="showUploadMode('folder')" id="btn-folder" class="btn">Folder Monitor</button>
    
    <div id="upload-single"><input type="file" id="file-input" accept="image/*" multiple onchange="handleFileSelect()" style="display:none">
        <label for="file-input" class="upload-zone" onclick="document.getElementById('file-input').click()">
            <h3 style="color:#1e293b;margin-bottom:.5rem">Click to browse or drag & drop images here</h3>
            <p style="color:#64748b">Supports JPG, PNG, WEBP</p>
        </label>
    </div>
    
    <div id="upload-folder" style="display:none">
        <input type="text" id="folder-path" placeholder="/path/to/your/products/folder" readonly style="width:100%;padding:.75rem;border:1px solid #e2e8f0;margin-bottom:1rem">
        <button type="button" onclick="selectFolder()" class="btn btn-warning">📁 Select Folder to Monitor</button>
    </div>
</div>

<div class="section"><h2>📋 Processing Queue</h2><table class="queue-table" id="queue-table">
    <thead><tr><th style="width:30%">File Name</th><th style="width:15%">Status</th><th style="width:40%">AI Analysis</th><th style="width:15%">Actions</th></tr></thead>
    <tbody id="queue-body"></tbody>
</table></div>

<div class="section settings-panel" id="settings-panel">
    <h2>⚙️ AI & Server Settings</h2>
    <label for="setting-lmstudio-url">LM Studio Server URL</label>
    <input type="text" id="setting-lmstudio-url" value="{lmstudio_url}" onchange="saveSettings()">
    
    <label for="setting-primary-model" style="margin-top:1rem">Primary Model Name</label>
    <input type="text" id="setting-primary-model" value="{primary_model}">
    
    <label for="setting-threshold" style="margin-top:1rem">Confidence Threshold (0.0-1.0)</label>
    <input type="number" step="0.05" min="0" max="1" id="setting-threshold" value="{confidence_threshold}" onchange="saveSettings()">
</div>

<button type="button" onclick="toggleSettings()" id="settings-toggle-btn" class="btn">⚙️ Configure AI Settings</button>
</div>

<script src="/static/app.js"></script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    total_files = len(processing_queue)
    analyzed = sum(1 for f in processing_queue if f['status'] == 'analyzed')
    flagged = sum(1 for f in processing_queue if f.get('needs_review'))
    
    html_content = get_dashboard_html(total_files, analyzed, flagged)
    return HTMLResponse(content=html_content)


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    file_id = f"file_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:6]}"
    filename = file.filename
    
    temp_path = Path("./inventory/uploaded") / f"{file_id}_{filename}"
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    processing_queue.append({
        "id": file_id,
        "filename": filename,
        "status": "pending",
        "confidence": 0,
        "analysis": None,
        "needs_review": False,
        "uploaded_at": datetime.now()
    })
    
    logger.info(f"File uploaded: {filename} (ID: {file_id})")
    return {"success": True, "file_id": file_id}


@app.post("/api/analyze/{file_id}")
async def analyze_file(file_id: str):
    item = next((i for i in processing_queue if i['id'] == file_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        await asyncio.sleep(0.5)  # Simulate delay
        
        mock_analysis = {
            "title": f"Beautiful Item - {{item['filename'].split('.')[0]}}",
            "description": "AI will extract details from your product photo.",
            "price": round(random.uniform(19.99, 149.99), 2),
            "condition": random.choice(["new", "like new", "good"]),
            "category": random.choice(["cars", "dolls", "collectibles"])
        }
        
        needs_review = random.random() < 0.3
        confidence = random.uniform(0.6, 0.95) if not needs_review else random.uniform(0.4, 0.7)
        
        item['analysis'] = mock_analysis
        item['confidence'] = confidence
        item['needs_review'] = needs_review
        
        return JSONResponse(content={
            "success": True,
            "result": mock_analysis,
            "confidence": round(confidence, 2),
            "needs_review": needs_review
        })
    except Exception as e:
        logger.error(f"Analysis failed for {file_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/settings")
async def save_settings(settings: dict):
    global settings_state
    
    if 'lmstudio_url' in settings:
        settings_state['ai_parser']['lmstudio_url'] = settings['lmstudio_url']
    if 'primary_model' in settings:
        settings_state['ai_parser']['primary_model'] = settings['primary_model']
    if 'confidence_threshold' in settings:
        settings_state['ai_parser']['confidence_threshold'] = settings['confidence_threshold']
    
    logger.info(f"Settings updated: {settings}")
    return {"success": True, "message": "Settings saved"}


if __name__ == "__main__":
    import uvicorn
    
    for folder in ["./inventory/uploaded", "./logs"]:
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("  📦 Listings Manager - Marine Proof Dashboard")
    print("="*60)
    print("\nStarting web dashboard...")
    print("Open your browser to: http://localhost:8000")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
