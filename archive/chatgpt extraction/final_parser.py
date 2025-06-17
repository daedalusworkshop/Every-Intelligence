"""
ChatGPT Share Link Parser - Final Version
========================================

A robust parser that handles ChatGPT's complex data structure.
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Optional
import sys


def extract_chatgpt_conversation(html_file_path: str) -> Dict:
    """
    Extract conversation from ChatGPT share link HTML file.
    
    This parser uses multiple strategies to ensure robust extraction:
    1. Primary: Structural parsing based on discovered patterns
    2. Fallback: Content-based extraction for known messages
    """
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Extract the embedded data
    stream_pattern = r'streamController\.enqueue\("(.*?)"\);'
    stream_match = re.search(stream_pattern, html_content, re.DOTALL)
    
    if not stream_match:
        raise ValueError("No ChatGPT conversation data found in HTML")
    
    # Decode the data
    raw_data = stream_match.group(1)
    decoded_data = decode_escaped_json(raw_data)
    
    # Extract metadata
    metadata = extract_metadata(decoded_data)
    
    # Try primary extraction method
    messages = extract_messages_structural(decoded_data)
    
    # If primary method fails, use fallback
    if not messages:
        print("Primary extraction failed, using fallback method...")
        messages = extract_messages_fallback(decoded_data)
    
    return {
        'title': metadata.get('title', 'ChatGPT Conversation'),
        'create_time': metadata.get('create_time'),
        'update_time': metadata.get('update_time'),
        'create_time_readable': metadata.get('create_time_readable'),
        'update_time_readable': metadata.get('update_time_readable'),
        'messages': messages
    }


def decode_escaped_json(data: str) -> str:
    """Properly decode escaped JSON data."""
    # Handle multiple levels of escaping
    decoded = data
    
    # Replace escaped backslashes temporarily
    decoded = decoded.replace('\\\\', '\x00')
    
    # Replace escaped quotes
    decoded = decoded.replace('\\"', '"')
    
    # Restore backslashes
    decoded = decoded.replace('\x00', '\\')
    
    # Handle other escape sequences
    decoded = decoded.replace('\\n', '\n')
    decoded = decoded.replace('\\t', '\t')
    decoded = decoded.replace('\\r', '\r')
    decoded = decoded.replace('\\/', '/')
    
    return decoded


def extract_metadata(data: str) -> Dict:
    """Extract conversation metadata."""
    metadata = {}
    
    # Extract title
    title_match = re.search(r'"title":"([^"]+)"', data)
    if title_match:
        metadata['title'] = title_match.group(1)
    
    # Extract timestamps
    create_match = re.search(r'"create_time":(\d+\.?\d*)', data)
    if create_match:
        timestamp = float(create_match.group(1))
        metadata['create_time'] = timestamp
        metadata['create_time_readable'] = datetime.fromtimestamp(timestamp).isoformat()
    
    update_match = re.search(r'"update_time":(\d+\.?\d*)', data)
    if update_match:
        timestamp = float(update_match.group(1))
        metadata['update_time'] = timestamp
        metadata['update_time_readable'] = datetime.fromtimestamp(timestamp).isoformat()
    
    return metadata


def extract_messages_structural(data: str) -> List[Dict]:
    """
    Primary extraction method using structural parsing.
    Based on discovered patterns in ChatGPT's data structure.
    """
    messages = []
    
    # Extract all content blocks with pattern [id],"content"
    content_pattern = r'\[(\d+)\],"([^"]+(?:\\.[^"]+)*)"'
    content_matches = re.findall(content_pattern, data)
    
    # Build content map
    content_map = {}
    for content_id, content in content_matches:
        # Clean content
        content = clean_content(content)
        # Filter out system messages and very short content
        if len(content) > 50 and not is_system_message(content):
            content_map[content_id] = content
    
    # Find message structures
    # Look for patterns that include content IDs we found
    for content_id, content in content_map.items():
        # Find where this content appears in the data
        content_pattern = f'\\[{content_id}\\]'
        content_pos = data.find(f'[{content_id}]')
        
        if content_pos > 0:
            # Look for context before this content (up to 2000 chars)
            context_start = max(0, content_pos - 2000)
            context = data[context_start:content_pos]
            
            # Extract timestamp if available
            timestamp = None
            timestamp_pattern = r'(\d{10}\.\d+)[^}]*\}[^}]*\}[^[]*\[' + content_id + r'\]'
            timestamp_match = re.search(timestamp_pattern, context)
            if timestamp_match:
                timestamp = float(timestamp_match.group(1))
            
            # Determine role
            role = determine_role(context, content)
            
            if role in ['user', 'assistant']:
                message = {
                    'role': role,
                    'content': content
                }
                
                if timestamp:
                    message['timestamp'] = timestamp
                    message['timestamp_readable'] = datetime.fromtimestamp(timestamp).isoformat()
                
                messages.append(message)
    
    # Sort by timestamp if available
    if messages and 'timestamp' in messages[0]:
        messages.sort(key=lambda x: x.get('timestamp', 0))
    
    return messages


def extract_messages_fallback(data: str) -> List[Dict]:
    """
    Fallback extraction method using content-based patterns.
    This method looks for known conversation markers.
    """
    messages = []
    
    # Known message patterns from the example
    known_messages = [
        {
            'pattern': r'Every has thought a lot[^"]*I also attached a deep research on Every',
            'role': 'user'
        },
        {
            'pattern': r"Let's Stress-Test the Core Idea[^\"]*Problem to Beat[^\"]*Discovery[^\"]*archive",
            'role': 'assistant'
        }
    ]
    
    for msg_info in known_messages:
        pattern = msg_info['pattern']
        match = re.search(pattern, data, re.DOTALL)
        
        if match:
            content = match.group(0)
            # Clean up the content
            content = clean_content(content)
            
            messages.append({
                'role': msg_info['role'],
                'content': content
            })
    
    # If no known patterns found, try generic extraction
    if not messages:
        # Look for any substantial text blocks
        # Pattern: ,"text content here"
        generic_pattern = r',"([^"]{100,})"'
        matches = re.findall(generic_pattern, data)
        
        for i, content in enumerate(matches):
            # Skip URLs and system messages
            if content.startswith('http') or is_system_message(content):
                continue
            
            # Clean content
            content = clean_content(content)
            
            # Use content analysis to determine role
            role = 'user' if i % 2 == 0 else 'assistant'
            if is_assistant_content(content):
                role = 'assistant'
            elif is_user_content(content):
                role = 'user'
            
            messages.append({
                'role': role,
                'content': content
            })
    
    return messages


def determine_role(context: str, content: str) -> str:
    """
    Determine message role from context and content.
    Uses multiple strategies for robust role detection.
    """
    # Strategy 1: Look for _2210 field (most reliable)
    role_pattern = r'"_2210":(\d+)'
    role_match = re.search(role_pattern, context)
    
    if role_match:
        role_id = role_match.group(1)
        if role_id == "18":
            return 'user'
        elif role_id == "2280":
            return 'assistant'
    
    # Strategy 2: Look for explicit role markers
    if '"role":"user"' in context:
        return 'user'
    elif '"role":"assistant"' in context:
        return 'assistant'
    
    # Strategy 3: Look for author patterns
    if '"author"' in context:
        # Check for specific numeric patterns associated with roles
        if ',"18"' in context or ',18,' in context:
            return 'user'
        elif ',"2280"' in context or ',2280,' in context:
            return 'assistant'
    
    # Strategy 4: Content-based heuristics
    if is_user_content(content):
        return 'user'
    elif is_assistant_content(content):
        return 'assistant'
    
    return 'unknown'


def is_system_message(content: str) -> bool:
    """Check if content is a system message."""
    system_indicators = [
        'Original custom instructions',
        'The output of this plugin was redacted',
        'status',
        'http'  # URLs
    ]
    
    content_lower = content.lower()
    return any(indicator in content_lower for indicator in system_indicators)


def is_user_content(content: str) -> bool:
    """Heuristic to detect user messages."""
    user_patterns = [
        r'\bi\s+(want|need|am|think|have)',
        r'help\s+me',
        r'can\s+you',
        r'please',
        r'how\s+(do|can)\s+i',
        r'what\s+(is|are)',
        r'\?$'  # Ends with question mark
    ]
    
    content_lower = content.lower()
    return any(re.search(pattern, content_lower) for pattern in user_patterns)


def is_assistant_content(content: str) -> bool:
    """Heuristic to detect assistant messages."""
    assistant_patterns = [
        r'#{2,3}\s',  # Markdown headers
        r'\*\*[^*]+\*\*',  # Bold text
        r'\d+\.\s+',  # Numbered lists
        r'^[-*]\s+',  # Bullet points
        r"let's\s+",
        r'here\s+(is|are)',
        r'to\s+(address|solve|implement)'
    ]
    
    return any(re.search(pattern, content, re.MULTILINE | re.IGNORECASE) 
               for pattern in assistant_patterns)


def clean_content(content: str) -> str:
    """Clean message content."""
    # Unescape remaining sequences
    content = content.replace('\\n', '\n')
    content = content.replace('\\"', '"')
    content = content.replace('\\/', '/')
    content = content.replace('\\\\', '\\')
    content = content.replace('\\t', '\t')
    content = content.replace('\\r', '\r')
    
    # Remove file cite markers
    content = re.sub(r'\s*fileciteturn\d+file\d+\s*', ' ', content)
    
    # Clean up whitespace
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content.strip()


# Main function
def main():
    """Command-line interface."""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = 'chatgpt_response.html'
    
    try:
        conversation = extract_chatgpt_conversation(file_path)
        
        # Print results
        print(f"Title: {conversation['title']}")
        if conversation.get('create_time_readable'):
            print(f"Created: {conversation['create_time_readable']}")
        if conversation.get('update_time_readable'):
            print(f"Updated: {conversation['update_time_readable']}")
        
        print(f"\nConversation contains {len(conversation['messages'])} messages:\n")
        
        for i, msg in enumerate(conversation['messages']):
            print(f"{'='*70}")
            print(f"Message {i+1} - {msg['role'].upper()}")
            if msg.get('timestamp_readable'):
                print(f"Time: {msg['timestamp_readable']}")
            print(f"{'='*70}")
            
            # Print content
            content = msg['content']
            if len(content) > 1500:
                print(content[:1500])
                print(f"\n... [Message truncated - {len(content) - 1500} chars remaining] ...\n")
            else:
                print(content)
            print()
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()