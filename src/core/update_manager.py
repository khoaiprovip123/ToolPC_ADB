# src/core/update_manager.py
"""
Update Manager - Handle application updates from GitHub releases
"""

import requests
import json
import re
from typing import Optional, Tuple, Dict
from PySide6.QtCore import QObject, Signal, QThread
from src.version import __version__, __version_info__, GITHUB_API_URL, GITHUB_REPO_URL


class UpdateManager(QObject):
    """
    Manages application updates via GitHub Releases API
    """
    
    # Signals
    update_available = Signal(dict)  # Emit update info
    no_update_available = Signal()
    check_failed = Signal(str)  # Error message
    
    def __init__(self):
        super().__init__()
        self.current_version = __version__
        self.current_version_tuple = __version_info__
        
    def check_for_updates(self, include_prerelease: bool = False) -> Optional[Dict]:
        """
        Check GitHub for new releases
        
        Args:
            include_prerelease: Whether to include pre-release versions
            
        Returns:
            Dict with update info if available, None otherwise
        """
        try:
            # Query GitHub API
            response = requests.get(
                GITHUB_API_URL,
                timeout=10,
                headers={'Accept': 'application/vnd.github.v3+json'}
            )
            response.raise_for_status()
            
            release_data = response.json()
            
            # Skip pre-releases if not included
            if release_data.get('prerelease', False) and not include_prerelease:
                return None
            
            # Parse version from tag_name
            tag_name = release_data.get('tag_name', '')
            latest_version = self._parse_version(tag_name)
            
            if not latest_version:
                return None
            
            # Compare versions
            if self._is_newer_version(latest_version):
                # Extract update info
                update_info = {
                    'version': tag_name,
                    'version_tuple': latest_version,
                    'name': release_data.get('name', tag_name),
                    'changelog': release_data.get('body', 'Không có thông tin thay đổi.'),
                    'published_at': release_data.get('published_at', ''),
                    'html_url': release_data.get('html_url', GITHUB_REPO_URL),
                    'download_url': None,
                    'file_size': 0,
                    'file_name': None
                }
                
                # Find installer asset (*.exe)
                assets = release_data.get('assets', [])
                for asset in assets:
                    asset_name = asset.get('name', '').lower()
                    if asset_name.endswith('.exe') and 'setup' in asset_name:
                        update_info['download_url'] = asset.get('browser_download_url')
                        update_info['file_size'] = asset.get('size', 0)
                        update_info['file_name'] = asset.get('name')
                        break
                
                return update_info
            
            return None
            
        except requests.RequestException as e:
            self.check_failed.emit(f"Không thể kết nối đến GitHub: {str(e)}")
            return None
        except Exception as e:
            self.check_failed.emit(f"Lỗi kiểm tra cập nhật: {str(e)}")
            return None
    
    def _parse_version(self, version_string: str) -> Optional[Tuple[int, int, int]]:
        """
        Parse version string to tuple (major, minor, patch)
        
        Examples:
            "v2.5.0" -> (2, 5, 0)
            "2.5.0" -> (2, 5, 0)
            "v2.5.0-beta" -> (2, 5, 0)
        """
        # Remove 'v' prefix and any suffix like '-beta'
        version_string = version_string.lower().strip()
        if version_string.startswith('v'):
            version_string = version_string[1:]
        
        # Extract numbers
        match = re.match(r'(\d+)\.(\d+)\.(\d+)', version_string)
        if match:
            return tuple(int(x) for x in match.groups())
        
        return None
    
    def _is_newer_version(self, latest_version: Tuple[int, int, int]) -> bool:
        """
        Compare if latest version is newer than current
        
        Args:
            latest_version: Version tuple (major, minor, patch)
            
        Returns:
            True if latest is newer, False otherwise
        """
        return latest_version > self.current_version_tuple
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """
        Compare two version strings
        
        Returns:
            1 if version1 > version2
            0 if version1 == version2
            -1 if version1 < version2
        """
        v1 = self._parse_version(version1)
        v2 = self._parse_version(version2)
        
        if not v1 or not v2:
            return 0
        
        if v1 > v2:
            return 1
        elif v1 < v2:
            return -1
        else:
            return 0
    
    def format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted string (e.g., "45.2 MB")
        """
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


class UpdateChecker(QThread):
    """
    Background thread for checking updates without blocking UI
    """
    
    # Signals
    update_found = Signal(dict)
    no_update = Signal()
    error_occurred = Signal(str)
    
    def __init__(self, include_prerelease: bool = False):
        super().__init__()
        self.include_prerelease = include_prerelease
        self.update_manager = UpdateManager()
    
    def run(self):
        """Run update check in background"""
        try:
            update_info = self.update_manager.check_for_updates(self.include_prerelease)
            
            if update_info:
                self.update_found.emit(update_info)
            else:
                self.no_update.emit()
                
        except Exception as e:
            self.error_occurred.emit(str(e))
