
print("Testing imports...")
try:
    print("Importing PySide6...")
    from PySide6.QtWidgets import QApplication, QWidget
    print("PySide6 OK")
    
    app = QApplication([])
    
    print("Importing xiaomi_optimizer...")
    from src.ui.widgets.xiaomi_optimizer import XiaomiBaseWidget
    print("xiaomi_optimizer OK")

    print("Importing app_manager...")
    import src.ui.widgets.app_manager
    print("app_manager OK")

    print("Importing main_window...")
    import src.ui.main_window
    print("main_window OK")
    
    print("All Imports Successful")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
