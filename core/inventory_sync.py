"""
Inventory Sync Engine
Monitors marketplace sales and auto-duplicates products across platforms.
Handles relisting schedules for rank boosting.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ListingStatus(Enum):
    ACTIVE = "active"
    SOLD = "sold"
    EXPIRED = "expired"
    DRAFT = "draft"
    PENDING_RELIST = "pending_relist"


@dataclass
class PlatformListing:
    """Represents a single listing on a marketplace"""
    platform: str
    listing_id: str
    product_title: str
    status: ListingStatus
    created_at: datetime
    last_updated: datetime
    relist_scheduled: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "platform": self.platform,
            "listing_id": self.listing_id,
            "product_title": self.product_title,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "relist_scheduled": self.relist_scheduled.isoformat() if self.relist_scheduled else None
        }


@dataclass 
class InventoryItem:
    """Represents a product across all platforms"""
    item_id: str
    title: str
    description: str
    price: float
    original_image: str
    
    # Platform listings (one per marketplace)
    listings: Dict[str, PlatformListing] = field(default_factory=dict)
    
    last_synced: Optional[datetime] = None
    
    def add_listing(self, platform: str, listing_id: str):
        """Add a new listing for this item"""
        now = datetime.now()
        self.listings[platform] = PlatformListing(
            platform=platform,
            listing_id=listing_id,
            product_title=self.title,
            status=ListingStatus.ACTIVE,
            created_at=now,
            last_updated=now
        )
        logger.info(f"Added {platform} listing for item {self.item_id}")
    
    def mark_sold(self, platform: str):
        """Mark item as sold on one platform"""
        if platform in self.listings:
            now = datetime.now()
            self.listings[platform].status = ListingStatus.SOLD
            self.listings[platform].last_updated = now
            
            # Auto-duplicate to other platforms
            logger.info(f"Item {self.item_id} sold on {platform}, auto-duplicating...")
            self._auto_duplicate(platform)
            
            # Schedule relist for sold platform after X days
            config = load_config()
            relist_days = config.get("platforms", {}).get(platform, {}).get("auto_relist_days", 30)
            self.listings[platform].relist_scheduled = now + timedelta(days=relist_days)
    
    def _auto_duplicate(self, sold_platform: str):
        """Duplicate listing to all other platforms"""
        for platform in ["ebay", "poshmark", "mercari"]:
            if platform != sold_platform and platform not in self.listings:
                # In real implementation: create new listing via API
                logger.info(f"Auto-duplicating {self.title} to {platform}")


class InventorySyncEngine:
    """Main sync engine for cross-platform inventory management"""
    
    def __init__(self, db_path: str = "./data/listings.db"):
        self.db_path = Path(db_path)
        self.listings_db: Dict[str, InventoryItem] = {}  # In-memory cache
        
        logger.info(f"Inventory sync engine initialized at {db_path}")
    
    def load_from_database(self):
        """Load inventory state from database"""
        # TODO: Implement SQLite loading
        pass
    
    def save_to_database(self):
        """Save current state to database"""
        # TODO: Implement SQLite saving
        pass
    
    def scan_for_sales(self) -> List[str]:
        """Scan all platforms for sold items"""
        sold_items = []
        
        # In real implementation: query marketplace APIs/webhooks
        # For now, placeholder logic
        
        return sold_items
    
    def process_sold_item(self, item_id: str, platform: str):
        """Process a sold item - duplicate and schedule relist"""
        if item_id not in self.listings_db:
            logger.warning(f"Unknown item {item_id} marked as sold")
            return
        
        item = self.listings_db[item_id]
        item.mark_sold(platform)
        self.save_to_database()
    
    def check_relist_schedule(self) -> List[str]:
        """Find items ready for relisting"""
        now = datetime.now()
        ready_for_relist = []
        
        for item_id, item in self.listings_db.items():
            for platform, listing in item.listings.items():
                if (listing.status == ListingStatus.EXPIRED and 
                    listing.relist_scheduled and 
                    listing.relist_scheduled <= now):
                    
                    ready_for_relist.append(item_id)
        
        return ready_for_relist
    
    def get_active_listings(self, platform: str = None) -> List[Dict]:
        """Get all active listings, optionally filtered by platform"""
        results = []
        
        for item in self.listings_db.values():
            for p, listing in item.listings.items():
                if (listing.status == ListingStatus.ACTIVE and 
                    (platform is None or p == platform)):
                    
                    results.append({
                        "item_id": item.item_id,
                        "title": item.title,
                        "price": item.price,
                        "platform": p,
                        "listing_id": listing.listing_id,
                        "created_at": listing.created_at.isoformat()
                    })
        
        return results


def load_config():
    """Load configuration from settings file"""
    import yaml
    with open("./config/settings.yaml", 'r') as f:
        return yaml.safe_load(f)
