import os
import openai

PERSONALITY_NAME = "ChatGPT 3.5 turbo"

# Create the OpenAI client using the new interface
client = openai.Client(api_key=os.environ.get("CHATGPTAPIKEY"))

# Stronger System Prompt with stricter silence rules
SYSTEM_PROMPT = """
You are participating in a busy multi-person chat room. Messages are numbered, and each message shows the name of the sender before the message content.

⚠️ CRITICAL RULES ⚠️
- Remain SILENT unless your response is CLEARLY required.
- DO NOT respond unless:
   - Your name ("ChatGPT" or "AI") is directly mentioned.
   - Someone asks a factual question, requests information, or asks for help that is clearly directed at you.
- Ignore casual greetings like "Hello" or "How’s everyone doing?" unless you are directly addressed.
- DO NOT act as a moderator, rule-enforcer, or conversation guide. You are NOT in charge — you are only a participant.
- DO NOT give social advice, comment on user behavior, or attempt to influence the conversation unless requested.
- If you're unsure whether to respond — stay silent. **Silence is better than an unnecessary response.**

✅ When responding:
- Be concise, factual, and helpful.
- Avoid pleasantries like "Sure!" or "I'm happy to help!" unless explicitly asked.

❗ If your response would add no value — remain silent. SILENCE is the default state.
"""

def generate_response(chat_history, new_message):
    """
    Generate a response from ChatGPT based on the chat history and the new message (or do not respond)

    :param chat_history: A list of chat history objects. Each object is expected to have
                         attributes like room_message_id, sender_name, and message.
    :param new_message: The latest user message (string).
    :return: The AI's response as a string.
    """
    # Format the conversation messages for better context
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add previous chat history with proper formatting
    for entry in chat_history:
        role = "assistant" if entry.sender_name == "ChatGPT" else "user"
        formatted_message = f"#{entry.room_message_id} {entry.sender_name}: {entry.message}"
        messages.append({"role": role, "content": formatted_message})

    # Add the new user message with the same format
    formatted_new_message = f"{new_message}"
    messages.append({"role": "user", "content": formatted_new_message})

    try:
        # Correct usage for the new API format
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=300
        )

        # Extract the assistant's reply
        ai_reply = response.choices[0].message.content.strip()

        # Filter out non-essential responses
        if not ai_reply or ai_reply.lower() in ["", "i'm not sure", "i don't know"]:
            return ""  # Suppress unwanted responses
        return ai_reply

    except Exception as e:
        return f"Error: {str(e)}"
