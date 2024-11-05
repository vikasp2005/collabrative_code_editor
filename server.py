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



def execute_java_code(code):
    # Write the Java code to a temporary file
    file_path = "/tmp/TempProgram.java"
    with open(file_path, 'w') as java_file:
        java_file.write(code)

    # Locate the class that contains the main method
    class_with_main = re.search(
        r'class\s+(\w+)[\s\S]*?public\s+static\s+void\s+main\s*\(\s*String\s*\[\]\s*args\s*\)',
        code
    )
    if not class_with_main:
        return "Error: No public class with main method found in Java code."
    
    class_name = class_with_main.group(1)

    # Compile the Java code
    compile_result = subprocess.run(["javac", file_path], capture_output=True, text=True)
    if compile_result.returncode != 0:
        return f"Compilation error: {compile_result.stderr}"

    # Execute the Java code
    run_result = subprocess.run(["java", "-cp", "/tmp", class_name], capture_output=True, text=True)
    if run_result.returncode != 0:
        return f"Execution error: {run_result.stderr}"
    
    # Clean up by removing the compiled .class file
    os.remove(f"/tmp/{class_name}.class")
    return run_result.stdout




# Function to execute code based on language
def execute_code(code, language):
    try:
        if language == "python":
            # Python code execution
            old_stdout = sys.stdout
            redirected_output = sys.stdout = io.StringIO()
            exec(code)
            sys.stdout = old_stdout
            return redirected_output.getvalue() or "Code executed successfully with no output."
        
        elif language == "c":
            # C code execution
            with open("temp.c", "w") as f:
                f.write(code)
            compile_process = subprocess.run(["gcc", "temp.c", "-o", "temp_c_exec"], capture_output=True, text=True)
            if compile_process.returncode != 0:
                return compile_process.stderr
            run_process = subprocess.run(["./temp_c_exec"], capture_output=True, text=True)
            return run_process.stdout if run_process.returncode == 0 else run_process.stderr
        
        elif language == "cpp":
            # C++ code execution
            with open("temp.cpp", "w") as f:
                f.write(code)
            compile_process = subprocess.run(["g++", "temp.cpp", "-o", "temp_cpp_exec"], capture_output=True, text=True)
            if compile_process.returncode != 0:
                return compile_process.stderr
            run_process = subprocess.run(["./temp_cpp_exec"], capture_output=True, text=True)
            return run_process.stdout if run_process.returncode == 0 else run_process.stderr
        
        elif language == "java":
            return execute_java_code(code)

    except Exception as e:
        return f"Error: {str(e)}"



# In the `handle_client` function, update to accept language and pass it to `execute_code`
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
                language = request.get("language", "python")  # Default to Python if not specified
                response = execute_code(request['code'], language)
            else:
                response = "Invalid action."

            client_socket.sendall(response.encode('utf-8'))

        except:
            break
    client_socket.close()

# User registration
def register_user(username, password):
    if users_collection.find_one({"username": username}):
        return "Username already exists."

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({"username": username, "password": hashed_password})
    return "Registration successful."

# User login
def login_user(username, password):
    user = users_collection.find_one({"username": username})
    if user and check_password_hash(user["password"], password):
        return "Login successful."
    return "Invalid credentials."

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
