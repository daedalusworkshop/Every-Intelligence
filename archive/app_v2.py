import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
from query_system import ArticleQuerySystem
from chatgptReader import ChatGPTReader
import json
from typing import List, Dict, Any

# Load environment variables
load_dotenv()

# Initialize systems
client = AsyncOpenAI()
query_system = ArticleQuerySystem()
reader = ChatGPTReader()

# =============================================================================
# LEGO BLOCKS - Compose these however you want
# =============================================================================

async def extract_conversation(chatgpt_url: str) -> str:
    """Block 1: ChatGPT URL → conversation text"""
    return await reader.extract_conversation(chatgpt_url)

async def generate_search_queries(conversation_text: str) -> List[str]:
    """Block 2: Conversation → search queries that actually relate to the conversation"""
    
    prompt = f"""From this conversation, generate 8-12 search queries that would find articles this person would find intellectually resonant.

CONVERSATION:
{conversation_text}

Generate queries that capture:
- The specific problems/challenges they're discussing
- Their way of thinking about things
- The intellectual frameworks they're using
- The emotions/tensions they're experiencing
- The specific domain knowledge they need

Each query should be 1-3 sentences that would match similar thinking in Every.to articles.

Return as a JSON object with a "queries" key containing an array of strings."""

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a search query generator. Return ONLY a JSON array of strings. Each string should be a search query that captures how this specific person thinks, not generic topics."},
            {"role": "user", "content": prompt + "\n\nReturn format: [\"query 1\", \"query 2\", \"query 3\", ...]"}
        ],
        temperature=0.6,
        max_tokens=800,
        response_format={"type": "json_object"}
    )
    
    # Parse response into list
    queries = [q.strip() for q in response.choices[0].message.content.split('\n') if q.strip()]
    return queries

async def search_articles(queries: list[str], articles_per_query: int = 5) -> list[dict]:
    """Block 3: Search queries → candidate articles"""
    
    all_articles = []
    for query in queries:
        results = query_system.query(query, top_k=articles_per_query, include_preview=True, deduplicate=True)
        all_articles.extend(results)
    
    # Deduplicate by URL, keeping highest scoring version
    seen_urls = {}
    for article in all_articles:
        url = article['url']
        if url not in seen_urls or article['score'] > seen_urls[url]['score']:
            seen_urls[url] = article
    
    return list(seen_urls.values())

async def select_resonant_articles(conversation_text: str, candidate_articles: list[dict], num_select: int = 5) -> str:
    """Block 4: Conversation + candidate articles → resonant selections"""
    
    # Format articles for LLM
    formatted_articles = []
    for i, article in enumerate(candidate_articles, 1):
        formatted_articles.append(f"""
Article {i}:
Title: {article['title']}
Author: {article['author']}
Preview: {article.get('preview', 'No preview available')}
Relevance Score: {article['score']:.3f}
""")
    
    articles_text = "\n---\n".join(formatted_articles)
    
    prompt = f"""You are an expert at intellectual matchmaking.

Here's someone's conversation:
{conversation_text}

Here are {len(candidate_articles)} candidate articles:
{articles_text}

Select the {num_select} articles that would most deeply resonate with this specific person based on their conversation.

Look for resonance in:
- How they think and approach problems
- Their current intellectual/emotional state  
- What would make them feel understood
- Ideas that would genuinely help their specific situation

For each selected article, explain the resonance connection.

ONLY reference articles from the list above. Do NOT invent articles."""

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert at intellectual matchmaking. Select articles that would resonate with this specific person's way of thinking."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    
    return response.choices[0].message.content

# =============================================================================
# SIMPLE COMPOSITIONS - Examples of how to use the blocks
# =============================================================================

async def simple_pipeline(chatgpt_url: str) -> dict:
    """Basic composition: URL → queries → search → select → output"""
    
    conversation = await extract_conversation(chatgpt_url)
    queries = await generate_search_queries(conversation)
    candidates = await search_articles(queries)
    resonant = await select_resonant_articles(conversation, candidates)
    
    return {
        "conversation_length": len(conversation),
        "queries_generated": len(queries),
        "candidates_found": len(candidates),
        "resonant_articles": resonant
    }

async def text_pipeline(conversation_text: str) -> dict:
    """For when you already have the conversation text"""
    
    queries = await generate_search_queries(conversation_text)
    candidates = await search_articles(queries)
    resonant = await select_resonant_articles(conversation_text, candidates)
    
    return {
        "queries_generated": len(queries),
        "candidates_found": len(candidates),
        "resonant_articles": resonant
    }

async def debug_pipeline(chatgpt_url: str) -> dict:
    """See all the intermediate steps"""
    
    print("🔄 Extracting conversation...")
    conversation = await extract_conversation(chatgpt_url)
    print(f"✅ Got {len(conversation)} characters")
    
    print("\n🧠 Generating search queries...")
    queries = await generate_search_queries(conversation)
    print(f"✅ Generated {len(queries)} queries:")
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")
    
    print("\n🔍 Searching for articles...")
    candidates = await search_articles(queries)
    print(f"✅ Found {len(candidates)} unique articles")
    
    print("\n💫 Selecting resonant matches...")
    resonant = await select_resonant_articles(conversation, candidates)
    print("✅ Selected resonant articles")
    
    return {
        "conversation": conversation[:500] + "..." if len(conversation) > 500 else conversation,
        "queries": queries,
        "candidates": candidates,
        "resonant_articles": resonant
    }

# =============================================================================
# MAIN - Choose your own adventure
# =============================================================================

async def main():
    print("🧱 LEGO BLOCKS - Conversation Resonance Matching")
    print("=" * 50)
    
    choice = input("\nWhat do you want to do?\n1. Simple pipeline\n2. Debug pipeline\n3. Text input\nChoice: ")
    
    if choice == "3":
        print("\nPaste your conversation text (Ctrl+D when done):")
        lines = []
        try:
            while True:
                lines.append(input())
        except EOFError:
            pass
        conversation_text = "\n".join(lines)
        result = await text_pipeline(conversation_text)
        
    else:
        chatgpt_url = input("\nChatGPT URL: ").strip()
        if choice == "2":
            result = await debug_pipeline(chatgpt_url)
        else:
            result = await simple_pipeline(chatgpt_url)
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"Queries: {result['queries_generated']}")
    print(f"Candidates: {result['candidates_found']}")
    print("\n💫 RESONANT ARTICLES:")
    print(result['resonant_articles'])

if __name__ == '__main__':
    asyncio.run(main()) 