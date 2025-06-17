#!/usr/bin/env python3
"""
Comparison: requests vs browser automation
==========================================

This shows why we need browser automation for ChatGPT share links.
"""

import requests
from playwright.sync_api import sync_playwright


def test_requests_approach(url):
    """Try to get the page with simple requests (like we did before)."""
    print("=== TESTING REQUESTS APPROACH ===")
    
    try:
        response = requests.get(url)
        html_content = response.text
        
        print(f"Status code: {response.status_code}")
        print(f"Content length: {len(html_content)} characters")
        print(f"First 500 characters:")
        print(html_content[:500])
        print("...")
        
        # Look for our special attribute
        if 'data-message-author-role' in html_content:
            print("✅ Found message markers!")
        else:
            print("❌ No message markers found")
            
        # Look for actual conversation content
        if 'Before we begin setting this up' in html_content:
            print("✅ Found conversation content!")
        else:
            print("❌ No conversation content found")
            
    except Exception as e:
        print(f"Error: {e}")


def test_browser_approach(url):
    """Try to get the page with browser automation."""
    print("\n=== TESTING BROWSER APPROACH ===")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, wait_until='networkidle')
            
            # Wait for messages to load
            page.wait_for_selector('[data-message-author-role]', timeout=10000)
            
            # Get the HTML after JavaScript runs
            html_content = page.content()
            
            print(f"Content length: {len(html_content)} characters")
            
            # Look for our special attribute
            message_elements = page.query_selector_all('[data-message-author-role]')
            print(f"✅ Found {len(message_elements)} message elements!")
            
            # Look for actual conversation content
            if message_elements:
                first_message = message_elements[0].inner_text()
                print(f"✅ First message content: {first_message[:100]}...")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()


def main():
    url = "https://chatgpt.com/share/684b7830-18f8-8009-adda-d13c18235e79"
    
    print("Comparing requests vs browser automation")
    print("=" * 50)
    
    test_requests_approach(url)
    test_browser_approach(url)


if __name__ == "__main__":
    main() 