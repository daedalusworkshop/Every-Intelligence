#!/usr/bin/env python3
"""
Article Vectorizer for Every.to Scraped Content
==============================================

This script takes the scraped articles and vectorizes them into Pinecone
for semantic search and retrieval.

Key Features:
- Handles large articles by chunking them intelligently
- Preserves metadata for filtering and context
- Batches uploads for efficiency
- Progress tracking and resumable processing
- Validation and testing utilities

Usage:
    python vectorize_articles.py --chunk-size 1000 --overlap 200
    python vectorize_articles.py --test-mode --max-articles 10
    python vectorize_articles.py --validate-index
"""

import json
import logging
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import argparse
import re
import time

from pinecone import Pinecone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from tenacity import retry, stop_after_attempt, wait_exponential

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
INDEX_NAME = "every-to-articles"
DEFAULT_CHUNK_SIZE = 1000  # characters per chunk
DEFAULT_OVERLAP = 200      # character overlap between chunks
BATCH_SIZE = 96           # records per batch upload (Pinecone limit for text records)

@dataclass
class ChunkMetadata:
    """Metadata preserved with each chunk"""
    article_url: str
    title: str
    author: str
    column: str
    publication_date: str
    word_count: int
    chunk_index: int
    total_chunks: int
    chunk_type: str  # 'title_only', 'content', 'full_text'

