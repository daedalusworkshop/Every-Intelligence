# Every Intelligence - Conversation Resonance Matching

A web application that finds resonant Every.to articles for ChatGPT conversations.

## 🚀 Quick Start

```bash
# Start the server
./start_server.sh

# Visit http://localhost:3000
```

## 📁 Project Structure

### Core Application Files
- `web_server.py` - FastAPI web server (main entry point)
- `kissedApp3.py` - Core application logic and AI matching
- `query_system.py` - Article search and retrieval system
- `chatgptReader.py` - ChatGPT conversation extraction
- `start_server.sh` - Server startup script

### Frontend
- `every_clone.html` - Main landing page
- `every_results2.html` - Results display page
- `every.png`, `CoverImage.png` - UI assets

### Data
- `scraped_articles.json` - Article database (5.2MB)
- `requirements.txt` - Python dependencies

### Utilities
- `data_processing/` - Data preparation scripts (scraper, vectorization)
- `archive/` - Legacy code and experiments
- `every_env/` - Python virtual environment

## 🔧 Technical Stack

- **Backend**: FastAPI + AsyncIO
- **AI**: OpenAI GPT-4 (via API)
- **Search**: Pinecone vector database
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Extraction**: Playwright for web scraping

## 📋 Dependencies

All dependencies are listed in `requirements.txt`. Key components:
- `openai` - AI conversation analysis
- `pinecone` - Vector search
- `fastapi` - Web framework
- `playwright` - Web scraping
- `beautifulsoup4` - HTML parsing

## 🎯 How It Works

1. User submits ChatGPT conversation URL
2. `chatgptReader.py` extracts conversation text
3. `query_system.py` searches for relevant articles via Pinecone
4. `kissedApp3.py` uses GPT-4 to generate resonant insights
5. Results displayed in structured format with article links and images

---

*This application has been cleaned up from multiple experimental versions. All legacy code has been moved to `archive/` or removed.* 