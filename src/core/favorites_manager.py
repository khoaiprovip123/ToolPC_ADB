from PySide6.QtCore import QSettings
from typing import List, Dict

# Key lưu trong QSettings
_SETTINGS_KEY = "favorites/commands"


class FavoritesManager:
    """
    B3: Quản lý danh sách lệnh ADB yêu thích.
    Lưu/tải từ QSettings (persistent qua các lần mở app).

    Mỗi mục là dict: {"name": str, "command": str}
    """

    def __init__(self):
        self._settings = QSettings("VanKhoai", "XiaomiADBCommander")

    def get_all(self) -> List[Dict[str, str]]:
        """Lấy toàn bộ danh sách yêu thích."""
        raw = self._settings.value(_SETTINGS_KEY, [])
        # QSettings có thể trả về dict đơn lẻ nếu chỉ có 1 phần tử
        if isinstance(raw, dict):
            raw = [raw]
        return raw if isinstance(raw, list) else []

    def add(self, name: str, command: str) -> bool:
        """
        Thêm lệnh vào yêu thích.
        Returns: True nếu thêm thành công, False nếu đã tồn tại.
        """
        if not name.strip() or not command.strip():
            return False
        items = self.get_all()
        # Kiểm tra trùng command
        if any(item.get("command") == command.strip() for item in items):
            return False
        items.insert(0, {"name": name.strip(), "command": command.strip()})
        self._settings.setValue(_SETTINGS_KEY, items)
        return True

    def remove(self, command: str) -> bool:
        """
        Xóa lệnh khỏi yêu thích theo command string.
        Returns: True nếu xóa thành công.
        """
        items = self.get_all()
        new_items = [item for item in items if item.get("command") != command]
        if len(new_items) == len(items):
            return False  # Không tìm thấy
        self._settings.setValue(_SETTINGS_KEY, new_items)
        return True

    def remove_by_index(self, index: int) -> bool:
        """Xóa item theo vị trí trong danh sách."""
        items = self.get_all()
        if 0 <= index < len(items):
            items.pop(index)
            self._settings.setValue(_SETTINGS_KEY, items)
            return True
        return False

    def clear(self):
        """Xóa toàn bộ danh sách yêu thích."""
        self._settings.setValue(_SETTINGS_KEY, [])

    def count(self) -> int:
        """Số lượng mục yêu thích."""
        return len(self.get_all())
