
try:
    from PySide6.QtWidgets import QSizePolicy
    print(f"QSizePolicy imported successfully: {QSizePolicy}")
    print(f"Expanding: {QSizePolicy.Expanding}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
