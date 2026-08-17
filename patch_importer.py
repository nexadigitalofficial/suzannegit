import re

file_path = r"C:\Users\USER\Desktop\3\nexa_data_importer.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

target = """            if not info:
                continue
            item["price_display"] = info["price_display"] or ""
            item["room_info"] = ", ".join(info["rooms"]) if info["rooms"] else ""
            if info.get("description"):
                item["description"] = info["description"]
            updated += 1"""

replacement = """            if not info:
                continue
            
            if info.get("price_display"):
                item["price_display"] = info["price_display"]
            if info.get("price_numeric") is not None and str(info.get("price_numeric")).strip() != "":
                item["price_numeric"] = info["price_numeric"]
            if info.get("price_min") is not None and str(info.get("price_min")).strip() != "":
                item["price_min"] = info["price_min"]
            if info.get("price_max") is not None and str(info.get("price_max")).strip() != "":
                item["price_max"] = info["price_max"]
                
            item["room_info"] = ", ".join(info["rooms"]) if info["rooms"] else ""
            if info.get("description"):
                item["description"] = info["description"]
            updated += 1"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched nexa_data_importer.py successfully.")
else:
    print("Could not find target content in nexa_data_importer.py.")
