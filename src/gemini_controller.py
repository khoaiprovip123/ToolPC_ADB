
import json
import os
import time

# We will try to import google.generativeai, but handle if it's not installed
try:
    import google.generativeai as genai
except ImportError:
    genai = None

from src.core.log_manager import LogManager
from src.core.workers.macro_worker import MacroWorker
from src.core.adb.adb_manager import ADBManager

# Load API key from environment variable (set in .env or system env)
# Never hardcode the key directly in source code
API_KEY = os.environ.get("GEMINI_API_KEY", "")

class GeminiController:
    """
    Uses the Gemini API to translate natural language commands into
    executable ADB macros and runs them.
    """
    def __init__(self, adb_manager: ADBManager):
        self.adb = adb_manager
        self.worker = None

        if not genai:
            LogManager.log("GeminiAI", "⚠️ Thư viện 'google-generativeai' chưa được cài đặt (pip install google-generativeai)", "warning")
            self.api_enabled = False
        elif not API_KEY:
            LogManager.log("GeminiAI", "⚠️ GEMINI_API_KEY chưa được cấu hình trong biến môi trường", "warning")
            self.api_enabled = False
        else:
            try:
                genai.configure(api_key=API_KEY)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.api_enabled = True
                LogManager.log("GeminiAI", "✅ Gemini API đã được cấu hình thành công", "success")
            except Exception as e:
                LogManager.log("GeminiAI", f"❌ Lỗi cấu hình Gemini API: {e}", "error")
                self.api_enabled = False

    def _build_prompt(self, command_text: str) -> str:
        return f"""
        You are an expert ADB macro generator. Your task is to convert a natural language command into a JSON array of actions for an ADB macro tool.

        Available Action Types:
        1. "Click": Taps a specific coordinate.
           - Parameters: "x", "y"
           - Example: {{"type": "Click", "x": 540, "y": 1200}}
        2. "Swipe": Swipes from a start to an end coordinate over a duration.
           - Parameters: "x1", "y1", "x2", "y2", "duration" (in ms)
           - Example: {{"type": "Swipe", "x1": 540, "y1": 1800, "x2": 540, "y2": 600, "duration": 500}}
        3. "Text": Types a string of text. The tool will handle spaces.
           - Parameters: "text"
           - Example: {{"type": "Text", "text": "hello world"}}
        4. "Key": Simulates a hardware key press.
           - Parameters: "keycode" (string)
           - Common Keycodes: "3" (HOME), "4" (BACK), "26" (POWER), "66" (ENTER), "187" (APP_SWITCH)
           - Example: {{"type": "Key", "keycode": "4"}}
        5. "Wait": Pauses the macro for a specified time.
           - Parameters: "ms" (in milliseconds)
           - Example: {{"type": "Wait", "ms": 1000}}

        IMPORTANT:
        - You MUST respond with ONLY the raw JSON array. Do not include any other text, explanations, or markdown formatting like ```json.
        - Assume a standard phone screen size of 1080x1920 pixels if specific coordinates are not given. The top-left is (0,0).
        - Be precise. If the user says "center", calculate it (e.g., 540, 960).

        Now, please convert the following command into a JSON macro:

        Command: "{command_text}"
        """

    def _get_demo_macro(self):
        """Returns a hardcoded macro for demonstration purposes."""
        LogManager.log("GeminiAI", "Đang chạy macro demo (API chưa được cấu hình)", "info")
        return [
            {"type": "Key", "keycode": "3"},
            {"type": "Wait", "ms": 1500},
            {"type": "Swipe", "x1": 540, "y1": 1600, "x2": 540, "y2": 400, "duration": 400},
            {"type": "Wait", "ms": 1500},
            {"type": "Click", "x": 540, "y": 960}
        ]

    def _generate_macro_from_api(self, command_text: str) -> list | None:
        """Generates macro by calling the Gemini API."""
        prompt = self._build_prompt(command_text)
        try:
            LogManager.log("GeminiAI", "Đang gửi lệnh đến Gemini API...", "info")
            response = self.model.generate_content(prompt)
            json_text = response.text.strip().replace("```json", "").replace("```", "").strip()
            macro = json.loads(json_text)
            if isinstance(macro, list):
                LogManager.log("GeminiAI", f"✅ Nhận được macro từ Gemini ({len(macro)} bước)", "success")
                return macro
            else:
                LogManager.log("GeminiAI", f"❌ API trả về dữ liệu không hợp lệ (không phải list)", "error")
                return None
        except Exception as e:
            LogManager.log("GeminiAI", f"❌ Lỗi khi gọi Gemini API: {e}", "error")
            return None

    def execute_command(self, command_text: str, progress_callback=None, finished_callback=None):
        """
        Generates and executes a macro from a natural language command.
        """
        macro_actions = None
        if self.api_enabled:
            macro_actions = self._generate_macro_from_api(command_text)
        else:
            macro_actions = self._get_demo_macro()
        
        if not macro_actions:
            LogManager.log("GeminiAI", "❌ Không thể tạo macro. Hủy thực thi.", "error")
            if finished_callback:
                finished_callback()
            return
        
        # Now, execute the macro
        if not self.adb.check_connection():
            LogManager.log("GeminiAI", "❌ Không có thiết bị kết nối. Hủy thực thi.", "error")
            if finished_callback:
                finished_callback()
            return
            
        LogManager.log("GeminiAI", f"▶️ Đang thực thi macro ({len(macro_actions)} bước)...", "info")
        # Guard: stop old worker before creating new
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait(3000)
        self.worker = MacroWorker(self.adb, macro_actions)
        
        # Connect signals
        effective_progress_callback = progress_callback or (lambda msg: LogManager.log("GeminiAI", msg, "info"))
        self.worker.progress.connect(effective_progress_callback)

        def on_finish():
            LogManager.log("GeminiAI", "✅ Thực thi macro hoàn tất", "success")
            if finished_callback:
                finished_callback()
        
        self.worker.finished.connect(on_finish)
            
        self.worker.start()

    def stop_macro(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            LogManager.log("GeminiAI", "⏹️ Macro đã dừng bởi người dùng", "info")
