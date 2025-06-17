#!/usr/bin/env python3
"""
Elegant Conversation Intelligence Extractor
==========================================

Extracts intellectual DNA from AI conversations with maximum simplicity and elegance.
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
    """Structured conversation intelligence for Every's knowledge matching."""
    # Problem Analysis
    problem_domain: str
    problem_statement: str
    problem_complexity: str
    
    # Thinking Process
    thinking_patterns: List[str]
    frameworks_used: List[str]
    decision_points: List[str]
    
    # Context Clues
    topics_of_interest: List[str]
    intellectual_style: str
    current_focus: str
    
    # Raw Data
    user_messages: List[str]
    ai_responses: List[str]
    conversation_flow: str


class ConversationExtractor:
    """Universal AI conversation intelligence extractor."""
    
    # Configuration data - all the patterns and keywords in one place
    DOMAINS = {
        "AI product development": ["ai", "machine learning", "model", "llm", "gpt", "claude"],
        "startup strategy": ["startup", "business", "market", "customers", "revenue"],
        "technical architecture": ["system", "architecture", "database", "api", "infrastructure"],
        "product design": ["user", "interface", "ux", "design", "product"],
        "content strategy": ["content", "writing", "blog", "newsletter", "audience"],
        "research": ["research", "study", "analysis", "data", "findings"]
    }
    
    PROBLEM_PATTERNS = [
        r"I'm trying to (.*?)(?:\.|$)",
        r"I want to (.*?)(?:\.|$)", 
        r"How (?:do I|can I) (.*?)(?:\?|$)",
        r"I need to (.*?)(?:\.|$)",
        r"The problem is (.*?)(?:\.|$)",
        r"I'm working on (.*?)(?:\.|$)"
    ]
    
    COMPLEXITY_INDICATORS = {
        "exploratory": ["explore", "understand", "learn", "what is", "how does", "brainstorm"],
        "implementation": ["build", "create", "implement", "code", "develop", "make"],
        "optimization": ["improve", "optimize", "better", "faster", "efficient", "scale"]
    }
    
    THINKING_PATTERNS = {
        "systematic analysis": ["step by step", "systematic", "methodical"],
        "creative thinking": ["brainstorm", "creative", "innovative", "outside the box"],
        "data-driven approach": ["data", "metrics", "measure", "analytics"],
        "user-centered thinking": ["user", "customer", "audience", "people"],
        "iterative development": ["iterate", "test", "experiment", "prototype"]
    }
    
    FRAMEWORKS = [
        "lean startup", "design thinking", "agile", "first principles",
        "mvp", "minimum viable product", "jobs to be done",
        "product market fit", "growth hacking", "design sprint",
        "user journey", "customer development"
    ]
    
    DECISION_PATTERNS = [
        r"should I (.*?)(?:\?|$)",
        r"(?:choose|pick|select) between (.*?)(?:\.|$)",
        r"deciding (?:on|whether) (.*?)(?:\.|$)",
        r"not sure (?:if|whether) (.*?)(?:\.|$)"
    ]
    
    EVERY_TOPICS = [
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
    
    INTELLECTUAL_STYLES = {
        "analytical": ["analyze", "data", "logic", "rational", "systematic"],
        "creative": ["creative", "innovative", "brainstorm", "imagine", "artistic"],
        "practical": ["practical", "actionable", "implement", "execute", "results"],
        "theoretical": ["theory", "concept", "framework", "model", "abstract"]
    }
    
    FOCUS_PATTERNS = [
        r"currently (?:working on|building|developing) (.*?)(?:\.|$)",
        r"right now I'm (.*?)(?:\.|$)",
        r"this week I'm (.*?)(?:\.|$)",
        r"I'm in the process of (.*?)(?:\.|$)"
    ]
    
    CONVERSATION_PATTERNS = [
        (r'User:(.*?)(?=Assistant:|AI:|ChatGPT:|$)', r'(?:Assistant:|AI:|ChatGPT:)(.*?)(?=User:|$)'),
        (r'Human:(.*?)(?=AI:|Assistant:|$)', r'(?:AI:|Assistant:)(.*?)(?=Human:|$)'),
        (r'You:(.*?)(?=ChatGPT:|Claude:|$)', r'(?:ChatGPT:|Claude:)(.*?)(?=You:|$)')
    ]

    def extract_from_file(self, file_path: str) -> ConversationContext:
        """Extract intelligence from any conversation file format."""
        path = Path(file_path)
        content = path.read_text(encoding='utf-8')
        
        if path.suffix == '.html':
            return self._process_html(content)
        elif path.suffix == '.json':
            return self._process_json(content)
        else:
            return self._process_text(content)

    def extract_from_text(self, text: str) -> ConversationContext:
        """Extract intelligence from raw conversation text."""
        return self._process_text(text)

    def _process_html(self, content: str) -> ConversationContext:
        """Process HTML content with smart fallbacks."""
        # Try structured extraction first
        structured_data = self._extract_html_conversation(content)
        if structured_data:
            return self._analyze_messages(
                structured_data.get('user_messages', []),
                structured_data.get('ai_responses', [])
            )
        
        # Fallback to visible text
        soup = BeautifulSoup(content, 'html.parser')
        return self._process_text(soup.get_text())

    def _process_json(self, content: str) -> ConversationContext:
        """Process JSON conversation data."""
        try:
            data = json.loads(content)
            if 'messages' in data:
                user_msgs = [msg['content'] for msg in data['messages'] if msg.get('role') == 'user']
                ai_msgs = [msg['content'] for msg in data['messages'] if msg.get('role') in ['assistant', 'ai']]
                return self._analyze_messages(user_msgs, ai_msgs)
        except:
            pass
        return self._process_text(content)

    def _process_text(self, text: str) -> ConversationContext:
        """Process raw text conversation."""
        user_messages, ai_responses = self._split_conversation(text)
        return self._analyze_messages(user_messages, ai_responses)

    def _extract_html_conversation(self, html_content: str) -> Optional[Dict]:
        """Extract conversation from HTML with specific patterns."""
        # Look for specific ChatGPT patterns
        user_match = re.search(r'Every has thought.*?(?=\\"|$)', html_content, re.DOTALL)
        if user_match:
            user_msg = self._clean_escaped_text(user_match.group(0))
            
            # Look for AI response patterns
            ai_patterns = [
                r'Let.*?s Stress-Test the Core Idea.*?(?=\\"|$)',
                r'Problem to Beat.*?(?=\\"|$)',
                r'Interaction Model Variants.*?(?=\\"|$)'
            ]
            
            ai_msg = ""
            for pattern in ai_patterns:
                ai_match = re.search(pattern, html_content, re.DOTALL)
                if ai_match:
                    ai_msg = self._clean_escaped_text(ai_match.group(0))
                    break
            
            return {
                'user_messages': [user_msg],
                'ai_responses': [ai_msg] if ai_msg else []
            }
        
        # Try JSON patterns in HTML
        json_patterns = [
            r'"messages":\s*\[(.*?)\]',
            r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
        ]
        
        for pattern in json_patterns:
            match = re.search(pattern, html_content, re.DOTALL)
            if match:
                try:
                    json_str = re.sub(r'window\.__\w+__\s*=\s*', '', match.group(0)).rstrip(';')
                    return json.loads(json_str)
                except:
                    continue
        
        return None

    def _split_conversation(self, text: str) -> Tuple[List[str], List[str]]:
        """Split text into user and AI messages using smart patterns."""
        text = html.unescape(text).replace('\\n', '\n').replace('\\"', '"')
        
        # Try conversation patterns
        for user_pattern, ai_pattern in self.CONVERSATION_PATTERNS:
            user_matches = re.findall(user_pattern, text, re.DOTALL | re.IGNORECASE)
            ai_matches = re.findall(ai_pattern, text, re.DOTALL | re.IGNORECASE)
            
            if user_matches or ai_matches:
                return [msg.strip() for msg in user_matches], [msg.strip() for msg in ai_matches]
        
        # Fallback: infer structure from paragraph patterns
        return self._infer_structure(text)

    def _infer_structure(self, text: str) -> Tuple[List[str], List[str]]:
        """Infer conversation structure from text patterns."""
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        user_messages, ai_responses = [], []
        
        for para in paragraphs:
            if len(para) < 200 and ('?' in para or para.startswith(('I ', 'How ', 'What ', 'Can '))):
                user_messages.append(para)
            elif len(para) > 100:
                ai_responses.append(para)
        
        return user_messages, ai_responses

    def _analyze_messages(self, user_messages: List[str], ai_responses: List[str]) -> ConversationContext:
        """Extract all intelligence from conversation messages."""
        user_text = " ".join(user_messages)
        ai_text = " ".join(ai_responses)
        full_text = user_text + " " + ai_text
        
        return ConversationContext(
            problem_domain=self._extract_by_keywords(user_text, self.DOMAINS, "general problem solving"),
            problem_statement=self._extract_by_patterns(user_text, self.PROBLEM_PATTERNS) or self._extract_problem_fallback(user_text),
            problem_complexity=self._extract_by_keywords(full_text, self.COMPLEXITY_INDICATORS, "general"),
            thinking_patterns=self._extract_patterns_list(user_text, self.THINKING_PATTERNS),
            frameworks_used=self._extract_frameworks(full_text),
            decision_points=self._extract_by_patterns_list(user_text, self.DECISION_PATTERNS),
            topics_of_interest=self._extract_topics(user_text),
            intellectual_style=self._extract_by_keywords(user_text, self.INTELLECTUAL_STYLES, "balanced"),
            current_focus=self._extract_by_patterns(user_text, self.FOCUS_PATTERNS) or self._extract_focus_fallback(user_text),
            user_messages=user_messages,
            ai_responses=ai_responses,
            conversation_flow=self._analyze_flow(user_messages)
        )

    # Elegant utility methods that eliminate repetition
    def _extract_by_keywords(self, text: str, keyword_dict: Dict[str, List[str]], default: str) -> str:
        """Extract category by scoring keyword matches."""
        text_lower = text.lower()
        scores = {category: sum(1 for word in words if word in text_lower) 
                 for category, words in keyword_dict.items()}
        scores = {k: v for k, v in scores.items() if v > 0}
        return max(scores, key=scores.get) if scores else default

    def _extract_by_patterns(self, text: str, patterns: List[str]) -> Optional[str]:
        """Extract first match from regex patterns."""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return None

    def _extract_by_patterns_list(self, text: str, patterns: List[str]) -> List[str]:
        """Extract all matches from regex patterns."""
        results = []
        for pattern in patterns:
            results.extend(re.findall(pattern, text, re.IGNORECASE))
        return [r.strip() for r in results]

    def _extract_patterns_list(self, text: str, pattern_dict: Dict[str, List[str]]) -> List[str]:
        """Extract patterns that match keyword lists."""
        text_lower = text.lower()
        found = []
        for pattern_name, keywords in pattern_dict.items():
            if any(word in text_lower for word in keywords):
                found.append(pattern_name)
        return found or ["general problem solving"]

    def _extract_frameworks(self, text: str) -> List[str]:
        """Extract framework mentions."""
        text_lower = text.lower()
        return [fw for fw in self.FRAMEWORKS if fw in text_lower]

    def _extract_topics(self, text: str) -> List[str]:
        """Extract Every topics."""
        text_lower = text.lower()
        return [topic for topic in self.EVERY_TOPICS if topic in text_lower]

    def _extract_problem_fallback(self, text: str) -> str:
        """Fallback problem extraction from sentences."""
        sentences = text.split('.')[:3]
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['problem', 'challenge', 'issue', 'trying', 'want', 'need']):
                return sentence.strip()
        return "Problem statement not clearly identified"

    def _extract_focus_fallback(self, text: str) -> str:
        """Fallback focus extraction."""
        present_actions = re.findall(r"I'm (\w+ing) (.*?)(?:\.|$)", text, re.IGNORECASE)
        return f"{present_actions[0][0]} {present_actions[0][1]}" if present_actions else "General exploration"

    def _analyze_flow(self, user_messages: List[str]) -> str:
        """Analyze conversation flow pattern."""
        if not user_messages:
            return "unclear"
        
        first = user_messages[0].lower()
        last = user_messages[-1].lower() if len(user_messages) > 1 else ""
        
        if any(word in first for word in ["help", "how", "what", "explain"]):
            return "problem solved" if any(word in last for word in ["thanks", "perfect", "exactly", "got it"]) else "problem exploration"
        
        if len(user_messages) > 3:
            return "iterative refinement"
        elif len(user_messages) > 1:
            return "clarification seeking"
        else:
            return "single query"

    def _clean_escaped_text(self, text: str) -> str:
        """Clean escaped characters from text."""
        return text.replace('\\n', '\n').replace('\\"', '"').replace('\\\\', '\\')


def test_extractor():
    """Test the simplified extractor."""
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