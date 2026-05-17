"""
Platform Base Class
Abstract interface for marketplace automation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class PlatformAPIError(Exception):
    """Raised when platform API call fails"""
    pass


class ListingAlreadyExistsError(PlatformAPIError):
    """Raised when trying to create duplicate listing"""
    pass


class PlatformInterface(ABC):
    """Abstract base class for all marketplace integrations"""
    
    PLATFORM_NAME: str = NotImplemented
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to platform API"""
        pass
    
    @abstractmethod
    def create_listing(self, title: str, description: str, price: float, 
                       image_urls: List[str], condition: str) -> Dict[str, Any]:
        """Create a new product listing on the platform"""
        pass
    
    @abstractmethod
    def update_listing(self, listing_id: str, **kwargs) -> bool:
        """Update an existing listing"""
        pass
    
    @abstractmethod
    def delete_listing(self, listing_id: str) -> bool:
        """Delete/remove a listing from the platform"""
        pass
    
    @abstractmethod
    def get_listings(self, status: str = "active") -> List[Dict[str, Any]]:
        """Get all listings on this platform"""
        pass
    
    @abstractmethod
    def check_sale_status(self, listing_id: str) -> Optional[str]:
        """Check if a listing has been sold (returns None if still active)"""
        pass
    
    @abstractmethod
    def get_sales_history(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get sales from last N days for sync monitoring"""
        pass


class BasePlatform(PlatformInterface):
    """Base implementation with common utilities"""
    
    def __init__(self, config: Dict[str, Any], api_key: str = None):
        self.config = config
        self.api_key = api_key
        self.connected = False
    
    @property
    def platform_name(self) -> str:
        return self.PLATFORM_NAME
    
    def connect(self) -> bool:
        """Basic connection - override in subclasses"""
        # Placeholder for actual API authentication
        self.connected = True
        return True
    
    def _validate_listing_data(self, title: str, description: str, price: float) -> List[str]:
        """Validate listing data before posting"""
        issues = []
        
        if not title or len(title) > 140:
            issues.append("Title must be 1-140 characters")
        
        if not description or len(description) < 50:
            issues.append("Description must be at least 50 characters")
        
        if price <= 0 or price > 99999:
            issues.append(f"Price must be between $0.01 and $99,999 (got ${price})")
        
        return issues
    
    def _format_image_urls(self, image_paths: List[str]) -> List[str]:
        """Convert local paths to usable URLs"""
        # In real implementation: upload images to CDN/hosted storage first
        # Return placeholder URLs or actual CDN links
        return [f"https://cdn.example.com/images/{Path(p).name}" for p in image_paths]
