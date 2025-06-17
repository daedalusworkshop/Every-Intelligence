import asyncio
from openai import AsyncOpenAI
from dotenv import load_dotenv
from query_system import ArticleQuerySystem
from parsing import ConversationAnalyzer
from chatgptReader import ChatGPTReader
import time

# Load environment variables
load_dotenv()

# Initialize systems
client = AsyncOpenAI()
query_system = ArticleQuerySystem()
analyzer = ConversationAnalyzer()
reader = ChatGPTReader()

async def generate_quotations(conversation_text: str, search_results: list) -> str:
    """Transform search results into conversation-aware quotations."""
    
    # Format articles for the LLM
    articles = "\n---\n".join([
        f"Title: {r['title']}\nAuthor: {r['author']}\nPreview: {r.get('preview', '')}\nURL: {r['url']}"
        for r in search_results[:8]
    ])
    
    prompt = f"""Create 3-5 contextual insights from Every.to articles for this conversation:

CONVERSATION:
{conversation_text[:2000]}

RELEVANT ARTICLES:
{articles}

Format each as: "In your conversation about [specific reference], Every's [Author] wrote: '[quote/paraphrase].' This suggests [actionable insight]."

Make it feel like Every is directly responding to their specific challenge."""

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Connect Every.to's knowledge to specific user challenges with contextual quotations."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1500
    )
    
    return response.choices[0].message.content

async def analyze_conversation(conversation_text: str) -> dict:
    """Complete pipeline: conversation → search → quotations."""
    
    # Use existing ensemble search
    ensemble_result = await analyzer.search_with_ensemble(conversation_text)
    top_articles = ensemble_result["top_articles"]
    
    # Generate contextual quotations
    quotations = await generate_quotations(conversation_text, top_articles)
    
    return {
        "quotations": quotations,
        "sources": top_articles[:5],
        "stats": ensemble_result["stats"]
    }

async def process_chatgpt_url(url: str) -> dict:
    """Extract conversation from ChatGPT URL and analyze."""
    conversation = await reader.extract_conversation(url)
    return await analyze_conversation(conversation)

async def process_text(text: str) -> dict:
    """Analyze conversation text directly."""
    return await analyze_conversation(text)

