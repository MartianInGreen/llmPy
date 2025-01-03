# -------------------------------------------------
# Martian API
# -------------------------------------------------

# -------------------------------------------------
# Imports
# -------------------------------------------------

import chromadb
import sqlite3
from fastapi import FastAPI, Body, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from werkzeug.utils import secure_filename as werkzeug_secure_filename
from urllib3 import PoolManager, HTTPSConnectionPool
import certifi
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import uuid, os, hashlib, json, ast, re, base64, requests
import mimetypes

from backend.interpreter import python
# -------------------------------------------------
# Setup
# -------------------------------------------------

STORAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'storage')
# Create folder if it doesn't exist
if not os.path.exists(STORAGE_PATH):
    os.makedirs(STORAGE_PATH)
DB_PATH_USERS = os.path.join(STORAGE_PATH, 'users.db')
DB_PATH_SEARCH = os.path.join(STORAGE_PATH, 'search.db')
DB_PATH_IMAGES = os.path.join(STORAGE_PATH, 'images.db')
DB_PATH_INTERPRETER = os.path.join(STORAGE_PATH, 'interpreter.db')

persistent_client = chromadb.PersistentClient(path=STORAGE_PATH)
app = FastAPI()

app.mount("/static", StaticFiles(directory="api/static"), name="static")

# https = PoolManager(
#     cert_reqs='CERT_REQUIRED',
#     ca_certs=certifi.where()
# )

# Add CORS middlewear
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origin_regex=None,
    expose_headers=[],
    max_age=600,
)

@app.options("/{full_path:path}")
async def options_handler(full_path: str):
    print(f"OPTIONS request received for path: {full_path}")
    return {"message": "OK"}

# Get env vars from .env file
dot_env_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
#print(dot_env_path)
load_dotenv(dotenv_path=str(dot_env_path))

# --------------------------------------------------------
# Database setup
# --------------------------------------------------------

def get_db_connection(DB_PATH):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

db_interp = get_db_connection(DB_PATH_INTERPRETER)

