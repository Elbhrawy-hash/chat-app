import socket
import threading
from tkinter import *

# دالة البعت
def send():
    msg = entry.get()
    if msg:
        s.send(msg.encode())
        chat.insert(END, "me: " + msg + "\n")
        entry.delete(0, END)

# دالة الاستقبال
def receive():
    while True:
        msg = s.recv(1024).decode()
        chat.insert(END, "server: " + msg + "\n")

# الاتصال بالسيرفر
s = socket.socket()
s.connect(('localhost', 12345))

# الشاشه
root = Tk()
root.title("client")

chat = Text(root)
chat.pack()

frame = Frame(root)
frame.pack()

entry = Entry(frame, width=30)
entry.pack(side=LEFT)

Button(frame, text="send", command=send).pack(side=LEFT)

threading.Thread(target=receive, daemon=True).start()
root.mainloop()