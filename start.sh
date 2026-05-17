#!/bin/bash
# Desktop launcher script for Listing Manager (Linux/Mac)
# Save as ~/ListingManager.app and make executable: chmod +x ListingManager.app

echo "Starting Listings Manager..."
cd "$(dirname "$0")" || exit 1
python3 run.py &
echo ""
echo "✅ Dashboard is starting!"
echo "Open your browser to: http://localhost:8000"
echo "Press Ctrl+C in this window to stop the server."
