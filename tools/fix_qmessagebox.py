"""
Phase 3: Replace QMessageBox with LogManager.log across all widget files.
Keeps QMessageBox.question() dialogs intact (user interaction required).
Keeps update_dialog.py intact (separate dialog flow).
"""
import re
import os

FILES_TO_FIX = {
    # file_path: list of (line_pattern, replacement)
    # We'll do regex-based replacements
}

src_dir = 'src'
fixed_count = 0
fixed_files = []

# Files to SKIP (interactive dialogs that need QMessageBox.question)
SKIP_FILES = ['update_dialog.py', 'console.py']  # These have question() dialogs with user flow

for root, dirs, files in os.walk(src_dir):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for fname in files:
        if not fname.endswith('.py'):
            continue
        if fname in SKIP_FILES:
            continue
            
        fpath = os.path.join(root, fname)
        
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Skip files without QMessageBox
        if 'QMessageBox' not in content:
            continue
        
        # Check if LogManager is imported
        has_logmanager = 'from src.core.log_manager import LogManager' in content
        
        # === Pattern 1: QMessageBox.warning(self, "title", "msg") ===
        # Replace with LogManager.log("title", "msg", "warning")
        content = re.sub(
            r'QMessageBox\.warning\(self,\s*"([^"]+)",\s*"([^"]+)"\)',
            lambda m: f'LogManager.log("{m.group(1)}", "{m.group(2)}", "warning")',
            content
        )
        
        # === Pattern 2: QMessageBox.information(self, "title", "msg") ===
        content = re.sub(
            r'QMessageBox\.information\(self,\s*"([^"]+)",\s*"([^"]+)"\)',
            lambda m: f'LogManager.log("{m.group(1)}", "{m.group(2)}", "success")',
            content
        )
        
        # === Pattern 3: QMessageBox.critical(self, "title", "msg") ===
        content = re.sub(
            r'QMessageBox\.critical\(self,\s*"([^"]+)",\s*"([^"]+)"\)',
            lambda m: f'LogManager.log("{m.group(1)}", "{m.group(2)}", "error")',
            content
        )
        
        # === Pattern 4: QMessageBox.warning(self, "title", f"msg {var}") ===
        content = re.sub(
            r'QMessageBox\.warning\(self,\s*"([^"]+)",\s*(f"[^"]+"|f\'[^\']+\')\)',
            lambda m: f'LogManager.log("{m.group(1)}", {m.group(2)}, "warning")',
            content
        )
        
        # === Pattern 5: QMessageBox.information(self, "title", f"msg {var}") ===
        content = re.sub(
            r'QMessageBox\.information\(self,\s*"([^"]+)",\s*(f"[^"]+"|f\'[^\']+\')\)',
            lambda m: f'LogManager.log("{m.group(1)}", {m.group(2)}, "success")',
            content
        )
        
        # === Pattern 6: QMessageBox.critical(self, "title", f"msg {var}") ===
        content = re.sub(
            r'QMessageBox\.critical\(self,\s*"([^"]+)",\s*(f"[^"]+"|f\'[^\']+\')\)',
            lambda m: f'LogManager.log("{m.group(1)}", {m.group(2)}, "error")',
            content
        )

        # === Pattern 7: QMessageBox.critical(self, "title", str(e)) ===
        content = re.sub(
            r'QMessageBox\.critical\(self,\s*"([^"]+)",\s*str\(e\)\)',
            lambda m: f'LogManager.log("{m.group(1)}", str(e), "error")',
            content
        )

        # === Pattern 8: QMessageBox.warning(self, "title", msg) where msg is a variable ===
        content = re.sub(
            r'QMessageBox\.warning\(self,\s*"([^"]+)",\s*msg\)',
            lambda m: f'LogManager.log("{m.group(1)}", msg, "warning")',
            content
        )
        
        if content != original:
            # Add LogManager import if not present
            if not has_logmanager and 'LogManager.log' in content:
                # Find a good place to add import
                if 'from src.ui.theme_manager import ThemeManager' in content:
                    content = content.replace(
                        'from src.ui.theme_manager import ThemeManager',
                        'from src.ui.theme_manager import ThemeManager\nfrom src.core.log_manager import LogManager'
                    )
                elif 'from PySide6' in content:
                    # Add after last PySide6 import
                    lines = content.split('\n')
                    last_pyside = 0
                    for i, line in enumerate(lines):
                        if 'from PySide6' in line or 'import PySide6' in line:
                            last_pyside = i
                    lines.insert(last_pyside + 1, 'from src.core.log_manager import LogManager')
                    content = '\n'.join(lines)
            
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Count changes
            changes = len(re.findall(r'LogManager\.log\(', content)) - len(re.findall(r'LogManager\.log\(', original))
            fixed_count += changes
            fixed_files.append((fpath, changes))

print(f"DONE: {fixed_count} QMessageBox calls replaced across {len(fixed_files)} files:")
for f, c in fixed_files:
    print(f"  - {f}: {c} replacements")

# Show remaining QMessageBox for manual review
print("\n--- Remaining QMessageBox (interactive/multi-line) ---")
for root, dirs, files in os.walk(src_dir):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(root, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if 'QMessageBox.' in line and 'import' not in line:
                    print(f"  {fpath}:{i}: {line.strip()[:100]}")
