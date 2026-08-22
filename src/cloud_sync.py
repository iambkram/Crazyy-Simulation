import os
import json
import time
import uuid
import threading
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from google_auth_oauthlib.flow import InstalledAppFlow
from cryptography.fernet import Fernet
import bcrypt
from dotenv import load_dotenv
import sys
from pathlib import Path
import traceback


def load_environment():
    env_paths_to_try = []

    if getattr(sys, 'frozen', False):
        exe_path = Path(sys.executable)
        env_paths_to_try.extend([exe_path.parent / '.env', exe_path.parent.parent / '.env'])
    else:
        script_path = Path(__file__).resolve()
        env_paths_to_try.extend([script_path.parent / '.env', script_path.parent.parent / '.env'])

    env_paths_to_try.append(Path.cwd() / '.env')

    loaded = False
    for p in env_paths_to_try:
        if p.exists() and p.is_file():
            print(f"\n[SUCCESS] Found .env file at: {p}")
            # OVERRIDE=TRUE IS VERY IMPORTANT HERE
            load_dotenv(dotenv_path=str(p), override=True)
            loaded = True
            break

    if not loaded:
        print("\n[WARNING] Could not find .env file! Trying default load_dotenv()...")
        load_dotenv(override=True)


load_environment()


# Google Desktop OAuth Credentials (Inherently public for installed apps per Google Docs)
GLOBAL_CLIENT_ID = get_clean_env("GOOGLE_CLIENT_ID")
GLOBAL_CLIENT_SECRET = get_clean_env("GOOGLE_CLIENT_SECRET")

# Fetch and STRIP accidental quotes/spaces for Mongo
def get_clean_env(key, default=""):
    val = str(os.getenv(key, default)).strip().strip('"').strip("'")
    return val if val else default
MONGO_URI = get_clean_env("MONGODB_URI")
DB_NAME = "crazyy_simulation"
client = None
db = None

# Google Auth Configuration
SCOPES = ['openid', 'https://www.googleapis.com/auth/userinfo.profile',
          'https://www.googleapis.com/auth/userinfo.email']

# Encryption key for local session token
SECRET_KEY = get_clean_env("SESSION_SECRET_KEY", "7bXN8gG3zS_dF3xKqO0t-Pj4mQ9rY6A1vU2wL5sV8eM=").encode()
try:
    fernet = Fernet(SECRET_KEY)
except Exception:
    fernet = Fernet(b'7bXN8gG3zS_dF3xKqO0t-Pj4mQ9rY6A1vU2wL5sV8eM=')

# Use absolute paths based on app_dir from main if possible, but for simplicity, we'll use relative/current dir
SESSION_FILE = "session.token"
LOCAL_SAVE_FILE = "save.json"

# State variables for threading
sync_queue = []
sync_thread = None
is_running = True
current_session_id = None
current_account_type = None # "guest" or "google"
current_username = None

def init_db():
    global client, db
    if client is not None:
        return True
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        client.server_info() # trigger exception if cannot connect
        db = client[DB_NAME]
        return True
    except (ConnectionFailure, ServerSelectionTimeoutError, Exception) as e:
        print(f"MongoDB connection failed: {e}")
        client = None
        db = None
        return False

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def encrypt_session(data):
    return fernet.encrypt(json.dumps(data).encode('utf-8'))

def decrypt_session(token):
    try:
        return json.loads(fernet.decrypt(token).decode('utf-8'))
    except Exception:
        return None

def save_local_session(account_type, account_id, username=None):
    global current_session_id, current_account_type, current_username
    current_session_id = account_id
    current_account_type = account_type
    current_username = username
    data = {
        "type": account_type,
        "id": account_id,
        "username": username,
        "timestamp": time.time()
    }
    with open(SESSION_FILE, "wb") as f:
        f.write(encrypt_session(data))

def load_local_session():
    global current_session_id, current_account_type, current_username
    if not os.path.exists(SESSION_FILE):
        return None
    try:
        with open(SESSION_FILE, "rb") as f:
            token = f.read()
        session_data = decrypt_session(token)
        if session_data:
            current_session_id = session_data["id"]
            current_account_type = session_data["type"]
            current_username = session_data.get("username", session_data["id"])
        return session_data
    except Exception:
        return None

