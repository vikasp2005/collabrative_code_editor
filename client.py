from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import socket
import json

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Route for the home page
@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('editor'))
    return render_template("home.html")

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Simulate sending data to the server and receiving a response.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(('localhost', 6000))
            data = json.dumps({"action": "register", "username": username, "password": password})
            client_socket.sendall(data.encode())
            response = client_socket.recv(1024).decode()

        if "success" in response:
            return jsonify({"status": "success", "message": "Registration successful!"})
        else:
            return jsonify({"status": "error", "message": "Registration failed."})


    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Send login data to the socket server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(('localhost', 6000))
            data = json.dumps({"action": "login", "username": username, "password": password})
            client_socket.sendall(data.encode())
            response = client_socket.recv(1024).decode()

        if "success" in response:
            # Set a session variable to indicate the user is logged in
            session['username'] = username
            return jsonify({"status": "success", "message": "Login successful!"})
        else:
            return jsonify({"status": "error", "message": "Invalid credentials."})

    return render_template('login.html')


@app.route('/editor', methods=['GET', 'POST'])
def editor():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        data = request.get_json()  # Read JSON data
        code = data.get('code')
        language = data.get('language')

        if not code:
            return jsonify(error="Code is missing."), 400

        # Send code and language to the server
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
          client_socket.connect(('localhost', 6000))
          send_data = json.dumps({"action": "execute_code", "code": code, "language": language})
          client_socket.sendall(send_data.encode())
          result = client_socket.recv(4096).decode()

        return jsonify(result=result)

    return render_template('editor.html')




# Save the program by sending code to the server
@app.route('/save_program', methods=['POST'])
def save_program():
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    data = request.get_json()
    file_name = data.get('name')
    code = data.get('code')
    language = data.get('language')
    username = session['username']

    # Send the code to the server via socket for saving
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect(('localhost', 6000))
        send_data = json.dumps({
            "action": "save_code",
            "username": username,
            "file_name": file_name,
            "code": code,
            "language": language
        })
        client_socket.sendall(send_data.encode())
        response = client_socket.recv(1024).decode()

    return jsonify({"status": "success", "message": response})

# Fetch saved programs from the server
@app.route('/fetch_programs', methods=['GET'])
def fetch_programs():
    # Check if user is authenticated
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401

    username = session['username']

    # Send the request to the server to fetch the programs
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(('localhost', 6000))

            # Prepare and send data
            send_data = json.dumps({
                "action": "fetch_codes",
                "username": username
            })
            client_socket.sendall(send_data.encode())

            # Receive response from the server
            programs_data = client_socket.recv(4096).decode()
            # If no data received or empty response
            if not programs_data:
                return jsonify({"status": "error", "message": "No data received from server"}), 500

            # Parse and return the JSON response
            try:
                programs_list = json.loads(programs_data)
                # Convert each sublist into a dictionary with keys "name" and "language"
                programs = [{"name": program[0], "language": program[1]} for program in programs_list]
                return jsonify({"status": "success", "programs": programs})
            except json.JSONDecodeError:
                return jsonify({"status": "error", "message": "Failed to decode server response"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500




# Fetch saved programs from the server
@app.route('/fetch_code', methods=['POST'])
def fetch_codes():
    # Check if user is authenticated
    if 'username' not in session:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    

    data = request.get_json()
    file_name = data.get('name')
    username = session['username']

    # Send the request to the server to fetch the programs
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect(('localhost', 6000))

            # Prepare and send data
            send_data = json.dumps({
                "action": "fetch_codes_data",
                "username": username,
                "name" : file_name
            })
            client_socket.sendall(send_data.encode())

            # Receive response from the server
            programs_data = client_socket.recv(4096).decode()
            # If no data received or empty response
            if not programs_data:
                return jsonify({"status": "error", "message": "No data received from server"}), 500

            # Parse and return the JSON response
            try:
                programs_list = json.loads(programs_data)
                return jsonify({"status": "success", "programs": programs_list})
            except json.JSONDecodeError:
                return jsonify({"status": "error", "message": "Failed to decode server response"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500




# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
