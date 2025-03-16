from flask import session, current_app
from flask_socketio import join_room, leave_room, emit
from extensions import socketio, db
from models import Chat, ChatHistory
from datetime import datetime
from sqlalchemy import func
import uuid  # For generating anonymous usernames

# Tracks participants in each chat room (key=join_code, value=set of user names)
participants = {}

# REMOVE this line, as we no longer load personalities here:
# personalities = load_personalities()

@socketio.on('join')
def handle_join(data):
    """
    Handle a user (authenticated or anonymous) joining the chat room.
    chat_id = the chat's join_code (UUID)
    username = user's display name or a placeholder
    """
    chat_uuid = str(data.get('chat_id'))
    username = data.get('username')

    print(f"DEBUG: Checking chat join attempt for chat_id: {chat_uuid}, username: {username}")

    # Look up the chat by its join_code
    chat = Chat.query.filter_by(join_code=chat_uuid).first()
    if not chat:
        print(f"DEBUG: Chat not found for join_code: {chat_uuid}")
        emit('status', {'msg': 'Error: Chat room not found.'})
        return

    print(f"DEBUG: Chat found! Title={chat.title}, allow_anonymous={chat.allow_anonymous}")

    # If the chat requires authentication, ensure user is logged in
    if not chat.allow_anonymous and 'user_id' not in session:
        print("DEBUG: Access denied - user must be authenticated.")
        emit('status', {'msg': 'Error: Authentication required for this chat.'})
        return

    # If user is not authenticated, assign an anonymous name
    if 'user_id' not in session:
        username = f"anon-{uuid.uuid4().hex[:3]}"
        print(f"DEBUG: Assigned anonymous username: {username}")
    else:
        # Optionally, override the username with session data, if you prefer
        # username = session.get('username')
        pass

    # Join this chat room by its join_code
    join_room(chat_uuid)

    # Update the participants dictionary
    if chat_uuid not in participants:
        participants[chat_uuid] = set()
    participants[chat_uuid].add(username)

    print(f"DEBUG: Current participants in {chat_uuid}: {participants[chat_uuid]}")

    # Notify the room of a participant update and a status message
    emit('participant_update', {'participants': list(participants[chat_uuid])}, room=chat_uuid)
    emit('status', {'msg': f'{username} has entered the chat.'}, room=chat_uuid)


@socketio.on('leave')
def handle_leave(data):
    """
    Remove a user from the chat room (on page unload or explicit leave).
    """
    chat_uuid = str(data.get('chat_id'))
    username = data.get('username')

    leave_room(chat_uuid)
    if chat_uuid in participants and username in participants[chat_uuid]:
        participants[chat_uuid].remove(username)
        print(f"{username} left room {chat_uuid}")
        emit('participant_update', {'participants': list(participants[chat_uuid])}, room=chat_uuid)
        emit('status', {'msg': f'{username} has left the chat.'}, room=chat_uuid)


@socketio.on('chat_message')
def handle_chat_message(data):
    """
    Broadcast a new human message to the chat room and handle AI responses.
    chat_id = join_code (UUID)
    """
    chat_uuid = str(data.get('chat_id'))
    username = data.get('username')
    message = data.get('message')
    sender_id = data.get('sender_id')

    # Convert the join_code -> numeric ID for storing in ChatHistory
    chat = Chat.query.filter_by(join_code=chat_uuid).first()
    if not chat:
        print(f"DEBUG: Chat room not found for join_code={chat_uuid}")
        emit('status', {'msg': 'Error: Chat not found.'})
        return

    numeric_chat_id = str(chat.id)

    # Figure out the next message number for the room
    max_room_msg_id = db.session.query(func.max(ChatHistory.room_message_id)) \
                          .filter_by(chat_id=numeric_chat_id).scalar() or 0

    # Create the new message row in DB
    new_message = ChatHistory(
        chat_id=numeric_chat_id,
        sender_id=sender_id,
        sender_name=username,
        message=message,
        room_message_id=max_room_msg_id + 1
    )
    db.session.add(new_message)
    db.session.commit()

    # Broadcast the new message to all participants in chat_uuid
    emit('chat_message', {
        'room_message_id': new_message.room_message_id,
        'username': username,
        'message': message,
        'db_id': new_message.id  # So new messages can be deleted in real time
    }, room=chat_uuid, include_self=True)

    # Gather full context for the AI:
    chat_title = chat.title  # The chat's name
    current_participants = list(participants.get(chat_uuid, set()))  # All users in the chat
    full_history = ChatHistory.query.filter_by(chat_id=numeric_chat_id).order_by(ChatHistory.id).all()  # Entire conversation

    # Use current_app to get the single loaded personalities
    from flask import current_app
    all_personalities = current_app.loaded_personalities

    # Loop through AI personalities in the room
    for personality_name in current_participants:
        # If personality_name is in the dictionary
        if personality_name in all_personalities and username != personality_name:
            # Print debug info about what we'll pass
            print("\n===== AI Debug =====")
            print(f"Chat Title: {chat_title}")
            print(f"Participants: {current_participants}")
            print(f"History Count: {len(full_history)}")
            print(f"Latest User Message: {message}")
            print(f"AI Personality: {personality_name}")
            print("===== End Debug ====\n")

            # Retrieve the plugin module
            plugin_module = all_personalities[personality_name]["module"]

            # Suppose plugin's signature is generate_response(title, participants, history, latest_user_msg)
            ai_response = plugin_module.generate_response(
                chat_title,
                current_participants,
                full_history,
                message
            )

            if ai_response.strip() and len(ai_response.split()) >= 3:
                new_ai_msg = ChatHistory(
                    chat_id=numeric_chat_id,
                    sender_id=-1,
                    sender_name=personality_name,
                    message=ai_response,
                    room_message_id=max_room_msg_id + 2
                )
                db.session.add(new_ai_msg)
                db.session.commit()

                emit('chat_message', {
                    'room_message_id': new_ai_msg.room_message_id,
                    'username': personality_name,
                    'message': ai_response,
                    'db_id': new_ai_msg.id
                }, room=chat_uuid, include_self=True)


