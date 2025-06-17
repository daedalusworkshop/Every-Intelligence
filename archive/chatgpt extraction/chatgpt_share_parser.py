"""
ChatGPT Share Link Parser
========================

A robust parser for extracting conversations from ChatGPT share links.
Based on reverse engineering of ChatGPT's data embedding structure.

Key discoveries:
1. Data is embedded via streamController.enqueue() with escaped JSON
2. Messages are stored as arrays with format: [id],"content"
3. Role indicators: "_2210":18 for user, "_2210":2280 for assistant
4. Complex nested structure with ID references
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class ChatGPTShareParser:
    """
    Parser for ChatGPT share links that understands the complex data structure.
    """
    
    # Role indicator constants discovered through analysis
    USER_ROLE_ID = "18"
    ASSISTANT_ROLE_ID = "2280"
    
    def __init__(self):
        self.raw_data = None
        self.decoded_data = None
        self.messages = []
        self.metadata = {}
        
    def parse_html(self, html_content: str) -> Dict:
        """
        Parse ChatGPT share link HTML and extract conversation.
        
        Args:
            html_content: The full HTML content of the share link
            
        Returns:
            Dictionary containing conversation metadata and messages
        """
        # Step 1: Extract embedded data
        self._extract_stream_data(html_content)
        
        # Step 2: Decode the data
        self._decode_data()
        
        # Step 3: Extract metadata
        self._extract_metadata()
        
        # Step 4: Extract messages
        self._extract_messages()
        
        # Step 5: Build final conversation structure
        return self._build_conversation()
    
    def _extract_stream_data(self, html_content: str) -> None:
        """Extract the streamController.enqueue data from HTML."""
        pattern = r'streamController\.enqueue\("(.*?)"\);'
        match = re.search(pattern, html_content, re.DOTALL)
        
        if not match:
            raise ValueError("No ChatGPT conversation data found in HTML. "
                           "This may not be a valid ChatGPT share link.")
        
        self.raw_data = match.group(1)
        
    def _decode_data(self) -> None:
        """Decode the escaped JSON data."""
        # Handle multiple levels of escaping
        decoded = self.raw_data
        
        # First pass: handle escaped backslashes
        decoded = decoded.replace('\\\\', '\x00')  # Temporary marker
        
        # Handle escaped quotes
        decoded = decoded.replace('\\"', '"')
        
        # Restore backslashes
        decoded = decoded.replace('\x00', '\\')
        
        # Handle newlines and tabs
        decoded = decoded.replace('\\n', '\n')
        decoded = decoded.replace('\\t', '\t')
        decoded = decoded.replace('\\r', '\r')
        
        self.decoded_data = decoded
        
    def _extract_metadata(self) -> None:
        """Extract conversation metadata."""
        # Extract title
        title_match = re.search(r'"title":"([^"]+)"', self.decoded_data)
        if title_match:
            self.metadata['title'] = title_match.group(1)
        
        # Extract timestamps
        create_match = re.search(r'"create_time":(\d+\.?\d*)', self.decoded_data)
        if create_match:
            self.metadata['create_time'] = float(create_match.group(1))
            
        update_match = re.search(r'"update_time":(\d+\.?\d*)', self.decoded_data)
        if update_match:
            self.metadata['update_time'] = float(update_match.group(1))
            
    def _extract_messages(self) -> None:
        """Extract all messages with their roles."""
        # Find all message content blocks: [id],"content"
        content_pattern = r'\[(\d+)\],"([^"]+(?:\\.[^"]+)*)"'
        content_matches = re.findall(content_pattern, self.decoded_data)
        
        # Build content map
        content_map = {}
        for msg_id, content in content_matches:
            # Clean content
            content = self._clean_content(content)
            # Skip very short content or system messages
            if len(content) > 20 and not content.startswith("Original custom"):
                content_map[msg_id] = content
        
        # Find message structures with timestamps and roles
        # Pattern: timestamp,{"_2216":...,"_2218":...},[content_id]
        message_pattern = r'(\d+\.\d+),\{"[^}]+"\},\[(\d+)\]'
        message_matches = re.findall(message_pattern, self.decoded_data)
        
        for timestamp, content_id in message_matches:
            if content_id not in content_map:
                continue
                
            # Find the role for this message
            # Look backwards from the content ID for role indicators
            content_pos = self.decoded_data.find(f'[{content_id}]')
            if content_pos > 0:
                # Extract context before this message (up to 1000 chars)
                context = self.decoded_data[max(0, content_pos - 1000):content_pos]
                
                # Determine role based on the _2210 field value
                role = self._determine_role(context)
                
                # Skip if we couldn't determine a valid role
                if role not in ['user', 'assistant']:
                    continue
                
                self.messages.append({
                    'role': role,
                    'content': content_map[content_id],
                    'timestamp': float(timestamp)
                })
        
        # Sort messages by timestamp
        self.messages.sort(key=lambda x: x['timestamp'])
        
    def _determine_role(self, context: str) -> str:
        """Determine message role from context."""
        # Look for the _2210 field which indicates role
        # Pattern: {"_2210":value,...}
        role_pattern = r'"_2210":(\d+)'
        role_match = re.search(role_pattern, context)
        
        if role_match:
            role_id = role_match.group(1)
            if role_id == self.USER_ROLE_ID:
                return 'user'
            elif role_id == self.ASSISTANT_ROLE_ID:
                return 'assistant'
        
        # Fallback: check for explicit role markers
        if '"role":"user"' in context:
            return 'user'
        elif '"role":"assistant"' in context:
            return 'assistant'
        elif '"role":"system"' in context:
            return 'system'
            
        return 'unknown'
    
    def _clean_content(self, content: str) -> str:
        """Clean message content."""
        # Unescape remaining escape sequences
        content = content.replace('\\n', '\n')
        content = content.replace('\\"', '"')
        content = content.replace('\\/', '/')
        content = content.replace('\\\\', '\\')
        
        # Remove file cite markers if present
        content = re.sub(r'fileciteturn\d+file\d+', '', content)
        
        return content.strip()
    
    def _build_conversation(self) -> Dict:
        """Build the final conversation structure."""
        conversation = {
            'title': self.metadata.get('title', 'ChatGPT Conversation'),
            'create_time': self.metadata.get('create_time'),
            'update_time': self.metadata.get('update_time'),
            'messages': []
        }
        
        # Add human-readable timestamps
        if conversation['create_time']:
            conversation['create_time_readable'] = \
                datetime.fromtimestamp(conversation['create_time']).isoformat()
                
        if conversation['update_time']:
            conversation['update_time_readable'] = \
                datetime.fromtimestamp(conversation['update_time']).isoformat()
        
        # Process messages
        for msg in self.messages:
            message = {
                'role': msg['role'],
                'content': msg['content']
            }
            
            if 'timestamp' in msg:
                message['timestamp'] = msg['timestamp']
                message['timestamp_readable'] = \
                    datetime.fromtimestamp(msg['timestamp']).isoformat()
                    
            conversation['messages'].append(message)
        
        return conversation


def parse_chatgpt_share_link(html_content: str) -> Dict:
    """
    Parse a ChatGPT share link and extract the conversation.
    
    Args:
        html_content: The HTML content of the share link
        
    Returns:
        Dictionary containing the parsed conversation
    """
    parser = ChatGPTShareParser()
    return parser.parse_html(html_content)


def parse_chatgpt_share_file(file_path: str) -> Dict:
    """
    Parse a ChatGPT share link HTML file.
    
    Args:
        file_path: Path to the HTML file
        
    Returns:
        Dictionary containing the parsed conversation
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    return parse_chatgpt_share_link(html_content)


# Command-line interface
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = 'chatgpt_response.html'
    
    try:
        conversation = parse_chatgpt_share_file(file_path)
        
        print(f"Title: {conversation['title']}")
        if 'create_time_readable' in conversation:
            print(f"Created: {conversation['create_time_readable']}")
        if 'update_time_readable' in conversation:
            print(f"Updated: {conversation['update_time_readable']}")
        
        print(f"\nConversation contains {len(conversation['messages'])} messages:\n")
        
        for i, msg in enumerate(conversation['messages']):
            print(f"{'='*60}")
            print(f"Message {i+1} - {msg['role'].upper()}")
            if 'timestamp_readable' in msg:
                print(f"Time: {msg['timestamp_readable']}")
            print(f"{'='*60}")
            
            # Print content (truncate if very long)
            content = msg['content']
            if len(content) > 1000:
                print(content[:1000])
                print(f"\n... [truncated {len(content) - 1000} characters] ...\n")
            else:
                print(content)
            print()
            
    except Exception as e:
        print(f"Error parsing ChatGPT share link: {e}")
        sys.exit(1)