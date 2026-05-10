import socket
import threading
import struct
from tkinter import *
from tkinter import filedialog
import io
from PIL import Image
import os


def send_packet(sock, data):
    sock.sendall(struct.pack("!I", len(data)) + data)


def recvall(sock, n):
    data = b""
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data


def add_bubble(msg, side="left"):
    """إضافة فقاعة رسالة - side='right' للمرسِل، 'left' للمستقبِل"""
    frame = Frame(messages_frame, bg="#1e1e2e")
    frame.pack(fill=X, padx=10, pady=4, anchor="e" if side == "right" else "w")

    bubble_color = "#4f8ef7" if side == "right" else "#2e2e3e"
    text_color   = "#ffffff"

    bubble = Label(
        frame,
        text=msg,
        bg=bubble_color,
        fg=text_color,
        font=("Segoe UI", 10),
        wraplength=250,
        justify="right" if side == "right" else "left",
        padx=10,
        pady=6,
    )
    bubble.pack(anchor="e" if side == "right" else "w")

    # سكرول لآخر رسالة
    root.after(50, lambda: canvas.yview_moveto(1.0))


def send():
    msg = entry.get()
    if msg:
        send_packet(s, f"TEXT|eslam|{msg}".encode())
        add_bubble("me: " + msg, side="right")
        entry.delete(0, END)


def send_img():
    path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.jpeg")])
    if not path:
        return

    img = Image.open(path)
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    data = buf.getvalue()

    payload = f"IMG|eslam|{os.path.basename(path)}|".encode() + data
    send_packet(s, payload)
    add_bubble("📷 Image sent", side="right")


def send_file():
    path = filedialog.askopenfilename()
    if not path:
        return

    ext = os.path.splitext(path)[1]
    t = "VIDEO" if ext in [".mp4", ".avi", ".mov"] else "FILE"

    with open(path, "rb") as f:
        file_data = f.read()

    payload = f"{t}|eslam|{os.path.basename(path)}|".encode() + file_data
    send_packet(s, payload)
    add_bubble(f"📎 {t} sent", side="right")


def receive():
    while True:
        try:
            raw_len = recvall(s, 4)
            if not raw_len:
                continue

            length = struct.unpack("!I", raw_len)[0]
            data = recvall(s, length)
            if not data:
                continue

            if data.startswith(b"TEXT|"):
                _, user, msg = data.decode().split("|", 2)
                root.after(0, lambda u=user, m=msg: add_bubble(f"{u}: {m}", side="left"))

            elif data.startswith(b"IMG|") or data.startswith(b"FILE|") or data.startswith(b"VIDEO|"):
                header, user, name, filedata = data.split(b"|", 3)
                filename = "recv_" + name.decode()
                with open(filename, "wb") as f:
                    f.write(filedata)
                label = header.decode()
                icon = "📷" if label == "IMG" else "📎"
                root.after(0, lambda l=label, u=user.decode(), ic=icon: add_bubble(f"{ic} {l} from {u}", side="left"))

        except:
            break


# ── الاتصال ──────────────────────────────────────
s = socket.socket()
s.connect(("nozomi.proxy.rlwy.net", 41172))

# ── UI ───────────────────────────────────────────
root = Tk()
root.title("Chat")
root.geometry("400x600")
root.configure(bg="#1e1e2e")

# منطقة الرسائل (Canvas + Scrollbar)
chat_frame = Frame(root, bg="#1e1e2e")
chat_frame.pack(fill=BOTH, expand=True)

scrollbar = Scrollbar(chat_frame)
scrollbar.pack(side=RIGHT, fill=Y)

canvas = Canvas(chat_frame, bg="#1e1e2e", yscrollcommand=scrollbar.set, highlightthickness=0)
canvas.pack(side=LEFT, fill=BOTH, expand=True)
scrollbar.config(command=canvas.yview)

messages_frame = Frame(canvas, bg="#1e1e2e")
canvas_window = canvas.create_window((0, 0), window=messages_frame, anchor="nw")

def on_frame_configure(e):
    canvas.configure(scrollregion=canvas.bbox("all"))

def on_canvas_configure(e):
    canvas.itemconfig(canvas_window, width=e.width)

messages_frame.bind("<Configure>", on_frame_configure)
canvas.bind("<Configure>", on_canvas_configure)

# منطقة الإدخال
bottom = Frame(root, bg="#2e2e3e", pady=6)
bottom.pack(fill=X)

entry = Entry(bottom, font=("Segoe UI", 11), bg="#3e3e4e", fg="white",
              insertbackground="white", relief=FLAT, bd=5)
entry.pack(side=LEFT, fill=X, expand=True, padx=(10, 4))
entry.bind("<Return>", lambda e: send())

Button(bottom, text="➤", command=send, bg="#4f8ef7", fg="white",
       relief=FLAT, font=("Segoe UI", 12), padx=8).pack(side=LEFT, padx=(0, 4))
Button(bottom, text="🖼", command=send_img, bg="#2e2e3e", fg="white",
       relief=FLAT, font=("Segoe UI", 12), padx=6).pack(side=LEFT)
Button(bottom, text="📎", command=send_file, bg="#2e2e3e", fg="white",
       relief=FLAT, font=("Segoe UI", 12), padx=6).pack(side=LEFT, padx=(0, 10))

threading.Thread(target=receive, daemon=True).start()
root.mainloop()