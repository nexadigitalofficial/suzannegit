import re
with open(r'C:\Users\USER\Desktop\3\suzannegit\site.html', encoding='utf-8') as f:
    content = f.read()
# Find all listing_type values
types = re.findall(r'\"listing_type\":\s*\"([^\"]+)\"', content)
unique_types = list(set(types))
print('Unique listing_type values:')
for t in unique_types:
    print('  - \"' + t + '\"')
print('Total:', len(unique_types))