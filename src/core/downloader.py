# src/core/downloader.py
"""
File Downloader - Download files with progress tracking
"""

import os
import requests
from PySide6.QtCore import QObject, Signal, QThread
from typing import Optional


class FileDownloader(QThread):
    """
    Download files in background with progress updates
    """
    
    # Signals
    progress = Signal(int, int, int)  # downloaded, total, percentage
    speed_update = Signal(float)  # bytes per second
    finished = Signal(str)  # file path
    error = Signal(str)  # error message
    
    def __init__(self, url: str, destination: str):
        super().__init__()
        self.url = url
        self.destination = destination
        self._is_cancelled = False
        
    def run(self):
        """Download file with progress tracking"""
        try:
            # Create destination directory if needed
            os.makedirs(os.path.dirname(self.destination), exist_ok=True)
            
            # Stream download
            response = requests.get(self.url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            chunk_size = 8192  # 8KB chunks
            
            import time
            start_time = time.time()
            last_time = start_time
            last_downloaded = 0
            
            with open(self.destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if self._is_cancelled:
                        # Clean up partial file
                        f.close()
                        if os.path.exists(self.destination):
                            os.remove(self.destination)
                        return
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Calculate progress
                        percentage = int((downloaded_size / total_size) * 100) if total_size > 0 else 0
                        self.progress.emit(downloaded_size, total_size, percentage)
                        
                        # Calculate speed every 0.5 seconds
                        current_time = time.time()
                        if current_time - last_time >= 0.5:
                            time_diff = current_time - last_time
                            bytes_diff = downloaded_size - last_downloaded
                            speed = bytes_diff / time_diff if time_diff > 0 else 0
                            self.speed_update.emit(speed)
                            
                            last_time = current_time
                            last_downloaded = downloaded_size
            
            # Download complete
            self.finished.emit(self.destination)
            
        except requests.RequestException as e:
            self.error.emit(f"Lỗi tải file: {str(e)}")
            # Clean up failed download
            if os.path.exists(self.destination):
                try:
                    os.remove(self.destination)
                except:
                    pass
                    
        except Exception as e:
            self.error.emit(f"Lỗi không xác định: {str(e)}")
            if os.path.exists(self.destination):
                try:
                    os.remove(self.destination)
                except:
                    pass
    
    def cancel(self):
        """Cancel the download"""
        self._is_cancelled = True
    
    @staticmethod
    def format_speed(bytes_per_second: float) -> str:
        """
        Format download speed in human-readable format
        
        Args:
            bytes_per_second: Speed in bytes/second
            
        Returns:
            Formatted string (e.g., "2.5 MB/s")
        """
        if bytes_per_second < 1024:
            return f"{bytes_per_second:.0f} B/s"
        elif bytes_per_second < 1024 * 1024:
            return f"{bytes_per_second / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_second / (1024 * 1024):.1f} MB/s"
    
    @staticmethod
    def estimate_time_remaining(downloaded: int, total: int, speed: float) -> str:
        """
        Estimate remaining download time
        
        Args:
            downloaded: Bytes downloaded
            total: Total bytes
            speed: Current speed in bytes/second
            
        Returns:
            Formatted time string (e.g., "2 phút 30 giây")
        """
        if speed <= 0 or total <= downloaded:
            return "Đang tính toán..."
        
        remaining_bytes = total - downloaded
        seconds_remaining = remaining_bytes / speed
        
        if seconds_remaining < 60:
            return f"{int(seconds_remaining)} giây"
        elif seconds_remaining < 3600:
            minutes = int(seconds_remaining / 60)
            seconds = int(seconds_remaining % 60)
            return f"{minutes} phút {seconds} giây"
        else:
            hours = int(seconds_remaining / 3600)
            minutes = int((seconds_remaining % 3600) / 60)
            return f"{hours} giờ {minutes} phút"