async def flood_zone_resonance_matching(conversation_text: str, search_strategy: str = "ensemble", max_articles: int = 50) -> dict:
    """
    Flood zone with resonance matching: Find articles that would resonate with this person's way of thinking.
    
    Args:
        conversation_text: The full conversation
        search_strategy: "ensemble" (sophisticated) or "simple" (broad queries)
        max_articles: How many articles to give the LLM for selection
    """
    
    start_time = time.time()
    all_articles = []
    
    if search_strategy == "ensemble":
        print("🧠 Using sophisticated ensemble search...")
        # Use the existing sophisticated approach
        ensemble_result = await analyzer.search_with_ensemble(conversation_text)
        
        # Get more articles by running additional queries
        queries = (ensemble_result["content"].analytical_insights + 
                  ensemble_result["content"].narrative_scenarios + 
                  ensemble_result["content"].framework_descriptions + 
                  ensemble_result["content"].problem_statements + 
                  ensemble_result["content"].solution_approaches)
        
        for query in queries:
            results = query_system.query(query, top_k=8, include_preview=True, deduplicate=True)
            all_articles.extend(results)
            
    else:  # simple strategy
        print("⚡ Using simple broad search...")
        # Cast a very wide net with simple, broad queries
        simple_queries = [
            conversation_text[:300],  # First part of conversation
            "AI productivity tools systems",
            "building AI applications",
            "AI product development",
            "artificial intelligence strategy",
            "technology decision making",
            "AI system architecture",
            "creative AI tools",
            "AI workflow optimization",
            "AI product thinking",
            "AI development challenges"
        ]
        
        for query in simple_queries:
            results = query_system.query(query, top_k=12, include_preview=True, deduplicate=True)
            all_articles.extend(results)
    
    # Deduplicate and get top articles by score
    seen_urls = set()
    unique_articles = []
    for article in sorted(all_articles, key=lambda x: x['score'], reverse=True):
        if article['url'] not in seen_urls:
            unique_articles.append(article)
            seen_urls.add(article['url'])
            if len(unique_articles) >= max_articles:
                break
    
    search_time = time.time() - start_time
    print(f"📊 Found {len(unique_articles)} unique articles in {search_time:.2f}s")
    
    # Format articles for resonance matching
    formatted_articles = []
    for i, result in enumerate(unique_articles, 1):
        formatted_articles.append(f"""
Article {i}:
Title: {result['title']}
Author: {result['author']}
Column: {result.get('column', 'Unknown')}
Preview: {result.get('preview', 'No preview available')}
Relevance Score: {result['score']:.3f}
""")
    
    articles_text = "\n---\n".join(formatted_articles)
    
    # The resonance matching prompt
    resonance_prompt = f"""
You are an expert at intellectual matchmaking - connecting people with ideas that will resonate with their way of thinking.

Here's someone's conversation that reveals how they think, what they value, and their current intellectual journey:

THEIR CONVERSATION:
{conversation_text}

AVAILABLE EVERY ARTICLES ({len(unique_articles)} articles):
{articles_text}

Your task: From these articles, select the 5-7 that would most deeply resonate with this specific person based on their conversation.

Look for resonance in:
- Intellectual style and approach
- Values and priorities they express
- The way they frame problems
- Their current emotional/intellectual state
- What would make them feel understood and inspired

Don't just match topics - match the person. Which articles would make them think "This author gets how I think about things" or "This is exactly what I needed to read right now"?

For each selected article, write a resonance explanation like:
"[Author]'s '[Title]' would resonate because [specific connection to how this person thinks/feels/approaches problems]. The key insight that would speak to them: '[quote or paraphrase]'"

Focus on intellectual companionship - making them feel less alone in their thinking journey.
"""

    llm_start = time.time()
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are an expert at intellectual matchmaking. You MUST ONLY reference articles from Every's database. Do NOT create or invent any articles.You understand how different people think and can connect them with ideas that will deeply resonate with their specific way of approaching problems and viewing the world."},
            {"role": "user", "content": resonance_prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    llm_time = time.time() - llm_start
    total_time = time.time() - start_time
    
    return {
        "resonant_articles": response.choices[0].message.content,
        "search_strategy": search_strategy,
        "stats": {
            "articles_found": len(unique_articles),
            "search_time": search_time,
            "llm_time": llm_time,
            "total_time": total_time
        }
    }

async def compare_search_strategies(conversation_text: str) -> dict:
    """Compare both search strategies side by side."""
    
    print("🔬 COMPARING SEARCH STRATEGIES FOR RESONANCE MATCHING")
    print("=" * 70)
    
    # Test ensemble strategy
    print("\n1️⃣ ENSEMBLE STRATEGY (Sophisticated)")
    print("-" * 40)
    ensemble_result = await flood_zone_resonance_matching(conversation_text, "ensemble")
    
    print(f"⏱️  Total time: {ensemble_result['stats']['total_time']:.2f}s")
    print(f"📊 Articles: {ensemble_result['stats']['articles_found']}")
    print("\n💫 RESONANT ARTICLES (Ensemble):")
    print(ensemble_result['resonant_articles'])
    
    # Test simple strategy  
    print("\n" + "=" * 70)
    print("\n2️⃣ SIMPLE STRATEGY (Broad & Fast)")
    print("-" * 40)
    simple_result = await flood_zone_resonance_matching(conversation_text, "simple")
    
    print(f"⏱️  Total time: {simple_result['stats']['total_time']:.2f}s")
    print(f"📊 Articles: {simple_result['stats']['articles_found']}")
    print("\n💫 RESONANT ARTICLES (Simple):")
    print(simple_result['resonant_articles'])
    
    # Comparison
    print("\n" + "=" * 70)
    print("\n🤔 STRATEGY COMPARISON:")
    print(f"Speed difference: {ensemble_result['stats']['total_time'] - simple_result['stats']['total_time']:.2f}s")
    print("- Which found more resonant connections?")
    print("- Which articles would make you feel more understood?")
    print("- Is the speed difference worth it?")
    
    return {
        "ensemble": ensemble_result,
        "simple": simple_result
    }

# Main function for resonance matching test
async def test_resonance_matching():
    """Test the new resonance matching approach with real ChatGPT conversation."""
    
    print("🌊 FLOOD ZONE RESONANCE MATCHING")
    print("=" * 50)
    
    chatgpt_url = input("\n📎 Enter your ChatGPT conversation URL: ").strip()
    
    if not chatgpt_url:
        print("❌ No URL provided. Exiting.")
        return
    
    try:
        print("\n🔄 Extracting conversation...")
        conversation = await reader.extract_conversation(chatgpt_url)
        
        print(f"✅ Extracted {len(conversation)} characters")
        print(f"📝 Preview: {conversation[:200]}...")
        
        # Ask which strategy to test
        choice = input("\nWhich strategy? (1=Ensemble, 2=Simple, 3=Both): ").strip()
        
        if choice == "3":
            await compare_search_strategies(conversation)
        elif choice == "2":
            result = await flood_zone_resonance_matching(conversation, "simple")
            print(f"\n⏱️  Completed in {result['stats']['total_time']:.2f}s")
            print(f"📊 Found {result['stats']['articles_found']} articles")
            print("\n💫 RESONANT ARTICLES:")
            print("=" * 50)
            print(result['resonant_articles'])
        else:  # default to ensemble
            result = await flood_zone_resonance_matching(conversation, "ensemble")
            print(f"\n⏱️  Completed in {result['stats']['total_time']:.2f}s")
            print(f"📊 Found {result['stats']['articles_found']} articles")
            print("\n💫 RESONANT ARTICLES:")
            print("=" * 50)
            print(result['resonant_articles'])
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == '__main__':
    asyncio.run(test_resonance_matching()) 