def clear_local_session():
    global current_session_id, current_account_type, current_username
    current_session_id = None
    current_account_type = None
    current_username = None
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def login_guest():
    """Retrieves or generates a persistent device guest ID, saves it locally, and initializes a DB record asynchronously."""
    guest_id_file = "device_guest_id.txt"
    guest_id = None
    
    if os.path.exists(guest_id_file):
        try:
            with open(guest_id_file, "r") as f:
                guest_id = f.read().strip()
        except:
            pass
            
    if not guest_id or not guest_id.startswith("Guest_"):
        guest_id = f"Guest_{uuid.uuid4().hex[:8]}"
        try:
            with open(guest_id_file, "w") as f:
                f.write(guest_id)
        except:
            pass
            
    save_local_session("guest", guest_id, guest_id)
    local_data = {}
    if os.path.exists(LOCAL_SAVE_FILE):
        try:
            with open(LOCAL_SAVE_FILE, "r") as f:
                local_data = json.load(f)
        except:
            pass
    
    if not local_data:
        local_data = {"coins":0,"hp":200,"hp_step":0,"speed":7,"speed_step":0,
                    "bullets":1,"bullet_step":0,"max_galaxy_level":1,"max_nebula_level":1,
                    "max_blackhole_level":1,"env2_unlocked":False,"env3_unlocked":False,
                    "control_type":"PC","music_vol":0.5,"sfx_vol":0.7,
                    "show_fps":False,"visual_quality":"high","screen_shake":True,
                    "display_mode":"windowed"}
                    
    # The actual DB creation will happen in the background via queue_sync
    queue_sync(local_data)
    return guest_id

# Authentication Threading State
auth_status = None # None, "WAITING", "SUCCESS", "FAILED", "CANCELLED"
auth_result_info = None

def _google_auth_worker():
    global auth_status, auth_result_info
    
    try:
        if GLOBAL_CLIENT_ID and GLOBAL_CLIENT_SECRET:
            client_config = {
                "installed": {
                    "client_id": GLOBAL_CLIENT_ID,
                    "project_id": "crazyy-simulation",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": GLOBAL_CLIENT_SECRET,
                    "redirect_uris": ["http://localhost"]
                }
            }
            flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        elif os.path.exists('client_secret.json'):
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
        else:
            env_dump = ", ".join(os.environ.keys())
            auth_result_info = {"error": f"Missing CLIENT_ID. Loaded Env Keys: {env_dump[:200]}..."}
            auth_status = "FAILED"
            return

        credentials = flow.run_local_server(port=0)
        
        try:
            from googleapiclient.discovery import build
        except ImportError:
            auth_result_info = {"error": "Missing google-api-python-client. Run: pip install google-api-python-client"}
            auth_status = "FAILED"
            return
            
        user_info_service = build('oauth2', 'v2', credentials=credentials)
        user_info = user_info_service.userinfo().get().execute()
        
        google_id = user_info.get("id")
        email = user_info.get("email")
        name = user_info.get("name")
        
        auth_result_info = {"id": google_id, "email": email, "name": name}
        auth_status = "SUCCESS"
        
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"Google Login Error Traceback:")
        traceback.print_exc()
        auth_result_info = {"error": f"Auth Failed: {error_msg}"}
        auth_status = "FAILED"

def login_google_async():
    """Starts the Google OAuth browser flow in a background thread."""
    global auth_status, auth_result_info
    
    # Pre-flight diagnostic check
    if not GLOBAL_CLIENT_ID:
        env_dump = ", ".join(os.environ.keys())
        auth_result_info = {"error": f"Missing CLIENT_ID in Memory. Loaded Env Keys: {env_dump[:200]}..."}
        auth_status = "FAILED"
        return
        
    if auth_status == "WAITING": return
    
    auth_status = "WAITING"
    auth_result_info = None
    t = threading.Thread(target=_google_auth_worker, daemon=True)
    t.start()

def check_username_available(username):
    if not init_db():
        return False
    col = db["registered_users"]
    return col.find_one({"username": username}) is None

