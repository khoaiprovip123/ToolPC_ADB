
import sys
import os

path = r'd:\BT\AndroidTOOL\Xiaomi_ADB_Commander\src\ui\widgets\settings.py'
with open(path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if '# Release Notes v2.5.1.1 mapped content' in line:
        start_idx = i
    if 'if ThemeManager.get_theme() == "dark":' in line and start_idx != -1 and i > start_idx:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    new_content = [
        '        # Release Notes v2.5.1.2 mapped content\n',
        '        changelog_html = """\n',
        '        <h3 style="margin-bottom: 5px;">📦 Installer & Installer Support</h3>\n',
        '        <ul style="margin-top: 0px; margin-bottom: 10px; margin-left: -20px; color: #333;">\n',
        '            <li><b>Official Setup Installer:</b> Added Windows installer (<code>setup.exe</code>) for easier deployment.</li>\n',
        '             <li><b>Auto-Update:</b> Fully supported in installer version.</li>\n',
        '        </ul>\n',
        '\n',
        '        <h3 style="margin-bottom: 5px;">🛠 Improvements (v2.5.1.2)</h3>\n',
        '        <ul style="margin-top: 0px; margin-bottom: 0px; margin-left: -20px; color: #333;">\n',
        '            <li>✨ <b>Code Signing Prep:</b> Prepared structure for future code signing.</li>\n',
        '        </ul>\n',
        '        """\n'
    ]
    lines[start_idx:end_idx] = new_content
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    print('Successfully updated settings.py')
else:
    print('Could not find start/end markers')
    # fallback search for 2.5.1.2
    start_fallback = -1
    for i, line in enumerate(lines):
        if '# Release Notes v2.5.1.2 mapped content' in line:
            start_fallback = i
            break
    if start_fallback != -1:
         print('Already updated?')
