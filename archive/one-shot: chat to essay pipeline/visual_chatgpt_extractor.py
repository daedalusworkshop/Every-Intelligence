#!/usr/bin/env python3
"""
Visual ChatGPT Share Link Extractor
===================================

Uses browser automation to extract conversations by reading the visual page structure.
This approach sidesteps all obfuscation issues by working with what users actually see.

Usage:
    from visual_chatgpt_extractor import extract_conversation_visually
    
    transcript = extract_conversation_visually("https://chatgpt.com/share/your-link-here")
    print(transcript)
"""

from playwright.sync_api import sync_playwright
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from typing import List, Dict, Optional
import time
import re


def extract_conversation_visually(share_url: str, method: str = "playwright") -> str:
    """
    Extract conversation by reading the visual page structure.
    
    Args:
        share_url: ChatGPT share URL
        method: "playwright" (recommended), "selenium", or "pdf"
    
    Returns:
        Clean conversation transcript
    """
    if method == "playwright":
        return _extract_with_playwright(share_url)
    elif method == "selenium":
        return _extract_with_selenium(share_url)
    elif method == "pdf":
        return _extract_with_pdf_generation(share_url)
    else:
        raise ValueError("Method must be 'playwright', 'selenium', or 'pdf'")


def _extract_with_playwright(share_url: str) -> str:
    """
    Extract using Playwright (more reliable and faster).
    """
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        
        page = browser.new_page()
        
        # Set a reasonable viewport
        page.set_viewport_size({"width": 1200, "height": 800})
        
        try:
            # Navigate to the page
            page.goto(share_url, wait_until='networkidle', timeout=30000)
            
            # Wait for conversation to load - try multiple selectors
            selectors_to_try = [
                '[data-message-author-role]',
                '[class*="react-scroll-to-bottom"] .flex > div',
                '.markdown',
                '[class*="conversation"]',
                '[class*="message"]'
            ]
            
            messages_found = False
            for selector in selectors_to_try:
                try:
                    page.wait_for_selector(selector, timeout=10000)
                    messages_found = True
                    break
                except:
                    continue
            
            if not messages_found:
                return "Could not find conversation messages on the page"
            
            # SCROLL TO LOAD ALL CONTENT
            _scroll_to_load_all_content_playwright(page)
            
            # Extract messages using the most reliable method
            print("Starting message extraction...")
            conversation = _extract_messages_from_page(page)
            print(f"Extraction complete. Found {len(conversation)} messages.")
            
            return _format_conversation(conversation)
            
        except Exception as e:
            return f"Error extracting conversation: {str(e)}"
        finally:
            browser.close()