def create_interpreter_table():
    """
    Create the interpreter table if it doesn't exist.

    ID: Action UUID
    Interpreter_id: Interpreter UUID
    Input: JSON input to the interpreter function
    Result: JSON result from the interpreter function
    Created_at: Timestamp of when the interpreter function was called
    """

    cursor = db_interp.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interpreter (
        id TEXT PRIMARY KEY,
        interpreter_id TEXT,
        input TEXT,
        result TEXT,
        created_at TEXT
        )
    """)
    db_interp.commit()

create_interpreter_table()

# --------------------------------------------------------
# Helper Functions
# --------------------------------------------------------

def check_admin_key(key: str):
    #print(key)
    print(os.getenv('ADMIN_KEY'))
    # sha256 the incoming key
    key_hash = hashlib.sha256(key.encode()).hexdigest()
    print(key_hash)
    print(key_hash == os.getenv('ADMIN_KEY'))

    # Check if the hash matches the admin key
    return key_hash == os.getenv('ADMIN_KEY')

# --------------------------------------------------------
# API Endpoints
# --------------------------------------------------------

#
# Interpreter
#

def add_padding(base64_string):
    return base64_string + '=' * (-len(base64_string) % 4)

def is_base64(sb):
    try:
        if isinstance(sb, str):
            sb_bytes = bytes(sb, 'ascii')
        elif isinstance(sb, bytes):
            sb_bytes = sb
        else:
            raise ValueError("Argument must be string or bytes")
        return base64.b64encode(base64.b64decode(sb_bytes)) == sb_bytes
    except Exception:
        return False

@app.get("/ui/v1/interpreter/new")
async def interpreter_create():
    return FileResponse("api/static/ui_v1_interpreter_new.html")

@app.get("/ui/v1/interpreter/{uuid}")
async def interpreter():
    return FileResponse("api/static/ui_v1_interpreter_uuid.html")

@app.post("/api/v1/interpreter/create")
async def interpreter_create(request: Request):
    # Check the Auth header
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    key = str(auth_header.split(" ")[1])
    if not check_admin_key(key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Create new UUID
    uuid_value = str(uuid.uuid4().hex)

    # Create storage folder in the file stytem
    storage_folder = os.path.join(STORAGE_PATH, "interpreter", uuid_value)
    os.makedirs(storage_folder, exist_ok=True)

    return {"uuid": uuid_value}

@app.post("/api/v1/interpreter/python")
async def interpreter_python(request: Request):
    data = await request.json()
    uuid_value = data.get('uuid')
    code = data.get('code')
    py_packages = data.get('py_packages', "")
    sys_packages = data.get('sys_packages', "")

    if not uuid_value:
        raise HTTPException(status_code=400, detail="UUID parameter is required")
    if not code:
        raise HTTPException(status_code=400, detail="Code parameter is required")
    
    # Create new action id
    action_id = str(uuid.uuid4().hex)
    
    # Check the Auth header
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    key = str(auth_header.split(" ")[1])
    if not check_admin_key(key):
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Call the python function from interpreter.py
    result = python(STORAGE_PATH, code, py_packages, sys_packages, uuid_value)

    # Save the result to the database
    cursor = db_interp.cursor()
    cursor.execute("INSERT INTO interpreter (id, interpreter_id, input, result, created_at) VALUES (?, ?, ?, ?, datetime('now'))", (action_id, uuid_value, json.dumps(data), json.dumps(result)))
    db_interp.commit()

    return result

@app.post("/api/v1/interpreter/file/list")
async def list_files(request: Request):
    # Check the Auth header
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    key = str(auth_header.split(" ")[1])
    if not check_admin_key(key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    data = await request.json()
    uuid_value = data.get('uuid')
    dirname = data.get('dirname', "")

    # Make Dirname safe
    dirname = os.path.normpath(dirname)

    # Get the storage folder path
    storage_folder = os.path.join(STORAGE_PATH, "interpreter", uuid_value, dirname)

    # List files and directories in the directory
    items = []
    for item in os.listdir(storage_folder):
        item_path = os.path.join(storage_folder, item)
        items.append({
            "name": item,
            "is_dir": os.path.isdir(item_path)
        })

    # Return the list of files and directories
    return {"items": items}

@app.get("/api/v1/interpreter/file/download/{uuid}/{filename}")
async def interpreter_file_download(request: Request, uuid: str, filename: str):
    # Validate UUID format (only hex characters allowed) + Also allow "-" and "_"
    if not re.match(r'^[0-9a-fA-F\-_]+$', uuid):        
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Normalize and validate the filename to prevent directory traversal
    safe_filename = os.path.normpath(filename)
    if safe_filename.startswith('..') or safe_filename.startswith('/'):
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Get the storage folder path
    storage_folder = os.path.join(STORAGE_PATH, "interpreter", uuid)

    # Construct the full file path and ensure it's within the UUID directory
    file_path = os.path.join(storage_folder, safe_filename)
    if not os.path.abspath(file_path).startswith(os.path.abspath(storage_folder)):
        raise HTTPException(status_code=403, detail="Access denied")

    # Check if the file exists
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    # Guess the MIME type based on the file extension
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'  # Default to binary stream if MIME type cannot be determined

    # Return the file as a response
    return FileResponse(file_path, media_type=mime_type, filename=safe_filename)

@app.post("/api/v1/interpreter/file/upload")
async def interpreter_create(request: Request):
    # Check the Auth header
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    key = str(auth_header.split(" ")[1])
    if not check_admin_key(key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    data = await request.json()

    uuid_value = data.get('uuid')
    dirname = data.get('dirname', "")
    filename = data.get('filename', "")

    # Make Dirname safe
    dirname = os.path.normpath(dirname)
    filename = os.path.normpath(filename)

    # Get file data from the request
    file_data = data.get('file_data')

    # Validate UUID format
    if not re.match(r'^[0-9a-fA-F]+$', uuid_value):
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Validate base64 string
    if not is_base64(file_data):
        raise HTTPException(status_code=400, detail="Invalid base64-encoded string")

    # Construct the full path
    storage_folder = os.path.join(STORAGE_PATH, "interpreter", uuid_value, dirname)
    file_path = os.path.join(storage_folder, filename)

    # Ensure the path is within the storage folder
    if not os.path.abspath(file_path).startswith(os.path.abspath(storage_folder)):
        raise HTTPException(status_code=403, detail="Access denied")

    # Create directories if they don't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Write the file data
    try:
        with open(file_path, 'wb') as f:
            padded_file_data = add_padding(file_data)
            f.write(base64.b64decode(padded_file_data))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {str(e)}")

    return {"message": "File uploaded successfully", "path": file_path}

@app.post("/api/v1/interpreter/file/create-directory")
async def create_directory(request: Request):
    # Check the Auth header
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    key = str(auth_header.split(" ")[1])
    if not check_admin_key(key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    data = await request.json()

    uuid_value = data.get('uuid')
    dirname = data.get('dirname', "")

    # Make Dirname safe
    dirname = os.path.normpath(dirname)

    # Validate UUID format
    if not re.match(r'^[0-9a-fA-F]+$', uuid_value):
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    # Construct the full path
    storage_folder = os.path.join(STORAGE_PATH, "interpreter", uuid_value, dirname)

    # Ensure the path is within the storage folder
    if not os.path.abspath(storage_folder).startswith(os.path.abspath(os.path.join(STORAGE_PATH, "interpreter", uuid_value))):
        raise HTTPException(status_code=403, detail="Access denied")

    # Create the directory
    try:
        os.makedirs(storage_folder, exist_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create directory: {str(e)}")

    return {"message": "Directory created successfully", "path": storage_folder}
