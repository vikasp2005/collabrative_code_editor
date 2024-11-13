import socket
import threading
import sys
import io
import json
import os
import re
import tempfile
import subprocess
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# MongoDB connection setup
def connect_to_db():
    try:
        client = MongoClient("mongodb+srv://cn:cn@cluster0.dicdy.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
        db = client['code_editor']
        print("DB connected successfully")
        return db
    except Exception as e:
        print(f"Failed to connect to DB: {e}")
        sys.exit(1)  # Exit if the DB connection fails

# Initialize database
db = connect_to_db()
users_collection = db['users']

# Function to execute Java code
def execute_java_code(code):
    with tempfile.NamedTemporaryFile(suffix=".java", delete=False) as java_file:
        file_path = java_file.name
        java_file.write(code.encode())

    class_with_main = re.search(
        r'class\s+(\w+)[\s\S]*?public\s+static\s+void\s+main\s*\(\s*String\s*\[\]\s*args\s*\)',
        code
    )
    if not class_with_main:
        os.remove(file_path)
        return "Error: No public class with main method found in Java code."
    
    class_name = class_with_main.group(1)
    compile_result = subprocess.run(["javac", file_path], capture_output=True, text=True)
    if compile_result.returncode != 0:
        os.remove(file_path)
        return f"Compilation error: {compile_result.stderr}"

    run_result = subprocess.run(["java", "-cp", tempfile.gettempdir(), class_name], capture_output=True, text=True)
    os.remove(file_path)
    class_file_path = os.path.join(tempfile.gettempdir(), f"{class_name}.class")
    if os.path.exists(class_file_path):
        os.remove(class_file_path)

    return run_result.stdout if run_result.returncode == 0 else f"Execution error: {run_result.stderr}"

# Function to execute code based on language
def execute_code(code, language):
    try:
        if language == "python":
            old_stdout = sys.stdout
            redirected_output = sys.stdout = io.StringIO()
            exec(code)
            sys.stdout = old_stdout
            return redirected_output.getvalue() or "Code executed successfully with no output."
        
        elif language == "c":
            with tempfile.NamedTemporaryFile(suffix=".c", delete=False) as c_file:
                file_path = c_file.name
                c_file.write(code.encode())
            executable_path = tempfile.mktemp()
            compile_process = subprocess.run(["gcc", file_path, "-o", executable_path], capture_output=True, text=True)
            if compile_process.returncode != 0:
                os.remove(file_path)
                return compile_process.stderr

            run_process = subprocess.run([executable_path], capture_output=True, text=True)
            os.remove(file_path)
            if os.path.exists(executable_path):
                os.remove(executable_path)

            return run_process.stdout if run_process.returncode == 0 else run_process.stderr
        
        elif language == "cpp":
            with tempfile.NamedTemporaryFile(suffix=".cpp", delete=False) as cpp_file:
                file_path = cpp_file.name
                cpp_file.write(code.encode())
            executable_path = tempfile.mktemp()
            compile_process = subprocess.run(["g++", file_path, "-o", executable_path], capture_output=True, text=True)
            if compile_process.returncode != 0:
                os.remove(file_path)
                return compile_process.stderr

            run_process = subprocess.run([executable_path], capture_output=True, text=True)
            os.remove(file_path)
            if os.path.exists(executable_path):
                os.remove(executable_path)

            return run_process.stdout if run_process.returncode == 0 else run_process.stderr
        
        elif language == "java":
            return execute_java_code(code)

    except Exception as e:
        return f"Error: {str(e)}"

# User registration
def register_user(username, password):
    if users_collection.find_one({"username": username}):
        return "Username already exists."
    hashed_password = generate_password_hash(password)
    users_collection.insert_one({"username": username, "password": hashed_password})
    db.create_collection(username)

    return "Registration successful."

# User login
def login_user(username, password):
    user = users_collection.find_one({"username": username})
    if user and check_password_hash(user["password"], password):
        return "Login successful."
    return "Invalid credentials."

# Updated function to save code with a file name and ensure code is not empty
def save_code(username, file_name, code, language):
    # Check if the code is non-empty
    if not code.strip():
        return "Error: Code cannot be empty."
    

    # Create or get the user's collection
    user_collection= db[username]
    program_data = {
        "file_name": file_name,
        "code": code,
        "language": language,
        "timestamp": datetime.now()
    }
    user_collection.insert_one(program_data)
    return "Program saved successfully."

# Updated function to fetch only file names for the frontend
def fetch_saved_programs(username):
    user_collection = db[username]
    programs = user_collection.find({}, {"_id": 0, "file_name": 1,"language":1})  # Only retrieve file names
    file_names = [[program["file_name"],program["language"]] for program in programs]  # Collect file names in a list
    return json.dumps(file_names)  # Return as JSON string

# Handle client connections
def handle_client(client_socket):
    while True:
        try:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break
            request = json.loads(data)

            if request['action'] == "register":
                response = register_user(request['username'], request['password'])
            elif request['action'] == "login":
                response = login_user(request['username'], request['password'])
            elif request['action'] == "execute_code":
                language = request.get("language", "python")
                response = execute_code(request['code'], language)
            elif request['action'] == "save_code":
                response = save_code(request['username'], request['file_name'], request['code'], request['language'])
            elif request['action'] == "fetch_codes":
                response = fetch_saved_programs(request['username'])
            else:
                response = "Invalid action."

            client_socket.sendall(response.encode('utf-8'))

        except Exception as e:
            print(e)
            break
    client_socket.close()

# Start server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 6000))
    server_socket.listen(5)
    print("Server is listening on port 6000...")

    while True:
        client_socket, _ = server_socket.accept()
        client_thread = threading.Thread(target=handle_client, args=(client_socket,))
        client_thread.start()

if __name__ == "__main__":
    start_server()
