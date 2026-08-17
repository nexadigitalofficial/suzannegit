import json
from pathlib import Path

def main():
    base_dir = Path(r"C:\Users\USER\Desktop\3")
    projects_map_path = base_dir / "projects_map.json"
    portfolio_path = base_dir / "nexa_portfolio_data.json"

    with open(projects_map_path, "r", encoding="utf-8") as f:
        projects_map = json.load(f)
    
    with open(portfolio_path, "r", encoding="utf-8") as f:
        portfolio = json.load(f)

    # Convert projects_map to dictionary for easy lookup by title
    canonical_map = {}
    for p in projects_map:
        canonical_map[p["title"]] = p

    changes = 0
    
    for item in portfolio:
        if item.get("type") == "project":
            title = item.get("title")
            canonical = canonical_map.get(title)
            if canonical:
                changed = False
                
                # Check price_display
                if item.get("price_display") != canonical.get("price_display") or not item.get("price_display"):
                    print(f"Fixing {title.encode('ascii', 'ignore').decode()}: price_display")
                    item["price_display"] = canonical.get("price_display")
                    changed = True
                
                # Check price_numeric
                if canonical.get("price_numeric") is not None:
                    try:
                        c_val = int(canonical["price_numeric"])
                        if item.get("price_numeric") != c_val:
                            print(f"Fixing {title.encode('ascii', 'ignore').decode()}: price_numeric")
                            item["price_numeric"] = c_val
                            changed = True
                    except (ValueError, TypeError):
                        pass
                
                # Check down_payment
                if canonical.get("down_payment") is not None:
                    if item.get("down_payment") != canonical.get("down_payment"):
                        print(f"Fixing {title.encode('ascii', 'ignore').decode()}: down_payment")
                        item["down_payment"] = canonical.get("down_payment")
                        changed = True
                        
                if changed:
                    changes += 1

    with open(portfolio_path, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)
        
    print(f"Total projects fixed: {changes}")

if __name__ == "__main__":
    main()
