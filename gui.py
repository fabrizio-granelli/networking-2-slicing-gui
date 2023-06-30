import tkinter as tk
import socket

UDP_IP = "172.17.0.1"
UDP_PORT = 9933

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send_slice(mode):

    if mode == "WORK":
        sock.sendto("SLICE_0".encode("UTF-8"),(UDP_IP, UDP_PORT))
    elif mode == "GAMING":
        sock.sendto("SLICE_1".encode("UTF-8"),(UDP_IP, UDP_PORT))
    elif mode == "EMERGENCY":
        sock.sendto("SLICE_2".encode("UTF-8"),(UDP_IP, UDP_PORT))



root = tk.Tk()
root.geometry("400x300")

text_box = tk.Text(root)
text_box.grid(row=0, column=0, sticky="nsew", padx=(10,10), pady=(10, 10))

work_button = tk.Button(root, text="WORK", bg="green", command=lambda: send_slice("WORK"))
work_button.grid(row=1, column=0, sticky="w", padx=(10, 0), pady=(0, 10))

gaming_button = tk.Button(root, text="GAMING", bg="yellow", command=lambda: send_slice("GAMING"))
gaming_button.grid(row=1, column=0, sticky="w", padx=(81, 0), pady=(0, 10))

emergency_button = tk.Button(root, text="EMERGENCY", bg="red", command=lambda: send_slice("EMERGENCY"))
emergency_button.grid(row=1, column=0, sticky="w", padx=(166, 0), pady=(0, 10))

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

root.mainloop()
