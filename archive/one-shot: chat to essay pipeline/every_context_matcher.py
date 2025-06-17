#!/usr/bin/env python3
"""
Every Context Matcher
====================

Converts conversation intelligence into targeted Every content queries.
This is the bridge between "what they're thinking" and "what Every has thought."

Core Philosophy:
- Generate multiple query angles, not just keywords
- Prioritize conceptual matches over literal matches  
- Surface unexpected connections and insights
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
from conversation_extractor import ConversationContext
import json


@dataclass
class EveryQuery:
    """
    A targeted query for Every's knowledge base.
    
    Each query represents a different angle for finding relevant insights.
    """
    query_text: str          # The actual search query
    query_type: str          # "conceptual", "practical", "framework", "example"
    priority: int            # 1-5, higher = more relevant
    reasoning: str           # Why this query is relevant
    expected_content: str    # What kind of Every content we expect to find


@dataclass
class EveryInsightRequest:
    """
    Complete request for Every insights based on conversation context.
    
    Contains multiple query angles and context for ranking results.
    """
    primary_queries: List[EveryQuery]      # Main queries (3-5)
    exploratory_queries: List[EveryQuery]  # Broader exploration (2-3)
    context_filters: Dict[str, str]        # Filters for result ranking
    user_profile: Dict[str, str]           # User characteristics for personalization


class EveryContextMatcher:
    """
    Converts conversation intelligence into targeted Every content queries.
    
    This system understands:
    1. What the user is really asking about (beyond keywords)
    2. What Every content would be most valuable to them
    3. How to surface unexpected but relevant connections
    """
    
    def __init__(self):
        """Initialize with Every's content taxonomy and query patterns."""
        self.every_content_types = {
            "strategy": ["business strategy", "product strategy", "go-to-market"],
            "ai_development": ["ai product development", "llm applications", "ai tools"],
            "productivity": ["tools for thought", "note-taking", "knowledge management"],
            "creativity": ["creative process", "writing", "content creation"],
            "psychology": ["decision making", "cognitive science", "behavior"],
            "entrepreneurship": ["startup advice", "founder stories", "business building"],
            "technology": ["software development", "technical architecture", "programming"]
        }
        
        self.query_templates = {
            "conceptual": [
                "How does Every think about {concept}?",
                "Every's perspective on {concept}",
                "What has Every written about {concept}?"
            ],
            "practical": [
                "Every's advice on {action}",
                "How to {action} according to Every",
                "Every's framework for {action}"
            ],
            "framework": [
                "Every's {framework} approach",
                "{framework} in Every's writing",
                "How Every applies {framework}"
            ],
            "example": [
                "Every examples of {concept}",
                "Case studies about {concept} from Every",
                "{concept} stories from Every"
            ]
        }
    
    def generate_insight_request(self, context: ConversationContext) -> EveryInsightRequest:
        """
        Generate a complete insight request from conversation context.
        
        This is the main method that converts conversation intelligence
        into actionable Every content queries.
        """
        # Generate primary queries (most relevant)
        primary_queries = self._generate_primary_queries(context)
        
        # Generate exploratory queries (broader context)
        exploratory_queries = self._generate_exploratory_queries(context)
        
        # Create context filters for result ranking
        context_filters = self._create_context_filters(context)
        
        # Build user profile for personalization
        user_profile = self._build_user_profile(context)
        
        return EveryInsightRequest(
            primary_queries=primary_queries,
            exploratory_queries=exploratory_queries,
            context_filters=context_filters,
            user_profile=user_profile
        )
    
    def _generate_primary_queries(self, context: ConversationContext) -> List[EveryQuery]:
        """
        Generate 3-5 primary queries that directly address their problem.
        
        These are the most important queries - they should surface content
        that directly helps with their current challenge.
        """
        queries = []
        
        # Query 1: Direct problem domain query
        domain_query = self._create_domain_query(context)
        if domain_query:
            queries.append(domain_query)
        
        # Query 2: Problem statement query
        problem_query = self._create_problem_query(context)
        if problem_query:
            queries.append(problem_query)
        
        # Query 3: Framework/approach query
        framework_query = self._create_framework_query(context)
        if framework_query:
            queries.append(framework_query)
        
        # Query 4: Current focus query
        focus_query = self._create_focus_query(context)
        if focus_query:
            queries.append(focus_query)
        
        # Query 5: Decision support query
        decision_query = self._create_decision_query(context)
        if decision_query:
            queries.append(decision_query)
        
        # Sort by priority and return top 5
        queries.sort(key=lambda q: q.priority, reverse=True)
        return queries[:5]
    
    def _generate_exploratory_queries(self, context: ConversationContext) -> List[EveryQuery]:
        """
        Generate 2-3 exploratory queries for broader context.
        
        These surface related insights they might not have considered.
        """
        queries = []
        
        # Exploratory query 1: Adjacent domains
        adjacent_query = self._create_adjacent_domain_query(context)
        if adjacent_query:
            queries.append(adjacent_query)
        
        # Exploratory query 2: Meta-level thinking
        meta_query = self._create_meta_query(context)
        if meta_query:
            queries.append(meta_query)
        
        # Exploratory query 3: Contrarian perspective
        contrarian_query = self._create_contrarian_query(context)
        if contrarian_query:
            queries.append(contrarian_query)
        
        return queries
    
    def _create_domain_query(self, context: ConversationContext) -> EveryQuery:
        """Create a query focused on their problem domain."""
        domain = context.problem_domain
        
        # Map their domain to Every's content areas
        every_domain = self._map_to_every_domain(domain)
        
        query_text = f"Every's insights on {every_domain}"
        
        return EveryQuery(
            query_text=query_text,
            query_type="conceptual",
            priority=5,  # Highest priority
            reasoning=f"Direct match for their {domain} problem",
            expected_content=f"Every articles about {every_domain}"
        )
    
    def _create_problem_query(self, context: ConversationContext) -> EveryQuery:
        """Create a query focused on their specific problem statement."""
        problem = context.problem_statement
        
        # Extract key concepts from their problem
        key_concepts = self._extract_key_concepts(problem)
        
        if key_concepts:
            query_text = f"Every's approach to {key_concepts[0]}"
            
            return EveryQuery(
                query_text=query_text,
                query_type="practical",
                priority=4,
                reasoning=f"Addresses their specific challenge: {problem[:50]}...",
                expected_content="Actionable advice and frameworks"
            )
        
        return None
    
    def _create_framework_query(self, context: ConversationContext) -> EveryQuery:
        """Create a query based on frameworks they're using or need."""
        frameworks = context.frameworks_used
        thinking_patterns = context.thinking_patterns
        
        # If they mentioned specific frameworks, query those
        if frameworks:
            framework = frameworks[0]
            query_text = f"Every's perspective on {framework}"
            
            return EveryQuery(
                query_text=query_text,
                query_type="framework",
                priority=3,
                reasoning=f"They're using {framework} - find Every's take",
                expected_content=f"Every's analysis of {framework}"
            )
        
        # Otherwise, suggest frameworks based on their thinking patterns
        elif thinking_patterns:
            pattern = thinking_patterns[0]
            suggested_framework = self._suggest_framework(pattern)
            
            if suggested_framework:
                query_text = f"Every's {suggested_framework} framework"
                
                return EveryQuery(
                    query_text=query_text,
                    query_type="framework",
                    priority=3,
                    reasoning=f"Matches their {pattern} approach",
                    expected_content=f"Framework for {pattern}"
                )
        
        return None
    
    def _create_focus_query(self, context: ConversationContext) -> EveryQuery:
        """Create a query based on what they're currently working on."""
        focus = context.current_focus
        
        if focus and focus != "General exploration":
            # Extract actionable elements from their focus
            action_words = ["building", "creating", "developing", "implementing", "designing"]
            
            for word in action_words:
                if word in focus.lower():
                    query_text = f"Every's advice on {focus}"
                    
                    return EveryQuery(
                        query_text=query_text,
                        query_type="practical",
                        priority=4,
                        reasoning=f"Directly relevant to what they're working on",
                        expected_content="Tactical advice and lessons learned"
                    )
        
        return None
    
    def _create_decision_query(self, context: ConversationContext) -> EveryQuery:
        """Create a query to help with decisions they're facing."""
        decisions = context.decision_points
        
        if decisions:
            decision = decisions[0]
            query_text = f"Every's guidance on {decision}"
            
            return EveryQuery(
                query_text=query_text,
                query_type="practical",
                priority=3,
                reasoning=f"Help with their decision: {decision}",
                expected_content="Decision frameworks and case studies"
            )
        
        return None
    
    def _create_adjacent_domain_query(self, context: ConversationContext) -> EveryQuery:
        """Create a query for adjacent domains that might offer insights."""
        domain = context.problem_domain
        
        # Map to adjacent domains
        adjacent_domains = {
            "AI product development": "product strategy",
            "startup strategy": "entrepreneurship",
            "technical architecture": "systems thinking",
            "product design": "user psychology",
            "content strategy": "audience building"
        }
        
        adjacent = adjacent_domains.get(domain, "business strategy")
        query_text = f"Every's insights on {adjacent}"
        
        return EveryQuery(
            query_text=query_text,
            query_type="conceptual",
            priority=2,
            reasoning=f"Adjacent domain to {domain} - might offer fresh perspective",
            expected_content=f"Cross-domain insights from {adjacent}"
        )
    
    def _create_meta_query(self, context: ConversationContext) -> EveryQuery:
        """Create a meta-level query about their thinking process."""
        style = context.intellectual_style
        
        meta_topics = {
            "analytical": "decision making frameworks",
            "creative": "creative process",
            "practical": "execution strategies", 
            "theoretical": "mental models",
            "balanced": "thinking tools"
        }
        
        topic = meta_topics.get(style, "problem solving")
        query_text = f"Every's thoughts on {topic}"
        
        return EveryQuery(
            query_text=query_text,
            query_type="conceptual",
            priority=2,
            reasoning=f"Matches their {style} thinking style",
            expected_content=f"Meta-insights about {topic}"
        )
    
    def _create_contrarian_query(self, context: ConversationContext) -> EveryQuery:
        """Create a query that challenges their assumptions."""
        domain = context.problem_domain
        
        contrarian_angles = {
            "AI product development": "AI limitations and failures",
            "startup strategy": "why startups fail",
            "technical architecture": "over-engineering problems",
            "product design": "design thinking criticism",
            "content strategy": "content marketing myths"
        }
        
        angle = contrarian_angles.get(domain, "common mistakes")
        query_text = f"Every's perspective on {angle}"
        
        return EveryQuery(
            query_text=query_text,
            query_type="example",
            priority=1,
            reasoning=f"Contrarian view to challenge assumptions about {domain}",
            expected_content="Cautionary tales and alternative perspectives"
        )
    
    def _map_to_every_domain(self, problem_domain: str) -> str:
        """Map user's problem domain to Every's content areas."""
        domain_mapping = {
            "AI product development": "AI and machine learning",
            "startup strategy": "entrepreneurship and business strategy",
            "technical architecture": "software development and systems",
            "product design": "product management and design",
            "content strategy": "writing and content creation",
            "research": "analysis and research methods"
        }
        
        return domain_mapping.get(problem_domain, problem_domain)
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from problem statement."""
        # Simple keyword extraction - could be enhanced with NLP
        important_words = []
        
        # Remove common words and extract meaningful concepts
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = text.lower().split()
        
        for word in words:
            if len(word) > 3 and word not in stop_words:
                important_words.append(word)
        
        return important_words[:3]  # Return top 3 concepts
    
    def _suggest_framework(self, thinking_pattern: str) -> str:
        """Suggest a framework based on their thinking pattern."""
        framework_suggestions = {
            "systematic analysis": "first principles thinking",
            "creative thinking": "design thinking",
            "data-driven approach": "analytics frameworks",
            "user-centered thinking": "jobs to be done",
            "iterative development": "lean startup methodology"
        }
        
        return framework_suggestions.get(thinking_pattern)
    
    def _create_context_filters(self, context: ConversationContext) -> Dict[str, str]:
        """Create filters for ranking search results."""
        return {
            "complexity": context.problem_complexity,
            "style": context.intellectual_style,
            "domain": context.problem_domain,
            "recency_preference": "recent" if context.problem_complexity == "implementation" else "timeless"
        }
    
    def _build_user_profile(self, context: ConversationContext) -> Dict[str, str]:
        """Build user profile for personalization."""
        return {
            "thinking_style": context.intellectual_style,
            "problem_approach": context.problem_complexity,
            "primary_interests": ", ".join(context.topics_of_interest),
            "current_focus": context.current_focus,
            "conversation_type": context.conversation_flow
        }


def test_context_matcher():
    """Test the context matcher with extracted conversation intelligence."""
    from conversation_extractor import ConversationExtractor
    
    # Extract context from the ChatGPT conversation
    extractor = ConversationExtractor()
    context = extractor.extract_from_file('chatgpt extraction/chatgpt_response.html')
    
    # Generate Every insight request
    matcher = EveryContextMatcher()
    insight_request = matcher.generate_insight_request(context)
    
    print("=== EVERY INSIGHT REQUEST ===")
    print(f"\nPRIMARY QUERIES ({len(insight_request.primary_queries)}):")
    for i, query in enumerate(insight_request.primary_queries, 1):
        print(f"{i}. {query.query_text}")
        print(f"   Type: {query.query_type} | Priority: {query.priority}")
        print(f"   Reasoning: {query.reasoning}")
        print(f"   Expected: {query.expected_content}")
        print()
    
    print(f"EXPLORATORY QUERIES ({len(insight_request.exploratory_queries)}):")
    for i, query in enumerate(insight_request.exploratory_queries, 1):
        print(f"{i}. {query.query_text}")
        print(f"   Reasoning: {query.reasoning}")
        print()
    
    print("CONTEXT FILTERS:")
    for key, value in insight_request.context_filters.items():
        print(f"  {key}: {value}")
    
    print("\nUSER PROFILE:")
    for key, value in insight_request.user_profile.items():
        print(f"  {key}: {value}")
    
    return insight_request


if __name__ == "__main__":
    test_context_matcher() 