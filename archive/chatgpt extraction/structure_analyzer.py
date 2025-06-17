import re

def analyze_role_structure(html_file):
    """Analyze how roles are encoded in the ChatGPT share link"""
    
    with open(html_file, 'r') as f:
        content = f.read()
    
    # Extract streamController data
    stream_pattern = r'streamController\.enqueue\("(.*?)"\);'
    stream_match = re.search(stream_pattern, content, re.DOTALL)
    
    if not stream_match:
        print("No stream data found")
        return
    
    data = stream_match.group(1)
    # Basic decode
    data = data.replace('\\"', '"').replace('\\n', '\n')
    
    print("=== ANALYZING ROLE ENCODING STRUCTURE ===\n")
    
    # Find the known messages and their surrounding structure
    user_msg = "Every has thought a lot"
    assistant_msg = "Let's Stress-Test the Core Idea"
    
    # Find user message position
    user_pos = data.find(user_msg)
    if user_pos > 0:
        print("USER MESSAGE FOUND")
        print("-" * 50)
        
        # Get 500 chars before and after
        start = max(0, user_pos - 500)
        end = min(len(data), user_pos + 200)
        context = data[start:end]
        
        # Highlight the message
        context = context.replace(user_msg, f">>>>{user_msg}<<<<")
        print(context)
        
        # Look for author structures before this message
        author_before = data[max(0, user_pos - 1000):user_pos]
        author_matches = re.findall(r'"author":\{([^}]+)\}', author_before)
        if author_matches:
            print("\nAuthor structures found before user message:")
            for match in author_matches[-3:]:  # Last 3
                print(f"  {match}")
        
        # Look for role indicators
        role_matches = re.findall(r'"role":"([^"]+)"', author_before)
        if role_matches:
            print("\nRole indicators found:")
            for role in role_matches[-3:]:
                print(f"  role: {role}")
    
    print("\n" + "="*70 + "\n")
    
    # Find assistant message position
    assist_pos = data.find(assistant_msg)
    if assist_pos > 0:
        print("ASSISTANT MESSAGE FOUND")
        print("-" * 50)
        
        # Get context
        start = max(0, assist_pos - 500)
        end = min(len(data), assist_pos + 200)
        context = data[start:end]
        
        # Highlight the message
        context = context.replace(assistant_msg, f">>>>{assistant_msg}<<<<")
        print(context)
        
        # Look for author structures
        author_before = data[max(0, assist_pos - 1000):assist_pos]
        author_matches = re.findall(r'"author":\{([^}]+)\}', author_before)
        if author_matches:
            print("\nAuthor structures found before assistant message:")
            for match in author_matches[-3:]:
                print(f"  {match}")
    
    print("\n=== LOOKING FOR ROLE PATTERNS ===\n")
    
    # Find all unique author structures
    all_authors = re.findall(r'"author":\{([^}]+)\}', data)
    unique_authors = list(set(all_authors))
    
    print(f"Found {len(unique_authors)} unique author structures:")
    for i, author in enumerate(unique_authors[:10]):  # First 10
        print(f"{i+1}. {author}")
    
    # Look for patterns that distinguish user vs assistant
    print("\n=== ANALYZING AUTHOR ID PATTERNS ===\n")
    
    # Extract the ID values from author structures
    # Pattern: "_2210":value or "_2210":"value"
    for author in unique_authors[:5]:
        print(f"\nAuthor: {author}")
        # Extract all key-value pairs
        kv_pattern = r'"_(\d+)":([^,}]+)'
        kv_matches = re.findall(kv_pattern, author)
        for key, value in kv_matches:
            print(f"  _{key} = {value}")
    
    # Look for specific numeric patterns
    print("\n=== NUMERIC PATTERNS IN DATA ===\n")
    
    # The number 18 often appears for user, 2280 for assistant
    if "18" in data and "2280" in data:
        print("Found potential role indicators: 18 (user?) and 2280 (assistant?)")
        
        # Check context around these numbers
        patterns = ["18", "2280"]
        for pattern in patterns:
            occurrences = [m.start() for m in re.finditer(pattern, data)]
            print(f"\nPattern '{pattern}' appears {len(occurrences)} times")
            
            # Show first few contexts
            for i, pos in enumerate(occurrences[:3]):
                context = data[max(0, pos-30):min(len(data), pos+30)]
                print(f"  Context {i+1}: ...{context}...")


if __name__ == "__main__":
    analyze_role_structure('chatgpt_response.html')