import socket
import threading
import struct

clients = []


def recvall(conn, n):
    data = b""
    while len(data) < n:
        packet = conn.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def send_packet(conn, data):
    conn.sendall(struct.pack("!I", len(data)) + data)


def broadcast(data, sender):
    for c in clients:
        if c != sender:
            try:
                send_packet(c, data)
            except:
                pass


def handle(conn):
    while True:
        try:
            raw_len = recvall(conn, 4)
            if not raw_len:
                break

            length = struct.unpack("!I", raw_len)[0]
            data = recvall(conn, length)

            if not data:
                break

            broadcast(data, conn)

        except:
            break

    if conn in clients:
        clients.remove(conn)
    conn.close()


server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 12345))
server.listen(5)

print("Server running...")

while True:
    conn, addr = server.accept()
    clients.append(conn)
    print("Connected:", addr)

    threading.Thread(target=handle, args=(conn,), daemon=True).start()