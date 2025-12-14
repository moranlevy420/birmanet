"""
Create a new GitHub release with the zip file attached.

Usage:
    python scripts/create_release.py v2.2.5

This will:
1. Create a zip file of the current code
2. Create a GitHub release with that version tag
3. Upload the zip file as a release asset
"""

import os
import sys
import json
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

GITHUB_REPO = "moranlevy420/birmanet"
GITHUB_API = "https://api.github.com"


def get_token():
    """Get GitHub token."""
    # Check environment
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        return token
    
    # Check file
    token_file = Path(__file__).parent.parent / ".github_token"
    if token_file.exists():
        return token_file.read_text().strip()
    
    # Ask user
    print("GitHub token not found.")
    print("Go to https://github.com/settings/tokens to create one.")
    print("Required scope: 'repo'")
    print()
    token = input("Paste token: ").strip()
    
    if token:
        token_file.write_text(token)
        print("Token saved.")
    
    return token


def create_zip(version: str) -> str:
    """Create release zip file."""
    zip_name = f"FindBetter_{version}.zip"
    
    # Remove old zip if exists
    if os.path.exists(zip_name):
        os.remove(zip_name)
    
    # Files to include
    includes = [
        "app.py", "requirements.txt", "run_app.bat",
        "INSTALL_WINDOWS.bat", "UPDATE_WINDOWS.bat",
        "UNINSTALL_WINDOWS.bat", "RESET_PASSWORD.bat",
        "README.md", "README_SIMPLE.md",
        "alembic.ini", "manage.py", "pytest.ini",
        "config/", "models/", "services/", "ui/",
        "utils/", "scripts/", "migrations/", "tests/"
    ]
    
    # Exclusions
    excludes = [
        "*.pyc", "*__pycache__*", "*.db", ".git/*",
        ".github_token", "*.zip"
    ]
    
    # Build zip command
    cmd = ["zip", "-r", zip_name] + includes
    for ex in excludes:
        cmd.extend(["-x", ex])
    
    print(f"Creating {zip_name}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    
    print(f"[OK] Created {zip_name}")
    return zip_name


def create_github_release(version: str, token: str) -> dict:
    """Create a GitHub release."""
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/releases"
    
    data = json.dumps({
        "tag_name": version,
        "name": f"Find Better {version}",
        "body": f"Release {version}\n\nDownload the zip file and run INSTALL_WINDOWS.bat",
        "draft": False,
        "prerelease": False
    }).encode()
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Error creating release: {e.code} - {error_body}")
        return None


def upload_asset(upload_url: str, file_path: str, token: str) -> bool:
    """Upload zip file to release."""
    # Clean URL (remove template part)
    upload_url = upload_url.split("{")[0]
    file_name = os.path.basename(file_path)
    
    url = f"{upload_url}?name={file_name}"
    
    with open(file_path, "rb") as f:
        data = f.read()
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/zip",
        "Content-Length": str(len(data))
    }
    
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    
    try:
        print(f"Uploading {file_name}...")
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode())
            print(f"[OK] Uploaded: {result.get('browser_download_url', 'success')}")
            return True
    except urllib.error.HTTPError as e:
        print(f"Error uploading: {e.code}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/create_release.py <version>")
        print("Example: python scripts/create_release.py v2.2.5")
        sys.exit(1)
    
    version = sys.argv[1]
    if not version.startswith("v"):
        version = f"v{version}"
    
    print()
    print("=" * 50)
    print(f"  Creating Release: {version}")
    print("=" * 50)
    print()
    
    # Get token
    token = get_token()
    if not token:
        print("Cannot proceed without token.")
        sys.exit(1)
    
    # Create zip
    zip_file = create_zip(version)
    if not zip_file:
        sys.exit(1)
    
    # Create release
    print()
    print("Creating GitHub release...")
    release = create_github_release(version, token)
    
    if not release:
        print("Failed to create release")
        sys.exit(1)
    
    print(f"[OK] Created release: {release.get('html_url')}")
    
    # Upload zip
    print()
    upload_url = release.get("upload_url")
    if upload_url:
        success = upload_asset(upload_url, zip_file, token)
        if not success:
            print("Warning: Failed to upload zip file")
    
    # Cleanup
    if os.path.exists(zip_file):
        os.remove(zip_file)
    
    print()
    print("=" * 50)
    print("  Release Complete!")
    print("=" * 50)
    print()
    print(f"  View at: {release.get('html_url')}")
    print()


if __name__ == "__main__":
    main()