class ArticleVectorizer:
    """
    Handles vectorization of scraped articles into Pinecone
    """
    
    def __init__(self, api_key: str = PINECONE_API_KEY, index_name: str = INDEX_NAME):
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.index = None
        
    def setup_index(self, force_recreate: bool = False) -> None:
        """
        Create or connect to the Pinecone index
        
        Args:
            force_recreate: Delete and recreate index if it exists
        """
        logger.info(f"Setting up Pinecone index: {self.index_name}")
        
        # Delete existing index if force_recreate
        if force_recreate and self.pc.has_index(self.index_name):
            logger.warning(f"Deleting existing index: {self.index_name}")
            self.pc.delete_index(self.index_name)
            time.sleep(10)  # Wait for deletion to complete
        
        # Create index if it doesn't exist
        if not self.pc.has_index(self.index_name):
            logger.info(f"Creating new index: {self.index_name}")
            self.pc.create_index_for_model(
                name=self.index_name,
                cloud="aws",
                region="us-east-1",
                embed={
                    "model": "llama-text-embed-v2",
                    "field_map": {"text": "chunk_text"}
                }
            )
            # Wait for index to be ready
            time.sleep(30)
        
        self.index = self.pc.Index(self.index_name)
        logger.info("✅ Index setup complete")
        
    def load_articles(self, filepath: str = "scraped_articles.json") -> List[Dict]:
        """Load articles from the scraped JSON file"""
        logger.info(f"Loading articles from {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        articles = data.get('articles', [])
        logger.info(f"✅ Loaded {len(articles)} articles")
        return articles
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text for embedding"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters that might interfere with embedding
        text = re.sub(r'[^\w\s\-.,!?;:()\[\]"]', '', text)
        return text.strip()
    
    def chunk_article(self, article: Dict, chunk_size: int = DEFAULT_CHUNK_SIZE, 
                     overlap: int = DEFAULT_OVERLAP) -> List[Dict]:
        """
        Break an article into chunks for vectorization
        
        Strategy:
        1. Create a title-only chunk (for title-based searches)
        2. Chunk the content if it's long
        3. Preserve all metadata with each chunk
        """
        chunks = []
        content = article.get('content', '')
        title = article.get('title', '')
        
        # Clean the content
        content = self.clean_text(content)
        title = self.clean_text(title)
        
        # Ensure all metadata fields are strings (Pinecone requirement)
        def safe_string(value) -> str:
            """Convert any value to a safe string for Pinecone metadata"""
            if value is None:
                return "Unknown"
            return str(value).strip() or "Unknown"
        
        # Extract the first cover image URL if available
        def extract_image_url(article: Dict) -> str:
            """Extract the first cover image URL from the article's images array"""
            images = article.get('images', [])
            for image in images:
                if image.get('type') == 'cover' and image.get('url'):
                    return image['url']
            return ""
        
        image_url = extract_image_url(article)
        
        # Always create a title-focused chunk for title-based searches
        title_chunk = {
            "chunk_text": f"Title: {title}",
            "article_url": safe_string(article.get('url', '')),
            "title": safe_string(title),
            "author": safe_string(article.get('author', '')),
            "column": safe_string(article.get('column', '')),
            "publication_date": safe_string(article.get('publication_date', '')),
            "image_url": safe_string(image_url),
            "word_count": article.get('word_count', 0) or 0,
            "chunk_index": 0,
            "total_chunks": 1,  # Will be updated later
            "chunk_type": 'title_only'
        }
        chunks.append(title_chunk)
        
        # If content is short enough, create one full chunk
        if len(content) <= chunk_size:
            full_chunk = {
                "chunk_text": f"Title: {title}\n\nContent: {content}",
                "article_url": safe_string(article.get('url', '')),
                "title": safe_string(title),
                "author": safe_string(article.get('author', '')),
                "column": safe_string(article.get('column', '')),
                "publication_date": safe_string(article.get('publication_date', '')),
                "image_url": safe_string(image_url),
                "word_count": article.get('word_count', 0) or 0,
                "chunk_index": 1,
                "total_chunks": 2,  # title + full content
                "chunk_type": 'full_text'
            }
            chunks.append(full_chunk)
        else:
            # Chunk the content
            content_chunks = self._create_content_chunks(content, chunk_size, overlap)
            
            for i, chunk_content in enumerate(content_chunks):
                content_chunk = {
                    "chunk_text": chunk_content,
                    "article_url": safe_string(article.get('url', '')),
                    "title": safe_string(title),
                    "author": safe_string(article.get('author', '')),
                    "column": safe_string(article.get('column', '')),
                    "publication_date": safe_string(article.get('publication_date', '')),
                    "image_url": safe_string(image_url),
                    "word_count": article.get('word_count', 0) or 0,
                    "chunk_index": i + 1,  # +1 because title chunk is index 0
                    "total_chunks": len(content_chunks) + 1,
                    "chunk_type": 'content'
                }
                chunks.append(content_chunk)
        
        # Update total_chunks for the title chunk
        chunks[0]["total_chunks"] = len(chunks)
        
        return chunks
    
    def _create_content_chunks(self, content: str, chunk_size: int, overlap: int) -> List[str]:
        """Split content into overlapping chunks"""
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        start = 0
        
        while start < len(content):
            # Find the end of this chunk
            end = start + chunk_size
            
            # If this isn't the last chunk, try to break at a sentence or word boundary
            if end < len(content):
                # Look for sentence boundary within the last 100 characters
                sentence_break = content.rfind('.', start, end - 100)
                if sentence_break > start:
                    end = sentence_break + 1
                else:
                    # Look for word boundary
                    word_break = content.rfind(' ', start, end - 50)
                    if word_break > start:
                        end = word_break
            
            chunk = content[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move start position (with overlap)
            start = max(start + chunk_size - overlap, end)
        
        return chunks
    
    def vectorize_articles(self, articles: List[Dict], chunk_size: int = DEFAULT_CHUNK_SIZE,
                          overlap: int = DEFAULT_OVERLAP, max_articles: Optional[int] = None) -> None:
        """
        Vectorize all articles and upload to Pinecone
        
        Args:
            articles: List of article dictionaries
            chunk_size: Maximum characters per chunk
            overlap: Character overlap between chunks
            max_articles: Limit for testing (None = all articles)
        """
        if max_articles:
            articles = articles[:max_articles]
            logger.info(f"Limited to {max_articles} articles for testing")
        
        logger.info(f"Starting vectorization of {len(articles)} articles...")
        
        all_chunks = []
        failed_articles = []
        
        # Process each article
        for i, article in enumerate(articles):
            try:
                logger.info(f"Processing article {i+1}/{len(articles)}: {article.get('title', 'Unknown')[:50]}...")
                
                # Create chunks for this article
                chunks = self.chunk_article(article, chunk_size, overlap)
                
                # Add unique IDs to each chunk
                for j, chunk in enumerate(chunks):
                    chunk_id = f"article_{i}_{j}"
                    chunk["_id"] = chunk_id
                
                all_chunks.extend(chunks)
                
                # Log progress
                if (i + 1) % 50 == 0:
                    logger.info(f"Processed {i+1} articles, created {len(all_chunks)} chunks so far")
                    
            except Exception as e:
                logger.error(f"Failed to process article {i}: {e}")
                failed_articles.append(article.get('url', f'article_{i}'))
        
        logger.info(f"✅ Created {len(all_chunks)} chunks from {len(articles)} articles")
        
        if failed_articles:
            logger.warning(f"Failed to process {len(failed_articles)} articles: {failed_articles}")
        
        # Upload to Pinecone in batches
        self._upload_chunks_in_batches(all_chunks)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        reraise=True
    )
    def _upload_single_batch(self, batch: List[Dict], batch_num: int, total_batches: int) -> None:
        """Upload a single batch to Pinecone with retry logic"""
        logger.info(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} chunks)")
        self.index.upsert_records("every-to", batch)
    
    def _upload_chunks_in_batches(self, chunks: List[Dict]) -> None:
        """Upload chunks to Pinecone in batches for efficiency"""
        logger.info(f"Uploading {len(chunks)} chunks to Pinecone in batches of {BATCH_SIZE}...")
        
        total_batches = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE
        successful_batches = 0
        failed_batches = []
        
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            
            try:
                self._upload_single_batch(batch, batch_num, total_batches)
                successful_batches += 1
                
                # Small delay to avoid rate limits
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to upload batch {batch_num} after retries: {e}")
                failed_batches.append(batch_num)
        
        logger.info(f"✅ Upload complete! {successful_batches}/{total_batches} batches successful")
        if failed_batches:
            logger.warning(f"Failed batches: {failed_batches}")
        else:
            logger.info("🎉 All batches uploaded successfully!")
    
    def validate_index(self) -> Dict[str, Any]:
        """Validate the uploaded data and return statistics"""
        logger.info("Validating index...")
        
        stats = self.index.describe_index_stats()
        
        # Test a sample query
        test_query = "artificial intelligence and machine learning"
        search_results = self.index.search(
            namespace="every-to",
            query={
                "top_k": 5,
                "inputs": {
                    'text': test_query
                }
            },
            fields=["title", "author", "column", "chunk_text"]
        )
        
        # Extract matches from the API response
        matches = search_results.get('result', {}).get('hits', [])
        
        validation_report = {
            "index_stats": {
                "total_vector_count": stats.get('total_vector_count', 0),
                "namespace_count": len(stats.get('namespaces', {})),
                "namespaces": {k: {"vector_count": v.get('vector_count', 0)} for k, v in stats.get('namespaces', {}).items()}
            },
            "test_query": test_query,
            "test_results_count": len(matches),
            "sample_results": [
                {
                    "title": match.get('fields', {}).get('title', 'Unknown'),
                    "author": match.get('fields', {}).get('author', 'Unknown'),
                    "score": match.get('_score', 0),
                    "chunk_preview": match.get('fields', {}).get('chunk_text', '')[:100] + "..."
                }
                for match in matches[:3]
            ],
            "validation_time": datetime.now().isoformat()
        }
        
        logger.info(f"✅ Validation complete. Index contains {stats.get('total_vector_count', 0)} vectors")
        return validation_report

