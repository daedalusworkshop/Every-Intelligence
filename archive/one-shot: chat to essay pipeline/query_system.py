#!/usr/bin/env python3
"""
Query System for Every.to Articles
=================================

This system converts natural language questions into semantic searches
of the vectorized article database.

Usage:
    python query_system.py "How do I use AI for creative writing?"
    python query_system.py --interactive
"""

import argparse
import os
from pinecone import Pinecone
from typing import List, Dict, Any
import sys

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
INDEX_NAME = "every-to-articles"

class ArticleQuerySystem:
    """
    A system for querying vectorized Every.to articles
    """
    
    def __init__(self):
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index = self.pc.Index(INDEX_NAME)
        
    def query(self, question: str, top_k: int = 5, include_preview: bool = True, deduplicate: bool = True) -> List[Dict[str, Any]]:
        """
        Query the article database with a natural language question
        
        Args:
            question: Natural language question
            top_k: Number of results to return
            include_preview: Whether to include text preview
            deduplicate: Whether to deduplicate results by article URL
            
        Returns:
            List of matching articles with metadata
        """
        # Fetch extra results to account for potential duplicates (single API call)
        buffer_size = max(20, top_k * 4)  # Reasonable buffer, minimum 20
        
        search_results = self.index.search(
            namespace="every-to",
            query={
                "top_k": buffer_size,
                "inputs": {
                    'text': question
                }
            },
            fields=["title", "author", "column", "chunk_text", "chunk_type", "article_url"]
        )
        
        matches = search_results.get('result', {}).get('hits', [])
        
        # Process results
        results = []
        seen_urls = set() if deduplicate else None
        
        for match in matches:
            fields = match.get('fields', {})
            url = fields.get('article_url', '')
            
            # Skip duplicates if deduplicating
            if deduplicate and url in seen_urls:
                continue
            
            result = {
                'title': fields.get('title', 'Unknown'),
                'author': fields.get('author', 'Unknown'),
                'column': fields.get('column', 'Unknown'),
                'score': match.get('_score', 0),
                'chunk_type': fields.get('chunk_type', 'Unknown'),
                'url': url,
            }
            
            if include_preview:
                chunk_text = fields.get('chunk_text', '')
                # Clean up the preview text
                if chunk_text.startswith('Title: '):
                    # For title chunks, extract just the content part
                    parts = chunk_text.split('\n\nContent: ', 1)
                    if len(parts) > 1:
                        result['preview'] = parts[1][:300] + "..."
                    else:
                        result['preview'] = chunk_text[7:][:300] + "..."  # Remove "Title: " prefix
                else:
                    result['preview'] = chunk_text[:300] + "..."
            
            results.append(result)
            
            if deduplicate:
                seen_urls.add(url)
            
            # Stop when we have enough results
            if len(results) >= top_k:
                break
        
        return results
    
    def print_results(self, results: List[Dict[str, Any]], question: str, show_chunks: bool = False):
        """Pretty print search results"""
        print(f"\n🔍 Query: \"{question}\"")
        print("=" * 60)
        
        if not results:
            print("❌ No results found.")
            return
        
        for i, result in enumerate(results, 1):
            print(f"\n📄 Result {i} (Relevance: {result['score']:.3f})")
            print(f"   📝 Title: {result['title']}")
            print(f"   ✍️  Author: {result['author']}")
            print(f"   📁 Column: {result['column']}")
            
            if show_chunks:
                print(f"   🧩 Chunk Type: {result['chunk_type']}")
            
            if 'preview' in result:
                print(f"   📖 Preview: {result['preview']}")
            
            if result['url']:
                print(f"   🔗 URL: {result['url']}")
                
        if show_chunks:
            print(f"\n💡 Tip: These are individual chunks from articles. Use --deduplicate to see unique articles only.")
        else:
            print(f"\n💡 Tip: Use --show-chunks to see individual chunks that matched your query.")
    
    def interactive_mode(self):
        """Run in interactive mode for multiple queries"""
        print("🎯 Every.to Article Query System")
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
                
                results = self.query(question)
                self.print_results(results, question)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
    
    def suggest_questions(self):
        """Suggest some interesting questions to try"""
        suggestions = [
            "How can I use AI to improve my writing?",
            "What are the best practices for working with GPT-4?",
            "How is AI changing the future of work?",
            "What should I know about AI agents?",
            "How can AI help with creative projects?",
            "What are the latest developments in AI technology?",
            "How do I get better at prompting AI models?",
            "What are the implications of AI for productivity?"
        ]
        
        print("💡 Try asking questions like:")
        for i, suggestion in enumerate(suggestions, 1):
            print(f"   {i}. {suggestion}")


def main():
    parser = argparse.ArgumentParser(description="Query Every.to articles using natural language")
    parser.add_argument("question", nargs="?", help="Question to search for")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    parser.add_argument("--suggest", action="store_true", help="Show suggested questions")
    parser.add_argument("--show-chunks", action="store_true", help="Show individual chunks instead of deduplicated articles")
    
    args = parser.parse_args()
    
    query_system = ArticleQuerySystem()
    
    if args.suggest:
        query_system.suggest_questions()
        return
    
    if args.interactive:
        query_system.interactive_mode()
    elif args.question:
        # Default is deduplicated results, unless --show-chunks is specified
        deduplicate = not args.show_chunks
        results = query_system.query(args.question, top_k=args.top_k, include_preview=True, deduplicate=deduplicate)
        query_system.print_results(results, args.question, args.show_chunks)
    else:
        print("Please provide a question or use --interactive mode")
        print("Example: python query_system.py \"How do I use AI for writing?\"")
        query_system.suggest_questions()

if __name__ == "__main__":
    main() 