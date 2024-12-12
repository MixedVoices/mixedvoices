def history_to_transcript(history):
    messages = []
    for message in history:
        if message["role"] == "user":
            messages.append(f"Bot: {message['content']}")
        elif message["role"] == "assistant":
            messages.append(f"User: {message['content']}")
    return "\n".join(messages)