def main():
    parser = argparse.ArgumentParser(description="Vectorize Every.to articles for semantic search")
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE,
                       help="Maximum characters per chunk")
    parser.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP,
                       help="Character overlap between chunks")
    parser.add_argument("--max-articles", type=int, default=None,
                       help="Limit number of articles for testing")
    parser.add_argument("--test-mode", action="store_true",
                       help="Run in test mode with 10 articles")
    parser.add_argument("--force-recreate", action="store_true",
                       help="Delete and recreate the index")
    parser.add_argument("--validate-only", action="store_true",
                       help="Only validate existing index")
    parser.add_argument("--articles-file", default="scraped_articles.json",
                       help="Path to scraped articles JSON file")
    
    args = parser.parse_args()
    
    # Initialize vectorizer
    vectorizer = ArticleVectorizer()
    
    if args.test_mode:
        args.max_articles = 10
        logger.info("🧪 Running in test mode with 10 articles")
    
    if args.validate_only:
        vectorizer.setup_index()
        validation_report = vectorizer.validate_index()
        print(json.dumps(validation_report, indent=2))
        return
    
    # Setup index
    vectorizer.setup_index(force_recreate=args.force_recreate)
    
    # Load and vectorize articles
    articles = vectorizer.load_articles(args.articles_file)
    vectorizer.vectorize_articles(
        articles, 
        chunk_size=args.chunk_size,
        overlap=args.overlap,
        max_articles=args.max_articles
    )
    
    # Validate the results
    validation_report = vectorizer.validate_index()
    
    # Save validation report
    with open("vectorization_report.json", "w") as f:
        json.dump(validation_report, f, indent=2)
    
    logger.info("✅ Vectorization complete! Validation report saved to vectorization_report.json")

if __name__ == "__main__":
    main() 