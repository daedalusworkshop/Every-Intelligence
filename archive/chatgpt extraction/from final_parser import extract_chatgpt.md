from final_parser import extract_chatgpt_conversation

conversation = extract_chatgpt_conversation('chatgpt_share.html')

print(f"Title: {conversation['title']}")
print(f"Created: {conversation['create_time_readable']}")

for message in conversation['messages']:
    print(f"{message['role'].upper()}: {message['content'][:100]}...")