@socketio.on('delete_message')
def handle_delete_message(data):
    """
    Allows an admin to prune a specific message from the DB, in real time.
    chat_id = join_code (UUID)
    message_id = the numeric ID from ChatHistory
    """
    chat_uuid = data.get('chat_id')
    message_id = data.get('message_id')

    # Enforce admin check
    if not session.get('is_admin'):
        print("DEBUG: Non-admin user tried to delete a message.")
        emit('status', {'msg': 'Error: Not authorized to delete messages.'}, room=chat_uuid)
        return

    # Attempt to delete the row
    deleted_rows = ChatHistory.query.filter_by(id=message_id).delete()
    db.session.commit()

    if deleted_rows:
        print(f"DEBUG: Message {message_id} deleted from chat {chat_uuid}.")
        # Notify all clients in this chat room to remove the message
        emit('message_deleted', {'message_id': message_id}, room=chat_uuid)
    else:
        print(f"DEBUG: Message {message_id} not found.")
        emit('status', {'msg': f'Error: Message {message_id} not found.'}, room=chat_uuid)


@socketio.on('add_personality')
def handle_add_personality(data):
    """
    Add an AI personality to the chat.
    """
    chat_uuid = str(data.get('chat_id'))
    personality_name = data.get('personality')

    print(f"DEBUG: Received add_personality event for chat={chat_uuid}, AI={personality_name}")

    from flask import current_app
    all_personalities = current_app.loaded_personalities

    if personality_name not in all_personalities:
        emit('status', {'msg': f'Error: Personality \"{personality_name}\" not found.'}, room=chat_uuid)
        return

    join_room(chat_uuid)

    if chat_uuid not in participants:
        participants[chat_uuid] = set()

    if personality_name not in participants[chat_uuid]:
        participants[chat_uuid].add(personality_name)
        print(f"DEBUG: Added AI '{personality_name}' to room={chat_uuid}")
        emit('participant_update', {'participants': list(participants[chat_uuid])}, room=chat_uuid)
        emit('status', {'msg': f'{personality_name} has joined the chat.'}, room=chat_uuid)
    else:
        print(f"DEBUG: AI '{personality_name}' was already in the room={chat_uuid}")


@socketio.on('remove_personality')
def handle_remove_personality(data):
    """
    Remove an AI personality from the chat.
    """
    chat_uuid = str(data.get('chat_id'))
    personality_name = data.get('personality')

    print(f"DEBUG: remove_personality for chat={chat_uuid}, AI={personality_name}")

    if chat_uuid in participants and personality_name in participants[chat_uuid]:
        participants[chat_uuid].remove(personality_name)
        print(f"DEBUG: AI '{personality_name}' removed from room={chat_uuid}")
        emit('participant_update', {'participants': list(participants[chat_uuid])}, room=chat_uuid)
        emit('status', {'msg': f'{personality_name} has left the chat.'}, room=chat_uuid)


@socketio.on('disconnect')
def handle_disconnect():
    print("A user disconnected")
