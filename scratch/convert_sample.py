import json
import os
import re

# 1. Load the best placement data from the training results
json_path = "/home/pramudyanuar/ta/tugas-akhir/result/buffered3/logs/training/best/best_placement_data.json"
with open(json_path, "r") as f:
    data = json.load(f)

placed_items = data["placed_items"]
print(f"Found {len(placed_items)} items in best placement data.")

# 2. Scale factors for standard 20GP container (5900 x 2350 x 2390 mm) to grid (60 x 24 x 26)
scale_x = 5900 / 60
scale_y = 2350 / 24
scale_z = 2390 / 26

sample_items = []
for idx, it in enumerate(placed_items[:40]): # Limit to first 40 items for a clean demo
    l_mm = int(round(it["l"] * scale_x))
    w_mm = int(round(it["w"] * scale_y))
    h_mm = int(round(it["h"] * scale_z))
    
    # Map stacking string to boolean
    stackable = it.get("stacking") == "stackable"
    
    sample_items.append({
        "name": f"Item {idx+1} ({it['l']}x{it['w']}x{it['h']})",
        "type": "Box",
        "length": l_mm,
        "width": w_mm,
        "height": h_mm,
        "weight": float(it.get("weight", 10.0)),
        "qty": 1,
        "color_idx": idx % 12,
        "stackable": stackable
    })

# 3. Format as python code string
sample_items_code = "SAMPLE_ITEMS = [\n"
for it in sample_items:
    sample_items_code += f"    {repr(it)},\n"
sample_items_code += "]"

# 4. Replace SAMPLE_ITEMS in app_3dbpp_dash.py
dash_app_path = "/home/pramudyanuar/ta/tugas-akhir-view/app_3dbpp_dash.py"
with open(dash_app_path, "r") as f:
    content = f.read()

# Find and replace SAMPLE_ITEMS = [...]
pattern = r"SAMPLE_ITEMS = \[[^\]]*\]"
new_content = re.sub(pattern, sample_items_code, content)

with open(dash_app_path, "w") as f:
    f.write(new_content)

print("Successfully updated SAMPLE_ITEMS in app_3dbpp_dash.py with scaled training items!")
