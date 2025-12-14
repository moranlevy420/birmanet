"""
Download updates from private GitHub repository.
Handles authentication and downloads the latest release.

Usage:
    python scripts/download_update.py
"""

import os
import sys
import json
import urllib.request
import urllib.error
import zipfile
import shutil
from pathlib import Path

# Configuration
GITHUB_REPO = "moranlevy420/birmanet"
GITHUB_API = "https://api.github.com"
CONFIG_FILE = ".github_token"


def get_token():
    """Get GitHub token from config file or environment."""
    # Check environment variable first
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    
    # Check config file
    config_path = Path(__file__).parent.parent / CONFIG_FILE
    if config_path.exists():
        with open(config_path, "r") as f:
            token = f.read().strip()
            if token:
                return token
    
    return None


def save_token(token: str):
    """Save token to config file."""
    config_path = Path(__file__).parent.parent / CONFIG_FILE
    with open(config_path, "w") as f:
        f.write(token)
    print(f"  Token saved to {CONFIG_FILE}")


def api_request(url: str, token: str = None):
    """Make authenticated API request."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "FindBetter-Updater"
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("  [ERROR] Invalid or expired token")
        elif e.code == 404:
            print("  [ERROR] Repository not found or no access")
        else:
            print(f"  [ERROR] HTTP {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def download_file(url: str, dest: str, token: str = None):
    """Download file with authentication."""
    headers = {
        "Accept": "application/octet-stream",
        "User-Agent": "FindBetter-Updater"
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            with open(dest, "wb") as f:
                shutil.copyfileobj(response, f)
        return True
    except Exception as e:
        print(f"  [ERROR] Download failed: {e}")
        return False


def get_latest_release(token: str):
    """Get latest release info from GitHub."""
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/releases/latest"
    return api_request(url, token)


def download_release_asset(asset: dict, token: str):
    """Download a release asset."""
    # Use the browser_download_url for public or API url for private
    url = asset.get("url")  # API URL with Accept header for private repos
    name = asset.get("name")
    
    print(f"  Downloading {name}...")
    
    headers = {
        "Accept": "application/octet-stream",
        "User-Agent": "FindBetter-Updater"
    }
    if token:
        headers["Authorization"] = f"token {token}"
    
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=120) as response:
            with open(name, "wb") as f:
                shutil.copyfileobj(response, f)
        return name
    except Exception as e:
        print(f"  [ERROR] {e}")
        return None


def extract_and_update(zip_path: str):
    """Extract zip and update files."""
    print(f"  Extracting {zip_path}...")
    
    # Create temp directory
    temp_dir = Path("_update_temp")
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir()
    
    try:
        # Extract zip
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(temp_dir)
        
        # Copy files to current directory
        for item in temp_dir.iterdir():
            dest = Path(item.name)
            if item.is_dir():
                if dest.exists():
                    shutil.rmtree(dest)
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)
        
        print("  [OK] Files updated")
        return True
        
    except Exception as e:
        print(f"  [ERROR] Extraction failed: {e}")
        return False
    finally:
        # Cleanup
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
        if os.path.exists(zip_path):
            os.remove(zip_path)


def setup_token():
    """Interactive token setup."""
    print()
    print("=" * 60)
    print("       GitHub Token Setup")
    print("=" * 60)
    print()
    print("  To download updates from the private repository,")
    print("  you need a GitHub Personal Access Token.")
    print()
    print("  How to get a token:")
    print("  1. Go to: https://github.com/settings/tokens")
    print("  2. Click 'Generate new token (classic)'")
    print("  3. Give it a name like 'FindBetter Updates'")
    print("  4. Select scope: 'repo' (full control of private repos)")
    print("  5. Click 'Generate token'")
    print("  6. Copy the token (starts with 'ghp_...')")
    print()
    
    token = input("  Paste your token here: ").strip()
    
    if not token:
        print("  [!] No token provided")
        return None
    
    # Verify token works
    print()
    print("  Verifying token...")
    result = api_request(f"{GITHUB_API}/repos/{GITHUB_REPO}", token)
    
    if result:
        print("  [OK] Token is valid!")
        save_token(token)
        return token
    else:
        print("  [!] Token verification failed")
        return None


def main():
    print()
    print("=" * 60)
    print("       Find Better - Update from GitHub")
    print("=" * 60)
    print()
    
    # Get or setup token
    token = get_token()
    
    if not token:
        print("  No GitHub token found.")
        token = setup_token()
        if not token:
            print()
            print("  Cannot proceed without valid token.")
            print("  Run this script again after getting a token.")
            return False
    
    # Get latest release
    print()
    print("  Checking for latest release...")
    release = get_latest_release(token)
    
    if not release:
        print("  [!] Could not get release info.")
        print("  [!] Your token may have expired. Delete .github_token and try again.")
        return False
    
    version = release.get("tag_name", "unknown")
    print(f"  Latest version: {version}")
    
    # Find zip asset
    assets = release.get("assets", [])
    zip_asset = None
    for asset in assets:
        if asset.get("name", "").endswith(".zip"):
            zip_asset = asset
            break
    
    if not zip_asset:
        print("  [!] No zip file found in release")
        return False
    
    # Download
    print()
    zip_file = download_release_asset(zip_asset, token)
    
    if not zip_file:
        return False
    
    # Extract and update
    print()
    if not extract_and_update(zip_file):
        return False
    
    print()
    print("=" * 60)
    print("       Update Complete!")
    print("=" * 60)
    print()
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        input("\nPress Enter to exit...")
        sys.exit(1)