def register_new_user(google_info, username, password):
    """Registers a new user after Google Auth."""
    if not init_db():
        return False, "Database connection failed"
    
    col = db["registered_users"]
    
    # Check if google account already registered
    if col.find_one({"_id": google_info["id"]}):
        return False, "Google account already registered. Please Log In."
        
    # Check if username taken
    if col.find_one({"username": username}):
        return False, "Username already taken."
        
    hashed_pw = hash_password(password)
    col.insert_one({
        "_id": google_info["id"],
        "google_email": google_info.get("email", ""),
        "username": username,
        "password": hashed_pw,
        "created_at": time.time(),
        "save_data": {}
    })
    
    save_local_session("google", google_info["id"], username)
    return True, ""

def login_existing_user(username, password):
    """Logs in an existing user with username and password."""
    if not init_db():
        return False, "Database connection failed"
        
    col = db["registered_users"]
    user = col.find_one({"username": username})
    
    if not user:
        return False, "Username not found."
        
    if not check_password(password, user["password"]):
        return False, "Incorrect password."
        
    save_local_session("google", user["_id"], username)
    return True, ""

def reset_password(google_info, username, new_password):
    """Resets password if the google_info id matches the registered user's _id."""
    if not init_db():
        return False, "Database connection failed"
        
    col = db["registered_users"]
    user = col.find_one({"username": username})
    
    if not user:
        return False, "Username not found."
        
    if user["_id"] != google_info["id"]:
        return False, "This username belongs to a different Google account."
        
    hashed_pw = hash_password(new_password)
    col.update_one({"_id": user["_id"]}, {"$set": {"password": hashed_pw}})
    
    save_local_session("google", user["_id"], username)
    return True, ""

def bind_guest_to_google(google_info, username, password):
    """Upgrades a guest account to a google account, migrating data."""
    if not init_db():
        return False
    
    guest_col = db["guest_users"]
    reg_col = db["registered_users"]
    
    old_guest = guest_col.find_one({"_id": current_session_id})
    save_data = old_guest.get("save_data", {}) if old_guest else {}

    hashed_pw = hash_password(password)
    
    reg_col.update_one(
        {"_id": google_info["id"]},
        {"$set": {
            "google_email": google_info["email"],
            "username": username,
            "password": hashed_pw,
            "created_at": time.time(),
            "save_data": save_data
        }},
        upsert=True
    )
    
    guest_col.delete_one({"_id": current_session_id})
    save_local_session("google", google_info["id"], username)
    return True

# --- THREADED SYNC WORKER ---
sync_in_progress = False
save_updated_from_cloud = False

def queue_sync(local_save_data):
    """Pushes a sync job to the background thread."""
    global sync_in_progress
    if current_session_id:
        sync_queue.append(local_save_data)
        sync_in_progress = True

def _sync_worker():
    global sync_queue, sync_in_progress
    while is_running:
        if len(sync_queue) > 0 and current_session_id:
            sync_in_progress = True
            latest_save = sync_queue[-1]
            sync_queue.clear()
            
            if init_db():
                col = db["registered_users"] if current_account_type == "google" else db["guest_users"]
                try:
                    user_doc = col.find_one({"_id": current_session_id})
                    
                    if user_doc:
                        col.update_one(
                            {"_id": current_session_id},
                            {"$set": {"save_data": latest_save, "last_synced": time.time()}}
                        )
                    else:
                        # New user doc creation
                        new_doc = {
                            "_id": current_session_id,
                            "created_at": time.time(),
                            "save_data": latest_save
                        }
                        if current_account_type == "guest":
                            new_doc["username"] = current_session_id
                        col.insert_one(new_doc)

                except Exception as e:
                    print(f"Sync error: {e}")
            sync_in_progress = False
        time.sleep(1.0)

def start_sync_thread(save_file_path):
    global sync_thread, is_running, LOCAL_SAVE_FILE
    LOCAL_SAVE_FILE = save_file_path
    if sync_thread is None or not sync_thread.is_alive():
        is_running = True
        sync_thread = threading.Thread(target=_sync_worker, daemon=True)
        sync_thread.start()

def stop_sync_thread():
    global is_running
    is_running = False
