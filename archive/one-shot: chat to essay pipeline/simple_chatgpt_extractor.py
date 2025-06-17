#!/usr/bin/env python3
"""
Simple ChatGPT Share Link Extractor
===================================

Takes a ChatGPT share link and returns the conversation transcript.

Usage:
    from simple_chatgpt_extractor import extract_conversation_from_chatgpt_link
    
    transcript = extract_conversation_from_chatgpt_link("https://chatgpt.com/share/your-link-here")
    print(transcript)
"""

import requests
import re
import json
from bs4 import BeautifulSoup
from typing import List, Dict, Any


def extract_conversation_from_chatgpt_link(share_url: str) -> str:
    """
    Extract conversation transcript from ChatGPT share link.
    
    Args:
        share_url: ChatGPT share URL like https://chatgpt.com/share/684b6af3-fc08-8009-b864-a0b6761b22d0
    
    Returns:
        Clean conversation transcript as string
    """
    try:
        # Add headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Fetch the page
        response = requests.get(share_url, headers=headers)
        response.raise_for_status()
        
        # Extract conversation from the embedded JavaScript data
        conversation = extract_from_embedded_data(response.text)
        if conversation:
            return conversation
            
        return "Could not extract conversation - page might be private or format changed"
        
    except Exception as e:
        return f"Error extracting conversation: {str(e)}"


def extract_from_embedded_data(html_content: str) -> str:
    """
    Extract conversation from the embedded JavaScript data in ChatGPT pages.
    
    The conversation content is embedded as escaped strings in the React Router data.
    """
    messages = []
    
    # Find the large script tag with conversation data
    soup = BeautifulSoup(html_content, 'html.parser')
    scripts = soup.find_all('script')

    largest_script = None
    max_length = 0
    
    for script in scripts:
        if script.string and len(script.string) > max_length:
            max_length = len(script.string)
            largest_script = script.string
    
    if not largest_script:
        return ""
    
    # Based on debug output, the content is stored as direct string values in arrays
    # Look for long quoted strings that contain conversation content
    
    # Pattern: Look for substantial quoted content (50+ chars)
    content_pattern = r'"([^"]{100,})"'
    all_matches = re.findall(content_pattern, largest_script)
    
    # Process each potential content string
    for content in all_matches:
        cleaned = clean_message_content(content)
        
        # Skip if too short, looks like metadata, code-like, or is chain-of-thought reasoning
        if (len(cleaned) < 100 or 
            is_metadata(cleaned) or 
            is_code_like(cleaned) or 
            is_chain_of_thought(cleaned)):
            continue
        
        # Skip if it's just a URL or title
        if cleaned.startswith('http') or len(cleaned.split()) < 10:
            continue
            
        # Determine role based on content characteristics
        role = 'user' if is_likely_user_message(cleaned) else 'assistant'
        
        messages.append({
            'role': role,
            'content': cleaned
        })
    
    # Remove duplicates and combine fragmented messages
    unique_messages = remove_duplicate_messages(messages)
    
    # Sort messages: user messages first, then by length
    unique_messages.sort(key=lambda x: (x['role'] != 'user', -len(x['content'])))
    
    return format_messages(unique_messages)


def clean_message_content(content: str) -> str:
    """
    Clean up message content by removing escape characters and formatting.
    """
    # Remove common escape sequences
    content = content.replace('\\n', '\n')
    content = content.replace('\\t', '\t')
    content = content.replace('\\"', '"')
    content = content.replace('\\\\', '\\')
    content = content.replace('\\/', '/')
    
    # Remove unicode escape sequences
    content = re.sub(r'\\u[0-9a-fA-F]{4}', '', content)
    
    # Clean up extra whitespace but preserve paragraph breaks
    lines = content.split('\n')
    cleaned_lines = []
    for line in lines:
        cleaned_line = re.sub(r'\s+', ' ', line.strip())
        if cleaned_line:
            cleaned_lines.append(cleaned_line)
    
    # Join with proper paragraph breaks
    result = '\n\n'.join(cleaned_lines)
    
    # Remove any remaining escape artifacts
    result = re.sub(r'\\+', '', result)  # Remove remaining backslashes
    result = re.sub(r'\s+', ' ', result)  # Clean up extra spaces
    result = re.sub(r'\n\s*\n', '\n\n', result)  # Clean up paragraph breaks
    
    return result.strip()