def _extract_with_pdf_generation(share_url: str) -> str:
    """
    Extract by generating a PDF of the full page, then extracting text from PDF.
    This might capture content that scrolling methods miss.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            print("Loading page for PDF generation...")
            page.goto(share_url, wait_until='networkidle', timeout=30000)
            
            # Wait for conversation to load
            page.wait_for_selector('[data-message-author-role]', timeout=10000)
            
            # Scroll to load all content first
            print("Scrolling to load all content...")
            _scroll_to_load_all_content_playwright(page)
            
            # Generate PDF with full page content
            print("Generating PDF...")
            pdf_path = "temp_conversation.pdf"
            page.pdf(
                path=pdf_path,
                format='A4',
                print_background=True,
                margin={'top': '1cm', 'right': '1cm', 'bottom': '1cm', 'left': '1cm'}
            )
            
            # Extract text from PDF
            print("Extracting text from PDF...")
            import PyPDF2
            
            with open(pdf_path, 'rb') as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text_content = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page_obj = pdf_reader.pages[page_num]
                    text_content += page_obj.extract_text() + "\n"
            
            # Clean up temp file
            import os
            os.remove(pdf_path)
            
            # Try to parse the extracted text into conversation format
            return _parse_pdf_text_to_conversation(text_content)
            
        except Exception as e:
            return f"Error with PDF extraction: {str(e)}"
        finally:
            browser.close()


def _parse_pdf_text_to_conversation(text: str) -> str:
    """
    Parse PDF-extracted text into conversation format.
    PDF text extraction can be messy, so we need to clean it up.
    """
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        if len(line) > 10:  # Filter out very short lines
            cleaned_lines.append(line)
    
    # Try to identify conversation structure
    conversation_text = '\n'.join(cleaned_lines)
    
    # Basic cleanup
    conversation_text = conversation_text.replace('ChatGPT', '\n\nAssistant:')
    conversation_text = conversation_text.replace('You', '\n\nUser:')
    
    return f"PDF Extraction Result:\n{conversation_text}"


def _extract_with_selenium(share_url: str) -> str:
    """
    Extract using Selenium (fallback option).
    """
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1200,800')
    
    driver = webdriver.Chrome(options=options)
    
    try:
        driver.get(share_url)
        
        # Wait for conversation to load
        selectors_to_try = [
            '[data-message-author-role]',
            '.markdown',
            '[class*="message"]'
        ]
        
        messages_found = False
        for selector in selectors_to_try:
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                messages_found = True
                break
            except:
                continue
        
        if not messages_found:
            return "Could not find conversation messages on the page"
        
        # SCROLL TO LOAD ALL CONTENT
        _scroll_to_load_all_content_selenium(driver)
        
        # Extract messages
        conversation = _extract_messages_from_selenium(driver)
        
        return _format_conversation(conversation)
        
    except Exception as e:
        return f"Error extracting conversation: {str(e)}"
    finally:
        driver.quit()


def _scroll_to_load_all_content_playwright(page) -> None:
    """
    Scroll through the entire conversation to ensure all messages are loaded.
    ChatGPT uses lazy loading, so we need to scroll to see everything.
    CRITICAL: We must scroll to TOP first, then to bottom to capture everything!
    """
    print("Scrolling to load all conversation content...")
    
    # STEP 1: Multiple aggressive attempts to reach the true beginning
    print("  Aggressively finding the true beginning...")
    
    # First, try scrolling to absolute top
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(2000)  # Longer wait
    
    # Try pressing Home key to ensure we're at the very top
    page.keyboard.press("Home")
    page.wait_for_timeout(1000)
    
    # Try Ctrl+Home as well (some pages respond differently)
    page.keyboard.press("Control+Home")
    page.wait_for_timeout(1000)
    
    # STEP 2: Scroll up repeatedly with longer waits to load any hidden content
    print("  Loading content from the absolute beginning...")
    scroll_up_attempts = 0
    max_up_scrolls = 30  # Increased attempts
    
    while scroll_up_attempts < max_up_scrolls:
        # Get current scroll position
        current_scroll = page.evaluate("window.pageYOffset")
        
        # Try multiple scroll up methods
        page.evaluate("window.scrollBy(0, -1000)")  # Bigger scroll increments
        page.wait_for_timeout(1500)  # Longer wait for lazy loading
        
        # Also try Page Up key
        if scroll_up_attempts % 3 == 0:
            page.keyboard.press("PageUp")
            page.wait_for_timeout(1000)
        
        # Check if we can scroll up further
        new_scroll = page.evaluate("window.pageYOffset")
        
        if new_scroll == current_scroll and new_scroll == 0:
            # We're at the absolute top, but let's try a few more times to be sure
            if scroll_up_attempts < 5:
                scroll_up_attempts += 1
                continue
            else:
                break
            
        scroll_up_attempts += 1
        
        # Progress indicator
        if scroll_up_attempts % 5 == 0:
            print(f"    Up-scroll attempt {scroll_up_attempts}, position: {new_scroll}px")
    
    print(f"  Reached the top after {scroll_up_attempts} up-scrolls")
    
    # STEP 2.5: One final aggressive top attempt
    print("  Final aggressive top positioning...")
    page.evaluate("window.scrollTo(0, 0)")
    page.keyboard.press("Control+Home")
    page.wait_for_timeout(2000)
    
    # DIAGNOSTIC: Let's see what we can actually find on the page
    print("  DIAGNOSTIC: Checking page content...")
    
    # Get ALL messages to see what we're actually capturing
    all_messages = page.query_selector_all('[data-message-author-role]')
    print(f"    Found {len(all_messages)} total messages")
    
    # Show first few messages
    for i, msg in enumerate(all_messages[:5]):
        role = msg.get_attribute('data-message-author-role')
        content = msg.inner_text()[:100] + "..." if len(msg.inner_text()) > 100 else msg.inner_text()
        print(f"    Message {i+1} ({role}): {content}")
    
    # Check scroll position
    scroll_pos = page.evaluate("window.pageYOffset")
    page_height = page.evaluate("document.body.scrollHeight")
    print(f"    Current scroll position: {scroll_pos}px")
    print(f"    Total page height: {page_height}px")
    print(f"    Ready to extract {len(all_messages)} messages...")
    
    # STEP 3: Now scroll down to load all content
    print("  Now scrolling down to load all content...")
    previous_height = page.evaluate("document.body.scrollHeight")
    
    scroll_attempts = 0
    max_scrolls = 50  # Prevent infinite loops
    
    while scroll_attempts < max_scrolls:
        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        
        # Wait for potential new content to load
        page.wait_for_timeout(1000)  # 1 second wait
        
        # Check if new content loaded
        new_height = page.evaluate("document.body.scrollHeight")
        
        if new_height == previous_height:
            # No new content loaded, we've reached the end
            break
            
        previous_height = new_height
        scroll_attempts += 1
        
        # Progress indicator
        if scroll_attempts % 5 == 0:
            print(f"    Scrolled down {scroll_attempts} times, page height: {new_height}px")
    
    # STEP 4: Scroll back to top to ensure we capture everything from the beginning
    print("  Finally, scrolling back to top for extraction...")
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1000)
    
    print(f"Finished complete scroll sequence: {scroll_up_attempts} up + {scroll_attempts} down")


def _scroll_to_load_all_content_selenium(driver) -> None:
    """
    Scroll through the entire conversation to ensure all messages are loaded.
    ChatGPT uses lazy loading, so we need to scroll to see everything.
    CRITICAL: We must scroll to TOP first, then to bottom to capture everything!
    """
    print("Scrolling to load all conversation content...")
    
    # STEP 1: Scroll to the very top first to ensure we get the beginning
    print("  First, scrolling to the very top...")
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    
    # STEP 2: Scroll up repeatedly to load any content above current viewport
    print("  Loading content from the beginning...")
    scroll_up_attempts = 0
    max_up_scrolls = 20
    
    while scroll_up_attempts < max_up_scrolls:
        # Get current scroll position
        current_scroll = driver.execute_script("return window.pageYOffset")
        
        # Scroll up a bit more
        driver.execute_script("window.scrollBy(0, -500);")
        time.sleep(0.5)
        
        # Check if we can scroll up further
        new_scroll = driver.execute_script("return window.pageYOffset")
        
        if new_scroll == current_scroll and new_scroll == 0:
            # We're at the absolute top
            break
            
        scroll_up_attempts += 1
    
    print(f"  Reached the top after {scroll_up_attempts} up-scrolls")
    
    # STEP 3: Now scroll down to load all content
    print("  Now scrolling down to load all content...")
    previous_height = driver.execute_script("return document.body.scrollHeight")
    
    scroll_attempts = 0
    max_scrolls = 50  # Prevent infinite loops
    
    while scroll_attempts < max_scrolls:
        # Scroll to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Wait for potential new content to load
        time.sleep(1)
        
        # Check if new content loaded
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == previous_height:
            # No new content loaded, we've reached the end
            break
            
        previous_height = new_height
        scroll_attempts += 1
        
        # Progress indicator
        if scroll_attempts % 5 == 0:
            print(f"    Scrolled down {scroll_attempts} times, page height: {new_height}px")
    
    # STEP 4: Scroll back to top to ensure we capture everything from the beginning
    print("  Finally, scrolling back to top for extraction...")
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)
    
    print(f"Finished complete scroll sequence: {scroll_up_attempts} up + {scroll_attempts} down")


def _extract_messages_from_page(page) -> List[Dict[str, str]]:
    """
    Extract messages from Playwright page using multiple strategies.
    """
    messages = []
    
    # Strategy 1: Use data-message-author-role attribute (most reliable)
    try:
        message_elements = page.query_selector_all('[data-message-author-role]')
        print(f"  EXTRACTION DEBUG: Found {len(message_elements)} message elements")
        
        if message_elements:
            for i, element in enumerate(message_elements):
                role = element.get_attribute('data-message-author-role')
                
                # Try different content selectors
                content_selectors = ['.markdown', '.message-content', 'div[class*="prose"]', 'div']
                content = ""
                
                for selector in content_selectors:
                    content_element = element.query_selector(selector)
                    if content_element:
                        content = content_element.inner_text()
                        if content.strip():
                            break
                
                # DEBUG: Show what we're extracting
                content_preview = content[:100] + "..." if len(content) > 100 else content
                print(f"    Extracting message {i+1} ({role}): {content_preview}")
                
                if content.strip():
                    messages.append({
                        'role': role,
                        'content': content.strip()
                    })
            
            print(f"  EXTRACTION DEBUG: Successfully extracted {len(messages)} messages")
            if messages:
                # DEBUG: Show first few extracted messages
                print("  First 3 extracted messages:")
                for i, msg in enumerate(messages[:3]):
                    content_preview = msg['content'][:100] + "..." if len(msg['content']) > 100 else msg['content']
                    print(f"    {i+1}. {msg['role']}: {content_preview}")
                return messages
    except Exception as e:
        print(f"Strategy 1 failed: {e}")
    
    # Strategy 2: Look for conversation container structure
    try:
        conversation_container = page.query_selector('[class*="react-scroll-to-bottom"]')
        if conversation_container:
            message_divs = conversation_container.query_selector_all('.flex > div')
            
            for i, div in enumerate(message_divs):
                content = div.inner_text().strip()
                if len(content) > 20:  # Filter out empty or very short divs
                    # Alternate between user and assistant based on position
                    role = 'user' if i % 2 == 0 else 'assistant'
                    messages.append({
                        'role': role,
                        'content': content
                    })
            
            if messages:
                return messages
    except Exception as e:
        print(f"Strategy 2 failed: {e}")
    
    # Strategy 3: Look for any substantial text blocks and infer roles
    try:
        all_text_elements = page.query_selector_all('div')
        substantial_texts = []
        
        for element in all_text_elements:
            text = element.inner_text().strip()
            if len(text) > 100 and not _is_likely_metadata(text):
                substantial_texts.append(text)
        
        # Remove duplicates and infer roles
        unique_texts = []
        for text in substantial_texts:
            is_duplicate = False
            for existing in unique_texts:
                if text in existing or existing in text:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_texts.append(text)
        
        # Infer roles based on content patterns
        for text in unique_texts:
            role = 'user' if _is_likely_user_message(text) else 'assistant'
            messages.append({
                'role': role,
                'content': text
            })
        
        return messages
        
    except Exception as e:
        print(f"Strategy 3 failed: {e}")
    
    return messages


def _extract_messages_from_selenium(driver) -> List[Dict[str, str]]:
    """
    Extract messages from Selenium driver using similar strategies.
    """
    messages = []
    
    # Strategy 1: Use data-message-author-role
    try:
        message_elements = driver.find_elements(By.CSS_SELECTOR, '[data-message-author-role]')
        if message_elements:
            for element in message_elements:
                role = element.get_attribute('data-message-author-role')
                
                # Try to find content within the element
                content_selectors = ['.markdown', '.message-content', 'div']
                content = ""
                
                for selector in content_selectors:
                    try:
                        content_element = element.find_element(By.CSS_SELECTOR, selector)
                        content = content_element.text
                        if content.strip():
                            break
                    except:
                        continue
                
                if content.strip():
                    messages.append({
                        'role': role,
                        'content': content.strip()
                    })
            
            if messages:
                return messages
    except Exception as e:
        print(f"Selenium Strategy 1 failed: {e}")
    
    # Strategy 2: Look for markdown content
    try:
        markdown_elements = driver.find_elements(By.CSS_SELECTOR, '.markdown')
        for i, element in enumerate(markdown_elements):
            content = element.text.strip()
            if len(content) > 20:
                role = 'user' if i % 2 == 0 else 'assistant'
                messages.append({
                    'role': role,
                    'content': content
                })
        
        if messages:
            return messages
    except Exception as e:
        print(f"Selenium Strategy 2 failed: {e}")
    
    return messages


def _is_likely_metadata(text: str) -> bool:
    """
    Check if text looks like metadata rather than conversation content.
    """
    metadata_indicators = [
        len(text) < 50,
        'ChatGPT' in text and len(text) < 100,
        'OpenAI' in text,
        'Terms' in text and 'Privacy' in text,
        text.count('\n') > len(text) / 20,  # Too many line breaks
        re.search(r'^\d+$', text),  # Just numbers
        'cookie' in text.lower() and len(text) < 200,
    ]
    
    return any(metadata_indicators)


def _is_likely_user_message(text: str) -> bool:
    """
    Determine if content is likely from a user based on patterns.
    """
    user_indicators = [
        '?' in text,  # Questions are often from users
        text.startswith(('I ', 'Can you', 'How do', 'What is', 'Please')),
        'help me' in text.lower(),
        'explain' in text.lower(),
        len(text) < 500,  # User messages tend to be shorter
    ]
    
    ai_indicators = [
        text.startswith(('I understand', 'Certainly', 'Here\'s', 'Based on')),
        'analysis' in text.lower(),
        'however' in text.lower(),
        'therefore' in text.lower(),
        len(text) > 1000,  # AI responses tend to be longer
    ]
    
    user_score = sum(1 for indicator in user_indicators if indicator)
    ai_score = sum(1 for indicator in ai_indicators if indicator)
    
    return user_score > ai_score


def _format_conversation(messages: List[Dict[str, str]]) -> str:
    """
    Format extracted messages into a readable conversation transcript.
    """
    print(f"FORMATTING DEBUG: Received {len(messages)} messages to format")
    if messages:
        print(f"First message: {messages[0]['role']} - {messages[0]['content'][:100]}...")
        print(f"Last message: {messages[-1]['role']} - {messages[-1]['content'][:100]}...")
    
    if not messages:
        return "No conversation messages found"
    
    formatted = []
    for i, msg in enumerate(messages):
        role = msg.get('role', 'unknown').title()
        content = msg.get('content', '')
        
        if content and len(content) > 10:
            formatted.append(f"{role}:\n{content}")
            if i < 3:  # Debug first few
                print(f"  Formatted message {i+1}: {role} - {content[:50]}...")
    
    if not formatted:
        return "No valid conversation content found"
    
    print(f"FORMATTING DEBUG: Successfully formatted {len(formatted)} messages")
    return "\n\n" + ("\n\n" + "="*80 + "\n\n").join(formatted)


def main():
    """Test the visual extractor."""
    ## roadmap convo: https://chatgpt.com/share/684b6af3-fc08-8009-b864-a0b6761b22d0
    ## LONG Voice Poet convo: https://chatgpt.com/share/684b7830-18f8-8009-adda-d13c18235e79
    test_url = "https://chatgpt.com/share/684b7830-18f8-8009-adda-d13c18235e79"
    
    print("Visual ChatGPT Share Link Extractor")
    print("=" * 50)
    print(f"Extracting from: {test_url}")
    print()
    
    # Try Playwright with enhanced scrolling
    print("Trying Playwright method with enhanced scrolling...")
    transcript = extract_conversation_visually(test_url, method="playwright")
    
    if "Error" in transcript or "Could not find" in transcript:
        print("Playwright failed, trying Selenium...")
        transcript = extract_conversation_visually(test_url, method="selenium")
    
    print(transcript)
    
    print("\n" + "=" * 50)
    print(f"Extracted {len(transcript)} characters")
    print("Done!")


if __name__ == "__main__":
    main() 