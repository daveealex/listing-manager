"""
Web Dashboard - FastAPI Backend
Simple UI for non-technical users to manage listings
"""

import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

app = FastAPI(title="Listing Manager Dashboard", version="0.1.0")


# Data models for API
class ProductRequest(BaseModel):
    title: str
    description: str
    price: float
    condition: str = "good"
    category: str = "other"


class ListingResponse(BaseModel):
    item_id: str
    platform: str
    listing_url: str
    status: str
    created_at: datetime


# In-memory storage (replace with real database later)
inventory_db = {}
active_listings = []


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main dashboard page"""
    
    # Generate summary stats
    total_items = len(inventory_db)
    active_count = sum(1 for item in inventory_db.values() 
                       if any(l.status == "active" for l in item.get("listings", [])))
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Listing Manager Dashboard</title>
    <style>
        :root {{
            --primary: #2563eb;
            --success: #16a34a;
            --warning: #ca8a04;
            --danger: #dc2626;
            --bg: #f8fafc;
            --card-bg: #ffffff;
            --text: #1e293b;
        }}
        
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
        }}
        
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
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .stat-value {{ font-size: 2rem; font-weight: bold; color: var(--primary); }}
        .stat-label {{ color: #64748b; font-size: 0.9rem; }}
        
        .section {{
            background: var(--card-bg);
            padding: 1.5rem;
            border-radius: 8px;
            margin-bottom: 1rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        h2 {{ font-size: 1.25rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid #e2e8f0; }}
        
        .btn {{
            display: inline-block;
            background: var(--primary);
            color: white;
            padding: 0.75rem 1.5rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 500;
            cursor: pointer;
            border: none;
        }}
        
        .btn:hover {{ background: #1d4ed8; }}
        
        .listings-table {{ width: 100%; border-collapse: collapse; }}
        .listings-table th, .listings-table td {{ 
            padding: 0.75rem; 
            text-align: left;
            border-bottom: 1px solid #e2e8f0;
        }}
        
        .listings-table th {{ background: #f1f5f9; font-weight: 600; }}
        
        .status-badge {{
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 500;
        }}
        
        .status-active {{ background: #dcfce7; color: #166534; }}
        .status-sold {{ background: #fee2e2; color: #991b1b; }}
        
        .empty-state {{ text-align: center; padding: 2rem; color: #64748b; }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📦 Listing Manager Dashboard</h1>
            <p class="subtitle">AI-Powered Multi-Platform Sales Management</p>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{total_items}</div>
                <div class="stat-label">Total Items</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{active_count}</div>
                <div class="stat-label">Active Listings</div>
            </div>
        </div>
        
        <div class="section">
            <h2>🚀 Quick Actions</h2>
            <p style="margin-bottom: 1rem; color: #64748b;">
                Drop product photos in the input folder to auto-process, or use the API to add listings.
            </p>
            <a href="/docs" class="btn">API Documentation</a>
        </div>
        
        <div class="section">
            <h2>📋 Active Listings</h2>
            
            {'<table class="listings-table"><thead><tr><th>Title</th><th>Platform</th><th>Status</th><th>Created</th></tr></thead><tbody>' if active_listings else ''}
            
            {"".join(f'<tr><td>{l.title}</td><td>{l.platform}</td><td><span class="status-badge status-active">Active</span></td><td>{datetime.now().strftime("%Y-%m-%d")}</td></tr>' for l in active_listings[:10])}
            
            {'</tbody></table>' if active_listings else '<div class="empty-state">No active listings yet. Add your first product!</div>'}
        </div>
    </div>
</body>
</html>"""

    return HTMLResponse(content=html_content)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/api/products")
async def create_product(product: ProductRequest):
    """Create a new product entry"""
    
    item_id = f"item_{int(datetime.now().timestamp())}"
    
    inventory_db[item_id] = {
        "title": product.title,
        "description": product.description,
        "price": product.price,
        "condition": product.condition,
        "category": product.category,
        "listings": []
    }
    
    logger.info(f"Created product: {product.title}")
    
    return {"item_id": item_id, "status": "created"}


@app.get("/api/products")
async def list_products():
    """List all products"""
    return list(inventory_db.values())


@app.get("/api/listings")
async def list_listings(status: Optional[str] = None):
    """List active listings with details"""
    
    if status:
        filtered = [l for l in active_listings if l.status == status]
    else:
        filtered = active_listings
    
    return JSONResponse(content=[
        {
            "item_id": l.item_id,
            "platform": l.platform,
            "listing_url": l.listing_url,
            "status": l.status,
            "created_at": l.created_at.isoformat()
        }
        for l in filtered
    ])


@app.post("/api/sync")
async def trigger_sync():
    """Trigger inventory sync check"""
    
    logger.info("Manual sync triggered via API")
    
    # TODO: Actually perform sync logic
    
    return {"status": "sync_triggered"}
