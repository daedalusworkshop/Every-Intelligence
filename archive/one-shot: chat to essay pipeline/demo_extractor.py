#!/usr/bin/env python3
"""
Demo: Using the ChatGPT Extractor with User Input
================================================

This shows how to use simple_extractor.py from another file,
with user-provided ChatGPT share links.

Usage:
    python demo_extractor.py
"""

from simple_chatgpt_extractor import extract_conversation_from_chatgpt_link as extract_chatgpt_conversation
from datetime import datetime
import os


def get_chatgpt_url():
    """
    Get a ChatGPT share URL from the user with basic validation.
    """
    print("ChatGPT Conversation Extractor")
    print("=" * 40)
    
    while True:
        url = input("\nEnter the ChatGPT share URL: ").strip()
        
        # Basic validation
        if not url:
            print("Please enter a URL.")
            continue
            
        if not url.startswith("https://chatgpt.com/share/"):
            print("Please enter a valid ChatGPT share URL (should start with https://chatgpt.com/share/)")
            continue
            
        return url


def save_conversation(conversation, source_url):
    """
    Save conversation to file with metadata.
    This is a modified version that takes the URL as a parameter.
    """
    # Create a meaningful filename
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    url_parts = source_url.split('/')
    chat_id = url_parts[-1][:8] if url_parts else "unknown"
    filename = f"chatgpt_conversation_{chat_id}_{timestamp}.txt"
    
    # Save to file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # Add metadata at the top
            f.write(f"ChatGPT Conversation Export\n")
            f.write(f"Source URL: {source_url}\n")
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


def main():
    """
    Main demo function that ties everything together.
    """
    try:
        # Get URL from user
        url = get_chatgpt_url()
        
        print(f"\n🔄 Extracting conversation from: {url}")
        print("This might take a few seconds...")
        
        # Extract the conversation using the imported function
        conversation = extract_chatgpt_conversation(url)
        
        # Check if extraction was successful
        if conversation.startswith("Error:"):
            print(f"\n❌ Extraction failed: {conversation}")
            return
        
        # Show a preview
        print(f"\n✅ Extraction successful!")
        print(f"📄 Preview (first 200 characters):")
        print("-" * 40)
        print(conversation[:200] + "..." if len(conversation) > 200 else conversation)
        print("-" * 40)
        
        # Ask if user wants to save
        save_choice = input("\nSave to file? (y/n): ").strip().lower()
        if save_choice in ['y', 'yes']:
            save_conversation(conversation, url)
        else:
            print("Conversation not saved.")
            
        # Ask if user wants to see the full conversation
        view_choice = input("View full conversation? (y/n): ").strip().lower()
        if view_choice in ['y', 'yes']:
            print("\n" + "="*80)
            print("FULL CONVERSATION")
            print("="*80)
            print(conversation)
            
    except KeyboardInterrupt:
        print("\n\n👋 Extraction cancelled by user.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    main() 