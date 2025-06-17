# One-Shot: Chat to Essay Pipeline

**Universal Conversation Intelligence for Every's Knowledge Base**

This system extracts "intellectual DNA" from AI conversations and bridges them with Every's content. Instead of keyword matching, it understands *what you're really thinking about* and surfaces the most relevant Every insights.

## What It Does

1. **Extracts Conversation Intelligence**: Analyzes your AI conversations to understand:
   - Problem domain and complexity
   - Thinking patterns and frameworks
   - Decision points and areas of focus
   - Intellectual style and current mental model

2. **Generates Targeted Queries**: Converts conversation context into multiple query angles:
   - Conceptual matches (what Every thinks about your topic)
   - Practical frameworks (how Every approaches similar problems)
   - Adjacent domains (unexpected but relevant connections)
   - Contrarian perspectives (alternative viewpoints)

3. **Returns Contextual Insights**: Provides Every articles with:
   - Relevance scoring and reasoning
   - Key quotes that apply to your situation
   - Confidence levels for each insight
   - Suggested follow-up questions

## Core Files

### Pipeline Components
- `conversation_extractor.py` - Universal conversation parser (ChatGPT, Claude, text)
- `every_context_matcher.py` - Converts conversation intelligence to targeted queries
- `conversation_intelligence_pipeline.py` - Complete system orchestration
- `query_system.py` - Vector search interface to Every's content

### Testing
- `test_pipeline.py` - Test the complete system on your ChatGPT conversation
- `chatgpt extraction/` - Sample conversation data for testing

## Quick Start

```bash
# Test with the included ChatGPT conversation
python test_pipeline.py

# Use with your own conversation file
python -c "
from conversation_intelligence_pipeline import ConversationIntelligencePipeline
pipeline = ConversationIntelligencePipeline()
insights = pipeline.process_conversation_file('your_conversation.html')
pipeline.print_insights(insights, detailed=True)
"
```

## Example Output

```
🧠 CONVERSATION INTELLIGENCE INSIGHTS

📋 CONVERSATION SUMMARY:
   User is working on AI product development, specifically trying to connect 
   the human who loves AI and loves reading Every...

🎯 PRIMARY INSIGHTS (5):
   1. 📄 Going Against the Startup Grain
      💡 Why relevant: Direct match for their AI product development problem
      💬 Key quote: "We build tools for our team to become faster and better..."
      🔗 https://every.to/context-window/going-against-the-startup-grain
```

## Architecture Philosophy

**"We Are So Back" Protocol**: Deep conceptual understanding over speed
- Extract intellectual DNA, not just text
- Understand cognitive patterns, not just keywords  
- Build contextual bridges to Every's knowledge
- Generate insights with reasoning, not just search results

## Supported Conversation Formats

- **ChatGPT**: Shared conversation HTML files
- **Claude**: JSON conversation exports  
- **Raw Text**: Any "User: ... Assistant: ..." format
- **Custom**: Extensible for other AI platforms

## Next Steps

This is Step 2 of the Every Content Intelligence Roadmap. The system successfully demonstrates:
- ✅ Universal conversation parsing
- ✅ Intelligent context extraction  
- ✅ Multi-angle query generation
- ✅ Contextual insight synthesis

Ready for Step 3: Web interface and real-time conversation analysis. 