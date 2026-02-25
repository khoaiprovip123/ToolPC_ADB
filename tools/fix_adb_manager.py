"""Fix adb_manager.py using line-by-line approach"""

path = r'src\core\adb\adb_manager.py'

with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
changes = 0

while i < len(lines):
    line = lines[i]
    
    # === 1. Add shlex import after subprocess ===
    if line.strip() == 'import subprocess' and i == 0:
        new_lines.append(line)
        new_lines.append('import shlex\n')
        changes += 1
        i += 1
        continue
    
    # === 2. Add LogManager import after `import sys` (first occurrence) ===
    if line.strip() == 'import sys' and i < 10:
        new_lines.append(line)
        new_lines.append('from src.core.log_manager import LogManager\n')
        changes += 1
        i += 1
        continue
    
    # === 3. Fix get_fastboot_devices: replace cmd string + shell=True block ===
    if "cmd = f'\"" in line and 'fastboot_path' in line and 'devices' in line:
        # Skip this line and the old block, replace with new
        # Skip lines until ".strip()" line
        new_lines.append('            # Build command list without shell for security\n')
        new_lines.append('            cmd_list = [fastboot_path, "devices"]\n')
        new_lines.append('            out = subprocess.check_output(\n')
        new_lines.append('                cmd_list, stderr=subprocess.STDOUT,\n')
        new_lines.append("                creationflags=0x08000000 if os.name == 'nt' else 0,\n")
        new_lines.append("                encoding='utf-8', errors='replace', timeout=30\n")
        new_lines.append('            ).strip()\n')
        changes += 1
        # Skip old lines until we find .strip()
        while i < len(lines) and '.strip()' not in lines[i]:
            i += 1
        i += 1  # skip the .strip() line too
        continue
    
    # === 4. Fix execute() method: remove shell=True ===
    if line.strip().startswith("cmd_list = f'\"") and 'adb_path' in line:
        # Replace string command with shlex.split
        new_lines.append('            # Convert string to list for security (no shell injection)\n')
        new_lines.append('            args = shlex.split(command)\n')
        new_lines.append('            cmd_list = [self.adb_path] + args\n')
        changes += 1
        i += 1
        continue
    
    # Skip "# Use shell=True for string command" line
    if '# Use shell=True for string command' in line:
        i += 1
        continue
    
    # Skip "use_shell = isinstance(command, str)" line
    if 'use_shell = isinstance(command, str)' in line:
        i += 1
        continue
    
    # Fix subprocess.check_output call: remove shell=use_shell, add timeout
    if 'shell=use_shell,' in line:
        # Skip this line (shell param)
        i += 1
        continue
    
    # Add timeout before ).strip() in execute
    if line.strip() == "errors='replace'" and i+1 < len(lines) and ').strip()' in lines[i+1]:
        new_lines.append(line.rstrip('\r\n') + ',\n')
        new_lines.append('                timeout=30\n')
        changes += 1
        i += 1
        continue
    
    # === 5. Fix CalledProcessError handler in execute() — add logging ===
    if 'except subprocess.CalledProcessError as e:' in line and i+1 < len(lines) and 'return e.output.strip()' in lines[i+1]:
        new_lines.append(line)
        new_lines.append("            LogManager.log('ADB Error', f'Command failed', 'error')\n")
        new_lines.append(lines[i+1])  # keep return e.output.strip()
        changes += 1
        i += 2
        continue
    
    # === 6. Add TimeoutExpired handler before generic Exception ===
    if 'except Exception as e:' in line and i+1 < len(lines) and 'return f"Error: {e}"' in lines[i+1]:
        new_lines.append("        except subprocess.TimeoutExpired:\n")
        new_lines.append("            LogManager.log('ADB Timeout', 'Command timed out after 30s', 'error')\n")
        new_lines.append("            return 'Error: Timeout after 30s'\n")
        new_lines.append(line)  # except Exception as e:
        new_lines.append("            LogManager.log('ADB Exception', str(e), 'error')\n")
        new_lines.append(lines[i+1])  # return f"Error: {e}"
        changes += 1
        i += 2
        continue
    
    # === 7. Replace bare `except:` with proper handler ===
    if line.strip() == 'except:':
        # Check next line
        next_line = lines[i+1] if i+1 < len(lines) else ''
        indent = line[:len(line) - len(line.lstrip())]
        inner_indent = indent + '    '
        
        if next_line.strip() == 'pass':
            new_lines.append(f"{indent}except Exception as e:\n")
            new_lines.append(f"{inner_indent}LogManager.log('ADB', f'Unexpected error: {{e}}', 'error')\n")
            changes += 1
            i += 2  # skip both except: and pass
            continue
        else:
            new_lines.append(f"{indent}except Exception as e:\n")
            changes += 1
            i += 1
            continue
    
    # === 8. Replace bare `except: pass` on single line ===
    stripped = line.strip()
    if stripped == 'except: pass':
        indent = line[:len(line) - len(line.lstrip())]
        inner_indent = indent + '    '
        new_lines.append(f"{indent}except Exception as e:\n")
        new_lines.append(f"{inner_indent}LogManager.log('ADB', f'Unexpected error: {{e}}', 'error')\n")
        changes += 1
        i += 1
        continue
    
    # Default: keep line as-is
    new_lines.append(line)
    i += 1

with open(path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"DONE: {changes} changes applied to adb_manager.py")
