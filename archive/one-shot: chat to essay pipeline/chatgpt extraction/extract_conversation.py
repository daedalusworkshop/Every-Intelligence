import re
import json

# Read the file
with open('chatgpt_response.html', 'r') as f:
    content = f.read()

# Find the user's message
user_match = re.search(r'Every has thought a lot.*?I also attached a deep research on Every', content, re.DOTALL)
if user_match:
    user_msg = user_match.group(0).replace('\\\\n', '\n').replace('\\\\\"', '"')
    print('=== USER MESSAGE ===')
    print(user_msg)
    print()

# Find ChatGPT's response - looking for the structured response
response_pattern = r'Let.*?s Stress-Test the Core Idea.*?Next Moves.*?granularity'
response_match = re.search(response_pattern, content, re.DOTALL)
if response_match:
    response = response_match.group(0).replace('\\\\n', '\n').replace('\\\\\"', '"')
    print('=== CHATGPT RESPONSE (First 2000 chars) ===')
    print(response[:2000] + '...')
    print()
    print('=== FULL RESPONSE LENGTH ===')
    print(f"Total response length: {len(response)} characters")

# Try to find any other conversation content
print('\n=== SEARCHING FOR OTHER PATTERNS ===')
# Look for other structured content patterns
patterns = [
    r'Problem to Beat.*?Discovery.*?archive',
    r'Interaction Model Variants.*?Variant.*?What the User Sees',
    r'System Architecture.*?User Speech/Text.*?Front-end'
]

for i, pattern in enumerate(patterns):
    match = re.search(pattern, content, re.DOTALL)
    if match:
        print(f"Pattern {i+1} found: {match.group(0)[:200]}...") 