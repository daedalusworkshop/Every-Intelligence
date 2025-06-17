#!/usr/bin/env python3
"""
Simple ChatGPT Conversation Extractor
====================================

The minimal version that does exactly what we need:
1. Open the ChatGPT share page
2. Scroll to load everything  
3. Extract all messages
4. Format them nicely
5. Export to file

Usage:
    python simple_extractor.py
"""

from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import asyncio

# URL to extract - change this to whatever conversation you want
TEST_URL = "https://chatgpt.com/share/684b7830-18f8-8009-adda-d13c18235e79"


class ChatGPTReader:
    """
    Async wrapper for ChatGPT conversation extraction.
    This class provides the async interface expected by parsing.py
    while using the sync Playwright implementation under the hood.
    """
    
    async def extract_conversation(self, share_url: str) -> str:
        """
        Extract a full ChatGPT conversation from a share link (async version).
        
        Args:
            share_url: The ChatGPT share URL
            
        Returns:
            The full conversation as formatted text
        """
        # Run the sync function in a thread pool to make it async
        return await asyncio.to_thread(extract_chatgpt_conversation, share_url)


def extract_chatgpt_conversation(share_url: str) -> str:
    """
    Extract a full ChatGPT conversation from a share link.
    
    Args:
        share_url: The ChatGPT share URL
        
    Returns:
        The full conversation as formatted text
    """
    with sync_playwright() as p:
        # Open a browser (headless = invisible)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Go to the ChatGPT page
            print(f"Loading: {share_url}")
            page.goto(share_url, wait_until='networkidle')
            
            # Wait for messages to appear (timeout is literally 10 seconds to let it load)
            page.wait_for_selector('[data-message-author-role]', timeout=10000)
            
            # Scroll to load everything
            print("Scrolling to load full conversation...")
            scroll_to_load_all(page)
            
            # Get all the messages
            print("Extracting messages...")
            messages = extract_all_messages(page)
            
            # Format them nicely
            return format_conversation(messages)
            
        except Exception as e:
            # Temporarily log the actual error for debugging
            print(f"🔍 ACTUAL PLAYWRIGHT ERROR: {str(e)}")
            print(f"🔍 Error type: {type(e)}")
            # Simple, user-friendly error message instead of exposing technical details
            return "Unable to extract conversation. ChatGPT may have changed their sharing system or the conversation is no longer accessible. Please verify the URL is a valid, public ChatGPT share link."
        finally:
            browser.close()


def scroll_to_load_all(page):
    """
    Scroll the page to make sure all messages are loaded.
    ChatGPT uses lazy loading, so we need to scroll to see everything.
    """
    # First, go to the very top
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)
    
    # Scroll up a bunch to make sure we get the beginning
    for _ in range(10):
        page.evaluate("window.scrollBy(0, -1000)")
        page.wait_for_timeout(500)
    
    # Now scroll down to load everything
    previous_height = page.evaluate("document.body.scrollHeight")
    
    for _ in range(50):  # Max 50 scrolls to prevent infinite loops
        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        
        # Check if page got taller (new content loaded)
        new_height = page.evaluate("document.body.scrollHeight")
        if new_height == previous_height:
            break  # No new content, we're done
        previous_height = new_height
    
    # Go back to top for extraction
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)


def extract_all_messages(page):
    """
    Find all the conversation messages on the page.
    
    Returns:
        List of message dictionaries with 'role' and 'content'
    """
    messages = []
    
    # Find all message elements (ChatGPT marks them with this attribute)
    message_elements = page.query_selector_all('[data-message-author-role]')
    
    for element in message_elements:
        # Get who said it (user or assistant)
        role = element.get_attribute('data-message-author-role')
        
        # Get what they said
        content = element.inner_text().strip()
        
        if content:  # Only add if there's actual content
            messages.append({
                'role': role,
                'content': content
            })
    
    return messages


def format_conversation(messages):
    """
    Turn the list of messages into a nice readable format.
    """
    if not messages:
        return "No messages found"
    
    formatted_parts = []
    
    for msg in messages:
        role = msg['role'].title()  # 'user' -> 'User'
        content = msg['content']
        
        formatted_parts.append(f"{role}:\n{content}")
    
    # Join with separators
    return "\n\n" + ("\n\n" + "="*80 + "\n\n").join(formatted_parts)


def main():
    """Extract conversation and return it."""
    # Extract the conversation
    conversation = extract_chatgpt_conversation(TEST_URL)
    
    # Show the result
    print(conversation)
    
    return conversation


def save(conversation):
    """Save conversation to file with metadata."""
    # Create a meaningful filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    url_parts = TEST_URL.split('/')
    chat_id = url_parts[-1][:8] if url_parts else "unknown"
    filename = f"chatgpt_conversation_{chat_id}_{timestamp}.txt"
    
    # Save to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # Add metadata at the top
            f.write(f"ChatGPT Conversation Export\n")
            f.write(f"Source URL: {TEST_URL}\n")
            f.write(f"Extracted on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"{'='*80}\n")
            f.write(conversation)
        
        print(f"\n✅ Conversation saved to: {filename}")
        print(f"📊 File size: {os.path.getsize(filename)} bytes")
        print(f"📄 Character count: {len(conversation)}")
        return filename
        
    except Exception as e:
        print(f"❌ Error saving file: {str(e)}")
        print("The conversation was extracted but couldn't be saved.")
        return None


if __name__ == "__main__":
    # Extract once
    conversation = main()
    
    # Save it
    save(conversation)