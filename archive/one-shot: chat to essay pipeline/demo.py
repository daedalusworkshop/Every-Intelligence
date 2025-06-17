#!/usr/bin/env python3
"""
Demo: Conversation Intelligence Pipeline
=======================================

Shows different ways to use the chat-to-essay pipeline.
"""

from conversation_intelligence_pipeline import ConversationIntelligencePipeline

def demo_chatgpt_file():
    """Demo: Process ChatGPT conversation from HTML file"""
    print("🎯 DEMO 1: ChatGPT Conversation File")
    print("=" * 50)
    
    pipeline = ConversationIntelligencePipeline()
    insights = pipeline.process_conversation_file('chatgpt extraction/chatgpt_response.html')
    
    # Show just the summary and top 2 insights
    print(f"📋 Summary: {insights.conversation_summary}")
    print(f"⚡ Found {len(insights.primary_insights)} primary insights in {insights.processing_time:.1f}s")
    
    for i, insight in enumerate(insights.primary_insights[:2], 1):
        print(f"\n   {i}. {insight.title}")
        print(f"      💡 {insight.why_relevant}")
        print(f"      🔗 {insight.url}")

def demo_raw_text():
    """Demo: Process raw conversation text"""
    print("\n\n🎯 DEMO 2: Raw Conversation Text")
    print("=" * 50)
    
    # Example conversation about productivity
    conversation = """
    User: I'm struggling with information overload. I read tons of articles and take notes, but I can never find what I need when I need it. How do I build a better knowledge management system?

    Assistant: This is a classic "tools for thought" problem. You need a system that captures information and makes it retrievable when you need it. Consider these approaches:

    1. Use a note-taking system with strong linking capabilities
    2. Develop consistent tagging and categorization habits  
    3. Regular review cycles to reinforce important concepts
    4. Focus on connecting ideas rather than just collecting them

    The key is building a system that works with your natural thinking patterns, not against them.
    """
    
    pipeline = ConversationIntelligencePipeline()
    insights = pipeline.process_conversation_text(conversation)
    
    print(f"📋 Summary: {insights.conversation_summary}")
    print(f"⚡ Found {len(insights.primary_insights)} insights")
    
    # Show top insight
    if insights.primary_insights:
        top_insight = insights.primary_insights[0]
        print(f"\n   🏆 Top Match: {top_insight.title}")
        print(f"      💡 {top_insight.why_relevant}")
        print(f"      🔗 {top_insight.url}")

def demo_conversation_analysis():
    """Demo: Show what the system extracts from conversations"""
    print("\n\n🎯 DEMO 3: Conversation Analysis Deep Dive")
    print("=" * 50)
    
    pipeline = ConversationIntelligencePipeline()
    
    # Extract just the conversation intelligence (no Every search)
    context = pipeline.conversation_extractor.extract_from_file('chatgpt extraction/chatgpt_response.html')
    
    print("🧠 EXTRACTED INTELLIGENCE:")
    print(f"   Problem Domain: {context.problem_domain}")
    print(f"   Problem Statement: {context.problem_statement}")
    print(f"   Complexity Level: {context.problem_complexity}")
    print(f"   Thinking Patterns: {', '.join(context.thinking_patterns)}")
    print(f"   Frameworks Used: {', '.join(context.frameworks_used)}")
    print(f"   Topics of Interest: {', '.join(context.topics_of_interest)}")
    print(f"   Intellectual Style: {context.intellectual_style}")
    print(f"   Current Focus: {context.current_focus}")
    
    # Show generated queries
    insight_request = pipeline.context_matcher.generate_insight_request(context)
    print(f"\n🎯 GENERATED QUERIES ({len(insight_request.primary_queries)} primary):")
    for i, query in enumerate(insight_request.primary_queries, 1):
        print(f"   {i}. {query.query_text} (Priority: {query.priority})")
        print(f"      💡 {query.reasoning}")

if __name__ == "__main__":
    print("🚀 CONVERSATION INTELLIGENCE PIPELINE DEMOS")
    print("=" * 60)
    
    # Run all demos
    demo_chatgpt_file()
    demo_raw_text() 
    demo_conversation_analysis()
    
    print("\n\n✨ All demos complete!")
    print("💡 Try running: python test_pipeline.py for the full experience") 