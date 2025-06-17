#!/usr/bin/env python3
"""
Test the conversation intelligence pipeline on your ChatGPT conversation
"""

from conversation_intelligence_pipeline import ConversationIntelligencePipeline
import json

def main():
    # Initialize the pipeline
    pipeline = ConversationIntelligencePipeline()
    
    # Process your ChatGPT conversation
    print('🧠 Processing your ChatGPT conversation...')
    insights = pipeline.process_conversation_file('chatgpt extraction/chatgpt_response.html')
    
    # Print the results
    pipeline.print_insights(insights, detailed=True)

if __name__ == "__main__":
    main() 