def is_metadata(content: str) -> bool:
    """
    Check if content looks like metadata rather than conversation content.
    """
    metadata_indicators = [
        'window.__', 'function(', 'var ', 'const ', 'let ',
        'http://', 'https://', '.js', '.css', '.png', '.jpg',
        'getElementById', 'addEventListener', 'document.',
        'undefined', 'null', 'true', 'false',
        len(content) < 20,  # Very short content
        content.count('"') > len(content) / 10,  # Too many quotes (likely code)
    ]
    
    content_lower = content.lower()
    return any(
        indicator in content_lower if isinstance(indicator, str) else indicator
        for indicator in metadata_indicators
    )


def remove_duplicate_messages(messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Remove duplicate messages and combine fragmented messages from the same role.
    """
    # First, remove exact duplicates
    unique_messages = []
    seen_content = set()
    
    for msg in messages:
        content_key = msg['content'][:200].strip()
        
        is_duplicate = False
        for seen in seen_content:
            if content_key in seen or seen in content_key:
                is_duplicate = True
                break
        
        if not is_duplicate:
            seen_content.add(content_key)
            unique_messages.append(msg)
    
    # Separate user and AI messages
    user_fragments = []
    ai_fragments = []
    
    for msg in unique_messages:
        if msg['role'] == 'user':
            user_fragments.append(msg['content'])
        else:
            ai_fragments.append(msg['content'])
    
    combined_messages = []
    
    # Combine user fragments into one coherent message
    if user_fragments:
        # Sort fragments to put the main content first and ending fragments last
        def sort_user_fragments(fragments):
            main_fragments = []
            ending_fragments = []
            
            for fragment in fragments:
                # Check if this fragment contains the ending
                if 'what do you think' in fragment.lower():
                    ending_fragments.append(fragment)
                # Check if this fragment looks like a main content piece
                elif any(indicator in fragment.lower() for indicator in [
                    'roadmap', 'phase 1', 'phase 2', 'vision:', 'core use case'
                ]):
                    main_fragments.insert(0, fragment)  # Put main content first
                else:
                    main_fragments.append(fragment)
            
            return main_fragments + ending_fragments
        
        sorted_fragments = sort_user_fragments(user_fragments)
        
        # Clean up and combine
        cleaned_fragments = []
        for fragment in sorted_fragments:
            # Remove obvious AI thinking patterns from user content
            if not is_ai_thinking_fragment(fragment):
                cleaned_fragments.append(fragment.strip())
        
        if cleaned_fragments:
            combined_user_content = '\n\n'.join(cleaned_fragments)
            combined_messages.append({
                'role': 'user',
                'content': combined_user_content
            })
    
    # Add AI messages (keep them separate as they might be distinct responses)
    for ai_content in ai_fragments:
        # Skip AI thinking fragments
        if not is_ai_thinking_fragment(ai_content):
            combined_messages.append({
                'role': 'assistant',
                'content': ai_content
            })
    
    return combined_messages


def is_ai_thinking_fragment(content: str) -> bool:
    """
    Check if a fragment is AI internal thinking that should be excluded.
    """
    thinking_patterns = [
        "i'm aiming to offer",
        "i want to avoid fluff",
        "i'm thinking it's too early",
        "i'll stick to assessing",
        "i'll focus on",
        "i'll provide",
        "we need to analyze",
        "mozilla/5.0",  # User agent strings
    ]
    
    content_lower = content.lower()
    
    # Check for thinking patterns
    for pattern in thinking_patterns:
        if pattern in content_lower:
            return True
    
    # Check if it's very short and looks like metadata
    if len(content) < 200 and any(indicator in content_lower for indicator in [
        'mozilla', 'webkit', 'chrome', 'safari'
    ]):
        return True
    
    return False


def is_likely_user_message(content: str) -> bool:
    """
    Determine if content is likely from a user based on patterns.
    """
    # Strong user indicators
    strong_user_indicators = [
        '# ', '## ', '### ',  # Markdown headers
        '**vision:**', '**core use case:**', '**task:**',
        'phase 1', 'phase 2', 'phase 3',
        'what do you think', 'what has every thought',
        'roadmap', 'goal', 'vision',
    ]
    
    # Strong AI indicators (if present, likely AI)
    ai_indicators = [
        'ruthless debrief', 'strategic coherence', 'technical stack',
        'reality check', 'risk mitigation', 'verdict',
        'aspect', 'strength', 'blind spot',
        'thought for', 'seconds', 'evaluation', 'kpi',
        'mitigation matrix', 'surgical notes',
    ]
    
    content_lower = content.lower()
    
    # Check for AI indicators first
    ai_score = sum(1 for indicator in ai_indicators if indicator in content_lower)
    if ai_score > 0:
        return False
    
    # Check for strong user indicators
    strong_user_score = sum(1 for indicator in strong_user_indicators if indicator in content_lower)
    if strong_user_score > 0:
        return True
    
    # Default heuristics
    # User messages tend to be more structured with lists and planning
    structure_score = content.count('*') + content.count('#') + content.count('1.') + content.count('2.')
    
    # AI messages tend to have more analytical language
    analytical_words = ['analysis', 'approach', 'consider', 'however', 'therefore', 'specifically']
    analytical_score = sum(1 for word in analytical_words if word in content_lower)
    
    return structure_score > analytical_score


def format_messages(messages: List[Dict[str, str]]) -> str:
    """
    Format extracted messages into a readable conversation transcript.
    """
    if not messages:
        return ""
    
    formatted = []
    for msg in messages:
        role = msg.get('role', 'unknown').title()
        content = msg.get('content', '')
        
        if content and len(content) > 20:
            formatted.append(f"{role}:\n{content}")
    
    return "\n\n" + ("\n\n" + "="*80 + "\n\n").join(formatted)


def is_code_like(content: str) -> bool:
    """
    Check if content looks like code or technical strings rather than conversation.
    """
    code_indicators = [
        content.count('{') > 3,
        content.count('[') > 3,
        content.count('_') > len(content) / 20,  # Too many underscores
        content.count(':') > len(content) / 30,  # Too many colons
        '\\u' in content and content.count('\\u') > 2,  # Unicode escapes
        content.startswith(('window.', 'function', 'var ', 'const ')),
        'getElementById' in content,
        'addEventListener' in content,
    ]
    
    return any(code_indicators)


def is_chain_of_thought(content: str) -> bool:
    """
    Check if content is chain-of-thought reasoning that should be excluded.
    
    o1 models show their internal reasoning process which should not be part
    of the actual conversation transcript.
    """
    cot_indicators = [
        'thought for',
        'thinking for',
        'seconds',
        'minutes',
        # Common chain-of-thought patterns
        'let me think',
        'i need to',
        'first, i should',
        'step by step',
        'breaking this down',
    ]
    
    content_lower = content.lower()
    
    # Check for time-based thinking indicators (like "Thought for 18 seconds")
    time_pattern = r'thought for \d+ seconds?'
    if re.search(time_pattern, content_lower):
        return True
    
    # Check for other chain-of-thought indicators
    cot_score = sum(1 for indicator in cot_indicators if indicator in content_lower)
    
    # If it's short and has CoT indicators, likely chain-of-thought
    if len(content) < 500 and cot_score > 1:
        return True
    
    return False


def main():
    """Test the extractor with a sample URL."""
    test_url = "https://chatgpt.com/share/684b6af3-fc08-8009-b864-a0b6761b22d0"
    
    print("Simple ChatGPT Share Link Extractor")
    print("=" * 50)
    print(f"Extracting from: {test_url}")
    print()
    
    transcript = extract_conversation_from_chatgpt_link(test_url)
    print(transcript)
    
    print("\n" + "=" * 50)
    print(f"Extracted {len(transcript)} characters")
    print("Done!")


if __name__ == "__main__":
    main()