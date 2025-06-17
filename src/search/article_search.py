#!/usr/bin/env python3
"""
KISS Query System for Every.to Articles
======================================

Simple, focused system for querying vectorized articles.
Does one thing well: semantic search with optional deduplication.

Usage:
    python query_system.py "How do I use AI for creative writing?"
    python query_system.py --interactive
"""

import argparse
from pinecone import Pinecone
from typing import List, Dict, Any
import os
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Simple configuration
@dataclass
class Config:
    """Simple configuration container"""
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    INDEX_NAME: str = "every-to-articles"
    NAMESPACE: str = "every-to"
    DEFAULT_TOP_K: int = 5
    BUFFER_MULTIPLIER: int = 6  # How many extra results to fetch for deduplication
    MIN_BUFFER_SIZE: int = 50
    PREVIEW_LENGTH: int = 300

class ArticleQuerySystem:
    """
    Simple semantic search for Every.to articles.
    
    Key principle: Do one thing well - semantic search with clean deduplication.
    """
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.pc = Pinecone(api_key=self.config.PINECONE_API_KEY)
        self.index = self.pc.Index(self.config.INDEX_NAME)
    
    def search(self, question: str, top_k: int = None, deduplicate: bool = True) -> List[Dict[str, Any]]:
        """
        Search for articles matching the question.
        
        Args:
            question: What to search for
            top_k: How many results to return (defaults to config)
            deduplicate: Whether to remove duplicate articles
            
        Returns:
            List of article results, sorted by relevance
        """
        if top_k is None:
            top_k = self.config.DEFAULT_TOP_K
            
        # Fetch results from Pinecone
        raw_results = self._fetch_from_pinecone(question, top_k)
        
        # Process and optionally deduplicate
        if deduplicate:
            return self._deduplicate_articles(raw_results, top_k)
        else:
            return raw_results[:top_k]
    
    def _fetch_from_pinecone(self, question: str, top_k: int) -> List[Dict[str, Any]]:
        """Fetch raw results from Pinecone and convert to simple format."""
        # Calculate buffer size to handle duplicates
        buffer_size = max(self.config.MIN_BUFFER_SIZE, top_k * self.config.BUFFER_MULTIPLIER)
        
        # Single API call to Pinecone
        response = self.index.search(
            namespace=self.config.NAMESPACE,
            query={"top_k": buffer_size, "inputs": {"text": question}},
            fields=["title", "author", "column", "chunk_text", "chunk_type", "article_url", "image_url"]
        )
        
        # Convert to simple format
        results = []
        for match in response.get('result', {}).get('hits', []):
            article = self._convert_match_to_article(match)
            results.append(article)
        
        return results
    
    def _convert_match_to_article(self, match: Dict) -> Dict[str, Any]:
        """Convert a Pinecone match to a simple article dictionary."""
        fields = match.get('fields', {})
        
        article = {
            'title': fields.get('title', 'Unknown Title'),
            'author': fields.get('author', 'Unknown Author'),
            'column': fields.get('column', 'Unknown Column'),
            'url': fields.get('article_url', ''),
            'image_url': fields.get('image_url', ''),
            'score': match.get('_score', 0.0),
            'chunk_type': fields.get('chunk_type', 'content'),
            'preview': self._create_preview(fields.get('chunk_text', ''))
        }
        
        return article
    
    def _create_preview(self, chunk_text: str) -> str:
        """Return full chunk text instead of truncated preview."""
        if not chunk_text:
            return "No preview available"
        
        # Simple rule: if it starts with "Title:", extract content part
        if chunk_text.startswith('Title: '):
            # Look for content after title
            parts = chunk_text.split('\n\nContent: ', 1)
            text = parts[1] if len(parts) > 1 else chunk_text[7:]  # Remove "Title: "
        else:
            text = chunk_text
        
        # Return full text instead of truncating
        return text.strip()
    
    def _deduplicate_articles(self, articles: List[Dict], top_k: int) -> List[Dict]:
        """
        Simple deduplication: keep the best-scoring chunk for each unique article URL.
        
        Strategy:
        1. Group articles by URL
        2. Keep the highest-scoring chunk for each URL
        3. Sort by score and return top K
        """
        # Group by URL, keeping the best score for each
        best_articles = {}
        
        for article in articles:
            url = article['url']
            if not url:  # Skip articles without URLs
                continue
            
            # Keep this article if it's the first or has a better score
            if url not in best_articles or article['score'] > best_articles[url]['score']:
                best_articles[url] = article
        
        # Sort by relevance score and return top K
        sorted_articles = sorted(best_articles.values(), key=lambda x: x['score'], reverse=True)
        return sorted_articles[:top_k]
    
    def print_results(self, results: List[Dict[str, Any]], question: str = ""):
        """Print search results in a clean, readable format."""
        if question:
            print(f"\n🔍 Results for: \"{question}\"")
            print("=" * 60)
        
        if not results:
            print("❌ No results found.")
            return
        
        for i, article in enumerate(results, 1):
            print(f"\n📄 {i}. {article['title']}")
            print(f"   👤 {article['author']} • 📁 {article['column']} • ⭐ {article['score']:.3f}")
            print(f"   📖 {article['preview']}")
            if article['url']:
                print(f"   🔗 {article['url']}")
    
    def interactive_mode(self):
        """Simple interactive mode for testing queries."""
        print("🎯 Every.to Article Search")
        print("Enter your questions (type 'quit' to exit)")
        print("-" * 40)
        
        while True:
            try:
                question = input("\n❓ Question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not question:
                    continue
                
                results = self.search(question)
                self.print_results(results, question)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def suggest_questions(self):
        """Simple question suggestions"""
        suggestions = [
            "How can I use AI to improve my writing?",
            "What are the best practices for working with GPT-4?", 
            "How is AI changing the future of work?",
            "What should I know about AI agents?",
            "How can AI help with creative projects?"
        ]
        
        print("💡 Try asking:")
        for suggestion in suggestions:
            print(f"   • {suggestion}")
    
    # Legacy compatibility methods for backward compatibility
    def query(self, question: str, top_k: int = 5, include_preview: bool = True, deduplicate: bool = True) -> List[Dict[str, Any]]:
        """Legacy method name - maps to search()"""
        return self.search(question, top_k, deduplicate)

def main():
    """Simple CLI interface"""
    parser = argparse.ArgumentParser(description="Search Every.to articles")
    parser.add_argument("question", nargs="?", help="What to search for")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results")
    parser.add_argument("--no-dedupe", action="store_true", help="Show all chunks (no deduplication)")
    
    args = parser.parse_args()
    
    # Create the search system
    search_system = ArticleQuerySystem()
    
    if args.interactive:
        search_system.interactive_mode()
    elif args.question:
        # Perform the search
        results = search_system.search(
            question=args.question,
            top_k=args.top_k,
            deduplicate=not args.no_dedupe
        )
        search_system.print_results(results, args.question)
    else:
        print("Please provide a question or use --interactive mode")
        print("Example: python query_system.py \"How do I use AI for writing?\"")
        search_system.suggest_questions()

if __name__ == "__main__":
    main() 