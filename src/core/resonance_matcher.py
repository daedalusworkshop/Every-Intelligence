#!/usr/bin/env python3
import asyncio
import argparse
import time
import json
from typing import List, Dict
from datetime import datetime
from openai import AsyncOpenAI
from dotenv import load_dotenv
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.search.article_search import ArticleQuerySystem
from src.extractors.conversation_extractor import ChatGPTReader

load_dotenv()

class KISSResonanceMatcher:
    def __init__(self):
        self.openai_client = AsyncOpenAI()
        self.article_search = ArticleQuerySystem()
        self.conversation_reader = ChatGPTReader()
        # Load scraped articles for image URL enrichment
        self._load_scraped_articles()
        
    def _load_scraped_articles(self):
        """Load the original scraped articles to get image URLs"""
        try:
            with open('data/articles.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
            articles = data.get('articles', [])
            
            # Create a URL -> image_url mapping
            self.url_to_image = {}
            for article in articles:
                url = article.get('url', '')
                images = article.get('images', [])
                # Find the first cover image
                cover_image = None
                for image in images:
                    if image.get('type') == 'cover' and image.get('url'):
                        cover_image = image['url']
                        break
                if url and cover_image:
                    self.url_to_image[url] = cover_image
                    
            print(f"📸 Loaded image URLs for {len(self.url_to_image)} articles")
        except Exception as e:
            print(f"⚠️ Could not load scraped articles for image enrichment: {e}")
            self.url_to_image = {}
    
    def _enrich_with_images(self, articles: List[Dict]) -> List[Dict]:
        """Enrich articles with image URLs from scraped data"""
        for article in articles:
            url = article.get('url', '')
            if url in self.url_to_image:
                article['image_url'] = self.url_to_image[url]
            elif not article.get('image_url'):
                article['image_url'] = ''  # Ensure the field exists
        return articles
    
    async def extract_conversation(self, url: str, progress_callback=None) -> str:
        if progress_callback:
            progress_callback("Connecting to ChatGPT...")
        conversation_text = await self.conversation_reader.extract_conversation(url)
        if progress_callback:
            progress_callback("Conversation extracted successfully")
        return conversation_text
    
    def search_articles(self, conversation: str, top_k: int = 25, progress_callback=None) -> List[Dict]:    
        if progress_callback:
            progress_callback("Diving into Every's knowledge vault...")
        
        articles = self.article_search.query(
            question=conversation,
            top_k=top_k,
            include_preview=True,
            deduplicate=True
        )
        
        if progress_callback:
            progress_callback(f"Found {len(articles)} resonant articles")
        
        articles = self._enrich_with_images(articles)
        
        if progress_callback:
            progress_callback("Finding accompanying thumbnails...")
            
        return articles
    
    async def generate_insights(self, conversation: str, articles: List[Dict], progress_callback=None) -> str:
        if not articles:
            return "No articles found for this conversation."
        
        if progress_callback:
            progress_callback("Preparing articles for AI analysis...")
            
        # Format articles
        formatted = []
        for i, article in enumerate(articles, 1):
            formatted.append(
                f"{i}. **{article['title']}** by {article['author']}\n"
                f"   Full Content: {article.get('preview', 'No content available')}\n"
                f"   URL: {article['url']}\n"
                f"   Image URL: {article.get('image_url', 'No image available')}\n"
            )
        formatted_articles = "\n".join(formatted)
        
        # Build prompt with current date awareness
        current_date = datetime.now().strftime("%B %d, %Y")
        prompt = f"""Today is {current_date}. Your task is to analyze the user's CONVERSATION and the provided RELEVANT ARTICLES and find genuine, helpful connections. Since AI timelines move fast, prioritize more recent articles (2025 > 2024 > 2023) unless the content is timeless.



For each strong connection you find, you will contribute an object to a JSON array. Your entire output must be a single, valid JSON array of these objects.

Each JSON object must have the following structure:



hook: A single, insightful question or observation that gets to the heart of the user's struggle. This serves as the headline for the connection.

bridge: A paragraph of 2-3 concise sentences (around 55-70 words) that expands on the hook, explaining how the article connects to the human. Weave in the author's name naturally. A quote is not required, but use one if it's powerful.



metadata: A nested object containing the article's data. It must include the following keys: title, author, link, and image_url.



Focus on making the hook and bridge feel like a cohesive, natural thought from a helpful colleague. Skip weak connections.

CONVERSATION:

{conversation}

RELEVANT ARTICLES:

{formatted_articles}



Your final output should be a single JSON array, like this. Do not include any text before or after the array."""
        
        try:
            if progress_callback:
                progress_callback("AI is in deep thought...")
                
            response = await self.openai_client.chat.completions.create(
                model="o3",
                messages=[
                    {"role": "system", "content": "You are the 'Chief Resonance Officer' at Every. You are not a search engine. You are an empathetic and deeply-read curator. Your job is to listen carefully to what a person is thinking about and make them feel seen by connecting their thoughts to the wisdom in our archives. You are a guide and a conversation partner."},
                    {"role": "user", "content": prompt}
                ],
            )
            
            if progress_callback:
                progress_callback("Crafting your personal resonance map...")
            
            result = response.choices[0].message.content
            return result or "No insights could be generated from the available articles."
        except Exception as e:
            return f"Error generating insights: {e}"

    async def process(self, url: str = None, text: str = None, progress_callback=None) -> str:
        if progress_callback:
            progress_callback("Starting your resonance journey...")
            
        if url:
            conversation = await self.extract_conversation(url, progress_callback)
        else:
            conversation = text
            if progress_callback:
                progress_callback("Processing your conversation text...")
            
        articles = self.search_articles(conversation, progress_callback=progress_callback)
        insights = await self.generate_insights(conversation, articles, progress_callback)
        
        if progress_callback:
            progress_callback("Ready! Your insights await...")
            
        return insights

def print_insights(insights: str, elapsed_time: float = None):
    print(f"\n{'='*60}")
    print("RESONANT INSIGHTS:")
    if elapsed_time is not None:
        print(f"⏱️  Generated in {elapsed_time:.2f}s")
    print('='*60)
    if insights and insights.strip():
        print(insights)
    else:
        print("⚠️  No insights generated")

async def main():
    parser = argparse.ArgumentParser(description="KISS Conversation Resonance Matching")
    parser.add_argument("url", nargs="?", help="ChatGPT conversation URL")
    parser.add_argument("--text", help="Direct conversation text input")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    matcher = KISSResonanceMatcher()
    
    try:
        if args.interactive:
            print("🎯 KISS Conversation Resonance Matcher")
            print("Enter 'url' for URL mode, 'text' for text mode, or 'quit' to exit")
            
            while True:
                try:
                    mode = input("\nMode (url/text/quit): ").strip().lower()
                except EOFError:
                    break
                
                if mode in ['quit', 'q', 'exit']:
                    break
                elif mode == 'url':
                    try:
                        url = input("ChatGPT URL: ").strip()
                        if url:
                            start_time = time.perf_counter()
                            insights = await matcher.process(url=url)
                            elapsed_time = time.perf_counter() - start_time
                            print_insights(insights, elapsed_time)
                    except EOFError:
                        break
                elif mode == 'text':
                    try:
                        print("Paste your conversation text (press Enter twice when done):")
                        lines = []
                        while True:
                            line = input()
                            if line == "" and lines and lines[-1] == "":
                                break
                            lines.append(line)
                        
                        text = "\n".join(lines[:-1])
                        if text.strip():
                            start_time = time.perf_counter()
                            insights = await matcher.process(text=text)
                            elapsed_time = time.perf_counter() - start_time
                            print_insights(insights, elapsed_time)
                    except EOFError:
                        break
                else:
                    print("Please enter 'url', 'text', or 'quit'")
                    
        elif args.text:
            start_time = time.perf_counter()
            insights = await matcher.process(text=args.text)
            elapsed_time = time.perf_counter() - start_time
            print_insights(insights, elapsed_time)
            
        elif args.url:
            start_time = time.perf_counter()
            insights = await matcher.process(url=args.url)
            elapsed_time = time.perf_counter() - start_time
            print_insights(insights, elapsed_time)
            
        else:
            parser.print_help()
            
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(asyncio.run(main())) 