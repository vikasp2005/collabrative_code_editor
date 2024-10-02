import socket
import threading
import sys
import io

clients = []

# Function to execute the received code
def execute_code(code):
    try:
        # Redirect stdout to capture print statements
        old_stdout = sys.stdout
        redirected_output = sys.stdout = io.StringIO()

        # Use exec to run the code
        exec(code)

        # Get the output
        sys.stdout = old_stdout
        output = redirected_output.getvalue()
        return output if output else "Code executed successfully with no output."
    
    except Exception as e:
        return f"Error: {str(e)}"

# Function to handle client communication
def handle_client(client_socket, client_address):
    while True:
        try:
            # Receive the code from the client
            code = client_socket.recv(1024).decode('utf-8')
            if not code:
                break
            print(f"Received code from {client_address}:\n{code}")

            # Execute the code and get the result
            result = execute_code(code)

            # Send the result back to the client
            client_socket.sendall(result.encode('utf-8'))

        except:
            break

    print(f"Client {client_address} disconnected.")
    clients.remove(client_socket)
    client_socket.close()

# Function to start the server
def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('localhost', 1000))
    server_socket.listen(5)  # Up to 5 clients can connect simultaneously
    print("Server is listening on port 1000...")

    while True:
        client_socket, client_address = server_socket.accept()
        print(f"New connection from {client_address}")
        clients.append(client_socket)

        # Start a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
        client_thread.start()

if __name__ == "__main__":
    start_server()
