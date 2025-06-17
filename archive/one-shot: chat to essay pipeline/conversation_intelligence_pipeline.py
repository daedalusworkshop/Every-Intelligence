#!/usr/bin/env python3
"""
Conversation Intelligence Pipeline
=================================

The complete system that bridges AI conversations with Every's knowledge.

Flow:
1. Extract conversation intelligence (problem context, thinking process, mental model)
2. Generate targeted Every queries (multiple angles, not just keywords)
3. Search Every's vectorized content with intelligent ranking
4. Return contextual insights with reasoning

This is the core of your "What has Every thought about this?" system.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
from conversation_extractor import ConversationExtractor, ConversationContext
from every_context_matcher import EveryContextMatcher, EveryInsightRequest, EveryQuery
from query_system import ArticleQuerySystem


@dataclass
class EveryInsight:
    """
    A single insight from Every's content, contextualized for the user's conversation.
    """
    # Article Information
    title: str
    author: str
    column: str
    url: str
    
    # Relevance Information
    relevance_score: float
    query_that_found_it: str
    why_relevant: str
    
    # Content
    preview: str
    
    # Context
    insight_type: str  # "direct_answer", "framework", "example", "contrarian"
    confidence: float  # How confident we are this is useful
    key_quote: Optional[str] = None


@dataclass
class ConversationInsights:
    """
    Complete set of insights for a conversation, organized by relevance and type.
    """
    # Core Insights (most relevant)
    primary_insights: List[EveryInsight]
    
    # Broader Context
    exploratory_insights: List[EveryInsight]
    
    # Meta Information
    conversation_summary: str
    total_queries_run: int
    processing_time: float
    
    # User Context
    user_problem_domain: str
    user_thinking_style: str
    suggested_next_questions: List[str]


class ConversationIntelligencePipeline:
    """
    The complete pipeline from conversation to Every insights.
    
    This is your "We Are So Back" system - it understands what someone is
    really thinking about and surfaces the most relevant Every content.
    """
    
    def __init__(self):
        """Initialize all components of the pipeline."""
        self.conversation_extractor = ConversationExtractor()
        self.context_matcher = EveryContextMatcher()
        self.query_system = ArticleQuerySystem()
    
    def process_conversation_file(self, file_path: str) -> ConversationInsights:
        """
        Process a conversation file and return Every insights.
        
        This is the main entry point for file-based conversations.
        """
        import time
        start_time = time.time()
        
        # Step 1: Extract conversation intelligence
        context = self.conversation_extractor.extract_from_file(file_path)
        
        # Step 2: Generate targeted Every queries
        insight_request = self.context_matcher.generate_insight_request(context)
        
        # Step 3: Execute queries and gather insights
        insights = self._execute_insight_request(insight_request, context)
        
        # Step 4: Add meta information
        processing_time = time.time() - start_time
        insights.processing_time = processing_time
        insights.total_queries_run = len(insight_request.primary_queries) + len(insight_request.exploratory_queries)
        
        return insights
    
    def process_conversation_text(self, conversation_text: str) -> ConversationInsights:
        """
        Process raw conversation text and return Every insights.
        
        This is the main entry point for direct text input.
        """
        import time
        start_time = time.time()
        
        # Step 1: Extract conversation intelligence
        context = self.conversation_extractor.extract_from_text(conversation_text)
        
        # Step 2: Generate targeted Every queries
        insight_request = self.context_matcher.generate_insight_request(context)
        
        # Step 3: Execute queries and gather insights
        insights = self._execute_insight_request(insight_request, context)
        
        # Step 4: Add meta information
        processing_time = time.time() - start_time
        insights.processing_time = processing_time
        insights.total_queries_run = len(insight_request.primary_queries) + len(insight_request.exploratory_queries)
        
        return insights
    
    def _execute_insight_request(self, insight_request: EveryInsightRequest, context: ConversationContext) -> ConversationInsights:
        """
        Execute the insight request and return organized results.
        
        This is where we run the actual searches and organize the results.
        """
        primary_insights = []
        exploratory_insights = []
        
        # Execute primary queries (most relevant)
        for query in insight_request.primary_queries:
            insights = self._execute_single_query(query, context, is_primary=True)
            primary_insights.extend(insights)
        
        # Execute exploratory queries (broader context)
        for query in insight_request.exploratory_queries:
            insights = self._execute_single_query(query, context, is_primary=False)
            exploratory_insights.extend(insights)
        
        # Remove duplicates and rank results
        primary_insights = self._deduplicate_and_rank(primary_insights)[:5]
        exploratory_insights = self._deduplicate_and_rank(exploratory_insights)[:3]
        
        # Generate conversation summary
        conversation_summary = self._generate_conversation_summary(context)
        
        # Generate suggested next questions
        suggested_questions = self._generate_suggested_questions(context, primary_insights)
        
        return ConversationInsights(
            primary_insights=primary_insights,
            exploratory_insights=exploratory_insights,
            conversation_summary=conversation_summary,
            total_queries_run=0,  # Will be set by caller
            processing_time=0.0,  # Will be set by caller
            user_problem_domain=context.problem_domain,
            user_thinking_style=context.intellectual_style,
            suggested_next_questions=suggested_questions
        )
    
    def _execute_single_query(self, query: EveryQuery, context: ConversationContext, is_primary: bool) -> List[EveryInsight]:
        """
        Execute a single query and convert results to EveryInsight objects.
        """
        # Search Every's content
        search_results = self.query_system.query(
            question=query.query_text,
            top_k=8 if is_primary else 5,  # Get more results for primary queries
            include_preview=True,
            deduplicate=True
        )
        
        insights = []
        for result in search_results:
            # Convert search result to EveryInsight
            insight = EveryInsight(
                title=result['title'],
                author=result['author'],
                column=result['column'],
                url=result['url'],
                relevance_score=result['score'],
                query_that_found_it=query.query_text,
                why_relevant=query.reasoning,
                preview=result.get('preview', ''),
                insight_type=query.query_type,
                confidence=self._calculate_confidence(result, query, context)
            )
            
            # Extract key quote if possible
            insight.key_quote = self._extract_key_quote(result.get('preview', ''), query)
            
            insights.append(insight)
        
        return insights
    
    def _calculate_confidence(self, result: Dict, query: EveryQuery, context: ConversationContext) -> float:
        """
        Calculate confidence score for how useful this insight will be.
        
        Combines relevance score with contextual factors.
        """
        base_score = result['score']
        
        # Boost score based on query priority
        priority_boost = query.priority * 0.1
        
        # Boost score if author/column matches their interests
        author_boost = 0.0
        if any(topic in result['author'].lower() for topic in context.topics_of_interest):
            author_boost = 0.1
        
        # Boost score for implementation-focused content if they're implementing
        implementation_boost = 0.0
        if context.problem_complexity == "implementation":
            implementation_keywords = ["how to", "step by step", "guide", "framework", "process"]
            if any(keyword in result.get('preview', '').lower() for keyword in implementation_keywords):
                implementation_boost = 0.1
        
        confidence = min(1.0, base_score + priority_boost + author_boost + implementation_boost)
        return confidence
    
    def _extract_key_quote(self, preview: str, query: EveryQuery) -> Optional[str]:
        """
        Extract a key quote from the preview that's most relevant to the query.
        
        This could be enhanced with more sophisticated NLP.
        """
        if not preview:
            return None
        
        # Simple approach: find sentences that contain query keywords
        sentences = preview.split('.')
        query_words = query.query_text.lower().split()
        
        best_sentence = None
        best_score = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20:  # Skip very short sentences
                continue
            
            # Count how many query words appear in this sentence
            sentence_lower = sentence.lower()
            score = sum(1 for word in query_words if word in sentence_lower)
            
            if score > best_score:
                best_score = score
                best_sentence = sentence
        
        return best_sentence if best_sentence else None
    
    def _deduplicate_and_rank(self, insights: List[EveryInsight]) -> List[EveryInsight]:
        """
        Remove duplicate articles and rank by confidence.
        """
        # Remove duplicates by URL
        seen_urls = set()
        unique_insights = []
        
        for insight in insights:
            if insight.url not in seen_urls:
                unique_insights.append(insight)
                seen_urls.add(insight.url)
        
        # Sort by confidence score (descending)
        unique_insights.sort(key=lambda x: x.confidence, reverse=True)
        
        return unique_insights
    
    def _generate_conversation_summary(self, context: ConversationContext) -> str:
        """
        Generate a human-readable summary of what the conversation is about.
        """
        domain = context.problem_domain
        problem = context.problem_statement
        complexity = context.problem_complexity
        
        summary = f"User is working on {domain}"
        
        if problem and problem != "Problem statement not clearly identified":
            summary += f", specifically trying to {problem}"
        
        summary += f". They're in the {complexity} phase"
        
        if context.thinking_patterns:
            patterns = ", ".join(context.thinking_patterns)
            summary += f" and tend toward {patterns}"
        
        summary += "."
        
        return summary
    
    def _generate_suggested_questions(self, context: ConversationContext, insights: List[EveryInsight]) -> List[str]:
        """
        Generate suggested follow-up questions based on the insights found.
        """
        suggestions = []
        
        # Suggest questions based on their domain
        domain_questions = {
            "AI product development": [
                "How do I validate AI product ideas?",
                "What are common AI product pitfalls?",
                "How do I measure AI product success?"
            ],
            "startup strategy": [
                "How do I find product-market fit?",
                "What are the key startup metrics?",
                "How do I build a strong team?"
            ],
            "content strategy": [
                "How do I grow my audience?",
                "What makes content go viral?",
                "How do I monetize content?"
            ]
        }
        
        domain_suggestions = domain_questions.get(context.problem_domain, [])
        suggestions.extend(domain_suggestions[:2])
        
        # Suggest questions based on insights found
        if insights:
            # Look at the authors of top insights
            top_authors = [insight.author for insight in insights[:3]]
            for author in set(top_authors):
                suggestions.append(f"What else has {author} written about?")
                break  # Only suggest one author question
        
        return suggestions[:3]  # Return top 3 suggestions
    
    def print_insights(self, insights: ConversationInsights, detailed: bool = False):
        """
        Pretty print the insights in a readable format.
        
        This is what the user sees - the final output of the system.
        """
        print("=" * 80)
        print("🧠 CONVERSATION INTELLIGENCE INSIGHTS")
        print("=" * 80)
        
        print(f"\n📋 CONVERSATION SUMMARY:")
        print(f"   {insights.conversation_summary}")
        
        print(f"\n⚡ PROCESSING INFO:")
        print(f"   • Queries executed: {insights.total_queries_run}")
        print(f"   • Processing time: {insights.processing_time:.2f}s")
        print(f"   • Problem domain: {insights.user_problem_domain}")
        print(f"   • Thinking style: {insights.user_thinking_style}")
        
        print(f"\n🎯 PRIMARY INSIGHTS ({len(insights.primary_insights)}):")
        for i, insight in enumerate(insights.primary_insights, 1):
            print(f"\n   {i}. 📄 {insight.title}")
            print(f"      ✍️  {insight.author} • {insight.column}")
            print(f"      🎯 Relevance: {insight.confidence:.2f} | Found via: {insight.query_that_found_it}")
            print(f"      💡 Why relevant: {insight.why_relevant}")
            
            if insight.key_quote:
                print(f"      💬 Key quote: \"{insight.key_quote}\"")
            
            if detailed:
                print(f"      📖 Preview: {insight.preview}")
            
            print(f"      🔗 {insight.url}")
        
        if insights.exploratory_insights:
            print(f"\n🔍 EXPLORATORY INSIGHTS ({len(insights.exploratory_insights)}):")
            for i, insight in enumerate(insights.exploratory_insights, 1):
                print(f"\n   {i}. 📄 {insight.title}")
                print(f"      ✍️  {insight.author} • {insight.column}")
                print(f"      💡 {insight.why_relevant}")
                print(f"      🔗 {insight.url}")
        
        if insights.suggested_next_questions:
            print(f"\n❓ SUGGESTED FOLLOW-UP QUESTIONS:")
            for i, question in enumerate(insights.suggested_next_questions, 1):
                print(f"   {i}. {question}")
        
        print("\n" + "=" * 80)


def test_pipeline():
    """
    Test the complete pipeline with the ChatGPT conversation.
    
    This demonstrates the full "conversation → Every insights" flow.
    """
    print("🚀 Testing Conversation Intelligence Pipeline")
    print("=" * 60)
    
    pipeline = ConversationIntelligencePipeline()
    
    # Process the ChatGPT conversation
    insights = pipeline.process_conversation_file('chatgpt extraction/chatgpt_response.html')
    
    # Display the results
    pipeline.print_insights(insights, detailed=False)
    
    return insights


if __name__ == "__main__":
    test_pipeline() 