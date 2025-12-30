"""
Script để thêm các thiết bị Xiaomi 2021-2024 vào database
"""
import json
from collections import OrderedDict

# Đọc database hiện tại
with open('src/data/soc_database.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Danh sách thiết bị Xiaomi/Redmi/POCO mới cần thêm
new_devices = {
    # Xiaomi 12 Series
    "cupid": "Xiaomi 12",
    "zeus": "Xiaomi 12 Pro", 
    "thor": "Xiaomi 12X",
    "psyche": "Xiaomi 12 Lite",
    "mayfly": "Xiaomi 12S",
    "unicorn": "Xiaomi 12S Pro",
    "diting": "Xiaomi 12S Ultra",
    "plato": "Xiaomi 12T Pro",
    
    # Xiaomi 13 Series
    "ziyi": "Xiaomi 13 Lite",
    "aristotle": "Xiaomi 13T",
    "corot": "Xiaomi 13T Pro",
    "babylon": "Xiaomi 13 Lite 5G",
    
    # Xiaomi 14 Series (thêm variants)
    "aurora": "Xiaomi 14 Ultra",
    
    # Xiaomi 15 Series
    "dada": "Xiaomi 15",
    "haotian": "Xiaomi 15 Pro",
    "xuanyuan": "Xiaomi 15 Ultra",
    
    # Redmi K Series
    "renoir": "Redmi K40 Gaming",
    "picasso": "Redmi K30 5G Racing",
    "phoenix": "Redmi K30",
    "lancelot": "Redmi K30 Ultra",
    
    # Redmi Note 10 Series
    "mojito": "Redmi Note 10",
    "rosemary": "Redmi Note 10S",
    "secret": "Redmi Note 10S (India)",
    "camellia": "Redmi Note 10 5G",
    "camellian": "Redmi Note 10 5G (China)",
    
    # Redmi Note 11 Series
    "evergo": "Redmi Note 11",
    "spes": "Redmi Note 11 4G",
    "spesn": "Redmi Note 11 NFC",
    "selenes": "Redmi Note 11 4G",
    "pissarro": "Redmi Note 11 Pro 4G",
    "viva": "Redmi Note 11 Pro 4G (Global)",
    "veux": "Redmi Note 11 Pro 5G",
    
    # Redmi Note 12 Series
    "tapas": "Redmi Note 12",
    "sunstone": "Redmi Note 12 5G",
    "topaz": "Redmi Note 12 4G",
    
    # Redmi Note 13 Series
    "sapphire": "Redmi Note 13 4G",
    "sapphiren": "Redmi Note 13 NFC",
    "gold": "Redmi Note 13 5G",
    
    # Redmi Note 14 Series
    "tanzanite": "Redmi Note 14 4G",
    "beryl": "Redmi Note 14 5G",
    "obsidian": "Redmi Note 14 Pro 4G",
    "malachite": "Redmi Note 14 Pro 5G",
    "amethyst": "Redmi Note 14 Pro+ 5G",
    "emerald": "Redmi Note 14S",
    
    # Redmi Series
    "stone": "Redmi 10",
    "selene": "Redmi 10 / Redmi 10 2022",
    "atom": "Redmi 10C",
    "fog": "Redmi 10",
    "citrus": "Redmi 9T",
    
    # POCO F Series (bổ sung)
    "ingres": "POCO F4 GT",
    
    # POCO X Series
    "surya": "POCO X3 / X3 NFC",
    "karna": "POCO X3 (India)",
    "vayu": "POCO X3 Pro (Global)",
    "veux": "POCO X4 Pro 5G",
    "xaga": "POCO X4 GT",
    "moonstone": "POCO X5 5G",
    "moonstone_p": "POCO X5 Pro 5G",
    "peridot": "POCO X6 Pro",
    
    # POCO M Series
    "light": "POCO M4 5G",
    "fleur": "POCO M4 Pro",
    "biloba": "POCO M5",
    "ivy": "POCO M5s",
    
    # POCO C Series
    "lightning": "POCO C50",
    "air": "POCO C55",
    
    # Xiaomi Pad
    "ares": "Xiaomi Pad 5 Pro",
    "moisens": "Xiaomi Pad 5 Pro 5G",
    "amber": "Xiaomi Pad 5",
}

# Chip mappings cho các device mới
new_mappings = {
    # Xiaomi 12 Series
    "cupid": "Snapdragon 8 Gen 1",
    "zeus": "Snapdragon 8 Gen 1",
    "thor": "Snapdragon 870",
    "psyche": "Snapdragon 778G",
    "mayfly": "Snapdragon 8+ Gen 1",
    "unicorn": "Snapdragon 8+ Gen 1",
    "diting": "Snapdragon 8+ Gen 1",
    "plato": "Dimensity 8100",
    
    # Xiaomi 13 Series
    "ziyi": "Snapdragon 7 Gen 1",
    "aristotle": "Dimensity 8200",
    "corot": "Dimensity 9200+",
    "babylon": "Snapdragon 7 Gen 1",
    
    # Xiaomi 14 Series
    "aurora": "Snapdragon 8 Gen 3",
    
    # Xiaomi 15 Series
    "dada": "Snapdragon 8 Elite",
    "haotian": "Snapdragon 8 Elite",
    "xuanyuan": "Snapdragon 8 Elite",
    
    # Redmi K Series
    "renoir": "Dimensity 1200",
    "picasso": "Snapdragon 765G",
    "phoenix": "Snapdragon 730G",
    "lancelot": "Dimensity 1000+",
    
    # Redmi Note 10 Series
    "mojito": "Snapdragon 678",
    "rosemary": "Helio G95",
    "secret": "Helio G95",
    "camellia": "Dimensity 700",
    "camellian": "Dimensity 700",
    
    # Redmi Note 11 Series
    "evergo": "Snapdragon 680",
    "spes": "Snapdragon 680",
    "spesn": "Snapdragon 680",  
    "selenes": "Helio G88",
    "pissarro": "Helio G96",
    "viva": "Helio G96",
    "veux": "Dimensity 920",
    
    # Redmi Note 12 Series
    "tapas": "Snapdragon 4 Gen 1",
    "sunstone": "Snapdragon 4 Gen 1",
    "topaz": "Snapdragon 685",
    
    # Redmi Note 13 Series
    "sapphire": "Snapdragon 685",
    "sapphiren": "Snapdragon 685",
    "gold": "Dimensity 6080",
    
    # Redmi Note 14 Series
    "tanzanite": "Helio G99-Ultra",
    "beryl": "Dimensity 7025",
    "obsidian": "Helio G100",
    "malachite": "Dimensity 7300",
    "amethyst": "Snapdragon 7s Gen 3",
    "emerald": "Helio G100",
    
    # Redmi Series
    "stone": "Helio G88",
    "selene": "Helio G88",
    "atom": "Snapdragon 680",
    "fog": "Snapdragon 680",
    "citrus": "Snapdragon 662",
    
    # POCO X Series
    "surya": "Snapdragon 732G",
    "karna": "Snapdragon 732G",
    "veux": "Dimensity 920",
    "moonstone": "Snapdragon 695",
    "moonstone_p": "Snapdragon 778G",
    "peridot": "Snapdragon 8s Gen 3",
    
    # POCO M Series
    "light": "Dimensity 700",
    "fleur": "Helio G96",
    "ivy": "Helio G99",
    
    # POCO C Series
    "lightning": "Helio A22",
    "air": "Helio G85",
    
    # Xiaomi Pad
    "ares": "Snapdragon 870",
    "moisens": "Snapdragon 870",
}

# Thêm vào database
data['mappings'].update(new_mappings)
data['devices'].update(new_devices)

# Sắp xếp lại devices để giữ Xiaomi ở đầu
xiaomi_devices = {k: v for k, v in data['devices'].items() 
                  if not any(x in k for x in ['OP','CPH','PE','PG','V2','RMX','G']) and 
                  not any(k.startswith(p) for p in ['o1s','p2s','p3s','b0','r0s','g0s','dm','e','q','a3','a5','m3','m5'])}
other_devices = {k: v for k, v in data['devices'].items() if k not in xiaomi_devices}

# Reorganize: Xiaomi first, then sorted
ordered_devices = OrderedDict(sorted(xiaomi_devices.items()))
ordered_devices.update(sorted(other_devices.items()))
data['devices'] = ordered_devices

# Ghi lại file
with open('src/data/soc_database.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f"✅ Đã thêm {len(new_devices)} thiết bị Xiaomi/Redmi/POCO mới!")
print(f"📊 Tổng database:")
print(f"  - Mappings: {len(data['mappings'])}")
print(f"  - Devices: {len(data['devices'])}")
