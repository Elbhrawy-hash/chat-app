import socket
import threading
import os

# EOF marker - بدل ما نبعت حجم الملف
EOF_MARKER = b'\x00\xFF\xEE\xFF\x00'

clients = {}  # {conn: username}


def broadcast(data, sender_conn):
    for conn in list(clients):
        if conn != sender_conn:
            try:
                conn.sendall(data)
            except:
                pass


def recv_message(conn):
    """استقبل رسالة كاملة لحد ما تلاقي الـ EOF_MARKER"""
    buffer = b''
    while True:
        chunk = conn.recv(4096)
        if not chunk:
            return None
        buffer += chunk
        if EOF_MARKER in buffer:
            data, _ = buffer.split(EOF_MARKER, 1)
            return data


def send_message(conn, data):
    conn.sendall(data + EOF_MARKER)


def handle_client(conn, addr):
    # أول رسالة = اسم المستخدم
    raw = recv_message(conn)
    if not raw:
        conn.close()
        return

    username = raw.decode()
    clients[conn] = username
    print(f"{username} connected")
    broadcast(f"SYSTEM|{username} joined\n".encode(), conn)

    while True:
        raw = recv_message(conn)
        if raw is None:
            break

        # Header في أول سطر: TYPE|extra
        newline = raw.find(b'\n')
        header = raw[:newline].decode()
        payload = raw[newline + 1:]

        parts = header.split('|')
        msg_type = parts[0]
        extra = '|'.join(parts[1:])

        # أضف اسم المرسل وابعت للكل
        new_header = f"{msg_type}|{username}|{extra}\n".encode()
        broadcast(new_header + payload, conn)

    del clients[conn]
    conn.close()
    broadcast(f"SYSTEM|{username} left\n".encode(), conn)
    print(f"{username} disconnected")


# Railway بيحدد الـ PORT تلقائياً عن طريق environment variable
PORT = int(os.environ.get("PORT", 12345))

server = socket.socket()
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server.bind(('0.0.0.0', PORT))
server.listen(5)
print(f"Server running on port {PORT}...")

while True:
    conn, addr = server.accept()
    threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()