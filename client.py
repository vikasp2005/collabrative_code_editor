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

@app.route('/login', methods=['GET','POST'])
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



    

# Logout route
@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
