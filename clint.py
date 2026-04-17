import socket
import threading
from tkinter import *


def send():
    msg = entry.get()
    if msg:
        s.send(msg.encode())
        chat.insert(END, "me: " + msg + "\n")
        entry.delete(0, END)


def receive():
    while True:
        msg = s.recv(1024).decode()
        chat.insert(END, "other: " + msg + "\n")


s = socket.socket()
s.connect(('nozomi.proxy.rlwy.net', 41172))


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