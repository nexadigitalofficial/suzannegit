import json, re

with open(r'C:\Users\USER\Desktop\3\suzannegit\site.html', encoding='utf-8') as f:
    content = f.read()

match = re.search(r'const EMBEDDED_PROJECTS = (\[.*?\]);', content, re.DOTALL)
if match:
    data = json.loads(match.group(1))
    print(f'EMBEDDED_PROJECTS length: {len(data)}')
    for i, p in enumerate(data[:3]):
        print(f'  {i}: id={p.get("id")} title={p.get("title")} name={p.get("name")}')
else:
    print('NOT FOUND')