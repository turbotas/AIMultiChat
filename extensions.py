# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import importlib
import os

db = SQLAlchemy()
socketio = SocketIO()  # Create the Socket.IO instance here

def load_personalities():
    personalities = {}
    plugin_dir = os.path.join(os.path.dirname(__file__), 'plugins')

    if not os.path.exists(plugin_dir):
        print(f"❌ Plugin directory not found: {plugin_dir}")
        return personalities

    print(f"🗂️ Looking for plugins in: {plugin_dir}")
    print(f"📋 Directory contents: {os.listdir(plugin_dir)}")

    for filename in os.listdir(plugin_dir):
        if filename.endswith(".py") and filename not in ["__init__.py", "init.py"]:
            try:
                module_name = f'plugins.{filename[:-3]}'
                plugin_module = importlib.import_module(module_name)

                personality_name = getattr(plugin_module, 'PERSONALITY_NAME', filename[:-3].capitalize())
                personalities[personality_name] = plugin_module
                print(f"✅ Loaded personality: {personality_name}")
            except Exception as e:
                print(f"⚠️ Failed to load {filename}: {e}")

    return personalities
