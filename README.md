# Every Intelligence - Conversation Resonance Matching

A web application that finds resonant Every.to articles for ChatGPT conversations.

## 🚀 Quick Start

```bash
# Start the server
./start_server.sh

# Visit http://localhost:3000
```

## 📁 Project Structure

```
├── src/                     # Source code (organized by function)
│   ├── core/               # Core application logic
│   │   └── resonance_matcher.py   # Main AI matching logic
│   ├── web/                # Web server
│   │   └── server.py       # FastAPI server (main entry point)
│   ├── extractors/         # Data extraction
│   │   └── conversation_extractor.py  # ChatGPT conversation extraction
│   └── search/             # Search functionality
│       └── article_search.py       # Article search system
├── frontend/               # User interface
│   ├── index.html         # Main landing page
│   ├── results.html       # Results display page
│   └── assets/            # UI assets
│       ├── logo.png       # Every logo
│       ├── cover.png      # Default article cover
│       └── link-icon.svg  # Link icon
├── data/                  # Application data
│   └── articles.json      # Article database (5.2MB)
├── scripts/               # Utility scripts
│   ├── scraper.py         # Article scraping
│   ├── vectorize.py       # Vector database setup
│   └── vectorization_report.json
├── archive/               # Legacy code and experiments
├── every_env/             # Python virtual environment
├── start_server.sh        # Server startup script
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

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

1. User submits ChatGPT conversation URL via `frontend/index.html`
2. `src/web/server.py` receives the request and orchestrates processing
3. `src/extractors/conversation_extractor.py` extracts conversation text
4. `src/search/article_search.py` searches for relevant articles via Pinecone
5. `src/core/resonance_matcher.py` uses GPT-4 to generate resonant insights
6. Results displayed in `frontend/results.html` with article links and images

---

## 🧹 What's New

This codebase has been completely reorganized for clarity and maintainability:

- **🗂️ Proper folder structure** - Code organized by function (`src/core/`, `src/web/`, etc.)
- **📝 Sensible naming** - No more `kissedApp3.py` or `chatgptReader.py` 
- **🧽 Clean imports** - All modules properly structured as packages
- **📁 Asset organization** - Frontend files and assets in dedicated folders
- **🗄️ Legacy cleanup** - Experimental versions moved to `archive/` or removed

*Ready for production with a professional structure!* 