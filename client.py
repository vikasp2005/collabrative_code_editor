import socket
import threading
import tkinter as tk
from tkinter import scrolledtext

# Function to handle incoming results/updates from the server
def receive_updates(client_socket, output_area):
    while True:
        try:
            result = client_socket.recv(1024).decode('utf-8')
            if not result:
                break
            # Clear the previous output and display the new result
            output_area.config(state=tk.NORMAL)
            output_area.delete(1.0, tk.END)  # Clear previous content
            output_area.insert(tk.END, f"Result: {result}\n")
            output_area.config(state=tk.DISABLED)
        except:
            break

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', 1000))

    # Create the GUI
    root = tk.Tk()
    root.title("Collaborative Code Editor")

    # Create a Text Area for code input (multiple lines)
    code_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=15)
    code_area.pack(padx=10, pady=10)

    # Create a button to run the code
    run_button = tk.Button(root, text="Run Code", height=2, width=10)

    def send_code():
        code = code_area.get("1.0", tk.END).strip()
        if code:
            client_socket.sendall(code.encode('utf-8'))

    run_button.config(command=send_code)
    run_button.pack(pady=10)

    # Create a Text Area to display results (output), placed at the bottom
    output_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=60, height=10)
    output_area.pack(padx=10, pady=10)
    output_area.config(state=tk.DISABLED)  # Disable editing directly in this area

    # Start a thread to receive updates/results from the server
    receive_thread = threading.Thread(target=receive_updates, args=(client_socket, output_area))
    receive_thread.daemon = True
    receive_thread.start()

    # Run the GUI main loop
    root.mainloop()

if __name__ == "__main__":
    start_client()
