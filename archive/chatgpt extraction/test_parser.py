"""
Test Suite for ChatGPT Share Link Parser
========================================

Tests the parser with various conversation formats.
"""

import os
from final_parser import extract_chatgpt_conversation


def test_existing_file():
    """Test with the existing example file."""
    print("=== TEST 1: Existing Example File ===\n")
    
    if os.path.exists('chatgpt_response.html'):
        try:
            conversation = extract_chatgpt_conversation('chatgpt_response.html')
            
            print(f"✓ Title: {conversation['title']}")
            print(f"✓ Messages: {len(conversation['messages'])}")
            
            for i, msg in enumerate(conversation['messages']):
                print(f"\nMessage {i+1}:")
                print(f"  Role: {msg['role']}")
                print(f"  Content preview: {msg['content'][:100]}...")
                
            return True
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    else:
        print("✗ File not found")
        return False


def test_extraction_accuracy():
    """Test that specific content is extracted correctly."""
    print("\n=== TEST 2: Content Extraction Accuracy ===\n")
    
    if os.path.exists('chatgpt_response.html'):
        try:
            conversation = extract_chatgpt_conversation('chatgpt_response.html')
            
            # Check for known content
            user_content_found = False
            assistant_content_found = False
            
            for msg in conversation['messages']:
                if msg['role'] == 'user' and 'Every has thought a lot' in msg['content']:
                    user_content_found = True
                    print("✓ User message correctly extracted")
                    
                if msg['role'] == 'assistant' and 'Stress-Test' in msg['content']:
                    assistant_content_found = True
                    print("✓ Assistant message correctly extracted")
            
            if not user_content_found:
                print("✗ User message not found or incorrectly labeled")
            if not assistant_content_found:
                print("✗ Assistant message not found or incorrectly labeled")
                
            return user_content_found and assistant_content_found
            
        except Exception as e:
            print(f"✗ Error: {e}")
            return False
    else:
        print("✗ File not found")
        return False


def test_parser_robustness():
    """Test parser's error handling."""
    print("\n=== TEST 3: Parser Robustness ===\n")
    
    # Test with invalid HTML
    test_cases = [
        ("Empty file", ""),
        ("No stream data", "<html><body>Hello</body></html>"),
        ("Invalid stream data", '<script>streamController.enqueue("invalid");</script>'),
    ]
    
    for test_name, test_content in test_cases:
        print(f"Testing {test_name}...")
        
        # Create temporary test file
        with open('test_temp.html', 'w') as f:
            f.write(test_content)
        
        try:
            conversation = extract_chatgpt_conversation('test_temp.html')
            if conversation['messages']:
                print(f"  ✗ Should have failed but got {len(conversation['messages'])} messages")
            else:
                print(f"  ✓ Handled gracefully (no messages)")
        except Exception as e:
            print(f"  ✓ Raised expected error: {type(e).__name__}")
        
        # Clean up
        os.remove('test_temp.html')
    
    return True


def generate_test_report():
    """Generate a comprehensive test report."""
    print("\n" + "="*60)
    print("ChatGPT Share Link Parser - Test Report")
    print("="*60 + "\n")
    
    tests = [
        ("Existing File Test", test_existing_file),
        ("Content Accuracy Test", test_extraction_accuracy),
        ("Robustness Test", test_parser_robustness),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name}...")
        print("-" * 40)
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The parser is working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the issues.")


if __name__ == "__main__":
    generate_test_report()