"""
Enhanced Dashboard with Settings Panel & File Upload UI
Completely marine-proof interface for Tracey
"""

import logging
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime
import uuid
import shutil

logger = logging.getLogger(__name__)

app = FastAPI(title="Listing Manager - Marine Proof Dashboard", version="1.0")


# Settings state (loaded from config)
settings_state = {
    "ai_parser": {
        "lmstudio_url": "http://localhost:1234/v1",
        "primary_model": "llama3-llava-next-8b",
        "fast_model": "qwen2.5-vl-7b-instruct",
        "temperature": 0.3,
        "confidence_threshold": 0.75
    },
    "platforms": {
        "ebay": {"enabled": True},
        "poshmark": {"enabled": True},
        "mercari": {"enabled": True}
    },
    "scanner": {
        "input_folder": "./inventory/input",
        "auto_scan": False,
        "scan_interval_seconds": 10
    }
}

# Processing queue (in-memory for UI)
processing_queue: List[Dict] = []


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    status: str
    uploaded_at: datetime


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main marine-proof dashboard"""
    
    # Generate summary stats
    total_files = len(processing_queue)
    analyzed = sum(1 for f in processing_queue if f['status'] == 'analyzed')
    flagged = sum(1 for f in processing_queue if f.get('needs_review'))
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Listings Manager - Marine Proof</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #16a34a;
            --warning: #ca8a04;
            --danger: #dc2626;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
            --border: #e2e8f0;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        
        body {{ background: var(--bg); color: var(--text); line-height: 1.6; }}
        
        .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
        
        header {{
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin-bottom: 2rem;
        }}
        
        h1 {{ font-size: 1.75rem; margin-bottom: 0.5rem; }}
        .subtitle {{ opacity: 0.9; font-size: 0.95rem; }}
        
        .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        
        .stat-card {{ background: var(--card-bg); padding: 1.5rem; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); text-align: center; }}
        .stat-value {{ font-size: 2rem; font-weight: bold; color: var(--primary); }}
        .stat-label {{ color: #64748b; font-size: 0.9rem; }}
        
        .section {{ background: var(--card-bg); padding: 1.5rem; border-radius: 8px; margin-bottom: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        h2 {{ font-size: 1.25rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid var(--border); display: flex; align-items: center; gap: 0.5rem; }}
        
        .btn {{ display: inline-block; background: var(--primary); color: white; padding: 0.75rem 1.5rem; border-radius: 6px; text-decoration: none; font-weight: 500; cursor: pointer; border: none; margin-right: 0.5rem; }}
        .btn:hover {{ background: #1d4ed8; }}
        .btn-success {{ background: var(--success); }}
        .btn-warning {{ background: var(--warning); }}
        .btn-danger {{ background: var(--danger); }}
        
        .upload-zone {{
            border: 2px dashed var(--border);
            border-radius: 8px;
            padding: 3rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }}
        .upload-zone:hover {{ border-color: var(--primary); background: #eff6ff; }}
        .upload-zone.dragover {{ border-color: var(--primary); background: #dbeafe; transform: scale(1.02); }}
        
        .file-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; margin-top: 1rem; }}
        
        .file-card {{ border: 1px solid var(--border); border-radius: 8px; padding: 1rem; background: #fafafa; }}
        .file-name {{ font-weight: 600; margin-bottom: 0.5rem; word-break: break-word; }}
        .file-meta {{ font-size: 0.85rem; color: #64748b; margin-bottom: 0.5rem; }}
        
        .status-badge {{ display: inline-block; padding: 0.25rem 0.75rem; border-radius: 999px; font-size: 0.85rem; font-weight: 500; }}
        .status-pending {{ background: #fef3c7; color: #92400e; }}
        .status-analyzing {{ background: #dbeafe; color: #1e40af; animation: pulse 2s infinite; }}
        .status-analyzed {{ background: #dcfce7; color: #166534; }}
        .status-flagged {{ background: #fee2e2; color: #991b1b; }}
        
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.7; }} }}
        
        .analysis-result {{ display: none; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--border); }}
        .analysis-result.show {{ display: block; }}
        
        .settings-panel {{ display: none; }}
        .settings-panel.show {{ display: block; }}
        
        .form-group {{ margin-bottom: 1rem; }}
        label {{ display: block; font-weight: 500; margin-bottom: 0.5rem; color: #374151; }}
        input[type="text"], input[type="number"], select {{ width: 100%; padding: 0.75rem; border: 1px solid var(--border); border-radius: 6px; font-size: 0.95rem; }}
        
        .toggle-row {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.75rem; }}
        .toggle-label {{ color: #4b5563; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📦 Listings Manager - Marine Proof Edition</h1>
            <p class="subtitle">Simple AI-powered product listing for eBay, Poshmark & Mercari</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_files}</div>
                <div class="stat-label">Files Loaded</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{analyzed}</div>
                <div class="stat-label">Analyzed</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{flagged}</div>
                <div class="stat-label">Need Review</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📤 Upload Products</h2>
            
            <!-- File upload mode selector -->
            <div style="margin-bottom: 1rem;">
                <button onclick="showUploadMode('single')" id="btn-single" class="btn btn-success">Single File Upload</button>
                <button onclick="showUploadMode('folder')" id="btn-folder" class="btn">Folder Monitor</button>
            </div>
            
            <!-- Single file upload -->
            <div id="upload-single" style="display: block;">
                <input type="file" id="file-input" accept="image/*" multiple onchange="handleFileSelect()">
                <p style="color: #64748b; margin-top: 0.5rem;">Drag & drop images here, or click to browse</p>
            </div>
            
            <!-- Folder monitoring -->
            <div id="upload-folder" style="display: none;">
                <input type="text" id="folder-path" placeholder="/path/to/your/products/folder" readonly>
                <button onclick="selectFolder()" class="btn btn-warning">📁 Select Folder to Monitor</button>
                <button onclick="toggleAutoScan()" id="auto-scan-btn" class="btn">⏸️ Pause Auto-Scan</button>
                <p style="color: #64748b; margin-top: 0.5rem;">All new images in this folder will be automatically processed</p>
            </div>
        </div>
        
        <!-- Processing Queue -->
        <div class="section">
            <h2>📋 Processing Queue</h2>
            
            <table style="width: 100%; border-collapse: collapse;">
                <thead>
                    <tr style="background: #f8fafc; text-align: left;">
                        <th style="padding: 0.75rem;">File</th>
                        <th style="padding: 0.75rem;">Status</th>
                        <th style="padding: 0.75rem;">AI Analysis</th>
                        <th style="padding: 0.75rem;">Actions</th>
                    </tr>
                </thead>
                <tbody id="queue-table">
                    <!-- Populated by JavaScript -->
                </tbody>
            </table>
        </div>
        
        <!-- Settings Panel (collapsed by default) -->
        <div class="section settings-panel" id="settings-panel">
            <h2>⚙️ AI & Server Settings</h2>
            
            <div class="form-group">
                <label>LM Studio Server URL</label>
                <input type="text" id="setting-lmstudio-url" value="{settings_state['ai_parser']['lmstudio_url']}" onchange="saveSettings()">
            </div>
            
            <div class="form-group">
                <label>Primary Model Name</label>
                <input type="text" id="setting-primary-model" value="{settings_state['ai_parser']['primary_model']}">
            </div>
            
            <div class="form-group">
                <label>Confidence Threshold (0.0-1.0)</label>
                <input type="number" step="0.05" min="0" max="1" id="setting-threshold" value="{settings_state['ai_parser']['confidence_threshold']}" onchange="saveSettings()">
            </div>
            
            <p style="color: #64748b; font-size: 0.9rem;">
                💡 Tip: Lower threshold = more items auto-posted but higher risk of errors<br>
                Recommended: 0.75 (items below this need manual review)
            </p>
        </div>
        
        <button onclick="toggleSettings()" class="btn" style="margin-top: 1rem;">⚙️ Configure AI Settings</button>
    </div>
    
    <script>
        let processingQueue = [];
        const queueTable = document.getElementById('queue-table');
        
        function updateQueue() {{
            queueTable.innerHTML = processingQueue.map((item, index) => `
                <tr>
                    <td style="padding: 0.75rem;">${{item.filename}}</td>
                    <td style="padding: 0.75rem;">
                        <span class="status-badge status-{{item.status}}">{{formatStatus(item.status)}}</span>
                    </td>
                    <td style="padding: 0.75rem; max-width: 200px;">
                        {{item.analysis ? `
                            <div><strong>Title:</strong> ${{item.analysis.title || 'N/A'}}</div>
                            <div><strong>Price:</strong> $${{item.analysis.price?.toFixed(2) || 'N/A'}}</div>
                            <div style="font-size: 0.85rem; color: #64748b;">Confidence: ${{Math.round(item.confidence * 100)}}%</div>
                        ` : '<span class="status-badge status-pending">Waiting...</span>'}}
                    </td>
                    <td style="padding: 0.75rem;">
                        {{item.status === 'analyzed' && item.analysis ? `
                            <button onclick="approveItem(${{index}})" class="btn btn-success" style="padding: 0.35rem 0.75rem; font-size: 0.85rem;">✓ Post</button>
                            <button onclick="rejectItem(${{index}})" class="btn btn-danger" style="padding: 0.35rem 0.75rem; font-size: 0.85rem;">✗ Skip</button>
                        ` : ''}}
                    </td>
                </tr>
            `).join('');
        }}
        
        function formatStatus(status) {{
            const labels = {{
                'pending': '📥 Pending',
                'analyzing': '🤖 Analyzing...',
                'analyzed': '✅ Done',
                'flagged': '⚠️ Needs Review'
            }};
            return labels[status] || status;
        }}
        
        function showUploadMode(mode) {{
            document.getElementById('upload-single').style.display = mode === 'single' ? 'block' : 'none';
            document.getElementById('upload-folder').style.display = mode === 'folder' ? 'block' : 'none';
            document.getElementById('btn-single').className = mode === 'single' ? 'btn btn-success' : 'btn';
            document.getElementById('btn-folder').className = mode === 'folder' ? 'btn btn-warning' : 'btn';
        }}
        
        function toggleSettings() {{
            const panel = document.getElementById('settings-panel');
            panel.classList.toggle('show');
        }}
        
        async function handleFileSelect() {{
            const input = document.getElementById('file-input');
            const files = Array.from(input.files);
            
            for (const file of files) {{
                await uploadFile(file);
            }}
            
            input.value = ''; // Clear selection
        }}
        
        async function uploadFile(file) {{
            const formData = new FormData();
            formData.append('file', file);
            
            try {{
                const response = await fetch('/api/upload', {{ method: 'POST', body: formData }});
                const data = await response.json();
                
                if (data.success) {{
                    processingQueue.push({{
                        id: data.file_id,
                        filename: file.name,
                        status: 'pending',
                        confidence: 0,
                        analysis: null
                    }});
                    updateQueue();
                    
                    // Start analyzing
                    await analyzeFile(data.file_id);
                }}
            }} catch (error) {{
                console.error('Upload failed:', error);
            }}
        }}
        
        async function analyzeFile(fileId) {{
            const item = processingQueue.find(i => i.id === fileId);
            if (!item) return;
            
            item.status = 'analyzing';
            updateQueue();
            
            try {{
                const response = await fetch(`/api/analyze/${{fileId}}`);
                const data = await response.json();
                
                if (data.success) {{
                    item.analysis = data.result;
                    item.confidence = data.confidence;
                    item.status = data.needs_review ? 'flagged' : 'analyzed';
                }} else {{
                    item.status = 'error';
                }}
            }} catch (error) {{
                item.status = 'error';
            }}
            
            updateQueue();
        }}
        
        function approveItem(index) {{
            const item = processingQueue[index];
            alert(`Posting ${{item.filename}} to marketplaces...\\n(This would connect to real platforms in full version)`);
            // TODO: Implement actual posting
        }}
        
        function rejectItem(index) {{
            processingQueue.splice(index, 1);
            updateQueue();
        }}
        
        function selectFolder() {{
            const path = prompt('Enter folder path to monitor (e.g., /home/user/products):');
            if (path) {{
                document.getElementById('folder-path').value = path;
                alert(`Monitoring started for: ${{path}}`);
                // TODO: Implement actual folder monitoring
            }}
        }}
        
        function toggleAutoScan() {{
            const btn = document.getElementById('auto-scan-btn');
            if (btn.textContent.includes('Pause')) {{
                btn.textContent = '⏸️ Pause Auto-Scan';
                alert('Auto-scan paused. New files will not be automatically added.');
            }} else {{
                btn.textContent = '▶️ Resume Auto-Scan';
                alert('Auto-scan resumed!');
            }}
        }}
        
        // Initial load
        updateQueue();
    </script>
</body>
</html>"""

    return HTMLResponse(content=html_content)


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handle file upload and queue for processing"""
    
    file_id = str(uuid.uuid4())[:8]
    filename = file.filename
    
    # Save uploaded file temporarily (in real app, save to input folder)
    temp_path = f"./inventory/uploaded/{file_id}_{filename}"
    Path(temp_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    
    # Add to processing queue
    processing_queue.append({
        "id": file_id,
        "filename": filename,
        "status": "pending",
        "confidence": 0,
        "analysis": None,
        "uploaded_at": datetime.now()
    })
    
    logger.info(f"File uploaded: {filename} (ID: {file_id})")
    
    return FileUploadResponse(
        file_id=file_id,
        filename=filename,
        status="pending",
        uploaded_at=datetime.now()
    ).model_dump()


@app.post("/api/analyze/{file_id}")
async def analyze_file(file_id: str):
    """Analyze an uploaded product image using AI"""
    
    # Find the file in queue
    item = next((i for i in processing_queue if i['id'] == file_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Update status
    item['status'] = 'analyzing'
    
    try:
        # TODO: Call actual AI parser here
        # For now, simulate analysis with mock data
        
        import time
        await asyncio.sleep(2)  # Simulate processing time
        
        # Mock analysis result (replace with real AI call)
        mock_analysis = {
            "title": f"Beautiful {item['filename'].split('.')[0]} Item",
            "description": "This is a sample description. In the real version, AI will extract actual details from your product photo.",
            "price": 49.99,
            "condition": "good",
            "category": "other"
        }
        
        item['analysis'] = mock_analysis
        item['confidence'] = 0.85  # Simulated confidence score
        item['status'] = 'flagged' if random.random() < 0.3 else 'analyzed'
        
        return JSONResponse(content={
            "success": True,
            "result": mock_analysis,
            "confidence": item['confidence'],
            "needs_review": item['status'] == 'flagged'
        })
        
    except Exception as e:
        logger.error(f"Analysis failed for {file_id}: {e}")
        item['status'] = 'error'
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/queue")
async def get_queue():
    """Get current processing queue status"""
    return {"items": processing_queue}


if __name__ == "__main__":
    import uvicorn
    from pathlib import Path
    
    # Create necessary directories
    for folder in ["./inventory/uploaded", "./logs"]:
        Path(folder).mkdir(parents=True, exist_ok=True)
    
    print("="*60)
    print("  📦 Listings Manager - Marine Proof Dashboard")
    print("="*60)
    print("\nStarting web dashboard...")
    print("Open your browser to: http://localhost:8000")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
