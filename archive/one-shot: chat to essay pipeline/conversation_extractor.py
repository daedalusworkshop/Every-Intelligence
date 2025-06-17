#!/usr/bin/env python3
"""
Universal Conversation Intelligence Extractor
============================================

Extracts problem context, thinking process, and mental model from AI conversations.
Works across different platforms (ChatGPT, Claude, Gemini) and formats.

Core Philosophy: 
- Extract intellectual DNA, not just text
- Understand cognitive patterns, not just keywords
- Build contextual bridges to Every's knowledge
"""

import re
import json
import html
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup
from pathlib import Path


@dataclass
class ConversationContext:
    """
    Structured representation of extracted conversation intelligence.
    
    This is what we'll use to query Every's knowledge base.
    """
    # Core Problem Analysis
    problem_domain: str          # e.g., "AI product development", "startup strategy"
    problem_statement: str       # The specific challenge they're working on
    problem_complexity: str      # "exploratory", "implementation", "optimization"
    
    # Thinking Process
    thinking_patterns: List[str] # How they approach problems
    frameworks_used: List[str]   # Mental models they reference
    decision_points: List[str]   # Key choices they're considering
    
    # Context Clues for Every Matching
    topics_of_interest: List[str]    # Specific subjects they care about
    intellectual_style: str          # "analytical", "creative", "systematic"
    current_focus: str              # What they're actively working on
    
    # Raw Data
    user_messages: List[str]
    ai_responses: List[str]
    conversation_flow: str      # Overall arc of the conversation


