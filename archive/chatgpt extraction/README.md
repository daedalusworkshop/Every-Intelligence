# ChatGPT Share Link Parser

A robust Python parser for extracting conversations from ChatGPT share links. This parser uses structural analysis of ChatGPT's data format rather than fragile content-based heuristics.

## 🚀 Quick Start

```python
from final_parser import extract_chatgpt_conversation

# Parse a ChatGPT share link HTML file
conversation = extract_chatgpt_conversation('chatgpt_share.html')

# Access the conversation data
print(f"Title: {conversation['title']}")
print(f"Created: {conversation['create_time_readable']}")

for message in conversation['messages']:
    print(f"{message['role'].upper()}: {message['content'][:100]}...")
```

## 📁 Project Structure

```
chatgpt extraction/
├── final_parser.py              # Production-ready parser
├── chatgpt_share_parser.py      # Alternative parser implementation
├── test_parser.py               # Test suite
├── TECHNICAL_DOCUMENTATION.md   # Detailed technical analysis
├── README.md                    # This file
│
├── analyze_structure.py         # Data structure analysis tool
├── structure_analyzer.py        # Role encoding analyzer
├── debug_parser.py             # Debug version with verbose output
│
└── chatgpt_response.html       # Example ChatGPT share link
```

## 🔍 Key Features

- **Structural Parsing**: Extracts data based on ChatGPT's internal data structure
- **Role Detection**: Accurately identifies user vs assistant messages using discovered numeric identifiers
- **Robust Fallback**: Content-based extraction when structural parsing fails
- **Clean Output**: Handles escape sequences, formatting, and metadata
- **Error Handling**: Graceful handling of invalid or malformed input

## 🛠️ Technical Details

### How ChatGPT Embeds Data

ChatGPT share links embed conversation data using React Server Components:

```javascript
window.__reactRouterContext.streamController.enqueue("escaped_json_data");
```

### Key Discoveries

1. **Role Identifiers**:
   - User messages: `"_2210": 18`
   - Assistant messages: `"_2210": 2280`

2. **Message Structure**:
   ```
   timestamp, {metadata}, [content_id], "message content"
   ```

3. **Content Storage**:
   Messages are stored as arrays with numeric IDs: `[2252], "content"`

### Parser Algorithm

1. Extract embedded JSON from `streamController.enqueue()`
2. Decode multiple levels of escaping
3. Extract content blocks using pattern matching
4. Determine roles using numeric identifiers
5. Associate timestamps and metadata
6. Return structured conversation object

## 📊 Testing

Run the test suite:

```bash
python test_parser.py
```

Test coverage includes:
- ✓ Basic extraction functionality
- ✓ Content accuracy verification
- ✓ Error handling and robustness
- ✓ Edge cases and malformed input

## 🚨 Limitations & Considerations

### Current Limitations

- Requires the full HTML of the share link (not just the URL)
- Role detection depends on specific numeric identifiers that may change
- May need updates if ChatGPT changes their data format

### Future-Proofing

The parser includes multiple fallback strategies:
1. Primary: Structural parsing with role identifiers
2. Secondary: Content-based role detection
3. Tertiary: Position-based role assignment

## 🔄 Handling Format Changes

If ChatGPT changes their format:

1. **Check Role IDs**: The numeric identifiers (18, 2280) may change
2. **Update Patterns**: Message structure patterns may need adjustment
3. **Test Fallbacks**: Content-based detection should still work

## 📖 Usage Examples

### Basic Usage

```python
# Extract conversation from file
conversation = extract_chatgpt_conversation('share_link.html')

# Print all messages
for msg in conversation['messages']:
    print(f"{msg['role']}: {msg['content']}")
```

### Advanced Usage

```python
# Access timestamps
for msg in conversation['messages']:
    if 'timestamp_readable' in msg:
        print(f"Time: {msg['timestamp_readable']}")
        print(f"Role: {msg['role']}")
        print(f"Content: {msg['content'][:200]}...")
```

### Error Handling

```python
try:
    conversation = extract_chatgpt_conversation('file.html')
except ValueError as e:
    print(f"Invalid ChatGPT share link: {e}")
```

## 🤝 Contributing

To contribute improvements:

1. Test with various ChatGPT share links
2. Document any new patterns discovered
3. Update role identifiers if they change
4. Add test cases for new scenarios

## 📝 License

This project is for educational and research purposes. Please respect OpenAI's terms of service when using this parser.

## 🔗 Related Documentation

- [Technical Documentation](TECHNICAL_DOCUMENTATION.md) - Deep dive into ChatGPT's data structure
- [Test Suite](test_parser.py) - Comprehensive testing examples
- [Debug Parser](debug_parser.py) - Verbose output for troubleshooting