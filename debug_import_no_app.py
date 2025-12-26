
print("Testing imports WITHOUT QApplication...")
try:
    # Emulate main.py order: Imports first
    print("Importing PySide6...")
    from PySide6.QtWidgets import QApplication, QWidget
    
    print("Importing main_window (should imply all widgets)...")
    import src.ui.main_window
    
    print("Imports OK. Now creating App...")
    app = QApplication([])
    print("App Created.")
    
except Exception as e:
    print(f"CRASH DURING IMPORT: {e}")
    import traceback
    traceback.print_exc()
