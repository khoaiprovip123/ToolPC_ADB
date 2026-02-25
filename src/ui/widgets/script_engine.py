
"""
Script Engine / Macro Builder Widget
Style: Glassmorphism
"""

import json
import time
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFileDialog, QMessageBox, QGroupBox, QListWidget,
    QListWidgetItem, QInputDialog, QSpinBox, QComboBox, QDialog,
    QFormLayout, QLineEdit
)
from PySide6.QtCore import Qt, QThread, Signal
from src.core.workers.macro_worker import MacroWorker
from src.ui.theme_manager import ThemeManager
from src.gemini_controller import GeminiController
from src.core.log_manager import LogManager

class ActionDialog(QDialog):
    def __init__(self, action_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Thêm hành động: {action_type}")
        self.setStyleSheet(ThemeManager.get_main_window_style())
        self.action_type = action_type
        self.data = {}
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inputs = {}
        
        if self.action_type == "Click":
            self.inputs['x'] = QSpinBox()
            self.inputs['x'].setRange(0, 9999)
            self.inputs['y'] = QSpinBox()
            self.inputs['y'].setRange(0, 9999)
            form.addRow("X:", self.inputs['x'])
            form.addRow("Y:", self.inputs['y'])
            
        elif self.action_type == "Swipe":
            self.inputs['x1'] = QSpinBox()
            self.inputs['x1'].setRange(0, 9999)
            self.inputs['y1'] = QSpinBox()
            self.inputs['y1'].setRange(0, 9999)
            self.inputs['x2'] = QSpinBox()
            self.inputs['x2'].setRange(0, 9999)
            self.inputs['y2'] = QSpinBox()
            self.inputs['y2'].setRange(0, 9999)
            self.inputs['duration'] = QSpinBox()
            self.inputs['duration'].setRange(100, 5000)
            self.inputs['duration'].setValue(500)
            
            form.addRow("Start X:", self.inputs['x1'])
            form.addRow("Start Y:", self.inputs['y1'])
            form.addRow("End X:", self.inputs['x2'])
            form.addRow("End Y:", self.inputs['y2'])
            form.addRow("Duration (ms):", self.inputs['duration'])
            
        elif self.action_type == "Text":
            self.inputs['text'] = QLineEdit()
            form.addRow("Nội dung:", self.inputs['text'])
            
        elif self.action_type == "Key":
            self.inputs['keycode'] = QComboBox() 
            keys = {
                "HOME": "3", "BACK": "4", "APP_SWITCH": "187", 
                "POWER": "26", "VOLUME_UP": "24", "VOLUME_DOWN": "25",
                "ENTER": "66", "TAB": "61"
            }
            for k, v in keys.items():
                self.inputs['keycode'].addItem(f"{k} ({v})", v)
            form.addRow("Phím:", self.inputs['keycode'])
            
        elif self.action_type == "Wait":
            self.inputs['ms'] = QSpinBox()
            self.inputs['ms'].setRange(100, 60000)
            self.inputs['ms'].setValue(1000)
            form.addRow("Thời gian (ms):", self.inputs['ms'])
            
        layout.addLayout(form)
        
        btn_box = QHBoxLayout()
        btn_ok = QPushButton("OK")
        btn_ok.clicked.connect(self.accept)
        btn_cancel = QPushButton("Hủy")
        btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(btn_ok)
        btn_box.addWidget(btn_cancel)
        
        layout.addLayout(btn_box)
        
    def get_data(self):
        data = {"type": self.action_type}
        for k, w in self.inputs.items():
            if isinstance(w, QSpinBox):
                data[k] = w.value()
            elif isinstance(w, QLineEdit):
                data[k] = w.text()
            elif isinstance(w, QComboBox):
                data[k] = w.currentData()
        return data

class ScriptEngineWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.gemini_controller = GeminiController(self.adb)
        self.setup_ui()
        self.worker = None
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("⚡ Macro & AI Automation")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        main_layout.addWidget(header)
        
        # --- START NEW GEMINI UI ---
        gemini_group = QGroupBox("✨ Gemini AI Natural Language Control")
        gemini_group.setStyleSheet(ThemeManager.get_group_box_style())
        gemini_layout = QVBoxLayout(gemini_group)

        # Add instructions
        instructions_label = QLabel(
            "<b>Hướng dẫn:</b><br>"
            "1. Nhập lệnh bằng ngôn ngữ tự nhiên (VD: <i>mở cài đặt, tìm kiếm display</i>).<br>"
            "2. Nhấn nút 'Thực thi bằng Gemini'.<br>"
            "3. Quan sát điện thoại thực hiện theo lệnh."
        )
        instructions_label.setStyleSheet("color: #555; background: transparent; border: none; margin-bottom: 5px;")
        instructions_label.setWordWrap(True)
        gemini_layout.addWidget(instructions_label)

        self.gemini_input = QLineEdit()
        self.gemini_input.setPlaceholderText("Ví dụ: Mở Cài đặt, tìm kiếm 'display', sau đó nhấn back")
        self.gemini_input.setStyleSheet("padding: 8px; border-radius: 5px;")
        gemini_layout.addWidget(self.gemini_input)

        self.gemini_run_btn = QPushButton("⚡ Thực thi bằng Gemini")
        self.gemini_run_btn.setStyleSheet(ThemeManager.get_button_style("primary"))
        self.gemini_run_btn.clicked.connect(self.run_gemini_command)
        gemini_layout.addWidget(self.gemini_run_btn)

        main_layout.addWidget(gemini_group)
        # --- END NEW GEMINI UI ---

        # Main Area
        h_layout = QHBoxLayout()
        
        # Action List
        list_container = QGroupBox("Danh sách hành động (Macro Builder)")
        list_container.setStyleSheet(ThemeManager.get_group_box_style())
        list_layout = QVBoxLayout(list_container)
        
        self.action_list = QListWidget()
        self.action_list.setStyleSheet(f"""
            QListWidget {{
                background: {ThemeManager.get_theme()['COLOR_GLASS_WHITE']};
                border: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
                border-radius: 8px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
            QListWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {ThemeManager.get_theme()['COLOR_BORDER_LIGHT']};
            }}
            QListWidget::item:selected {{
                background: {ThemeManager.COLOR_ACCENT}20;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
                border-radius: 6px;
            }}
        """)
        list_layout.addWidget(self.action_list)
        
        # List Controls
        list_ctrl = QHBoxLayout()
        btn_del = QPushButton("❌ Xóa")
        btn_del.clicked.connect(self.delete_item)
        btn_clear = QPushButton("🗑️ Xóa hết")
        btn_clear.clicked.connect(self.action_list.clear)
        btn_up = QPushButton("⬆️")
        btn_up.clicked.connect(lambda: self.move_item(-1))
        btn_down = QPushButton("⬇️")
        btn_down.clicked.connect(lambda: self.move_item(1))
        
        for b in [btn_del, btn_clear, btn_up, btn_down]:
            b.setStyleSheet(ThemeManager.get_button_style("outline"))
            list_ctrl.addWidget(b)
            
        list_layout.addLayout(list_ctrl)
        h_layout.addWidget(list_container, stretch=2)
        
        # Toolbox
        toolbox = QGroupBox("Công cụ Macro")
        toolbox.setStyleSheet(ThemeManager.get_group_box_style())
        toolbox_layout = QVBoxLayout(toolbox)
        
        actions = ["Click", "Swipe", "Text", "Key", "Wait"]
        for act in actions:
            btn = QPushButton(f"➕ {act}")
            btn.clicked.connect(lambda checked, a=act: self.add_action_dialog(a))
            btn.setStyleSheet(ThemeManager.get_button_style("primary"))
            toolbox_layout.addWidget(btn)
            
        toolbox_layout.addStretch()
        h_layout.addWidget(toolbox, stretch=1)
        
        main_layout.addLayout(h_layout)
        
        # Bottom Controls
        bottom_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 Lưu Macro")
        btn_save.clicked.connect(self.save_macro)
        btn_save.setStyleSheet(ThemeManager.get_button_style("outline"))
        
        btn_load = QPushButton("📂 Mở Macro")
        btn_load.clicked.connect(self.load_macro)
        btn_load.setStyleSheet(ThemeManager.get_button_style("outline"))
        
        self.btn_run = QPushButton("▶ CHẠY MACRO")
        self.btn_run.clicked.connect(self.run_macro)
        self.btn_run.setStyleSheet(ThemeManager.get_button_style("success"))
        self.btn_run.setFixedHeight(45)
        
        self.btn_stop = QPushButton("⏹ DỪNG")
        self.btn_stop.clicked.connect(self.stop_macro)
        self.btn_stop.setStyleSheet(ThemeManager.get_button_style("danger"))
        self.btn_stop.setFixedHeight(45)
        self.btn_stop.setEnabled(False)
        
        bottom_layout.addWidget(btn_save)
        bottom_layout.addWidget(btn_load)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_run)
        bottom_layout.addWidget(self.btn_stop)
        
        main_layout.addLayout(bottom_layout)
        
        # Status
        self.status = QLabel("Ready")
        self.status.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.status)
        
    def run_gemini_command(self):
        command_text = self.gemini_input.text().strip()
        if not command_text:
            LogManager.log("Script Engine", "Vui lòng nhập một câu lệnh cho Gemini.", "warning")
            return

        self.gemini_run_btn.setEnabled(False)
        self.gemini_run_btn.setText("🔄 Đang xử lý...")
        self.status.setText(f"Gửi lệnh '{command_text}' đến Gemini...")

        def on_gemini_finished():
            self.gemini_run_btn.setEnabled(True)
            self.gemini_run_btn.setText("⚡ Thực thi bằng Gemini")
            self.status.setText("Sẵn sàng cho lệnh tiếp theo.")

        self.gemini_controller.execute_command(
            command_text,
            progress_callback=self.status.setText,
            finished_callback=on_gemini_finished
        )

    def add_action_dialog(self, action_type):
        dlg = ActionDialog(action_type, self)
        if dlg.exec():
            data = dlg.get_data()
            self.add_action_item(data)
            
    def add_action_item(self, data):
        item = QListWidgetItem()
        text = f"UNKNOWN"
        
        atype = data.get("type")
        if atype == "Click":
            text = f"🖱️ Click ({data['x']}, {data['y']})"
        elif atype == "Swipe":
            text = f"👆 Swipe ({data['x1']},{data['y1']}) -> ({data['x2']},{data['y2']}) in {data['duration']}ms"
        elif atype == "Text":
            text = f"⌨️ Type '{data['text']}'"
        elif atype == "Key":
            text = f"🔑 Keyevent {data['keycode']}"
        elif atype == "Wait":
            text = f"⏳ Wait {data['ms']}ms"
            
        item.setText(text)
        item.setData(Qt.UserRole, data)
        self.action_list.addItem(item)
        
    def delete_item(self):
        row = self.action_list.currentRow()
        if row >= 0:
            self.action_list.takeItem(row)
            
    def move_item(self, direction):
        row = self.action_list.currentRow()
        if row < 0: return
        
        new_row = row + direction
        if 0 <= new_row < self.action_list.count():
            item = self.action_list.takeItem(row)
            self.action_list.insertItem(new_row, item)
            self.action_list.setCurrentRow(new_row)
            
    def save_macro(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu Macro", "", "JSON Files (*.json)")
        if path:
            actions = []
            for i in range(self.action_list.count()):
                actions.append(self.action_list.item(i).data(Qt.UserRole))
            
            with open(path, 'w') as f:
                json.dump(actions, f, indent=2)
                
    def load_macro(self):
        path, _ = QFileDialog.getOpenFileName(self, "Mở Macro", "", "JSON Files (*.json)")
        if path:
            try:
                with open(path, 'r') as f:
                    actions = json.load(f)
                    self.action_list.clear()
                    for act in actions:
                        self.add_action_item(act)
            except Exception as e:
                LogManager.log("Script Engine", f"Lỗi file: {e}", "error")

    def run_macro(self):
        actions = []
        for i in range(self.action_list.count()):
            actions.append(self.action_list.item(i).data(Qt.UserRole))
            
        if not actions:
            return
            
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
        # Guard: stop old worker before creating new
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
        self.worker = MacroWorker(self.adb, actions)
        self.worker.progress.connect(self.status.setText)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
        
    def stop_macro(self):
        if self.worker:
            self.worker.stop()
            
    def on_finished(self):
        self.status.setText("Macro Completed")
        self.btn_run.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.worker = None
        
    def reset(self):
        self.stop_macro()
        self.status.setText("Ready")
