import re
from chatgpt_share_parser import ChatGPTShareParser

# Debug version with more output
class DebugChatGPTShareParser(ChatGPTShareParser):
    def _extract_messages(self):
        """Extract all messages with their roles - debug version."""
        print("\n=== DEBUG: Message Extraction ===")
        
        # Find all message content blocks: [id],"content"
        content_pattern = r'\[(\d+)\],"([^"]+(?:\\.[^"]+)*)"'
        content_matches = re.findall(content_pattern, self.decoded_data)
        
        print(f"Found {len(content_matches)} content blocks")
        
        # Build content map
        content_map = {}
        for msg_id, content in content_matches:
            # Clean content
            content = self._clean_content(content)
            # Show all content blocks for debugging
            print(f"\nContent ID {msg_id}: {content[:100]}...")
            if len(content) > 20 and not content.startswith("Original custom"):
                content_map[msg_id] = content
        
        print(f"\nFiltered to {len(content_map)} valid content blocks")
        
        # Find message structures with timestamps
        message_pattern = r'(\d+\.\d+),\{"[^}]+"\},\[(\d+)\]'
        message_matches = re.findall(message_pattern, self.decoded_data)
        
        print(f"\nFound {len(message_matches)} message structures")
        
        for timestamp, content_id in message_matches[:5]:  # First 5 for debugging
            print(f"\nMessage structure: timestamp={timestamp}, content_id={content_id}")
            
            if content_id not in content_map:
                print(f"  Content ID {content_id} not in content map")
                continue
                
            # Find the role for this message
            content_pos = self.decoded_data.find(f'[{content_id}]')
            if content_pos > 0:
                # Extract context before this message
                context = self.decoded_data[max(0, content_pos - 500):content_pos]
                
                # Show role determination context
                role_pattern = r'"_2210":(\d+)'
                role_match = re.search(role_pattern, context)
                
                if role_match:
                    role_id = role_match.group(1)
                    print(f"  Found _2210:{role_id}")
                    
                    if role_id == self.USER_ROLE_ID:
                        print(f"  Role: USER")
                    elif role_id == self.ASSISTANT_ROLE_ID:
                        print(f"  Role: ASSISTANT")
                    else:
                        print(f"  Role: Unknown (ID: {role_id})")
                else:
                    print(f"  No _2210 field found in context")
                
                # Show the actual context for manual inspection
                print(f"  Context snippet: ...{context[-100:]}...")
                
                role = self._determine_role(context)
                print(f"  Final determined role: {role}")
                
                if role not in ['user', 'assistant']:
                    print(f"  Skipping - invalid role")
                    continue
                
                self.messages.append({
                    'role': role,
                    'content': content_map[content_id],
                    'timestamp': float(timestamp)
                })
                print(f"  Added message!")
        
        # Sort messages by timestamp
        self.messages.sort(key=lambda x: x['timestamp'])
        print(f"\nTotal messages extracted: {len(self.messages)}")


# Test with debug parser
if __name__ == "__main__":
    with open('chatgpt_response.html', 'r') as f:
        html_content = f.read()
    
    parser = DebugChatGPTShareParser()
    conversation = parser.parse_html(html_content)
    
    print(f"\n\nFinal result: {len(conversation['messages'])} messages")
    
    # Also try a simpler extraction
    print("\n\n=== SIMPLE EXTRACTION TEST ===")
    
    # Extract streamController data
    stream_pattern = r'streamController\.enqueue\("(.*?)"\);'
    stream_match = re.search(stream_pattern, html_content, re.DOTALL)
    
    if stream_match:
        data = stream_match.group(1)
        # Basic decode
        data = data.replace('\\"', '"').replace('\\n', '\n')
        
        # Look for the specific messages we know exist
        if "Every has thought a lot" in data:
            print("Found user message!")
            
        if "Let's Stress-Test" in data:
            print("Found assistant message!")
            
        # Try a different pattern for messages
        # Look for patterns like: ,"content text here"
        simple_pattern = r',"([^"]{50,})"'  # Messages longer than 50 chars
        simple_matches = re.findall(simple_pattern, data)
        
        print(f"\nFound {len(simple_matches)} potential messages with simple pattern")
        
        for i, msg in enumerate(simple_matches[:5]):
            print(f"\nMessage {i+1}: {msg[:100]}...")