"""
Listing Manager - Main Entry Point
CLI tool for managing product listings across multiple marketplaces
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import yaml
from core.ai_parser import create_parser, ProductParser
from core.moderation import ContentModerator, create_moderator
from core.inventory_sync import InventorySyncEngine
from scanner.folder_watcher import FolderScanner, create_scanner
from platforms.ebay import eBayPlatform
from platforms.poshmark import PoshmarkPlatform
from platforms.mercari import MercariPlatform


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("./logs/app.log")
    ]
)

logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from YAML file"""
    config_path = Path("./config/settings.yaml")
    
    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def init_platforms(config):
    """Initialize all marketplace platform integrations"""
    platforms = {}
    
    if config["platforms"]["ebay"]["enabled"]:
        platforms["ebay"] = eBayPlatform(config)
        
    if config["platforms"]["poshmark"]["enabled"]:
        platforms["poshmark"] = PoshmarkPlatform(config)
        
    if config["platforms"]["mercari"]["enabled"]:
        platforms["mercari"] = MercariPlatform(config)
    
    return platforms


def process_single_item(image_path: str, parser: ProductParser, moderator: ContentModerator):
    """Process a single product image"""
    
    print(f"\n{'='*60}")
    print(f"Processing: {Path(image_path).name}")
    print('=' * 60)
    
    try:
        # Step 1: AI Analysis
        print("🔍 Analyzing with AI...")
        analysis = parser.analyze(image_path)
        
        print(f"\n📋 Results:")
        print(f"   Title: {analysis.title}")
        print(f"   Price: ${analysis.price:.2f}" if analysis.price else "   Price: Not detected")
        print(f"   Condition: {analysis.condition}")
        print(f"   Category: {analysis.category}")
        print(f"   Confidence: {analysis.confidence:.0%}")
        
        # Step 2: Moderation Check
        moderation = moderator.check_all(analysis.title, analysis.description)
        
        if not moderation["passed"]:
            print(f"\n⚠️  MODERATION FLAGS:")
            for flag in moderation["flags"]:
                print(f"   - {flag}")
            
            confirm = input("\nReview and approve? (y/n): ").strip().lower()
            if confirm != 'y':
                print("❌ Skipped by user")
                return None
        
        # Step 3: Create listing on platforms
        if analysis.confidence < 0.75 or moderation["needs_review"]:
            print("\n⚠️  LOW CONFIDENCE - Marked for manual review")
        
        print(f"\n✅ Analysis complete!")
        return {
            "title": analysis.title,
            "description": analysis.description,
            "price": analysis.price,
            "condition": analysis.condition,
            "category": analysis.category
        }
        
    except Exception as e:
        logger.error(f"Failed to process {image_path}: {e}")
        print(f"\n❌ Error processing item: {e}")
        return None


def run_dashboard(config):
    """Start the web dashboard"""
    from dashboard.web_app import app
    
    import uvicorn
    
    host = config.get("dashboard", {}).get("host", "0.0.0.0")
    port = config.get("dashboard", {}).get("port", 8000)
    
    print(f"\n🌐 Starting Dashboard at http://localhost:{port}")
    print("Press Ctrl+C to stop\n")
    
    uvicorn.run(app, host=host, port=port)


def main():
    """Main entry point"""
    
    config = load_config()
    
    # Initialize components
    parser = create_parser(config["ai_parser"]) if "ai_parser" in config else None
    moderator = create_moderator(config.get("moderation", {}))
    scanner = FolderScanner(config) if "scanner" in config else None
    
    print("\n" + "="*60)
    print("  📦 Listing Manager - AI-Powered Multi-Platform Sales")
    print("="*60)
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    # Command line interface
    while True:
        print("\nCommands:")
        print("  scan <image_path>     - Process a single product image")
        print("  monitor               - Start folder monitoring")
        print("  dashboard             - Launch web UI")
        print("  platforms             - Check platform connections")
        print("  sync                  - Run inventory sync check")
        print("  quit / exit           - Exit program\n")
        
        cmd = input("Listing Manager > ").strip().lower()
        
        if cmd in ["quit", "exit"]:
            print("\n👋 Goodbye!")
            break
            
        elif cmd == "scan":
            # Process single item
            if len(sys.argv) > 2:
                image_path = sys.argv[2]
            else:
                image_path = input("Image path: ").strip()
            
            if Path(image_path).exists():
                process_single_item(image_path, parser, moderator)
                scanner.move_to_processed(image_path) if scanner else None
            else:
                print(f"❌ File not found: {image_path}")
                
        elif cmd == "monitor":
            # Start folder monitoring
            print("\n👁️  Starting folder monitor (Ctrl+C to stop)\n")
            
            def on_new_file(file_path):
                result = process_single_item(file_path, parser, moderator)
                if scanner:
                    scanner.move_to_processed(file_path)
            
            observer = scanner.start_monitoring(on_new_file) if scanner else None
            
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n👋 Monitoring stopped")
                if scanner:
                    scanner.stop_monitoring(observer)
                    
        elif cmd == "dashboard":
            # Launch web dashboard
            run_dashboard(config)
            
        elif cmd == "platforms":
            # Check platform connections
            platforms = init_platforms(config)
            
            print("\nPlatform Connections:")
            for name, platform in platforms.items():
                connected = platform.connect()
                status = "✅ Connected" if connected else "❌ Disconnected"
                print(f"  {name}: {status}")
                
        elif cmd == "sync":
            # Run inventory sync
            print("\n🔄 Running inventory sync...")
            
            try:
                from core.inventory_sync import load_config as get_db_config
                db = InventorySyncEngine(config.get("database", {}).get("path"))
                db.load_from_database()
                
                sold_items = db.scan_for_sales()
                print(f"  Found {len(sold_items)} items marked for sync")
                
            except Exception as e:
                logger.error(f"Sync failed: {e}")
                print(f"  Error: {e}")
                
        else:
            print("❌ Unknown command. Type 'help' for options.")


if __name__ == "__main__":
    main()
