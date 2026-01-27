# src/ui/performance_utils.py
"""
Performance Utilities - Optimization Helpers
Provides caching, lazy loading, throttling, and worker pooling
"""

from PySide6.QtCore import QTimer, QThread, QObject, Signal
from PySide6.QtWidgets import QWidget
from typing import Dict, Any, Callable, Optional, List
from functools import wraps
import time


class WidgetCache:
    """Cache để tái sử dụng widgets và tránh recreate"""
    
    def __init__(self, max_size: int = 50):
        self._cache: Dict[str, QWidget] = {}
        self._max_size = max_size
        self._access_times: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[QWidget]:
        """Lấy widget từ cache"""
        if key in self._cache:
            self._access_times[key] = time.time()
            return self._cache[key]
        return None
    
    def put(self, key: str, widget: QWidget) -> None:
        """Lưu widget vào cache"""
        # Nếu cache đầy, xóa item ít dùng nhất
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._access_times.items(), key=lambda x: x[1])[0]
            self._cache.pop(oldest_key, None)
            self._access_times.pop(oldest_key, None)
        
        self._cache[key] = widget
        self._access_times[key] = time.time()
    
    def clear(self) -> None:
        """Xóa toàn bộ cache"""
        self._cache.clear()
        self._access_times.clear()
    
    def size(self) -> int:
        """Trả về kích thước hiện tại của cache"""
        return len(self._cache)


class LazyLoader:
    """Lazy initialization cho widgets phức tạp"""
    
    def __init__(self):
        self._loaded_widgets: Dict[str, bool] = {}
        self._widget_factories: Dict[str, Callable] = {}
    
    def register(self, name: str, factory: Callable) -> None:
        """Đăng ký factory function cho widget"""
        self._widget_factories[name] = factory
        self._loaded_widgets[name] = False
    
    def load(self, name: str) -> Optional[Any]:
        """Load widget lần đầu tiên"""
        if name not in self._widget_factories:
            return None
        
        if not self._loaded_widgets[name]:
            widget = self._widget_factories[name]()
            self._loaded_widgets[name] = True
            return widget
        
        return None
    
    def is_loaded(self, name: str) -> bool:
        """Kiểm tra xem widget đã được load chưa"""
        return self._loaded_widgets.get(name, False)


class ThrottledTimer(QTimer):
    """Timer với throttle/debounce support"""
    
    def __init__(self, interval: int = 300, debounce: bool = True, parent=None):
        super().__init__(parent)
        self.setInterval(interval)
        self.setSingleShot(debounce)
        self._callback = None
    
    def set_callback(self, callback: Callable) -> None:
        """Set callback function"""
        self._callback = callback
        if self._callback:
            self.timeout.connect(self._callback)
    
    def trigger(self) -> None:
        """Trigger timer (restart nếu đang chạy)"""
        if self.isActive():
            self.stop()
        self.start()


class WorkerPool(QObject):
    """Pool của QThread workers để tái sử dụng"""
    
    def __init__(self, max_workers: int = 4):
        super().__init__()
        self._max_workers = max_workers
        self._available_workers: List[QThread] = []
        self._busy_workers: List[QThread] = []
    
    def get_worker(self) -> QThread:
        """Lấy worker từ pool hoặc tạo mới nếu cần"""
        # Nếu có worker available, tái sử dụng
        if self._available_workers:
            worker = self._available_workers.pop()
            self._busy_workers.append(worker)
            return worker
        
        # Nếu chưa đến giới hạn, tạo worker mới
        if len(self._busy_workers) < self._max_workers:
            worker = QThread()
            self._busy_workers.append(worker)
            return worker
        
        # Nếu đầy, đợi worker cũ (fallback: tạo mới)
        worker = QThread()
        return worker
    
    def return_worker(self, worker: QThread) -> None:
        """Trả worker về pool để tái sử dụng"""
        if worker in self._busy_workers:
            self._busy_workers.remove(worker)
        
        # Clean up worker trước khi return về pool
        if worker.isRunning():
            worker.quit()
            worker.wait(1000)
        
        if len(self._available_workers) < self._max_workers:
            self._available_workers.append(worker)
        else:
            # Nếu pool đầy, hủy worker
            worker.deleteLater()
    
    def cleanup(self) -> None:
        """Dọn dẹp tất cả workers"""
        for worker in self._available_workers + self._busy_workers:
            if worker.isRunning():
                worker.quit()
                worker.wait(1000)
            worker.deleteLater()
        
        self._available_workers.clear()
        self._busy_workers.clear()