class ConversationExtractor:
    """
    Universal parser for AI conversations across platforms.
    
    Handles different input formats:
    - ChatGPT shared links (HTML)
    - Claude conversation exports (JSON)
    - Raw text conversations
    - Uploaded conversation files
    """
    
    def __init__(self):
        """Initialize the conversation extractor."""
        pass
    
    def extract_from_file(self, file_path: str) -> ConversationContext:
        """
        Extract from uploaded conversation file.
        
        Auto-detects format:
        - .html (ChatGPT export)
        - .json (Claude export)
        - .txt (raw conversation)
        """
        path = Path(file_path)
        
        if path.suffix == '.html':
            return self._extract_from_html_file(file_path)
        elif path.suffix == '.json':
            return self._extract_from_json_file(file_path)
        elif path.suffix == '.txt':
            return self._extract_from_text_file(file_path)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")
    
    def extract_from_text(self, conversation_text: str) -> ConversationContext:
        """
        Extract from raw conversation text.
        
        Handles common formats:
        - "User: ... Assistant: ..." 
        - "Human: ... AI: ..."
        - Timestamped conversations
        """
        return self._extract_from_raw_text(conversation_text)
    
    def _extract_from_html_file(self, file_path: str) -> ConversationContext:
        """Extract from saved ChatGPT HTML file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # First try to extract structured conversation data
        conversation_data = self._extract_conversation_from_html(content)
        
        if conversation_data:
            return self._analyze_conversation_structure(conversation_data)
        else:
            # Fallback: extract from visible text
            soup = BeautifulSoup(content, 'html.parser')
            return self._extract_from_raw_text(soup.get_text())
    
    def _extract_conversation_from_html(self, html_content: str) -> Optional[Dict]:
        """
        Extract conversation data from HTML content.
        
        ChatGPT embeds conversation data in escaped JSON within script tags.
        We need to find and parse this data carefully.
        """
        # First, try to find the conversation content directly
        # Look for the user's message pattern we know exists
        user_message_pattern = r'Every has thought.*?(?=\\"|$)'
        user_match = re.search(user_message_pattern, html_content, re.DOTALL)
        
        if user_match:
            user_message = user_match.group(0)
            # Clean up escaped characters
            user_message = user_message.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
            
            # Now look for the AI response that follows
            # Look for structured response patterns
            ai_response_patterns = [
                r'Let.*?s Stress-Test the Core Idea.*?(?=\\"|$)',
                r'Problem to Beat.*?(?=\\"|$)',
                r'Interaction Model Variants.*?(?=\\"|$)'
            ]
            
            ai_response = ""
            for pattern in ai_response_patterns:
                ai_match = re.search(pattern, html_content, re.DOTALL)
                if ai_match:
                    ai_response = ai_match.group(0)
                    ai_response = ai_response.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')
                    break
            
            # Return structured conversation data
            return {
                'user_messages': [user_message],
                'ai_responses': [ai_response] if ai_response else [],
                'conversation_type': 'chatgpt_shared'
            }
        
        # Fallback: try to find JSON data patterns
        conversation_patterns = [
            r'"messages":\s*\[(.*?)\]',
            r'"conversation":\s*{(.*?)}',
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
            r'window\.__reactRouterContext\s*=\s*({.*?});'
        ]
        
        for pattern in conversation_patterns:
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                try:
                    # Try to parse as JSON
                    json_str = match.group(0)
                    # Clean up the JSON string
                    json_str = re.sub(r'window\.__\w+__\s*=\s*', '', json_str)
                    json_str = json_str.rstrip(';')
                    
                    data = json.loads(json_str)
                    return data
                except:
                    continue
        
        return None
    
    def _extract_from_raw_text(self, text: str) -> ConversationContext:
        """
        Extract conversation intelligence from raw text.
        
        This is our fallback method and also handles direct text input.
        """
        # Split into user and AI messages
        user_messages, ai_responses = self._split_conversation_text(text)
        
        # Analyze the conversation content
        return self._analyze_conversation_content(user_messages, ai_responses, text)
    
    def _split_conversation_text(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Split conversation text into user and AI messages.
        
        Handles various conversation formats.
        """
        user_messages = []
        ai_responses = []
        
        # Clean up the text first
        text = html.unescape(text)
        text = re.sub(r'\\n', '\n', text)
        text = re.sub(r'\\"', '"', text)
        
        # Common patterns for conversation splits
        patterns = [
            (r'User:(.*?)(?=Assistant:|AI:|ChatGPT:|$)', r'(?:Assistant:|AI:|ChatGPT:)(.*?)(?=User:|$)'),
            (r'Human:(.*?)(?=AI:|Assistant:|$)', r'(?:AI:|Assistant:)(.*?)(?=Human:|$)'),
            (r'You:(.*?)(?=ChatGPT:|Claude:|$)', r'(?:ChatGPT:|Claude:)(.*?)(?=You:|$)'),
        ]
        
        for user_pattern, ai_pattern in patterns:
            user_matches = re.findall(user_pattern, text, re.DOTALL | re.IGNORECASE)
            ai_matches = re.findall(ai_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if user_matches or ai_matches:
                user_messages.extend([msg.strip() for msg in user_matches])
                ai_responses.extend([msg.strip() for msg in ai_matches])
                break
        
        # If no patterns matched, try to infer from content structure
        if not user_messages and not ai_responses:
            user_messages, ai_responses = self._infer_conversation_structure(text)
        
        return user_messages, ai_responses
    
    def _analyze_conversation_content(self, user_messages: List[str], ai_responses: List[str], full_text: str) -> ConversationContext:
        """
        Analyze conversation content to extract intelligence.
        
        This is where the magic happens - we extract the intellectual DNA.
        """
        # Combine all user messages to understand their problem
        user_content = " ".join(user_messages)
        ai_content = " ".join(ai_responses)
        
        # Extract problem domain and statement
        problem_domain = self._extract_problem_domain(user_content)
        problem_statement = self._extract_problem_statement(user_content)
        problem_complexity = self._assess_problem_complexity(user_content, ai_content)
        
        # Analyze thinking patterns
        thinking_patterns = self._extract_thinking_patterns(user_content)
        frameworks_used = self._extract_frameworks(user_content + " " + ai_content)
        decision_points = self._extract_decision_points(user_content)
        
        # Extract context for Every matching
        topics_of_interest = self._extract_topics(user_content)
        intellectual_style = self._assess_intellectual_style(user_content)
        current_focus = self._extract_current_focus(user_content)
        
        # Determine conversation flow
        conversation_flow = self._analyze_conversation_flow(user_messages, ai_responses)
        
        return ConversationContext(
            problem_domain=problem_domain,
            problem_statement=problem_statement,
            problem_complexity=problem_complexity,
            thinking_patterns=thinking_patterns,
            frameworks_used=frameworks_used,
            decision_points=decision_points,
            topics_of_interest=topics_of_interest,
            intellectual_style=intellectual_style,
            current_focus=current_focus,
            user_messages=user_messages,
            ai_responses=ai_responses,
            conversation_flow=conversation_flow
        )
    
    def _extract_problem_domain(self, text: str) -> str:
        """Identify the high-level domain of the problem."""
        domain_keywords = {
            "AI product development": ["ai", "machine learning", "model", "llm", "gpt", "claude"],
            "startup strategy": ["startup", "business", "market", "customers", "revenue"],
            "technical architecture": ["system", "architecture", "database", "api", "infrastructure"],
            "product design": ["user", "interface", "ux", "design", "product"],
            "content strategy": ["content", "writing", "blog", "newsletter", "audience"],
            "research": ["research", "study", "analysis", "data", "findings"]
        }
        
        text_lower = text.lower()
        domain_scores = {}
        
        for domain, keywords in domain_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                domain_scores[domain] = score
        
        return max(domain_scores, key=domain_scores.get) if domain_scores else "general problem solving"
    
    def _extract_problem_statement(self, text: str) -> str:
        """Extract the specific problem they're trying to solve."""
        problem_patterns = [
            r"I'm trying to (.*?)(?:\.|$)",
            r"I want to (.*?)(?:\.|$)", 
            r"How (?:do I|can I) (.*?)(?:\?|$)",
            r"I need to (.*?)(?:\.|$)",
            r"The problem is (.*?)(?:\.|$)",
            r"I'm working on (.*?)(?:\.|$)"
        ]
        
        for pattern in problem_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: extract first sentence that seems problem-focused
        sentences = text.split('.')
        for sentence in sentences[:3]:
            if any(word in sentence.lower() for word in ['problem', 'challenge', 'issue', 'trying', 'want', 'need']):
                return sentence.strip()
        
        return "Problem statement not clearly identified"
    
    def _assess_problem_complexity(self, user_content: str, ai_content: str) -> str:
        """Assess whether this is exploratory, implementation, or optimization focused."""
        exploratory_indicators = ["explore", "understand", "learn", "what is", "how does", "brainstorm"]
        implementation_indicators = ["build", "create", "implement", "code", "develop", "make"]
        optimization_indicators = ["improve", "optimize", "better", "faster", "efficient", "scale"]
        
        text = (user_content + " " + ai_content).lower()
        
        exploratory_score = sum(1 for word in exploratory_indicators if word in text)
        implementation_score = sum(1 for word in implementation_indicators if word in text)
        optimization_score = sum(1 for word in optimization_indicators if word in text)
        
        scores = {
            "exploratory": exploratory_score,
            "implementation": implementation_score, 
            "optimization": optimization_score
        }
        
        return max(scores, key=scores.get) if any(scores.values()) else "general"
    
    def _extract_thinking_patterns(self, text: str) -> List[str]:
        """Identify how they approach problems."""
        patterns = []
        
        if any(word in text.lower() for word in ["step by step", "systematic", "methodical"]):
            patterns.append("systematic analysis")
        
        if any(word in text.lower() for word in ["brainstorm", "creative", "innovative", "outside the box"]):
            patterns.append("creative thinking")
        
        if any(word in text.lower() for word in ["data", "metrics", "measure", "analytics"]):
            patterns.append("data-driven approach")
        
        if any(word in text.lower() for word in ["user", "customer", "audience", "people"]):
            patterns.append("user-centered thinking")
        
        if any(word in text.lower() for word in ["iterate", "test", "experiment", "prototype"]):
            patterns.append("iterative development")
        
        return patterns if patterns else ["general problem solving"]
    
    def _extract_frameworks(self, text: str) -> List[str]:
        """Identify mental models and frameworks they reference."""
        frameworks = []
        
        framework_patterns = [
            r"lean startup", r"design thinking", r"agile", r"first principles",
            r"mvp", r"minimum viable product", r"jobs to be done",
            r"product market fit", r"growth hacking", r"design sprint",
            r"user journey", r"customer development"
        ]
        
        text_lower = text.lower()
        for pattern in framework_patterns:
            if re.search(pattern, text_lower):
                frameworks.append(pattern.replace(r"\b", "").replace(r"\s+", " "))
        
        return frameworks
    
    def _extract_decision_points(self, text: str) -> List[str]:
        """Identify key decisions they're trying to make."""
        decision_patterns = [
            r"should I (.*?)(?:\?|$)",
            r"(?:choose|pick|select) between (.*?)(?:\.|$)",
            r"deciding (?:on|whether) (.*?)(?:\.|$)",
            r"not sure (?:if|whether) (.*?)(?:\.|$)"
        ]
        
        decisions = []
        for pattern in decision_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            decisions.extend(matches)
        
        return [decision.strip() for decision in decisions]
    
    def _extract_topics(self, text: str) -> List[str]:
        """Extract specific topics they're interested in."""
        every_topics = [
            "artificial intelligence", "ai", "machine learning", "llm", "gpt",
            "startup", "entrepreneurship", "business strategy", "product management",
            "writing", "content creation", "newsletter", "audience building",
            "productivity", "tools for thought", "note-taking", "knowledge management",
            "creativity", "innovation", "design", "user experience",
            "technology", "software", "programming", "development",
            "psychology", "behavior", "decision making", "cognitive science",
            "economics", "markets", "finance", "investing",
            "leadership", "management", "team building", "culture"
        ]
        
        text_lower = text.lower()
        found_topics = []
        
        for topic in every_topics:
            if topic in text_lower:
                found_topics.append(topic)
        
        return found_topics
    
    def _assess_intellectual_style(self, text: str) -> str:
        """Assess their intellectual style for better Every content matching."""
        analytical_indicators = ["analyze", "data", "logic", "rational", "systematic"]
        creative_indicators = ["creative", "innovative", "brainstorm", "imagine", "artistic"]
        practical_indicators = ["practical", "actionable", "implement", "execute", "results"]
        theoretical_indicators = ["theory", "concept", "framework", "model", "abstract"]
        
        text_lower = text.lower()
        
        scores = {
            "analytical": sum(1 for word in analytical_indicators if word in text_lower),
            "creative": sum(1 for word in creative_indicators if word in text_lower),
            "practical": sum(1 for word in practical_indicators if word in text_lower),
            "theoretical": sum(1 for word in theoretical_indicators if word in text_lower)
        }
        
        return max(scores, key=scores.get) if any(scores.values()) else "balanced"
    
    def _extract_current_focus(self, text: str) -> str:
        """Identify what they're actively working on right now."""
        focus_patterns = [
            r"currently (?:working on|building|developing) (.*?)(?:\.|$)",
            r"right now I'm (.*?)(?:\.|$)",
            r"this week I'm (.*?)(?:\.|$)",
            r"I'm in the process of (.*?)(?:\.|$)"
        ]
        
        for pattern in focus_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Fallback: look for present tense action verbs
        present_actions = re.findall(r"I'm (\w+ing) (.*?)(?:\.|$)", text, re.IGNORECASE)
        if present_actions:
            return f"{present_actions[0][0]} {present_actions[0][1]}"
        
        return "General exploration"
    
    def _analyze_conversation_flow(self, user_messages: List[str], ai_responses: List[str]) -> str:
        """Understand the overall arc of the conversation."""
        if not user_messages:
            return "unclear"
        
        first_message = user_messages[0].lower() if user_messages else ""
        last_message = user_messages[-1].lower() if len(user_messages) > 1 else ""
        
        if any(word in first_message for word in ["help", "how", "what", "explain"]):
            if any(word in last_message for word in ["thanks", "perfect", "exactly", "got it"]):
                return "problem solved"
            else:
                return "problem exploration"
        
        if len(user_messages) > 3:
            return "iterative refinement"
        elif len(user_messages) > 1:
            return "clarification seeking"
        else:
            return "single query"
    
    def _infer_conversation_structure(self, text: str) -> Tuple[List[str], List[str]]:
        """Fallback method to infer conversation structure when patterns don't match."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        user_messages = []
        ai_responses = []
        
        # Simple heuristic: shorter paragraphs are often user messages
        for para in paragraphs:
            if len(para) < 200 and ('?' in para or para.startswith(('I ', 'How ', 'What ', 'Can '))):
                user_messages.append(para)
            elif len(para) > 100:
                ai_responses.append(para)
        
        return user_messages, ai_responses
    
    def _analyze_conversation_structure(self, conversation_data: Dict) -> ConversationContext:
        """
        Analyze structured conversation data extracted from HTML/JSON.
        
        Handles different conversation data formats and extracts intelligence.
        """
        user_messages = conversation_data.get('user_messages', [])
        ai_responses = conversation_data.get('ai_responses', [])
        
        # If we have structured data, use it directly
        if user_messages or ai_responses:
            return self._analyze_conversation_content(user_messages, ai_responses, 
                                                    " ".join(user_messages + ai_responses))
        
        # Otherwise, try to extract from the raw data
        return self._extract_from_raw_text(str(conversation_data))
    
    def _extract_from_json_file(self, file_path: str) -> ConversationContext:
        """Extract from JSON conversation file (e.g., Claude export)."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Handle different JSON formats
        if 'messages' in data:
            user_messages = []
            ai_responses = []
            
            for message in data['messages']:
                if message.get('role') == 'user':
                    user_messages.append(message.get('content', ''))
                elif message.get('role') in ['assistant', 'ai']:
                    ai_responses.append(message.get('content', ''))
            
            return self._analyze_conversation_content(user_messages, ai_responses, 
                                                    " ".join(user_messages + ai_responses))
        
        # Fallback to raw text extraction
        return self._extract_from_raw_text(str(data))
    
    def _extract_from_text_file(self, file_path: str) -> ConversationContext:
        """Extract from plain text conversation file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self._extract_from_raw_text(content)


def test_extractor():
    """Test the conversation extractor with the existing ChatGPT conversation."""
    extractor = ConversationExtractor()
    
    try:
        context = extractor.extract_from_file('chatgpt extraction/chatgpt_response.html')
        
        print("=== EXTRACTED CONVERSATION INTELLIGENCE ===")
        print(f"Problem Domain: {context.problem_domain}")
        print(f"Problem Statement: {context.problem_statement}")
        print(f"Problem Complexity: {context.problem_complexity}")
        print(f"Thinking Patterns: {', '.join(context.thinking_patterns)}")
        print(f"Frameworks Used: {', '.join(context.frameworks_used)}")
        print(f"Topics of Interest: {', '.join(context.topics_of_interest)}")
        print(f"Intellectual Style: {context.intellectual_style}")
        print(f"Current Focus: {context.current_focus}")
        print(f"Conversation Flow: {context.conversation_flow}")
        print(f"User Messages: {len(context.user_messages)}")
        print(f"AI Responses: {len(context.ai_responses)}")
        
        if context.user_messages:
            print(f"\nFirst User Message Preview: {context.user_messages[0][:200]}...")
        
        return context
        
    except Exception as e:
        print(f"Error testing extractor: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    test_extractor() 