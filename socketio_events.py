from flask_socketio import join_room, leave_room, emit
from extensions import socketio, db, load_personalities
from models import ChatHistory
from datetime import datetime
from sqlalchemy import func

# Dictionary to track participants per room (chat_id -> set of usernames)
participants = {}

# Load available personalities
personalities = load_personalities()

@socketio.on('add_personality')
def handle_add_personality(data):
    chat_id = str(data.get('chat_id'))
    personality_name = data.get('personality')

    if personality_name not in personalities:
        emit('status', {'msg': f'Error: Personality "{personality_name}" not found.'}, room=chat_id)
        return

    # Add personality to the room
    join_room(chat_id)

    # Ensure the room has an entry in the participants dictionary
    if chat_id not in participants:
        participants[chat_id] = set()

    if personality_name not in participants[chat_id]:
        participants[chat_id].add(personality_name)
        print(f"{personality_name} added to room {chat_id}")
        emit('participant_update', {'participants': list(participants[chat_id])}, room=chat_id)
        emit('status', {'msg': f'{personality_name} has joined the chat.'}, room=chat_id)


@socketio.on('remove_personality')
def handle_remove_personality(data):
    chat_id = str(data.get('chat_id'))
    personality_name = data.get('personality')

    if chat_id in participants and personality_name in participants[chat_id]:
        participants[chat_id].remove(personality_name)
        print(f"{personality_name} removed from room {chat_id}")
        emit('participant_update', {'participants': list(participants[chat_id])}, room=chat_id)
        emit('status', {'msg': f'{personality_name} has left the chat.'}, room=chat_id)


@socketio.on('join')
def handle_join(data):
    chat_id = str(data.get('chat_id'))
    username = data.get('username')
    join_room(chat_id)

    if chat_id not in participants:
        participants[chat_id] = set()
    participants[chat_id].add(username)

    print(f"{username} joined room {chat_id}")
    emit('participant_update', {'participants': list(participants[chat_id])}, room=chat_id)
    emit('status', {'msg': f'{username} has entered the chat.'}, room=chat_id)


@socketio.on('chat_message')
def handle_chat_message(data):
    chat_id = str(data.get('chat_id'))
    username = data.get('username')
    message = data.get('message')
    sender_id = data.get('sender_id')

    max_room_msg_id = db.session.query(func.max(ChatHistory.room_message_id)) \
                          .filter_by(chat_id=chat_id).scalar() or 0

    # Save the human message
    new_message = ChatHistory(
        chat_id=chat_id,
        sender_id=sender_id,
        sender_name=username,
        message=message,
        room_message_id=max_room_msg_id + 1
    )
    db.session.add(new_message)
    db.session.commit()

    emit('chat_message', {
        'room_message_id': new_message.room_message_id,
        'username': username,
        'message': message,
    }, room=chat_id, include_self=True)

    # Process responses for active AI personalities
    for personality_name in participants.get(chat_id, set()):
        if personality_name in personalities and username != personality_name:
            ai_response = personalities[personality_name].generate_response([], message)

            if ai_response.strip() and len(ai_response.split()) >= 3:
                new_ai_message = ChatHistory(
                    chat_id=chat_id,
                    sender_id=-1,
                    sender_name=personality_name,
                    message=ai_response,
                    room_message_id=max_room_msg_id + 2
                )
                db.session.add(new_ai_message)
                db.session.commit()

                emit('chat_message', {
                    'room_message_id': new_ai_message.room_message_id,
                    'username': personality_name,
                    'message': ai_response
                }, room=chat_id, include_self=True)


@socketio.on('leave')
def handle_leave(data):
    chat_id = str(data.get('chat_id'))
    username = data.get('username')
    leave_room(chat_id)
    if chat_id in participants and username in participants[chat_id]:
        participants[chat_id].remove(username)
        print(f"{username} left room {chat_id}")
        emit('participant_update', {'participants': list(participants[chat_id])}, room=chat_id)
        emit('status', {'msg': f'{username} has left the chat.'}, room=chat_id)


@socketio.on('disconnect')
def handle_disconnect():
    print("A user disconnected")
