# src/ui/widgets/dashboard.py
"""
Dashboard Widget - Real-time device monitoring
Displays device info, battery, storage, CPU, RAM, network
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QProgressBar, QGroupBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from typing import Optional
import pyqtgraph as pg
from collections import deque


class InfoCard(QFrame):
    """Reusable info card widget"""
    
    def __init__(self, title: str, icon: str = ""):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet("""
            InfoCard {
                background-color: #2d2d30;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"{icon} {title}")
        title_label.setStyleSheet("font-size: 14px; color: #858585; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Value label
        self.value_label = QLabel("--")
        self.value_label.setStyleSheet("font-size: 24px; color: #CCCCCC; font-weight: bold;")
        layout.addWidget(self.value_label)
        
        # Secondary info
        self.secondary_label = QLabel("")
        self.secondary_label.setStyleSheet("font-size: 12px; color: #858585;")
        layout.addWidget(self.secondary_label)
        
        layout.addStretch()
    
    def set_value(self, value: str):
        """Update main value"""
        self.value_label.setText(value)
    
    def set_secondary(self, text: str):
        """Update secondary info"""
        self.secondary_label.setText(text)


class ProgressCard(QFrame):
    """Card with progress bar"""
    
    def __init__(self, title: str, icon: str = "", color: str = "#4A9EFF"):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setStyleSheet(f"""
            ProgressCard {{
                background-color: #2d2d30;
                border-radius: 8px;
                padding: 15px;
            }}
        """)
        
        self.color = color
        
        layout = QVBoxLayout(self)
        
        # Title
        title_label = QLabel(f"{icon} {title}")
        title_label.setStyleSheet("font-size: 14px; color: #858585; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #1e1e1e;
                text-align: center;
                border-radius: 5px;
                height: 25px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)
        layout.addWidget(self.progress)
        
        # Info label
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("font-size: 12px; color: #858585;")
        layout.addWidget(self.info_label)
        
        layout.addStretch()
    
    def set_value(self, current: int, total: int, unit: str = ""):
        """Update progress value"""
        if total > 0:
            percentage = int((current / total) * 100)
            self.progress.setValue(percentage)
            self.info_label.setText(f"{current} / {total} {unit} ({percentage}%)")
        else:
            self.progress.setValue(0)
            self.info_label.setText("N/A")


class RealtimeChart(QWidget):
    """Real-time line chart using pyqtgraph"""
    
    def __init__(self, title: str, max_points: int = 60, y_range: tuple = (0, 100)):
        super().__init__()
        
        self.max_points = max_points
        self.data = deque(maxlen=max_points)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#2d2d30')
        self.plot_widget.setTitle(title, color='#CCCCCC', size='12pt')
        self.plot_widget.setLabel('left', 'Value', color='#858585')
        self.plot_widget.setLabel('bottom', 'Time (s)', color='#858585')
        self.plot_widget.setYRange(y_range[0], y_range[1])
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Plot curve
        self.curve = self.plot_widget.plot(pen=pg.mkPen('#4A9EFF', width=2))
        
        layout.addWidget(self.plot_widget)
    
    def add_data(self, value: float):
        """Add new data point"""
        self.data.append(value)
        self.curve.setData(list(self.data))
    
    def clear(self):
        """Clear all data"""
        self.data.clear()
        self.curve.setData([])


class DashboardWidget(QWidget):
    """
    Main Dashboard Widget
    Shows real-time device monitoring
    """
    
    device_changed = Signal(object)  # Emit when device info updates
    
    def __init__(self, adb_manager):
        super().__init__()
        self.adb = adb_manager
        self.device_info = None
        
        self.setup_ui()
        self.setup_timers()
    
    def setup_ui(self):
        """Setup UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Header with device name
        self.header_label = QLabel("Device Dashboard")
        self.header_label.setStyleSheet("""
            font-size: 20px;
            color: #CCCCCC;
            font-weight: bold;
            padding: 10px;
        """)
        main_layout.addWidget(self.header_label)
        
        # Quick info cards (top row)
        cards_layout = QGridLayout()
        cards_layout.setSpacing(10)
        
        # Device Info Card
        self.device_card = InfoCard("Device", "📱")
        cards_layout.addWidget(self.device_card, 0, 0)
        
        # Android Version Card
        self.android_card = InfoCard("Android", "🤖")
        cards_layout.addWidget(self.android_card, 0, 1)
        
        # Connection Card
        self.connection_card = InfoCard("Connection", "🔌")
        cards_layout.addWidget(self.connection_card, 0, 2)
        
        # Temperature Card
        self.temp_card = InfoCard("Temperature", "🌡️")
        cards_layout.addWidget(self.temp_card, 0, 3)
        
        main_layout.addLayout(cards_layout)
        
        # Progress cards (middle row)
        progress_layout = QGridLayout()
        progress_layout.setSpacing(10)
        
        # Battery Progress
        self.battery_progress = ProgressCard("Battery", "🔋", "#4ECB71")
        progress_layout.addWidget(self.battery_progress, 0, 0)
        
        # Storage Progress
        self.storage_progress = ProgressCard("Storage", "💾", "#FAA819")
        progress_layout.addWidget(self.storage_progress, 0, 1)
        
        # RAM Progress
        self.ram_progress = ProgressCard("RAM", "🧠", "#4A9EFF")
        progress_layout.addWidget(self.ram_progress, 1, 0)
        
        # Network Card (custom)
        self.network_card = self.create_network_card()
        progress_layout.addWidget(self.network_card, 1, 1)
        
        main_layout.addLayout(progress_layout)
        
        # Real-time charts
        charts_layout = QHBoxLayout()
        
        # CPU Chart
        self.cpu_chart = RealtimeChart("CPU Usage (%)", max_points=60, y_range=(0, 100))
        charts_layout.addWidget(self.cpu_chart)
        
        # Network Chart
        self.network_chart = RealtimeChart("Network Speed (KB/s)", max_points=60, y_range=(0, 1000))
        charts_layout.addWidget(self.network_chart)
        
        main_layout.addLayout(charts_layout)
        
        # Quick Actions
        actions_layout = QHBoxLayout()
        
        action_buttons = [
            ("🔄 Reboot", self.on_reboot),
            ("📸 Screenshot", self.on_screenshot),
            ("🧹 Clear Cache", self.on_clear_cache),
            ("⚡ Refresh", self.on_refresh),
        ]
        
        for text, callback in action_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d2d30;
                    color: #CCCCCC;
                    border: 1px solid #3e3e42;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #3e3e42;
                    border-color: #505050;
                }
                QPushButton:pressed {
                    background-color: #252526;
                }
            """)
            btn.clicked.connect(callback)
            actions_layout.addWidget(btn)
        
        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)
        
        main_layout.addStretch()
    
    def create_network_card(self) -> QFrame:
        """Create custom network info card"""
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        card.setStyleSheet("""
            QFrame {
                background-color: #2d2d30;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # Title
        title = QLabel("🌐 Network")
        title.setStyleSheet("font-size: 14px; color: #858585; font-weight: bold;")
        layout.addWidget(title)
        
        # WiFi Status
        self.wifi_label = QLabel("WiFi: --")
        self.wifi_label.setStyleSheet("font-size: 12px; color: #CCCCCC;")
        layout.addWidget(self.wifi_label)
        
        # IP Address
        self.ip_label = QLabel("IP: --")
        self.ip_label.setStyleSheet("font-size: 12px; color: #CCCCCC;")
        layout.addWidget(self.ip_label)
        
        # SSID
        self.ssid_label = QLabel("SSID: --")
        self.ssid_label.setStyleSheet("font-size: 12px; color: #858585;")
        layout.addWidget(self.ssid_label)
        
        layout.addStretch()
        
        return card
    
    def setup_timers(self):
        """Setup update timers"""
        # Quick update (1s) - Battery, CPU
        self.quick_timer = QTimer()
        self.quick_timer.timeout.connect(self.update_quick_metrics)
        self.quick_timer.start(1000)  # 1 second
        
        # Slow update (5s) - Storage, Network, etc.
        self.slow_timer = QTimer()
        self.slow_timer.timeout.connect(self.update_slow_metrics)
        self.slow_timer.start(5000)  # 5 seconds
    
    def set_device(self, device_serial: str):
        """Set current device"""
        try:
            self.adb.select_device(device_serial)
            self.device_info = self.adb.get_device_info()
            self.update_device_info()
            self.update_all_metrics()
        except Exception as e:
            print(f"Error setting device: {e}")
    
    def update_device_info(self):
        """Update static device information"""
        if not self.device_info:
            return
        
        # Header
        self.header_label.setText(f"📱 {self.device_info.model}")
        
        # Device card
        self.device_card.set_value(self.device_info.model)
        self.device_card.set_secondary(self.device_info.manufacturer)
        
        # Android card
        android_version = self.device_info.android_version
        miui = self.device_info.miui_version
        self.android_card.set_value(f"Android {android_version}")
        if miui:
            self.android_card.set_secondary(f"MIUI {miui}")
        
        # Connection card
        conn_type = self.device_info.connection_type.value.upper()
        self.connection_card.set_value(conn_type)
        if self.device_info.ip_address:
            self.connection_card.set_secondary(f"IP: {self.device_info.ip_address}")
    
    def update_quick_metrics(self):
        """Update metrics that change frequently (1s interval)"""
        if not self.adb.current_device:
            return
        
        try:
            # Battery
            battery = self.adb.get_battery_info()
            if battery.get('level'):
                level = battery['level']
                status = battery.get('status', 'Unknown')
                temp = battery.get('temperature', 0)
                
                self.battery_progress.set_value(level, 100, "%")
                
                # Update temperature card
                if temp:
                    self.temp_card.set_value(f"{temp:.1f}°C")
                    self.temp_card.set_secondary("Battery")
            
            # CPU (simulated for now - actual CPU usage requires more complex parsing)
            # In production, parse 'top -n 1' output
            import random
            cpu_usage = random.randint(10, 60)  # Replace with actual CPU parsing
            self.cpu_chart.add_data(cpu_usage)
            
            # Network speed (simulated)
            net_speed = random.randint(0, 500)  # Replace with actual network stats
            self.network_chart.add_data(net_speed)
            
        except Exception as e:
            print(f"Error updating quick metrics: {e}")
    
    def update_slow_metrics(self):
        """Update metrics that change slowly (5s interval)"""
        if not self.adb.current_device:
            return
        
        try:
            # Storage
            storage = self.adb.get_storage_info()
            if storage['total'] > 0:
                self.storage_progress.set_value(
                    storage['used'],
                    storage['total'],
                    "MB"
                )
            
            # RAM
            memory = self.adb.get_memory_info()
            if memory['total'] > 0:
                used = memory['total'] - memory['available']
                self.ram_progress.set_value(
                    used,
                    memory['total'],
                    "MB"
                )
            
            # Network info
            network = self.adb.get_network_info()
            wifi_status = "Connected" if network['wifi_enabled'] else "Disconnected"
            self.wifi_label.setText(f"WiFi: {wifi_status}")
            
            if network['ip_address']:
                self.ip_label.setText(f"IP: {network['ip_address']}")
            
            if network['ssid']:
                self.ssid_label.setText(f"SSID: {network['ssid']}")
            
        except Exception as e:
            print(f"Error updating slow metrics: {e}")
    
    def update_all_metrics(self):
        """Force update all metrics"""
        self.update_quick_metrics()
        self.update_slow_metrics()
    
    # ==================== Quick Actions ====================
    
    def on_reboot(self):
        """Handle reboot button"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            'Confirm Reboot',
            'Are you sure you want to reboot the device?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.adb.reboot()
                QMessageBox.information(self, 'Success', 'Device is rebooting...')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to reboot: {str(e)}')
    
    def on_screenshot(self):
        """Handle screenshot button"""
        from PySide6.QtWidgets import QFileDialog
        import datetime
        
        default_name = f"screenshot_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            'Save Screenshot',
            default_name,
            'PNG Images (*.png)'
        )
        
        if file_path:
            try:
                success = self.adb.screenshot(file_path)
                if success:
                    QMessageBox.information(self, 'Success', f'Screenshot saved to:\n{file_path}')
                else:
                    QMessageBox.warning(self, 'Failed', 'Could not capture screenshot')
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Screenshot failed: {str(e)}')
    
    def on_clear_cache(self):
        """Handle clear cache button"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            'Confirm Clear Cache',
            'This will clear cache for all apps. Continue?',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Trim caches to 1GB
                self.adb.shell("pm trim-caches 1G")
                QMessageBox.information(self, 'Success', 'Cache cleared successfully')
                self.update_slow_metrics()  # Refresh storage
            except Exception as e:
                QMessageBox.critical(self, 'Error', f'Failed to clear cache: {str(e)}')
    
    def on_refresh(self):
        """Handle refresh button"""
        self.cpu_chart.clear()
        self.network_chart.clear()
        self.update_all_metrics()
    
    def stop_updates(self):
        """Stop all update timers"""
        self.quick_timer.stop()
        self.slow_timer.stop()
    
    def start_updates(self):
        """Start update timers"""
        self.quick_timer.start(1000)
        self.slow_timer.start(5000)
