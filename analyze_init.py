with open(r'C:\Users\USER\Desktop\3\suzannegit\site.html', encoding='utf-8') as f:
    content = f.read()

# 1. Find forceInitializeAll function
idx = content.find('function forceInitializeAll')
if idx >= 0:
    # Get the function body
    bracket_count = 0
    in_string = False
    escape = False
    start = idx
    for i in range(idx, len(content)):
        c = content[i]
        if escape:
            escape = False
            continue
        if c == '\\':
            escape = True
            continue
        if c == '"' and not escape:
            in_string = not in_string
            continue
        if not in_string:
            if c == '[': bracket_count += 1
            elif c == ']': bracket_count -= 1
            elif c == '{': bracket_count += 1
            elif c == '}': bracket_count -= 1
            if bracket_count == 0 and c == '{':
                # Found the opening brace of the function
                # Now find the closing brace
                inner_count = 1
                j = i + 1
                while j < len(content) and inner_count > 0:
                    c2 = content[j]
                    if escape:
                        escape = False
                        j += 1
                        continue
                    if c2 == '\\':
                        escape = True
                        j += 1
                        continue
                    if c2 == '"' and not escape:
                        in_string = not in_string
                        j += 1
                        continue
                    if not in_string:
                        if c2 == '{': inner_count += 1
                        elif c2 == '}': inner_count -= 1
                    j += 1
                func_body = content[i:j]
                
                print("=" * 60)
                print("forceInitializeAll function body:")
                print("=" * 60)
                print(func_body[:3000])
                print("..." if len(func_body) > 3000 else "")
                
                # Check for renderProjectsCarousel call
                if 'renderProjectsCarousel' in func_body:
                    print("\n\n✅ renderProjectsCarousel is called inside forceInitializeAll")
                else:
                    print("\n\n❌ renderProjectsCarousel is NOT called inside forceInitializeAll")
                
                # Check for renderPortfolioCarousel call
                if 'renderPortfolioCarousel' in func_body:
                    print("✅ renderPortfolioCarousel is called inside forceInitializeAll")
                else:
                    print("❌ renderPortfolioCarousel is NOT called inside forceInitializeAll")
                
                # Check for EMBEDDED_PROJECTS usage
                if 'EMBEDDED_PROJECTS' in func_body:
                    print("✅ EMBEDDED_PROJECTS referenced inside forceInitializeAll")
                else:
                    print("❌ EMBEDDED_PROJECTS NOT referenced inside forceInitializeAll")
                
                # Check for EMBEDDED_LISTINGS usage
                if 'EMBEDDED_LISTINGS' in func_body:
                    print("✅ EMBEDDED_LISTINGS referenced inside forceInitializeAll")
                else:
                    print("❌ EMBEDDED_LISTINGS NOT referenced inside forceInitializeAll")
                
                # Check for projectsData initialization
                if 'projectsData' in func_body:
                    # Find the line
                    for line in func_body.split('\n'):
                        if 'projectsData' in line:
                            print(f"\nprojectsData line: {line.strip()[:100]}")
                
                # Check for portfolioData initialization
                if 'portfolioData' in func_body:
                    for line in func_body.split('\n'):
                        if 'portfolioData' in line:
                            print(f"portfolioData line: {line.strip()[:100]}")
                
                break