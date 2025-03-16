import os
import openai

PERSONALITY_NAME = "Cassie (ChatGPT 4o Mini)"
PERSONALITY_DESC = "GPT-4o mini (“o” for “omni”) is a fast, affordable small model for focused tasks. It accepts both text and image inputs, and produces text outputs (including Structured Outputs). It is ideal for fine-tuning, and model outputs from a larger model like GPT-4o can be distilled to GPT-4o-mini to produce similar results at lower cost and latency."
PERSONALITY_INTELLIGENCE = 2
# price per million tokens use the dearest of input and output!
PERSONALITY_COST = 0.6
PERSONALITY_WINDOW = 128000
PERSONALITY_MAXOUT = 16384

# Create the OpenAI client using the new interface
client = openai.Client(api_key=os.environ.get("CHATGPTAPIKEY"))

BASE_SYSTEM_PROMPT = """
You are in a multi-person chat. Each message shows the sender name.

- If a user or participant explicitly asks you for a summary or any detail about the conversation so far (the "chat history") or about who is in the chat, you can provide a concise, factual summary.
- You can mention or quote past messages if it helps clarify the user’s request.
- You are not a moderator or rule enforcer. You do not handle personal questions about users unless requested. 
- If no one is asking for your input, or the question doesn’t concern you, remain silent or respond minimally.
"""


def generate_response(chat_title, participants, chat_history, new_message):
    """
    Generate a response from ChatGPT based on:
      - chat_title       (str)  : The name/title of the chat
      - participants     (list) : The list of participant names
      - chat_history     (list) : A list of message objects from the DB
      - new_message      (str)  : The latest user message that triggered the AI

    :return: The AI's response as a string (or empty if it chooses to remain silent).
    """

    # Print a debug line to show the updated formatting
    print("\n===== Plugin Debug (No numbering) =====")
    print(f"Chat Title: {chat_title}")
    print(f"Participants: {participants}")
    print(f"History Count: {len(chat_history)}")
    for entry in chat_history:
        print(f"  HISTORY => {entry.sender_name}: {entry.message}")
    print(f"Latest User Message: {new_message}")
    print("===== End Plugin Debug =====\n")

    # Merge the base system prompt with the chat’s title/participants
    combined_system_prompt = (
        BASE_SYSTEM_PROMPT
        + f"\nAdditionally, the chat is titled '{chat_title}'.\n"
        + f"Participants: {participants}.\n"
        + f"IMPORTANT: Your assigned name for this chat is '{PERSONALITY_NAME}'. If someone asks your name or references you, reply with that exact name.\n"
    )

    # Start building the messages array
    messages = [
        {"role": "system", "content": combined_system_prompt.strip()}
    ]

    # Add each entry from chat_history
    for entry in chat_history:
        # "assistant" if entry.sender_name matches PERSONALITY_NAME, else "user"
        role = "assistant" if entry.sender_name == PERSONALITY_NAME else "user"
        formatted_message = f"{entry.sender_name}: {entry.message}"
        messages.append({"role": role, "content": formatted_message})

    # Finally add the new user message
    messages.append({"role": "user", "content": new_message})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300
        )

        ai_reply = response.choices[0].message.content.strip()

        # Filter out non-essential responses
        if not ai_reply or ai_reply.lower() in ["", "i'm not sure", "i don't know"]:
            return ""
        return ai_reply

    except Exception as e:
        return f"Error: {str(e)}"
