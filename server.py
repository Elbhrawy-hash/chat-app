import socket
import threading

clients = []

def handle(conn):
    while True:
        try:
            msg = conn.recv(1024)
            if not msg:
                break
            for c in clients:
                if c != conn:
                    c.send(msg)
        except:
            break
    clients.remove(conn)
    conn.close()

server = socket.socket()
server.bind(('0.0.0.0', 12345))
server.listen(5)
print("Server running...")

while True:
    conn, addr = server.accept()
    clients.append(conn)
    print(f"Connected: {addr}")
    threading.Thread(target=handle, args=(conn,), daemon=True).start()