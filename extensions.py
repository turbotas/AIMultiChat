# extensions.py
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import importlib
import os

db = SQLAlchemy()
socketio = SocketIO()  # Create the Socket.IO instance here

def load_personalities():
    """
    Scans the 'plugins' folder, loads each plugin, and returns a dictionary of:
        {
            internal_key: {
                "name": <string>,
                "module": <imported module object>,
                "desc": <string>,
                "intelligence": <int>,
                "cost": <int>,
            },
            ...
        }

    'internal_key' could be the personality name or a safe slug.
    The plugin itself must define:
        PERSONALITY_NAME       (str)
        PERSONALITY_DESC       (str) or optional
        PERSONALITY_INTELLIGENCE (int) or optional
        PERSONALITY_COST       (int) or optional

    If any field is missing, we default to something.
    """
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
                personality_desc = getattr(plugin_module, 'PERSONALITY_DESC', "No description provided.")
                personality_intel = getattr(plugin_module, 'PERSONALITY_INTELLIGENCE', 5)
                personality_cost = getattr(plugin_module, 'PERSONALITY_COST', 1)
                personality_window = getattr(plugin_module, 'PERSONALITY_WINDOW', 0)
                personality_maxout = getattr(plugin_module, 'PERSONALITY_MAXOUT', 0)

                # Build our record
                personalities[personality_name] = {
                    "name": personality_name,
                    "module": plugin_module,
                    "desc": personality_desc,
                    "intelligence": personality_intel,
                    "cost": personality_cost,
                    "window": personality_window,
                    "maxout": personality_maxout,
                }

                print(f"✅ Loaded personality: {personality_name}")
            except Exception as e:
                print(f"⚠️ Failed to load {filename}: {e}")

    return personalities
