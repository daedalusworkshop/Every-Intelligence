import re

# Read the file
with open('chatgpt_response.html', 'r') as f:
    content = f.read()

# Look for the main response content by finding the structured text
# The response appears to be embedded in the HTML, let's extract it more carefully

# Find content that contains "Let's Stress-Test the Core Idea"
start_marker = "Let's Stress-Test the Core Idea"
end_marker = "granularity.*?\""

# Search for the full response
match = re.search(rf'{start_marker}.*?{end_marker}', content, re.DOTALL)
if match:
    full_response = match.group(0)
    # Clean up the response
    full_response = full_response.replace('\\\\n', '\n').replace('\\\\\"', '"').replace('\\"', '"')
    full_response = full_response.replace('\\n', '\n')
    
    print("=== FULL CHATGPT RESPONSE ===")
    print(full_response)
else:
    print("Could not find the full response")
    
    # Let's try a different approach - look for any text containing the key sections
    sections = [
        "Problem to Beat",
        "Interaction Model Variants", 
        "System Architecture",
        "Product–Strategy Fit",
        "Roadmap Skeleton",
        "Open Questions"
    ]
    
    for section in sections:
        pattern = rf'{section}.*?(?=###|\Z)'
        match = re.search(pattern, content, re.DOTALL)
        if match:
            section_text = match.group(0).replace('\\\\n', '\n').replace('\\\\\"', '"')
            print(f"\n=== {section.upper()} ===")
            print(section_text[:500] + "..." if len(section_text) > 500 else section_text) 