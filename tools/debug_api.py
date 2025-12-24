import requests
import json
import yaml

URLS = [
    "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-downloads/master/stable/stable.json",
    "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/data/stable_recovery/stable_recovery.yml",
    "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/miui-updates-tracker/master/data/stable_recovery.yml",
    "https://raw.githubusercontent.com/XiaomiFirmwareUpdater/data/master/data.json"
]

target = "lisa"

for url in URLS:
    print(f"Checking {url}...")
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            print(f"SUCCESS: {len(r.content)} bytes")
            if url.endswith(".json"):
                data = r.json()
            elif url.endswith(".yml"):
                data = yaml.safe_load(r.content)
            else:
                data = []
                
            # Search for lisa
            found = False
            if isinstance(data, list):
                for item in data:
                    if item.get("codename") == target:
                        print(f"FOUND {target} in {url}")
                        print(item)
                        found = True
                        break
            elif isinstance(data, dict):
                 # Try to find in dict keys or values
                 pass

            if not found:
                print(f"NOT FOUND {target} in {url}")
        else:
            print(f"FAILED: {r.status_code}")
    except Exception as e:
        print(f"ERROR: {e}")
