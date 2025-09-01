"""
Simple Media Downloader for GroupMe Bot
"""

import os
import requests
import time

# Constants
DATA_DIR = 'Data'
DOWNLOAD_DIR = 'Data Download'
MEDIA_TYPES = {
    'images': 'Images',
    'gifs': 'GIFs', 
    'videos': 'Videos'
}

def download_file(url, filepath):
    """Download a file from URL."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"✅ Downloaded: {os.path.basename(filepath)}")
        return True
        
    except Exception as e:
        print(f"❌ Failed: {os.path.basename(filepath)} - {e}")
        return False

def download_media_type(media_type, folder_name):
    """Download all media of a specific type."""
    print(f"\n📁 Processing {media_type}...")
    
    # Read URLs
    filepath = os.path.join(DATA_DIR, f"{media_type}.txt")
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    with open(filepath, 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    print(f"Found {len(urls)} URLs")
    
    download_folder = os.path.join(DOWNLOAD_DIR, folder_name)
    
    # Get file extension
    ext = 'jpg' if media_type == 'images' else 'gif' if media_type == 'gifs' else 'mp4'
    
    successful = 0
    for i, url in enumerate(urls, 1):
        filename = f"{i:04d}.{ext}"
        file_path = os.path.join(download_folder, filename)
        
        # Skip if exists
        if os.path.exists(file_path):
            print(f"⏭️  Exists: {filename}")
            continue
        
        if download_file(url, file_path):
            successful += 1
    
    print(f"📊 Downloaded {successful} new files")

def main():
    print("🚀 Starting download...")
    
    for media_type, folder_name in MEDIA_TYPES.items():
        download_media_type(media_type, folder_name)
    
    print("\n🎉 Done!")

if __name__ == '__main__':
    main()