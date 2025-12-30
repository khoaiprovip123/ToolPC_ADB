"""
Script để reorganize soc_database.json theo hãng
"""
import json
from collections import OrderedDict

# Đọc database hiện tại
with open('src/data/soc_database.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Phân loại devices theo hãng dựa trên codename patterns
xiaomi_devices = {}
samsung_devices = {}
oneplus_devices = {}
oppo_devices = {}
vivo_devices = {}
realme_devices = {}
google_devices = {}

for codename, device_name in data['devices'].items():
    # Samsung: o1s, p2s, p3s, b0s, r0s, g0s, b0q, dm*, e*, q*, bloomq, a*x, m*x
    if (codename.startswith(('o1s', 'p2s', 'p3s', 'b0s', 'r0s', 'g0s', 'b0q', 'dm', 'e', 'q', 'bloomq', 'b4q', 'b5', 'b6')) or 
        codename.endswith('x') and any(codename.startswith(p) for p in ['a3', 'a5', 'm3', 'm5'])):
        samsung_devices[codename] = device_name
    # OnePlus: OP*, CPH* (một số), PGZ*
    elif codename.startswith('OP') or codename.startswith('PGZ'):
        oneplus_devices[codename] = device_name
    elif codename.startswith('CPH') and device_name.startswith('OnePlus'):
        oneplus_devices[codename] = device_name
    # OPPO: PE*, PG*, CPH* (OPPO branded)
    elif codename.startswith(('PEUM', 'PGEM', 'PGJM')) or (codename.startswith('CPH') and device_name.startswith('OPPO')):
        oppo_devices[codename] = device_name
    # vivo: V2*
    elif codename.startswith('V2'):
        vivo_devices[codename] = device_name
    # Realme: RMX*
    elif codename.startswith('RMX'):
        realme_devices[codename] = device_name
    # Google: G*, gs*, zuma, slider, whitechapel
    elif (codename.startswith('G') and len(codename) <= 6 and not codename.startswith('GP')) or \
         codename.startswith('gs') or codename in ['zuma', 'slider', 'whitechapel']:
        google_devices[codename] = device_name
    # Xiaomi & POCO: còn lại
    else:
        xiaomi_devices[codename] = device_name

# Tạo devices dict mới với thứ tự: Xiaomi → Samsung → OnePlus → OPPO → vivo → Realme → Google
ordered_devices = OrderedDict()

# 1. Xiaomi & POCO
ordered_devices.update(sorted(xiaomi_devices.items()))

# 2. Samsung  
ordered_devices.update(sorted(samsung_devices.items()))

# 3. OnePlus
ordered_devices.update(sorted(oneplus_devices.items()))

# 4. OPPO
ordered_devices.update(sorted(oppo_devices.items()))

# 5. vivo
ordered_devices.update(sorted(vivo_devices.items()))

# 6. Realme
ordered_devices.update(sorted(realme_devices.items()))

# 7. Google Pixel
ordered_devices.update(sorted(google_devices.items()))

# Cập nhật data với devices đã sắp xếp
data['devices'] = ordered_devices

# Ghi lại file với format đẹp
with open('src/data/soc_database.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

# In thống kê
print(f"✅ Đã reorganize database:")
print(f"  📱 Xiaomi & POCO: {len(xiaomi_devices)} devices")
print(f"  📱 Samsung: {len(samsung_devices)} devices")
print(f"  📱 OnePlus: {len(oneplus_devices)} devices")
print(f"  📱 OPPO: {len(oppo_devices)} devices")
print(f"  📱 vivo: {len(vivo_devices)} devices")
print(f"  📱 Realme: {len(realme_devices)} devices")
print(f"  📱 Google Pixel: {len(google_devices)} devices")
print(f"  📊 Total: {len(ordered_devices)} devices")
