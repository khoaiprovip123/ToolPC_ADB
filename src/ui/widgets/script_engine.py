
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
from src.ui.theme_manager import ThemeManager

class ActionDialog(QDialog):
    def __init__(self, action_type, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Thêm hành động: {action_type}")
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

class MacroWorker(QThread):
    progress = Signal(str)
    finished = Signal()
    
    def __init__(self, adb, actions):
        super().__init__()
        self.adb = adb
        self.actions = actions
        self._running = True
        
    def run(self):
        for i, action in enumerate(self.actions):
            if not self._running:
                break
                
            atype = action.get("type", "")
            self.progress.emit(f"Step {i+1}: {atype}")
            
            try:
                if atype == "Click":
                    self.adb.shell(f"input tap {action['x']} {action['y']}")
                elif atype == "Swipe":
                    self.adb.shell(f"input swipe {action['x1']} {action['y1']} {action['x2']} {action['y2']} {action['duration']}")
                elif atype == "Text":
                    # Escape spaces
                    text = action['text'].replace(" ", "%s")
                    self.adb.shell(f"input text {text}")
                elif atype == "Key":
                    self.adb.shell(f"input keyevent {action['keycode']}")
                elif atype == "Wait":
                    time.sleep(action['ms'] / 1000.0)
                    
                # Small delay between actions by default
                if atype != "Wait":
                    time.sleep(0.5)
                    
            except Exception as e:
                self.progress.emit(f"Error: {e}")
                
        self.finished.emit()
        
    def stop(self):
        self._running = False

class ScriptEngineWidget(QWidget):
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.setup_ui()
        self.worker = None
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel("⚡ Macro Automation Builder")
        header.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {ThemeManager.COLOR_TEXT_PRIMARY};")
        main_layout.addWidget(header)
        
        # Main Area
        h_layout = QHBoxLayout()
        
        # Action List
        list_container = QGroupBox("Danh sách hành động")
        list_container.setStyleSheet(ThemeManager.get_group_box_style())
        list_layout = QVBoxLayout(list_container)
        
        self.action_list = QListWidget()
        self.action_list.setStyleSheet(f"""
            QListWidget {{
                background: rgba(255,255,255,0.5);
                border: none;
                border-radius: 8px;
                color: {ThemeManager.COLOR_TEXT_PRIMARY};
            }}
            QListWidget::item {{
                padding: 5px;
                border-bottom: 1px solid rgba(0,0,0,0.05);
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
        toolbox = QGroupBox("Công cụ")
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
                QMessageBox.warning(self, "Lỗi", f"File không hợp lệ: {e}")

    def run_macro(self):
        actions = []
        for i in range(self.action_list.count()):
            actions.append(self.action_list.item(i).data(Qt.UserRole))
            
        if not actions:
            return
            
        self.btn_run.setEnabled(False)
        self.btn_stop.setEnabled(True)
        
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
