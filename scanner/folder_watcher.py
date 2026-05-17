"""
Folder Scanner Module
Monitors input folder for new product photos to process
"""

import logging
import time
from pathlib import Path
from typing import List, Optional, Callable
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

logger = logging.getLogger(__name__)


class ProductScanHandler(FileSystemEventHandler):
    """Handles file system events for product scanning"""
    
    def __init__(self, scan_callback: Callable[[str], None]):
        self.scan_callback = scan_callback
        self.processed_files = set()
        
    def on_created(self, event):
        """Called when a new file is created/added to folder"""
        if isinstance(event, FileCreatedEvent) and not event.is_directory:
            path = Path(event.src_path)
            
            # Only process image files
            if self._is_image_file(path):
                logger.info(f"New product photo detected: {path.name}")
                
                # Skip if already processed
                if str(path) in self.processed_files:
                    return
                
                # Queue for processing
                self.scan_callback(str(path))


class FolderScanner:
    """Monitors directory for new items to process"""
    
    SUPPORTED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    
    def __init__(self, config: dict):
        self.config = config.get("scanner", {})
        
        # Folder paths
        self.input_folder = Path(self.config.get("input_folder", "./inventory/input"))
        self.processed_folder = Path(self.config.get("processed_folder", "./inventory/processed"))
        self.failed_folder = Path(self.config.get("failed_folder", "./inventory/failed"))
        
        # Ensure folders exist
        for folder in [self.input_folder, self.processed_folder, self.failed_folder]:
            folder.mkdir(parents=True, exist_ok=True)
            logger.info(f"Scanner folder ready: {folder}")
    
    def _is_image_file(self, path: Path) -> bool:
        """Check if file is a supported image format"""
        return path.suffix.lower() in self.SUPPORTED_EXTENSIONS
    
    def scan_existing_folder(self) -> List[str]:
        """Scan input folder for unprocessed items"""
        processed_items = []
        
        logger.info(f"Scanning {self.input_folder} for new items...")
        
        for item_path in self.input_folder.iterdir():
            if not item_path.is_file():
                continue
            
            if not self._is_image_file(item_path):
                continue
            
            # Check if already processed (look for corresponding entry in database)
            # For now, assume all images are new
            
            logger.info(f"Found unprocessed image: {item_path.name}")
            processed_items.append(str(item_path))
        
        return processed_items
    
    def start_monitoring(self, on_scan: Callable[[str], None]):
        """Start watching folder for new files"""
        
        handler = ProductScanHandler(on_scan)
        observer = Observer()
        observer.schedule(handler, str(self.input_folder), recursive=False)
        observer.start()
        
        logger.info(f"Started monitoring {self.input_folder}")
        return observer
    
    def stop_monitoring(self, observer):
        """Stop folder monitoring"""
        if observer:
            observer.stop()
            observer.join()
            logger.info("Stopped folder monitoring")
    
    def move_to_processed(self, source_path: str):
        """Move processed item to processed folder"""
        try:
            src = Path(source_path)
            dest = self.processed_folder / src.name
            
            # Check if destination exists, add timestamp suffix if needed
            if dest.exists():
                stem = src.stem
                suffix = src.suffix
                counter = 1
                while (self.processed_folder / f"{stem}_{counter}{suffix}").exists():
                    counter += 1
                dest = self.processed_folder / f"{stem}_{counter}{suffix}"
            
            src.rename(dest)
            logger.info(f"Moved {src.name} to processed folder")
            
        except Exception as e:
            logger.error(f"Failed to move {source_path}: {e}")
    
    def move_to_failed(self, source_path: str, reason: str):
        """Move item that failed processing"""
        try:
            src = Path(source_path)
            dest = self.failed_folder / f"{src.name}_{int(time.time())}.log"
            
            # Write failure log
            with open(dest, 'w') as f:
                f.write(f"Failed to process: {src.name}\n")
                f.write(f"Reason: {reason}\n")
                f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            # Also move original image for review
            dest_img = self.failed_folder / src.name
            if not dest_img.exists():
                src.rename(dest_img)
            
            logger.info(f"Moved {src.name} to failed folder with log: {dest.name}")
            
        except Exception as e:
            logger.error(f"Failed to handle error for {source_path}: {e}")


def create_scanner(config: dict) -> FolderScanner:
    """Factory function"""
    return FolderScanner(config)
