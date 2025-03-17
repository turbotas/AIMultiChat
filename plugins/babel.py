import os
import openai

PERSONALITY_NAME = "Babel (Universal Translator)"
PERSONALITY_DESC = "Babel identifies all spoken languages in the conversation and translates each new message into those other languages."
PERSONALITY_INTELLIGENCE = 8
PERSONALITY_COST = 4.4
PERSONALITY_WINDOW = 200000
PERSONALITY_MAXOUT = 100000

# Create the OpenAI client using the new interface
client = openai.Client(api_key=os.environ.get("CHATGPTAPIKEY"))

# We'll alter the system prompt to instruct the model to detect languages & produce translations
BASE_SYSTEM_PROMPT = """
You are in a multi-person chat as a universal translator named "Babel."
Your goal: detect all languages that have appeared in the chat so far, and for each new message:
- Identify the language of the new message.
- If there's only one language overall, remain silent (return no output).
- Otherwise, translate the new message into every other language used in the conversation so far.
- If the new message is already in multiple languages, handle that gracefully (translate each portion if needed).
- Only produce translations, do not rewrite or comment on the content.
- If no translation is needed, remain silent.

Example behavior:
- If the conversation so far used English and Spanish, and the new message is in English,
  respond only with the Spanish translation. If it's in Spanish, respond only with the English translation.
- If the conversation has 3 languages: English, Spanish, French, then for each new message, respond with the other two languages.
- If a new language appears for the first time in the conversation, add that language to your set of known languages for future translations.

Remember:
- You are not a moderator or rule enforcer; only do translation.
- If no new message is truly in a different language or there's only 1 known language so far, produce no output.
"""

def generate_response(chat_title, participants, chat_history, new_message):
    """
    1) Parse chat_history to detect all unique languages used so far.
    2) For the new_message, figure out whether it requires translation into the other languages.
    3) Return the translations, or "" if no translations are needed.
    """

    # Debug output
    print("\n===== Babel Plugin Debug =====")
    print(f"Chat Title: {chat_title}")
    print(f"Participants: {participants}")
    print(f"History Count: {len(chat_history)}")
    for entry in chat_history:
        print(f"  HISTORY => {entry.sender_name}: {entry.message}")
    print(f"Latest User Message: {new_message}")
    print("===== End Debug =====\n")

    # Merge the base system prompt with some context about the assigned name, etc.
    # We'll degrade to "user" if the model does not support "system."
    combined_system_prompt = (
        BASE_SYSTEM_PROMPT
        + f"\nAdditionally, the chat is titled '{chat_title}'.\n"
        + f"Participants: {participants}.\n"
        + f"IMPORTANT: Your assigned name for this chat is '{PERSONALITY_NAME}'.\n"
        + f"You have to detect languages by analyzing all messages so far, including the newest one."
    )

    # The 'o3-mini' model doesn't allow a "system" role. We'll degrade it to "user."
    model_name = "o3-mini"
    first_role = "system"
    if model_name == "o3-mini":
        first_role = "user"

    # Build the messages array
    messages = [
        {"role": first_role, "content": combined_system_prompt.strip()}
    ]

    # Add each entry from chat_history
    for entry in chat_history:
        # "assistant" if entry.sender_name == PERSONALITY_NAME, else "user"
        role = "assistant" if entry.sender_name == PERSONALITY_NAME else "user"
        formatted_message = f"{entry.sender_name}: {entry.message}"
        messages.append({"role": role, "content": formatted_message})

    # Finally add the new user message
    messages.append({"role": "user", "content": new_message})

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_completion_tokens=2000  # or whatever suits your cost/limits
        )

        ai_reply = response.choices[0].message.content.strip()

        # If the AI decides no translation is needed, it can produce empty or disclaimers:
        if not ai_reply or ai_reply.lower() in ["", "i'm not sure", "i don't know"]:
            return ""

        return ai_reply

    except Exception as e:
        return f"Error: {str(e)}"
