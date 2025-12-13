"""
Update service for checking and applying updates from GitHub.
"""

import requests
from pathlib import Path
from typing import Tuple, List, Optional
import logging
import re

logger = logging.getLogger(__name__)


class UpdateService:
    """Service for managing application updates from GitHub."""
    
    def __init__(
        self,
        app_dir: Path,
        github_raw_url: str,
        current_version: str,
        update_files: List[str]
    ):
        self.app_dir = app_dir
        self.github_raw_url = github_raw_url
        self.current_version = current_version
        self.update_files = update_files
    
    def check_for_updates(self) -> Tuple[Optional[str], bool]:
        """
        Check GitHub for a newer version.
        
        Returns:
            Tuple of (remote_version, is_update_available)
        """
        try:
            # Fetch the settings file to get the version
            response = requests.get(
                f"{self.github_raw_url}/config/settings.py", 
                timeout=5
            )
            if response.status_code == 200:
                content = response.text
                # Extract VERSION from the file
                match = re.search(r'VERSION\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    remote_version = match.group(1)
                    is_newer = self._is_newer_version(remote_version)
                    return remote_version, is_newer
            return None, False
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return None, False
    
    def download_updates(self) -> Tuple[List[str], List[str]]:
        """
        Download and apply updates from GitHub.
        
        Returns:
            Tuple of (updated_files, errors)
        """
        updated_files = []
        errors = []
        
        for filepath in self.update_files:
            try:
                response = requests.get(
                    f"{self.github_raw_url}/{filepath}", 
                    timeout=30
                )
                if response.status_code == 200:
                    # Create directory if needed
                    file_path = self.app_dir / filepath
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write the new content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    updated_files.append(filepath)
                    logger.info(f"Updated: {filepath}")
                else:
                    errors.append(f"{filepath}: HTTP {response.status_code}")
            except Exception as e:
                errors.append(f"{filepath}: {str(e)}")
                logger.error(f"Error updating {filepath}: {e}")
        
        return updated_files, errors
    
    def _is_newer_version(self, remote_version: str) -> bool:
        """Check if remote version is newer than current version."""
        try:
            remote_parts = self._parse_version(remote_version)
            current_parts = self._parse_version(self.current_version)
            return remote_parts > current_parts
        except Exception:
            return False
    
    @staticmethod
    def _parse_version(version_str: str) -> Tuple[int, ...]:
        """Parse version string to tuple for comparison."""
        # Remove any prefix like 'v'
        version_str = version_str.lstrip('v')
        parts = version_str.split('.')
        return tuple(int(p) for p in parts)

