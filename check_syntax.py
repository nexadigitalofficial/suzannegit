with open(r'C:\Users\USER\Desktop\3\suzannegit\site.html', encoding='utf-8') as f:
    content = f.read()

# Quick check for obvious issues
open_braces = content.count('{')
close_braces = content.count('}')
print(f'Braces: {open_braces} open, {close_braces} close - Difference: {open_braces - close_braces}')

open_parens = content.count('(')
close_parens = content.count(')')
print(f'Parens: {open_parens} open, {close_parens} close - Difference: {open_parens - close_parens}')

open_brackets = content.count('[')
close_brackets = content.count(']')
print(f'Brackets: {open_brackets} open, {close_brackets} close - Difference: {open_brackets - close_brackets}')

# Check for unclosed template literals
import re
template_lits = len(re.findall(r'`', content))
print(f'Template literals: {template_lits} (even number is good)')

# Check for unmatched quotes
single_quotes = content.count("'")
double_quotes = content.count('"')
print(f"Single quotes: {single_quotes}, Double quotes: {double_quotes}")

# Check for unmatched template literals by counting backticks per line
lines = content.split('\n')
unclosed_templates = 0
for line in lines:
    diff = line.count('`')  # each backtick toggles state
    unclosed_templates += diff
# If odd number, something is wrong
print(f"Template literal parity: {'OK' if unclosed_templates % 2 == 0 else 'PROBLEM'}")

# Check for common JS error patterns
# Find lines with opening brace but no matching closing
brace_depth = 0
problem_lines = []
for i, line in enumerate(lines, 1):
    for char in line:
        if char == '{':
            brace_depth += 1
        elif char == '}':
            brace_depth -= 1
            if brace_depth < 0:
                problem_lines.append(f"Line {i}: extra closing brace")
                brace_depth = 0  # reset to continue checking
if brace_depth != 0:
    print(f"Unclosed braces remaining: {brace_depth}")
elif problem_lines:
    print(f"Problem lines: {problem_lines[:5]}")
else:
    print("Brace depth is balanced")

# Check for isChatOpen declaration count
isChatOpen_count = content.count("let isChatOpen")
print(f"\n'isChatOpen' declarations: {isChatOpen_count} (should be 1)")

# Check for unresolved promises or event handlers
unclosed_events = len(re.findall(r'addEventListener', content))
closed_events = len(re.findall(r'removeEventListener', content))
print(f"addEventListener: {unclosed_events}, removeEventListener: {closed_events}")

print("\n--- Summary ---")
print("If differences are non-zero, there may be syntax issues.")
print("isChatOpen count of 1 is correct after our fix.")