PERSONALITY_NAME = "Echo Bot"

BASE_SYSTEM_PROMPT = """
You are in a multi-person chat. Each message shows the sender name.

- If a user or participant explicitly asks you for a summary or any detail about the conversation so far (the "chat history") or about who is in the chat, you can provide a concise, factual summary.
- You can mention or quote past messages if it helps clarify the user’s request.
- You are not a moderator or rule enforcer. You do not handle personal questions about users unless requested.
- If no one is asking for your input, or the question doesn’t concern you, remain silent or respond minimally.
"""

def generate_response(chat_title, participants, chat_history, new_message):
    """
    A dummy plugin that just echoes back the user's last message.

    :param chat_title:       The name/title of the chat
    :param participants:     The list of participant names
    :param chat_history:     A list of message objects from the DB
    :param new_message:      The latest user message that triggered the AI
    :return:                 Echoes the new_message as the response
    """

    # Debug: print out details about the chat context
    print("\n===== Dummy Plugin Debug =====")
    print(f"Chat Title: {chat_title}")
    print(f"Participants: {participants}")
    print(f"History Count: {len(chat_history)}")
    for entry in chat_history:
        print(f"  HISTORY => {entry.sender_name}: {entry.message}")
    print(f"Latest User Message: {new_message}")
    print("===== End Dummy Plugin Debug =====\n")

    # In a real plugin, we'd incorporate chat_history & new_message
    # into an AI call. For this dummy, we ignore everything and just echo back:
    return new_message
