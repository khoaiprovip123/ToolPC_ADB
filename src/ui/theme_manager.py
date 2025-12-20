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
        "dashboard": "🏠",      # House
        "apps": "📱",           # Mobile Phone / Grid
        "files": "📁",          # Folder
        "xiaomi": "⚡",         # High Voltage (Xiaomi Power)
        "mirror": "🖥️",        # Desktop Computer
        "devtools": "🛠️",       # Hammer and Wrench
        "cloud": "☁️",         # Cloud
        "settings": "⚙️",       # Gear
        "fastboot": "🔌",       # Plug/Connection
        "tools": "🧰",          # Toolbox
        
        # Actions
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
        "COLOR_BG_GRADIENT": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #F2F2F7, stop:1 #FFFFFF)", # System Grouped Background
        "COLOR_BG_MAIN": "#F2F2F7",
        "COLOR_GLASS_WHITE": "rgba(255, 255, 255, 0.65)", # Ultra Thin
        "COLOR_GLASS_HOVER": "rgba(255, 255, 255, 0.85)",
        "COLOR_GLASS_CARD": "rgba(255, 255, 255, 0.95)",  # Opaque cards
        "COLOR_TEXT_PRIMARY": "#000000",
        "COLOR_TEXT_SECONDARY": "#8E8E93", # System Gray
        "COLOR_DATA": "#1C1C1E",
        "COLOR_BG_SECONDARY": "rgba(118, 118, 128, 0.12)", # System Fill
        "COLOR_SHADOW": "rgba(0, 0, 0, 0.1)",
        "COLOR_BORDER": "rgba(60, 60, 67, 0.1)",           # Separator
        "COLOR_BORDER_LIGHT": "rgba(60, 60, 67, 0.05)",
    }
    
    # Dark Mode
    DARK = {
        "COLOR_BG_GRADIENT": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #000000, stop:1 #1C1C1E)",
        "COLOR_BG_MAIN": "#000000",
        "COLOR_GLASS_WHITE": "rgba(30, 30, 30, 0.70)",
        "COLOR_GLASS_HOVER": "rgba(44, 44, 46, 0.85)",
        "COLOR_GLASS_CARD": "rgba(28, 28, 30, 0.95)",
        "COLOR_TEXT_PRIMARY": "#FFFFFF",
        "COLOR_TEXT_SECONDARY": "#98989E",
        "COLOR_DATA": "#FFFFFF",
        "COLOR_BG_SECONDARY": "rgba(118, 118, 128, 0.24)",
        "COLOR_SHADOW": "rgba(0, 0, 0, 0.3)",
        "COLOR_BORDER": "rgba(84, 84, 88, 0.50)",
        "COLOR_BORDER_LIGHT": "rgba(84, 84, 88, 0.25)",
    }

    # Cyberpunk Theme (Neon)
    CYBERPUNK = {
        "COLOR_BG_GRADIENT": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #050510, stop:1 #100b20)",
        "COLOR_BG_MAIN": "#0b0c15",
        "COLOR_GLASS_WHITE": "rgba(20, 20, 40, 0.70)",
        "COLOR_GLASS_HOVER": "rgba(40, 40, 80, 0.85)",
        "COLOR_GLASS_CARD": "rgba(15, 15, 30, 0.95)",
        "COLOR_TEXT_PRIMARY": "#00f2fe", # Cyan
        "COLOR_TEXT_SECONDARY": "#ff0099", # Neon Pink
        "COLOR_DATA": "#00e5ff",
        "COLOR_BG_SECONDARY": "rgba(0, 229, 255, 0.1)",
        "COLOR_SHADOW": "rgba(0, 229, 255, 0.2)",
        "COLOR_BORDER": "rgba(0, 242, 254, 0.4)",
        "COLOR_BORDER_LIGHT": "rgba(255, 0, 153, 0.3)",
    }

    # HyperOS Theme (Orange/Clean)
    HYPEROS = {
        "COLOR_BG_GRADIENT": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #f5f7fa, stop:1 #fffbf0)",
        "COLOR_BG_MAIN": "#ffffff",
        "COLOR_GLASS_WHITE": "rgba(255, 255, 255, 0.85)",
        "COLOR_GLASS_HOVER": "rgba(255, 165, 0, 0.1)", # Orange tint
        "COLOR_GLASS_CARD": "rgba(255, 255, 255, 0.98)",
        "COLOR_TEXT_PRIMARY": "#2c3e50",
        "COLOR_TEXT_SECONDARY": "#e67e22", # Orange
        "COLOR_DATA": "#fcf5ee",
        "COLOR_BG_SECONDARY": "rgba(230, 126, 34, 0.1)",
        "COLOR_SHADOW": "rgba(0, 0, 0, 0.08)",
        "COLOR_BORDER": "rgba(230, 126, 34, 0.2)",
        "COLOR_BORDER_LIGHT": "rgba(0, 0, 0, 0.05)",
    }

    # Minimal Theme (Slate)
    MINIMAL = {
        "COLOR_BG_GRADIENT": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #eef2f3, stop:1 #e0e4e7)",
        "COLOR_BG_MAIN": "#e0e4e7",
        "COLOR_GLASS_WHITE": "rgba(255, 255, 255, 0.5)", # More transp
        "COLOR_GLASS_HOVER": "rgba(255, 255, 255, 0.8)",
        "COLOR_GLASS_CARD": "rgba(240, 240, 245, 0.9)",
        "COLOR_TEXT_PRIMARY": "#37474f", # Slate
        "COLOR_TEXT_SECONDARY": "#78909c",
        "COLOR_DATA": "#000000",
        "COLOR_BG_SECONDARY": "rgba(0, 0, 0, 0.05)",
        "COLOR_SHADOW": "rgba(0, 0, 0, 0.08)",
        "COLOR_BORDER": "rgba(55, 71, 79, 0.1)",
        "COLOR_BORDER_LIGHT": "rgba(55, 71, 79, 0.05)",
    }
    
    # Ocean Blue Theme 🌊
    OCEAN_BLUE = {
        "COLOR_BG_GRADIENT": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #e3f2fd, stop:1 #bbdefb)",
        "COLOR_BG_MAIN": "#e1f5fe",
        "COLOR_GLASS_WHITE": "rgba(255, 255, 255, 0.75)",
        "COLOR_GLASS_HOVER": "rgba(33, 150, 243, 0.1)",
        "COLOR_GLASS_CARD": "rgba(255, 255, 255, 0.95)",
        "COLOR_TEXT_PRIMARY": "#01579b",
        "COLOR_TEXT_SECONDARY": "#0277bd",
        "COLOR_DATA": "#004d7a",
        "COLOR_BG_SECONDARY": "rgba(3, 169, 244, 0.1)",
        "COLOR_SHADOW": "rgba(0, 119, 190, 0.15)",
        "COLOR_BORDER": "rgba(33, 150, 243, 0.3)",
        "COLOR_BORDER_LIGHT": "rgba(33, 150, 243, 0.1)",
    }

    # Sunset Purple Theme 🌅
    SUNSET_PURPLE = {
        "COLOR_BG_GRADIENT": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #f3e5f5, stop:1 #e1bee7)",
        "COLOR_BG_MAIN": "#f3e5f5",
        "COLOR_GLASS_WHITE": "rgba(255, 255, 255, 0.7)",
        "COLOR_GLASS_HOVER": "rgba(156, 39, 176, 0.1)",
        "COLOR_GLASS_CARD": "rgba(255, 255, 255, 0.92)",
        "COLOR_TEXT_PRIMARY": "#4a148c",
        "COLOR_TEXT_SECONDARY": "#7b1fa2",
        "COLOR_DATA": "#38006b",
        "COLOR_BG_SECONDARY": "rgba(142, 68, 173, 0.12)",
        "COLOR_SHADOW": "rgba(106, 17, 203, 0.12)",
        "COLOR_BORDER": "rgba(156, 39, 176, 0.25)",
        "COLOR_BORDER_LIGHT": "rgba(156, 39, 176, 0.1)",
    }

    # Forest Green Theme 🌲
    FOREST_GREEN = {
        "COLOR_BG_GRADIENT": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #e8f5e9, stop:1 #c8e6c9)",
        "COLOR_BG_MAIN": "#e8f5e9",
        "COLOR_GLASS_WHITE": "rgba(255, 255, 255, 0.72)",
        "COLOR_GLASS_HOVER": "rgba(76, 175, 80, 0.1)",
        "COLOR_GLASS_CARD": "rgba(255, 255, 255, 0.94)",
        "COLOR_TEXT_PRIMARY": "#1b5e20",
        "COLOR_TEXT_SECONDARY": "#2e7d32",
        "COLOR_DATA": "#0d3d13",
        "COLOR_BG_SECONDARY": "rgba(46, 125, 50, 0.1)",
        "COLOR_SHADOW": "rgba(39, 174, 96, 0.12)",
        "COLOR_BORDER": "rgba(76, 175, 80, 0.3)",
        "COLOR_BORDER_LIGHT": "rgba(76, 175, 80, 0.1)",
    }

    # Rose Gold Theme 💎
    ROSE_GOLD = {
        "COLOR_BG_GRADIENT": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #fce4ec, stop:1 #f8bbd0)",
        "COLOR_BG_MAIN": "#fff0f3",
        "COLOR_GLASS_WHITE": "rgba(255, 255, 255, 0.78)",
        "COLOR_GLASS_HOVER": "rgba(233, 163, 173, 0.15)",
        "COLOR_GLASS_CARD": "rgba(255, 255, 255, 0.96)",
        "COLOR_TEXT_PRIMARY": "#880e4f",
        "COLOR_TEXT_SECONDARY": "#b76e79",
        "COLOR_DATA": "#6d0036",
        "COLOR_BG_SECONDARY": "rgba(232, 163, 157, 0.15)",
        "COLOR_SHADOW": "rgba(183, 110, 121, 0.18)",
        "COLOR_BORDER": "rgba(233, 163, 173, 0.35)",
        "COLOR_BORDER_LIGHT": "rgba(233, 163, 173, 0.12)",
    }

    # Nord Theme ❄️
    NORD = {
        "COLOR_BG_GRADIENT": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #2e3440, stop:1 #3b4252)",
        "COLOR_BG_MAIN": "#2e3440",
        "COLOR_GLASS_WHITE": "rgba(59, 66, 82, 0.75)",
        "COLOR_GLASS_HOVER": "rgba(76, 86, 106, 0.85)",
        "COLOR_GLASS_CARD": "rgba(46, 52, 64, 0.92)",
        "COLOR_TEXT_PRIMARY": "#eceff4",
        "COLOR_TEXT_SECONDARY": "#88c0d0",
        "COLOR_DATA": "#d8dee9",
        "COLOR_BG_SECONDARY": "rgba(136, 192, 208, 0.12)",
        "COLOR_SHADOW": "rgba(0, 0, 0, 0.25)",
        "COLOR_BORDER": "rgba(136, 192, 208, 0.3)",
        "COLOR_BORDER_LIGHT": "rgba(136, 192, 208, 0.15)",
    }

    # Material You Theme 🎨
    MATERIAL_YOU = {
        "COLOR_BG_GRADIENT": "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:1, stop:0 #fafafa, stop:1 #f5f5f5)",
        "COLOR_BG_MAIN": "#ffffff",
        "COLOR_GLASS_WHITE": "rgba(255, 255, 255, 0.88)",
        "COLOR_GLASS_HOVER": "rgba(0, 137, 123, 0.08)",
        "COLOR_GLASS_CARD": "rgba(255, 255, 255, 0.97)",
        "COLOR_TEXT_PRIMARY": "#1a1a1a",
        "COLOR_TEXT_SECONDARY": "#00897b",
        "COLOR_DATA": "#000000",
        "COLOR_BG_SECONDARY": "rgba(0, 137, 123, 0.08)",
        "COLOR_SHADOW": "rgba(0, 0, 0, 0.12)",
        "COLOR_BORDER": "rgba(0, 137, 123, 0.22)",
        "COLOR_BORDER_LIGHT": "rgba(0, 0, 0, 0.08)",
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
    RADIUS_INPUT = "10px"
    BLUR_RADIUS = "20px"      # Standard Blur
    
    # ==================== HELPER METHODS ====================
    @classmethod
    def get_theme(cls):
        """Get current theme colors"""
        if cls._current_theme == "dark": return cls.DARK
        if cls._current_theme == "cyberpunk": return cls.CYBERPUNK
        if cls._current_theme == "hyperos": return cls.HYPEROS
        if cls._current_theme == "minimal": return cls.MINIMAL
        if cls._current_theme == "ocean": return cls.OCEAN_BLUE
        if cls._current_theme == "sunset": return cls.SUNSET_PURPLE
        if cls._current_theme == "forest": return cls.FOREST_GREEN
        if cls._current_theme == "rose": return cls.ROSE_GOLD
        if cls._current_theme == "nord": return cls.NORD
        if cls._current_theme == "material": return cls.MATERIAL_YOU
        return cls.LIGHT

    @classmethod
    def get_available_themes(cls):
        """Return list of (Display Name, key)"""
        return [
            ("Sáng (Light)", "light"),
            ("Tối (Dark)", "dark"),
            ("Cyberpunk (Neon)", "cyberpunk"),
            ("HyperOS (Orange)", "hyperos"),
            ("Minimal (Slate)", "minimal"),
            ("Ocean Blue 🌊", "ocean"),
            ("Sunset Purple 🌅", "sunset"),
            ("Forest Green 🌲", "forest"),
            ("Rose Gold 💎", "rose"),
            ("Nord ❄️", "nord"),
            ("Material You 🎨", "material"),
        ]
    
    @classmethod
    def set_theme(cls, theme_name):
        """Set current theme"""
        valid_themes = ["light", "dark", "cyberpunk", "hyperos", "minimal", 
                       "ocean", "sunset", "forest", "rose", "nord", "material"]
        
        if theme_name in valid_themes:
            cls._current_theme = theme_name
            
            # Update Accent colors dynamically per theme
            if theme_name == "cyberpunk":
                cls.COLOR_ACCENT = "#00f2fe"
                cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #00f2fe, stop:1 #4facfe)"
            elif theme_name == "hyperos":
                cls.COLOR_ACCENT = "#ff6700"  # Xiaomi Orange
                cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #ff6700, stop:1 #ff8f00)"
            elif theme_name == "minimal":
                cls.COLOR_ACCENT = "#37474f"
                cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #37474f, stop:1 #546e7a)"
            elif theme_name == "ocean":
                cls.COLOR_ACCENT = "#0277bd"
                cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #0277bd, stop:1 #03a9f4)"
            elif theme_name == "sunset":
                cls.COLOR_ACCENT = "#7b1fa2"
                cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #7b1fa2, stop:1 #9c27b0)"
            elif theme_name == "forest":
                cls.COLOR_ACCENT = "#2e7d32"
                cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #2e7d32, stop:1 #4caf50)"
            elif theme_name == "rose":
                cls.COLOR_ACCENT = "#b76e79"
                cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #b76e79, stop:1 #e8a39d)"
            elif theme_name == "nord":
                cls.COLOR_ACCENT = "#88c0d0"
                cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #88c0d0, stop:1 #81a1c1)"
            elif theme_name == "material":
                cls.COLOR_ACCENT = "#00897b"
                cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #00897b, stop:1 #00acc1)"
            else:
                # Default: iOS Blue
                cls.COLOR_ACCENT = "#007AFF"
                cls.COLOR_ACCENT_GRADIENT = "qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 #007AFF, stop:1 #0A84FF)"
        else:
            cls._current_theme = "light"
    
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
