with open(r'C:\Users\USER\Desktop\3\suzannegit\site.html', encoding='utf-8') as f:
    content = f.read()

idx = content.find('const EMBEDDED_PROJECTS = [')
if idx >= 0:
    bracket_count = 0
    in_string = False
    escape = False
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
            if c == '[':
                bracket_count += 1
            elif c == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    print(f'End at position: {i}')
                    print(f'Context: {content[i-20:i+50]}')
                    break