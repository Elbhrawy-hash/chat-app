import socket
import threading
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import io
import os
from datetime import datetime

try:
    from PIL import Image, ImageTk
    PIL_OK = True
except:
    PIL_OK = False

# ==============================
# PROTOCOL
# ==============================
EOF_MARKER = b'\x00\xFF\xEE\xFF\x00'


def recv_message(conn):
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


# ==============================
# CONNECT
# ==============================
HOST = "nozomi.proxy.rlwy.net"
PORT = 41172

username = simpledialog.askstring("Username", "Enter your name:") or "User"

sock = socket.socket()
sock.connect((HOST, PORT))
send_message(sock, username.encode())

hd_mode = False

# ==============================
# GUI
# ==============================
root = tk.Tk()
root.title(f"Chat - {username}")
root.configure(bg="#1e1e2e")
root.geometry("420x600")

chat_frame = tk.Frame(root, bg="#1e1e2e")
chat_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

scrollbar = tk.Scrollbar(chat_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

chat_box = tk.Text(
    chat_frame, bg="#1e1e2e", fg="white",
    font=("Helvetica", 11), wrap=tk.WORD,
    yscrollcommand=scrollbar.set, state=tk.DISABLED,
    relief=tk.FLAT, padx=8, pady=8
)
chat_box.pack(fill=tk.BOTH, expand=True)
scrollbar.config(command=chat_box.yview)

chat_box.tag_config("me", foreground="#e94560", justify="right")
chat_box.tag_config("other", foreground="#4ecca3", justify="left")
chat_box.tag_config("system", foreground="#555", justify="center")
chat_box.tag_config("time", foreground="#444", font=("Helvetica", 8))


def add_message(sender, text, side):
    chat_box.config(state=tk.NORMAL)
    time_str = datetime.now().strftime("%H:%M")
    tag = "me" if side == "right" else "other"
    if side == "right":
        chat_box.insert(tk.END, f"\n{text}\n", tag)
        chat_box.insert(tk.END, f"{time_str}\n", "time")
    else:
        chat_box.insert(tk.END, f"\n{sender}: {text}\n", tag)
        chat_box.insert(tk.END, f"{time_str}\n", "time")
    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)


def add_system(text):
    chat_box.config(state=tk.NORMAL)
    chat_box.insert(tk.END, f"\n— {text} —\n", "system")
    chat_box.config(state=tk.DISABLED)
    chat_box.see(tk.END)


# ==============================
# SEND FUNCTIONS
# ==============================
def send_text():
    msg = entry.get().strip()
    if not msg:
        return
    header = f"TEXT||{msg}\n".encode()
    send_message(sock, header)
    add_message(username, msg, "right")
    entry.delete(0, tk.END)


def send_image():
    if not PIL_OK:
        messagebox.showerror("Error", "Install Pillow: pip install Pillow")
        return
    path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")])
    if not path:
        return

    filename = os.path.basename(path)
    with Image.open(path) as img:
        buf = io.BytesIO()
        if hd_mode:
            img.save(buf, format=img.format or "PNG")
            mode = "hd"
        else:
            img.thumbnail((800, 800))
            img.save(buf, format="JPEG", quality=60)
            mode = "normal"

    image_bytes = buf.getvalue()
    header = f"IMAGE||{filename}|{mode}\n".encode()
    send_message(sock, header + image_bytes)

    label = f"📷 {'[HD] ' if hd_mode else ''}Image: {filename}"
    add_message(username, label, "right")


def send_file():
    path = filedialog.askopenfilename()
    if not path:
        return
    filename = os.path.basename(path)
    with open(path, 'rb') as f:
        file_bytes = f.read()

    header = f"FILE||{filename}\n".encode()
    send_message(sock, header + file_bytes)
    add_message(username, f"📎 File: {filename}", "right")


def toggle_hd():
    global hd_mode
    hd_mode = not hd_mode
    hd_btn.config(
        text="HD: ON" if hd_mode else "HD: OFF",
        bg="#e94560" if hd_mode else "#333"
    )


# ==============================
# RECEIVE LOOP
# ==============================
def receive_loop():
    while True:
        raw = recv_message(sock)
        if raw is None:
            break

        newline = raw.find(b'\n')
        if newline == -1:
            continue

        header = raw[:newline].decode()
        payload = raw[newline + 1:]
        parts = header.split('|')

        msg_type = parts[0]
        sender = parts[1] if len(parts) > 1 else ''
        extra = parts[2] if len(parts) > 2 else ''

        if msg_type == "TEXT":
            root.after(0, add_message, sender, extra, "left")

        elif msg_type == "IMAGE":
            filename = extra
            mode = parts[3] if len(parts) > 3 else ''
            label = f"📷 {'[HD] ' if mode == 'hd' else ''}Image: {filename}"
            root.after(0, add_message, sender, label, "left")
            if payload and PIL_OK:
                def show_save(data=payload, fname=filename):
                    if messagebox.askyesno("Image received", f"Save {fname}?"):
                        save_path = filedialog.asksaveasfilename(initialfile=fname)
                        if save_path:
                            with open(save_path, 'wb') as f:
                                f.write(data)
                root.after(0, show_save)

        elif msg_type == "FILE":
            filename = extra
            size_kb = len(payload) / 1024
            label = f"📎 File: {filename} ({size_kb:.1f} KB)"
            root.after(0, add_message, sender, label, "left")
            if payload:
                def show_save_file(data=payload, fname=filename):
                    if messagebox.askyesno("File received", f"Save {fname}?"):
                        save_path = filedialog.asksaveasfilename(initialfile=fname)
                        if save_path:
                            with open(save_path, 'wb') as f:
                                f.write(data)
                root.after(0, show_save_file)

        elif msg_type == "SYSTEM":
            root.after(0, add_system, sender)


threading.Thread(target=receive_loop, daemon=True).start()

# ==============================
# BUTTONS
# ==============================
btn_frame = tk.Frame(root, bg="#16213e")
btn_frame.pack(fill=tk.X, padx=8)

s = {"font": ("Helvetica", 9), "relief": tk.FLAT, "padx": 8, "pady": 5, "cursor": "hand2"}

tk.Button(btn_frame, text="🖼 Image", command=send_image, bg="#0f3460", fg="white", **s).pack(side=tk.LEFT, padx=3, pady=4)
tk.Button(btn_frame, text="📁 File", command=send_file, bg="#0f3460", fg="white", **s).pack(side=tk.LEFT, padx=3)
hd_btn = tk.Button(btn_frame, text="HD: OFF", command=toggle_hd, bg="#333", fg="white", **s)
hd_btn.pack(side=tk.LEFT, padx=3)

input_frame = tk.Frame(root, bg="#16213e")
input_frame.pack(fill=tk.X, padx=8, pady=8)

entry = tk.Entry(input_frame, font=("Helvetica", 11), bg="#0f3460", fg="white",
                 insertbackground="white", relief=tk.FLAT)
entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=7, padx=(0, 6))
entry.bind("<Return>", lambda e: send_text())

tk.Button(input_frame, text="Send ➤", command=send_text,
          font=("Helvetica", 10, "bold"), bg="#e94560", fg="white",
          relief=tk.FLAT, padx=10, pady=7, cursor="hand2").pack(side=tk.RIGHT)

root.mainloop()