class DataCache:
    """Cache cho data với TTL (Time To Live)"""
    
    def __init__(self, ttl: int = 5):
        self._cache: Dict[str, Any] = {}
        self._timestamps: Dict[str, float] = {}
        self._ttl = ttl  # seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Lấy data từ cache nếu chưa expired"""
        if key not in self._cache:
            return None
        
        # Kiểm tra TTL
        if time.time() - self._timestamps[key] > self._ttl:
            # Expired, xóa khỏi cache
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)
            return None
        
        return self._cache[key]
    
    def put(self, key: str, data: Any) -> None:
        """Lưu data vào cache"""
        self._cache[key] = data
        self._timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Xóa toàn bộ cache"""
        self._cache.clear()
        self._timestamps.clear()
    
    def invalidate(self, key: str) -> None:
        """Invalidate một key cụ thể"""
        self._cache.pop(key, None)
        self._timestamps.pop(key, None)


def debounce(wait: int = 300):
    """
    Decorator để debounce function calls
    Usage:
        @debounce(wait=500)
        def my_function():
            pass
    """
    def decorator(func):
        timer = None
        
        @wraps(func)
        def debounced(*args, **kwargs):
            nonlocal timer
            
            def call_function():
                func(*args, **kwargs)
            
            if timer is not None:
                timer.stop()
            
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(call_function)
            timer.start(wait)
        
        return debounced
    return decorator


def throttle(wait: int = 300):
    """
    Decorator để throttle function calls
    Usage:
        @throttle(wait=1000)
        def my_function():
            pass
    """
    def decorator(func):
        last_called = [0]  # Use list to make it mutable
        
        @wraps(func)
        def throttled(*args, **kwargs):
            now = time.time()
            if now - last_called[0] >= wait / 1000:
                last_called[0] = now
                return func(*args, **kwargs)
        
        return throttled
    return decorator


class BatchProcessor:
    """Xử lý items theo batch để tránh blocking UI"""
    
    def __init__(self, batch_size: int = 50):
        self.batch_size = batch_size
        self._timer = QTimer()
        self._timer.setSingleShot(True)
        self._items = []
        self._process_func = None
        self._current_index = 0
    
    def process(self, items: List[Any], process_func: Callable, on_complete: Optional[Callable] = None):
        """
        Xử lý danh sách items theo batch
        
        Args:
            items: Danh sách items cần xử lý
            process_func: Function xử lý mỗi item
            on_complete: Callback khi hoàn thành
        """
        self._items = items
        self._process_func = process_func
        self._on_complete = on_complete
        self._current_index = 0
        
        self._timer.timeout.connect(self._process_batch)
        self._timer.start(0)
    
    def _process_batch(self):
        """Xử lý một batch items"""
        end_index = min(self._current_index + self.batch_size, len(self._items))
        
        for i in range(self._current_index, end_index):
            if self._process_func:
                self._process_func(self._items[i])
        
        self._current_index = end_index
        
        # Nếu còn items, tiếp tục batch tiếp theo
        if self._current_index < len(self._items):
            self._timer.start(10)  # Small delay giữa các batch
        elif self._on_complete:
            self._on_complete()


# Global instances cho toàn app
widget_cache = WidgetCache(max_size=100)
worker_pool = WorkerPool(max_workers=6)
data_cache = DataCache(ttl=10)
