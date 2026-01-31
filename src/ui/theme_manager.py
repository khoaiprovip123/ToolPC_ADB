# src/ui/theme_manager.py
"""
Theme Manager - Defines the visual style of the application
Style: Modern Glassmorphism (PM 4.0) with Light/Dark Theme Support
"""

class ThemeManager:
    # Current Theme (can be switched)
    _current_theme = "light"
    
    # ==================== ICON MAPPING (Vibrant Emojis for Windows) ====================
    ICONS = {
        # Navigation
        "dashboard": "dashboard.png",
        "apps": "apps.png",
        "files": "files.png",
        "xiaomi": "xiaomi.png",
        "mirror": "mirror.png",
        "devtools": "devtools.png",
        "cloud": "cloud.png",
        "settings": "settings.png",
        "fastboot": "devtools.png", # Re-use devtools
        "tools": "tools.png",
        "advanced": "⚡",  # Advanced commands - use emoji fallback
        
        # Actions (Keep emojis for now or find small icons later)
        "refresh": "↻",
        "refresh": "↻",
        "search": "🔍",
        "power": "⏻",
        "download": "⬇",
        "check": "✓",
        "error": "✕",
        "warning": "⚠",
        
        # Status
        "connected": "🟢",      # Green Circle
        "disconnected": "⚪",   # White Circle
    }
    
    # ==================== APPLE SYSTEM COLORS (iOS 15+) ====================
    # Light Mode
    LIGHT = {
        "COLOR_BG_GRADIENT": "transparent", # Let Acrylic shine through
        "COLOR_BG_MAIN": "rgba(255, 255, 255, 0.01)",
        "COLOR_GLASS_WHITE": "rgba(255, 255, 255, 0.25)", # Very Transparent (Glass)
        "COLOR_GLASS_HOVER": "rgba(255, 255, 255, 0.40)",
        "COLOR_GLASS_CARD": "rgba(255, 255, 255, 0.65)",  # Cards semi-transparent
        "COLOR_TEXT_PRIMARY": "#000000",
        "COLOR_TEXT_SECONDARY": "#48484a", # Darker gray for contrast
        "COLOR_DATA": "#1C1C1E",
        "COLOR_BG_SECONDARY": "rgba(118, 118, 128, 0.12)", # System Fill
        "COLOR_SHADOW": "rgba(0, 0, 0, 0.05)",
        "COLOR_BORDER": "rgba(60, 60, 67, 0.1)",           # Separator
        "COLOR_BORDER_LIGHT": "rgba(60, 60, 67, 0.05)",
        "COLOR_DIALOG_BG": "rgba(255, 255, 255, 0.94)",    # High Alpha Glass for Dialogs
    }
    
    # Dark Mode (Improved)
    DARK = {
        "COLOR_BG_GRADIENT": "transparent",
        "COLOR_BG_MAIN": "rgba(26, 26, 26, 0.01)",
        "COLOR_GLASS_WHITE": "rgba(45, 45, 45, 0.35)", # Dark glass transparent
        "COLOR_GLASS_HOVER": "rgba(60, 60, 60, 0.50)",
        "COLOR_GLASS_CARD": "rgba(30, 30, 30, 0.70)", # Cards darker opacity
        "COLOR_TEXT_PRIMARY": "#e8e8e8",
        "COLOR_TEXT_SECONDARY": "#a8a8a8",
        "COLOR_DATA": "#f0f0f0",
        "COLOR_BG_SECONDARY": "rgba(80, 80, 80, 0.20)",
        "COLOR_SHADOW": "rgba(0, 0, 0, 0.4)",
        "COLOR_BORDER": "rgba(100, 100, 100, 0.3)",
        "COLOR_BORDER_LIGHT": "rgba(100, 100, 100, 0.15)",
        "COLOR_DIALOG_BG": "rgba(35, 35, 35, 0.94)",       # High Alpha Dark Glass for Dialogs
    }


    # ==================== IOS ACCENT COLORS ====================
    COLOR_ACCENT = "#007AFF"        # System Blue
    COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #007AFF, stop:1 #0A84FF)"
    COLOR_DANGER = "#FF3B30"        # System Red
    COLOR_SUCCESS = "#34C759"       # System Green
    COLOR_ACCENT_TRANSPARENT = "rgba(0, 122, 255, 0.15)" # Accent with low opacity
    COLOR_WARNING = "#F2C94C"       # System Yellow
    COLOR_PURPLE = "#5856D6"        # System Indigo
    COLOR_ORANGE = "#FF9500"        # System Orange
    COLOR_PINK = "#FF2D55"          # System Pink
    COLOR_TEAL = "#5AC8FA"          # System Teal
    
    # Backgrounds for status alerts
    COLOR_SUCCESS_BG = "rgba(52, 199, 89, 0.2)"
    COLOR_WARNING_BG = "rgba(255, 204, 0, 0.2)"
    
    # ==================== TYPOGRAPHY ====================
    FONT_FAMILY = "'-apple-system', 'Segoe UI', 'Inter', 'Roboto', sans-serif"
    FONT_FAMILY_MONO = "'SF Mono', 'JetBrains Mono', 'Consolas', monospace"
    
    # ==================== IOS DIMENSIONS ====================
    RADIUS_CARD = "22px"      # Larger radius for cards
    RADIUS_BUTTON = "12px"    # Standard button radius
    RADIUS_INPUT = "0px"
    BLUR_RADIUS = "20px"      # Standard Blur
    
    # ==================== HELPER METHODS ====================
    @classmethod
    def get_theme(cls):
        """Get current theme colors"""
        if cls._current_theme == "dark": return cls.DARK
        if cls._current_theme == "minimal": return cls.MINIMAL
        return cls.LIGHT

    # ==================== SYSTEM INTEGRATION ====================
    @staticmethod
    def get_system_accent_color():
        """Get Windows System Accent Color using Registry"""
        try:
            import winreg
            registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
            key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\DWM")
            # Windows stores color as ABGR (int)
            value, type_ = winreg.QueryValueEx(key, "AccentColor") 
            
            # Convert integer to hex string
            # Format is 0xFFAABBCC -> AABBCC (Alpha is strictly not needed for hex css usually, or Windows uses weird format)
            # Actually Windows DWM AccentColor is typically 0xffbbggrr (ABGR) in DWORD
            
            # Let's parse it carefully.
            # Example: 0xffd77800 (A=ff, B=d7, G=78, R=00) -> Color is #0078d7
            a = (value >> 24) & 0xFF
            b = (value >> 16) & 0xFF
            g = (value >> 8) & 0xFF
            r = value & 0xFF
            
            # CSS uses RGB
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception as e:
            print(f"Error getting system accent: {e}")
            return "#007AFF" # Fallback to Blue
            
    @classmethod
    def get_available_themes(cls):
        """Return list of (Display Name, key)"""
        return [
            ("Tự động (Theo hệ thống) 🎨", "system"),
            ("Sáng (Light)", "light"),
            ("Tối (Dark)", "dark"),
            ("Huyền bí (Dark Slate)", "minimal"), # Keeping one nice dark variant
        ]
    
    @classmethod
    def set_theme(cls, theme_name):
        """Set current theme"""
        # Reset Accent to Default Blue first to avoid stuck colors
        cls.COLOR_ACCENT = "#007AFF" 
        
        if theme_name == "system":
            # Detect System Mode (Light/Dark) - Using registry or sticking to Light for now + Accent
            # For simplicity, we can default to Light or Dark based on naive check, 
            # OR we can check AppsUseLightTheme
            
            # 1. Get Color
            accent = cls.get_system_accent_color()
            cls.COLOR_ACCENT = accent
            
            # Create a gradient from it
            # Lighter variant for gradient end
            cls.COLOR_ACCENT_GRADIENT = f"qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 {accent}, stop:1 {cls.adjust_color(accent, 1.2)})"
            
            cls._current_theme = "light" # Default base
            
            # 2. Check Dark Mode preference
            try:
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                if val == 0:
                    cls._current_theme = "dark"
            except:
                pass
                
        elif theme_name == "minimal":
            cls._current_theme = "minimal"
            cls.COLOR_ACCENT = "#37474f"
            cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #37474f, stop:1 #546e7a)"
            
        elif theme_name == "dark":
            cls._current_theme = "dark"
            cls.COLOR_ACCENT = "#0A84FF" # iOS Dark Blue
            cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #0A84FF, stop:1 #007AFF)"
            
        else: # Light
            cls._current_theme = "light"
            cls.COLOR_ACCENT = "#007AFF"
            cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #007AFF, stop:1 #0A84FF)"

    
    @classmethod
    def toggle_theme(cls):
        """Toggle between light and dark theme"""
        cls._current_theme = "dark" if cls._current_theme == "light" else "light"
    
    @classmethod
    def is_dark(cls):
        """Check if dark theme is active"""
        return cls._current_theme == "dark"
    
    @classmethod
    def get_icon(cls, name, fallback="●"):
        """Get icon by name with fallback"""
        return cls.ICONS.get(name, fallback)

    @staticmethod
    def adjust_color(hex_color, factor):
        """
        Adjusts the brightness of a HEX color.
        factor > 1: Lighter, factor < 1: Darker
        """
        if not hex_color.startswith('#'):
            return hex_color
            
        hex_color = hex_color.lstrip('#')
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        
        return f"#{r:02x}{g:02x}{b:02x}"
    
    # ==================== STYLE GENERATORS ====================
    @classmethod
    def get_main_window_style(cls):
        theme = cls.get_theme()
        return f"""
            QMainWindow {{
                background: {theme['COLOR_BG_GRADIENT']};
            }}
            QWidget {{
                font-family: {cls.FONT_FAMILY};
                color: {theme['COLOR_TEXT_PRIMARY']};
            }}
            QLabel {{
                color: {theme['COLOR_TEXT_PRIMARY']};
            }}
            QScrollBar:vertical {{
                border: none;
                background: rgba(0,0,0,0.05);
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(128,128,128,0.3);
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(128,128,128,0.5);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QToolTip {{
                background-color: {theme['COLOR_TEXT_PRIMARY']};
                color: {'#1A1A2E' if cls.is_dark() else 'white'};
                border: none;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
            }}
            /* Dialog Styling - Critical Fix for Dark Mode */
            QMessageBox, QDialog {{
                background-color: {theme['COLOR_DIALOG_BG']}; 
                color: {theme['COLOR_TEXT_PRIMARY']};
            }}
            QMessageBox QLabel {{
                color: {theme['COLOR_TEXT_PRIMARY']};
                background: transparent;
                min-width: 250px; /* Ensure wide enough for text */
                font-size: 13px;
            }}
            QMessageBox QPushButton {{
                background-color: {theme['COLOR_BG_SECONDARY']};
                color: {theme['COLOR_TEXT_PRIMARY']};
                border: 1px solid {theme['COLOR_BORDER']};
                border-radius: 4px;
                padding: 6px 15px;
                min-width: 80px;
            }}
            QMessageBox QPushButton:hover {{
                background-color: {ThemeManager.COLOR_ACCENT};
                color: white;
                border: 1px solid {ThemeManager.COLOR_ACCENT};
            }}
            
            /* Enforce background for all widgets inside dialog to match main bg */
            QDialog QWidget {{
                background-color: transparent;
                color: {theme['COLOR_TEXT_PRIMARY']};
            }}

            /* Specific Fix for Message Box Labels */
            QMessageBox QLabel {{
                color: {theme['COLOR_TEXT_PRIMARY']};
                font-size: 14px;
                background-color: transparent;
                min-width: 240px;
            }}
            
            QMessageBox QLabel#qt_msgbox_informativelabel {{
                color: {theme['COLOR_TEXT_SECONDARY']};
                font-weight: normal;
            }}
            
            /* Buttons in Dialogs */
            QMessageBox QPushButton, QDialog QPushButton {{
                min-width: 80px;
                padding: 6px 16px;
                border-radius: 6px;
                background-color: {theme['COLOR_GLASS_CARD']};
                color: {theme['COLOR_TEXT_PRIMARY']};
                border: 1px solid {theme['COLOR_BORDER']};
                font-weight: bold;
            }}
            
            QMessageBox QPushButton:hover, QDialog QPushButton:hover {{
                background-color: {theme['COLOR_GLASS_HOVER']};
                border: 1px solid {cls.COLOR_ACCENT};
            }}
            
            QMessageBox QPushButton:pressed {{
                background-color: {cls.COLOR_ACCENT_TRANSPARENT};
            }}
        """

    @classmethod
    def get_card_style(cls):
        """Style for the floating glass cards"""
        theme = cls.get_theme()
        return f"""
            QFrame, QWidget#Card {{
                background-color: {theme['COLOR_GLASS_WHITE']};
                border-radius: {cls.RADIUS_CARD};
                border: 1px solid {theme['COLOR_BORDER_LIGHT']};
            }}
            QLabel {{
                background: transparent;
            }}
        """

    @classmethod
    def get_sidebar_style(cls):
        theme = cls.get_theme()
        return f"""
            QFrame {{
                background-color: {theme['COLOR_GLASS_WHITE']};
                border-right: 1px solid {theme['COLOR_BORDER']};
            }}
            QPushButton {{
                text-align: left;
                padding: 12px 20px;
                border: none;
                background: transparent;
                color: {theme['COLOR_TEXT_PRIMARY']};
                font-weight: 600;
                border-radius: {cls.RADIUS_BUTTON};
                margin: 4px 10px;
            }}
            QPushButton:hover {{
                background-color: {theme['COLOR_GLASS_HOVER']};
                border: 1px solid {theme['COLOR_BORDER_LIGHT']};
            }}
            QPushButton:checked {{
                background: {cls.COLOR_ACCENT_GRADIENT};
                color: white;
                border: 1px solid rgba(255,255,255,0.2);
                font-weight: bold;
            }}
        """

    @classmethod
    def get_button_style(cls, variant="primary"):
        theme = cls.get_theme()
        
        if variant == "primary":
            bg = cls.COLOR_ACCENT_GRADIENT
            color = "white"
            border = "none"
        elif variant == "danger":
            bg = cls.COLOR_DANGER
            color = "white"
            border = "none"
        elif variant == "success":
            bg = cls.COLOR_SUCCESS
            color = "white"
            border = "none"
        elif variant == "warning":
            bg = cls.COLOR_WARNING
            color = "#1A1A2E"
            border = "none"
        else:  # outline/ghost
            bg = "transparent"
            color = theme['COLOR_TEXT_PRIMARY']
            border = f"1px solid {theme['COLOR_TEXT_SECONDARY']}"

        return f"""
            QPushButton {{
                background: {bg};
                color: {color};
                border: {border};
                padding: 10px 20px;
                border-radius: {cls.RADIUS_BUTTON};
                font-weight: bold;
                font-family: {cls.FONT_FAMILY};
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
            QPushButton:pressed {{
                opacity: 0.8;
            }}
            QPushButton:disabled {{
                opacity: 0.5;
            }}
        """

    @classmethod
    def get_input_style(cls):
        theme = cls.get_theme()
        return f"""
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {theme['COLOR_GLASS_CARD']};
                border: 1px solid {theme['COLOR_BORDER']};
                border-radius: {cls.RADIUS_INPUT};
                padding: 10px 14px;
                color: {theme['COLOR_TEXT_PRIMARY']};
                font-family: {cls.FONT_FAMILY};
                font-size: 14px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 2px solid {cls.COLOR_ACCENT};
                background-color: {theme['COLOR_GLASS_HOVER']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
        """

    @classmethod
    def get_settings_nav_style(cls):
        theme = cls.get_theme()
        return f"""
            QListWidget {{
                background-color: {theme['COLOR_GLASS_WHITE']};
                border-right: 1px solid {theme['COLOR_BORDER']};
                outline: 0px;
            }}
            QListWidget::item {{
                padding: 12px 20px;
                color: {theme['COLOR_TEXT_PRIMARY']};
                font-weight: 600;
                border-radius: {cls.RADIUS_BUTTON};
                margin: 4px 10px;
            }}
            QListWidget::item:hover {{
                background-color: {theme['COLOR_BG_SECONDARY']};
            }}
            QListWidget::item:selected {{
                background-color: {cls.COLOR_ACCENT};
                color: white;
            }}
        """

    @classmethod
    def get_table_style(cls):
        """Style for data tables"""
        theme = cls.get_theme()
        return f"""
            QTableWidget {{
                background-color: {theme['COLOR_GLASS_WHITE']};
                border-radius: {cls.RADIUS_CARD};
                border: 1px solid {theme['COLOR_BORDER_LIGHT']};
                outline: none;
                gridline-color: {theme['COLOR_BORDER']};
            }}
            QTableWidget::item {{
                padding: 10px;
                border-bottom: 1px solid {theme['COLOR_BORDER']};
                color: {theme['COLOR_TEXT_PRIMARY']};
            }}
            QTableWidget::item:selected {{
                background-color: {cls.COLOR_ACCENT}30;
                color: {theme['COLOR_TEXT_PRIMARY']};
            }}
            QHeaderView::section {{
                background-color: {theme['COLOR_BG_SECONDARY']};
                color: {theme['COLOR_TEXT_SECONDARY']};
                padding: 12px;
                border: none;
                border-bottom: 1px solid {theme['COLOR_BORDER']};
                font-weight: bold;
                text-transform: uppercase;
                font-size: 11px;
                letter-spacing: 0.5px;
            }}
            QTableWidget QTableCornerButton::section {{
                background: transparent;
                border: none;
            }}
        """

    @classmethod
    def get_group_box_style(cls):
        """Style for group boxes"""
        theme = cls.get_theme()
        return f"""
            QGroupBox {{
                background-color: {theme['COLOR_GLASS_WHITE']};
                border: 1px solid {theme['COLOR_BORDER']};
                border-radius: {cls.RADIUS_BUTTON};
                margin-top: 16px;
                padding: 20px;
                padding-top: 30px;
                color: {theme['COLOR_TEXT_PRIMARY']};
                font-weight: bold;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 15px;
                top: 8px;
                padding: 0 8px;
                background-color: {theme['COLOR_GLASS_WHITE']};
            }}
        """

    @classmethod
    def get_checkbox_style(cls):
        """Style for CheckBox and RadioButton"""
        theme = cls.get_theme()
        return f"""
            QCheckBox, QRadioButton {{
                spacing: 10px;
                font-size: 14px;
                color: {theme['COLOR_TEXT_PRIMARY']};
                font-family: {cls.FONT_FAMILY};
                background: transparent;
                padding: 4px;
            }}
            QCheckBox::indicator, QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border: 2px solid {theme['COLOR_TEXT_SECONDARY']};
                background: {theme['COLOR_GLASS_WHITE']};
            }}
            QCheckBox::indicator {{
                border-radius: 4px;
            }}
            QRadioButton::indicator {{
                border-radius: 11px;
            }}
            QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
                border: 2px solid {cls.COLOR_ACCENT};
                background-color: {cls.COLOR_ACCENT};
            }}
            QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
                border-color: {cls.COLOR_ACCENT};
                background-color: {theme['COLOR_GLASS_HOVER']};
            }}
        """

    @classmethod
    def get_text_edit_style(cls):
        """Style for text areas/log panels"""
        theme = cls.get_theme()
        return f"""
            QTextEdit {{
                background-color: {theme['COLOR_GLASS_WHITE']};
                border: 1px solid {theme['COLOR_BORDER']};
                border-radius: {cls.RADIUS_BUTTON};
                color: {theme['COLOR_TEXT_PRIMARY']};
                font-family: {cls.FONT_FAMILY_MONO};
                font-size: 12px;
                padding: 12px;
            }}
            QTextEdit:focus {{
                border: 1px solid {cls.COLOR_ACCENT};
            }}
        """

    @classmethod
    def get_sidebar_logo_style(cls):
        return f"""
            QFrame {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #3DDC84, stop:1 #32B36C);
                border-radius: 14px;
                border: 1px solid rgba(255,255,255,0.2);
            }}
        """

    @classmethod
    def get_sidebar_title_style(cls):
        theme = cls.get_theme()
        return f"""
            font-size: 19px;
            font-weight: 700;
            color: {theme['COLOR_TEXT_PRIMARY']};
            background: transparent;
            font-family: {cls.FONT_FAMILY};
            letter-spacing: -0.5px;
        """

    @classmethod
    def get_sidebar_group_label_style(cls):
        theme = cls.get_theme()
        return f"""
            color: {theme['COLOR_TEXT_SECONDARY']};
            font-size: 11px;
            font-weight: 600;
            padding-left: 14px;
            margin-bottom: 6px;
            background: transparent;
            font-family: {cls.FONT_FAMILY};
            text-transform: uppercase;
            opacity: 0.8;
        """

    @classmethod
    def get_nav_button_style(cls, padding_left="16px", checked_padding=None, alignment="left"):
        theme = cls.get_theme()
        hover_bg = theme['COLOR_GLASS_HOVER']
        
        c_padding = checked_padding if checked_padding else padding_left
        margin = "8px" if alignment == "left" else "14px"
        
        return f"""
            QPushButton {{
                text-align: {alignment};
                padding-left: {padding_left};
                padding-right: {padding_left if alignment == "center" else "0px"};
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 500;
                color: {theme['COLOR_TEXT_PRIMARY']};
                background: transparent;
                font-family: {cls.FONT_FAMILY};
                margin-left: {margin};
                margin-right: {margin};
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
            }}
            QPushButton:checked {{
                background: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(61, 220, 132, 0.25), stop:1 rgba(50, 179, 108, 0.15));
                color: {theme['COLOR_TEXT_PRIMARY']};
                font-weight: 700;
                border: 1px solid rgba(61, 220, 132, 0.4);
                border-left: {'4px solid #3DDC84' if alignment == 'left' else 'none'};
                padding-left: {c_padding};
                border-bottom: {'3px solid #3DDC84' if alignment == 'center' else 'none'};
            }}
        """

    @classmethod
    def get_statusbar_style(cls):
        theme = cls.get_theme()
        return f"""
            QStatusBar {{
                background: {theme['COLOR_GLASS_WHITE']};
                color: {theme['COLOR_TEXT_SECONDARY']};
                border-top: 1px solid {theme['COLOR_BORDER']};
                font-family: {cls.FONT_FAMILY};
                padding: 8px 16px;
                font-size: 12px;
            }}
        """

    @classmethod
    def get_header_frame_style(cls):
        theme = cls.get_theme()
        return f"""
            #MainHeader {{
                background-color: {theme['COLOR_GLASS_WHITE']};
                border-radius: 16px;
                border: 1px solid {theme['COLOR_BORDER_LIGHT']};
            }}
        """

    @classmethod
    def get_header_title_style(cls):
        theme = cls.get_theme()
        return f"""
            font-size: 22px;
            font-weight: 700;
            color: {theme['COLOR_TEXT_PRIMARY']};
            background: transparent;
            font-family: {cls.FONT_FAMILY};
        """

    @classmethod
    def get_icon_button_style(cls):
        theme = cls.get_theme()
        return f"""
            QPushButton {{
                background-color: {theme['COLOR_GLASS_CARD']};
                border-radius: 12px;
                border: 2px solid {theme['COLOR_BORDER']};
                font-size: 20px;
                color: {theme['COLOR_TEXT_PRIMARY']};
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {cls.COLOR_ACCENT}15;
                border: 2px solid {cls.COLOR_ACCENT};
                color: {cls.COLOR_ACCENT};
            }}
        """

    # Legacy compatibility - keep these as class variables pointing to light theme
    COLOR_BG_GRADIENT = LIGHT["COLOR_BG_GRADIENT"]
    COLOR_GLASS_WHITE = LIGHT["COLOR_GLASS_WHITE"]
    COLOR_GLASS_HOVER = LIGHT["COLOR_GLASS_HOVER"]
    COLOR_TEXT_PRIMARY = LIGHT["COLOR_TEXT_PRIMARY"]
    COLOR_TEXT_SECONDARY = LIGHT["COLOR_TEXT_SECONDARY"]
    COLOR_DATA = LIGHT["COLOR_DATA"]
    COLOR_BG_SECONDARY = LIGHT["COLOR_BG_SECONDARY"]
    COLOR_GLASS_CARD = LIGHT["COLOR_GLASS_CARD"]
    COLOR_SHADOW = LIGHT["COLOR_SHADOW"]
    COLOR_BORDER = LIGHT["COLOR_BORDER"]
    COLOR_BORDER_LIGHT = LIGHT["COLOR_BORDER_LIGHT"]
    COLOR_BACKGROUND = LIGHT["COLOR_BG_MAIN"]
