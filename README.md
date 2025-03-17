# AIMultiChat

AIMultiChat is a Python/Flask-based application that supports **multi-party** AI-assisted conversations. Unlike single-user chat solutions, AIMultiChat allows multiple human participants and multiple AI personalities to join a single session. It also provides convenient admin features, chat management, and real-time updates via Socket.IO.

## Key Features

- **Multi-User Chats**  
  Multiple human participants can join the same chat room and see each other's messages in real time.
- **Multiple AI Agents**  
  Allows you to add or remove different AI "personalities" – e.g., GPT-based or custom plugins – to the same conversation.
- **Live Admin Tools**  
  Admins can manage users, create or delete chat rooms, and prune specific messages from the conversation.
- **Dynamic AI Plugin System**  
  AI personalities are "plugins" stored in a `plugins/` folder, each describing a custom prompt or logic. The system automatically loads them once at startup.
- **Flexible Architecture**  
  - Uses Flask for routing and serving HTML templates  
  - Socket.IO for real-time communication  
  - SQLAlchemy for database (SQLite by default)
- **Pruning**
  - In particular each conversation can be pruned to preserve memory and context window of AI agents and may help keep costs under control.
- **Security**
  - Chats can be public or private
  - admins can create, edit and remove chats

## Installation

1. **Clone** this repository:
```bash
   git clone https://github.com/YourUsername/AIMultiChat.git
   cd AIMultiChat
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows etc
   pip install -r requirements.txt
   copy .env.dist to .env and edit settings as required, in particulaar chatGPT API key will be needed to add any agents to chats.
   python app.py
   
   The app will now be running on http://localhost:5000/
   The default username is test@aimultichat.null and the password is F7svijfIin 
```
  
2. **Container Deployment** There is also a Dockerfile if you want to run in a container.
   ```bash
   docker build -t aimultichat .
   docker run -p 5000:5000 aimultichat
    ```

## Known Issues
- **Translation**  
  If you add Babel, the translator to a chat, it only translates what the human speakers say.

## To Do
- **Database**  
  Only runs with a local flat database at the moment: add support for MySQL etc.
- **AAA**  
  AAA model is very simple and needs revamping.
- 