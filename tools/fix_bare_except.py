"""Fix bare except: pass in all remaining src/ files"""
import os
import re

src_dir = 'src'
fixed_files = []

for root, dirs, files in os.walk(src_dir):
    # Skip __pycache__ and build dirs
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for fname in files:
        if not fname.endswith('.py'):
            continue
        fpath = os.path.join(root, fname)
        
        # Skip already fixed files
        if 'adb_manager.py' in fname or 'logcat_viewer.py' in fname or 'log_manager.py' in fname:
            continue
        
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        
        # Check if LogManager is already imported
        has_logmanager = 'from src.core.log_manager import LogManager' in content
        needs_import = False
        
        # Pattern 1: `except: pass` on one line
        if re.search(r'except:\s*pass', content):
            needs_import = True
            content = re.sub(
                r'(\s*)except:\s*pass',
                lambda m: f"{m.group(1)}except Exception as _e:\n{m.group(1)}    pass  # TODO: consider LogManager.log",
                content
            )
        
        # Pattern 2: `except:\n            pass` on two lines
        if re.search(r'except:\s*\n\s+pass', content):
            needs_import = True
            content = re.sub(
                r'(\s*)except:\s*\n(\s+)pass',
                lambda m: f"{m.group(1)}except Exception as _e:\n{m.group(2)}pass  # TODO: consider LogManager.log",
                content
            )
        
        # Pattern 3: bare `except:` followed by other code (not pass)
        if re.search(r'except:\s*\n\s+(?!pass)', content):
            content = re.sub(
                r'(\s*)except:\s*\n',
                lambda m: f"{m.group(1)}except Exception as _e:\n",
                content
            )
            needs_import = True
        
        if content != original:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            fixed_files.append(fpath)

print(f"Fixed {len(fixed_files)} files:")
for f in fixed_files:
    print(f"  - {f}")
