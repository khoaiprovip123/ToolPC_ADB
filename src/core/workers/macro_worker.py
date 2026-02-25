"""
MacroWorker: A QThread for executing ADB macro actions in the background.
"""
import time
from PySide6.QtCore import QThread, Signal

class MacroWorker(QThread):
    progress = Signal(str)
    finished = Signal()
    
    def __init__(self, adb, actions):
        super().__init__()
        self.adb = adb
        self.actions = actions
        self._running = True
        
    def run(self):
        """Executes the list of actions."""
        for i, action in enumerate(self.actions):
            if not self._running:
                self.progress.emit("Macro cancelled.")
                break
                
            atype = action.get("type", "")
            self.progress.emit(f"Step {i+1}/{len(self.actions)}: {atype}")
            
            try:
                if atype == "Click":
                    self.adb.shell(f"input tap {action['x']} {action['y']}")
                elif atype == "Swipe":
                    self.adb.shell(f"input swipe {action['x1']} {action['y1']} {action['x2']} {action['y2']} {action['duration']}")
                elif atype == "Text":
                    # Escape spaces and other special characters for adb shell
                    text = action['text'].replace(" ", "%s")
                    # Add more escaping here if needed
                    self.adb.shell(f"input text '{text}'")
                elif atype == "Key":
                    self.adb.shell(f"input keyevent {action['keycode']}")
                elif atype == "Wait":
                    time.sleep(action['ms'] / 1000.0)
                    
                # Small delay between actions by default to ensure commands complete
                if atype != "Wait":
                    time.sleep(0.5)
                    
            except Exception as e:
                self.progress.emit(f"Error on step {i+1}: {e}")
                # Decide if we should stop on error
                break
                
        self.finished.emit()
        
    def stop(self):
        """Stops the execution loop."""
        self._running = False
