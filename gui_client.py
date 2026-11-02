# ==============================================================================
# Nama       : Aidil Ilham Werfete
# NIM        : 2322105052
# No. Absen  : 42
# Kelas      : 4TI01
# Kampus     : Universitas Cendekia Abditama
# Mata Kuliah: Jaringan Komputer (Praktikum)
# Deskripsi  : Desktop GUI Client TCP Chat (Tkinter - Tanpa Library Eksternal)
# ==============================================================================

import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import sys
import datetime

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080


class ChatClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP Chat Client - Aidil Ilham Werfete (4TI01)")
        self.root.geometry("520x650")
        self.root.minsize(450, 550)
        self.root.configure(bg="#0f172a")

        self.client_socket = None
        self.is_connected = False
        self.receiver_thread = None

        self._apply_styles()
        self._build_ui()

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _apply_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", background="#0f172a", foreground="#cbd5e1", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=5)
        style.configure("TEntry", fieldbackground="#1e293b", foreground="#f8fafc", padding=5)

    def _build_ui(self):
        # 1. Header Banner Identitas
        header_frame = tk.Frame(self.root, bg="#1e293b", padx=12, pady=10)
        header_frame.pack(fill=tk.X, side=tk.TOP)

        title_lbl = tk.Label(
            header_frame,
            text="TCP CHAT CLIENT v2.0",
            bg="#1e293b",
            fg="#38bdf8",
            font=("Segoe UI", 12, "bold")
        )
        title_lbl.pack(anchor="w")

        info_lbl = tk.Label(
            header_frame,
            text="Aidil Ilham Werfete | NIM: 2322105052 | Absen: 42 | Kelas: 4TI01\nUniversitas Cendekia Abditama",
            bg="#1e293b",
            fg="#94a3b8",
            font=("Segoe UI", 8),
            justify=tk.LEFT
        )
        info_lbl.pack(anchor="w", pady=(2, 0))

        # 2. Connection Settings Frame
        conn_frame = tk.Frame(self.root, bg="#0f172a", padx=12, pady=8)
        conn_frame.pack(fill=tk.X)

        tk.Label(conn_frame, text="Host:", bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=(0, 4))
        self.entry_host = tk.Entry(conn_frame, bg="#1e293b", fg="#ffffff", insertbackground="white", width=14, relief="flat", font=("Segoe UI", 9))
        self.entry_host.insert(0, DEFAULT_HOST)
        self.entry_host.grid(row=0, column=1, padx=(0, 10))

        tk.Label(conn_frame, text="Port:", bg="#0f172a", fg="#94a3b8", font=("Segoe UI", 9)).grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.entry_port = tk.Entry(conn_frame, bg="#1e293b", fg="#ffffff", insertbackground="white", width=6, relief="flat", font=("Segoe UI", 9))
        self.entry_port.insert(0, str(DEFAULT_PORT))
        self.entry_port.grid(row=0, column=3, padx=(0, 10))

        self.btn_connect = tk.Button(
            conn_frame,
            text="Hubungkan",
            command=self.toggle_connection,
            bg="#0284c7",
            fg="white",
            activebackground="#0369a1",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            cursor="hand2"
        )
        self.btn_connect.grid(row=0, column=4, sticky="e")

        # Status Bar Badge
        self.status_badge = tk.Label(
            self.root,
            text="● Terputus dari server",
            bg="#334155",
            fg="#ef4444",
            font=("Segoe UI", 8, "bold"),
            pady=3
        )
        self.status_badge.pack(fill=tk.X)

        # 3. Chat History Display
        chat_frame = tk.Frame(self.root, bg="#0f172a", padx=12, pady=8)
        chat_frame.pack(fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            bg="#0a0f1d",
            fg="#e2e8f0",
            insertbackground="white",
            font=("Consolas", 10),
            relief="flat",
            padx=10,
            pady=10,
            state="disabled"
        )
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        # Tag configurations for colored chat messages
        self.chat_display.tag_config("system", foreground="#f59e0b", font=("Consolas", 9, "italic"))
        self.chat_display.tag_config("incoming", foreground="#38bdf8", font=("Consolas", 10))
        self.chat_display.tag_config("outgoing", foreground="#10b981", font=("Consolas", 10, "bold"))
        self.chat_display.tag_config("timestamp", foreground="#64748b", font=("Consolas", 8))

        # 4. Message Input & Quick Send Frame
        bottom_frame = tk.Frame(self.root, bg="#1e293b", padx=12, pady=10)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Quick chips
        chips_frame = tk.Frame(bottom_frame, bg="#1e293b")
        chips_frame.pack(fill=tk.X, pady=(0, 6))

        tk.Label(chips_frame, text="Quick:", bg="#1e293b", fg="#64748b", font=("Segoe UI", 8)).pack(side=tk.LEFT, padx=(0, 5))
        for text in ["Halo semua!", "Ping test", "Praktikum Jarkom OK"]:
            b = tk.Button(
                chips_frame,
                text=text,
                command=lambda t=text: self.quick_send(t),
                bg="#334155",
                fg="#cbd5e1",
                activebackground="#475569",
                activeforeground="white",
                relief="flat",
                font=("Segoe UI", 8),
                padx=6,
                pady=1,
                cursor="hand2"
            )
            b.pack(side=tk.LEFT, padx=3)

        # Input row
        input_row = tk.Frame(bottom_frame, bg="#1e293b")
        input_row.pack(fill=tk.X)

        self.entry_msg = tk.Entry(
            input_row,
            bg="#0f172a",
            fg="#ffffff",
            insertbackground="white",
            font=("Segoe UI", 10),
            relief="flat",
            state="disabled"
        )
        self.entry_msg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=6)
        self.entry_msg.bind("<Return>", lambda event: self.send_message())

        self.btn_send = tk.Button(
            input_row,
            text="Kirim",
            command=self.send_message,
            bg="#10b981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 9, "bold"),
            padx=14,
            pady=4,
            state="disabled",
            cursor="hand2"
        )
        self.btn_send.pack(side=tk.RIGHT)

    def append_message(self, tag, text):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.chat_display.config(state="normal")
        self.chat_display.insert(tk.END, f"[{now_str}] ", "timestamp")
        self.chat_display.insert(tk.END, f"{text}\n", tag)
        self.chat_display.config(state="disabled")
        self.chat_display.yview(tk.END)

    def toggle_connection(self):
        if not self.is_connected:
            self.connect_to_server()
        else:
            self.disconnect_from_server()

    def connect_to_server(self):
        host = self.entry_host.get().strip()
        try:
            port = int(self.entry_port.get().strip())
        except ValueError:
            messagebox.showerror("Port Error", "Nomor port harus berupa angka!")
            return

        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((host, port))
            self.is_connected = True

            local_ip, local_port = self.client_socket.getsockname()
            self.status_badge.config(
                text=f"● Terhubung ke {host}:{port} (Lokal: {local_port})",
                bg="#064e3b",
                fg="#34d399"
            )
            self.btn_connect.config(text="Putuskan", bg="#e11d48", activebackground="#be123c")
            self.entry_host.config(state="disabled")
            self.entry_port.config(state="disabled")
            self.entry_msg.config(state="normal")
            self.btn_send.config(state="normal")
            self.entry_msg.focus()

            self.append_message("system", f"*** Terhubung ke server {host}:{port} pada port lokal {local_port} ***")

            # Start receiver thread
            self.receiver_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.receiver_thread.start()

        except Exception as e:
            messagebox.showerror("Koneksi Gagal", f"Tidak dapat terhubung ke server:\n{e}")
            self.is_connected = False

    def disconnect_from_server(self):
        if self.client_socket:
            try:
                self.client_socket.sendall(b"/quit\n")
            except Exception:
                pass
            try:
                self.client_socket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                self.client_socket.close()
            except Exception:
                pass

        self.is_connected = False
        self.status_badge.config(text="● Terputus dari server", bg="#334155", fg="#ef4444")
        self.btn_connect.config(text="Hubungkan", bg="#0284c7", activebackground="#0369a1")
        self.entry_host.config(state="normal")
        self.entry_port.config(state="normal")
        self.entry_msg.config(state="disabled")
        self.btn_send.config(state="disabled")
        self.append_message("system", "*** Anda telah keluar dari obrolan ***")

    def _read_loop(self):
        buffer = ""
        while self.is_connected:
            try:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip("\r")
                    if line:
                        if line.startswith("*** SISTEM"):
                            self.root.after(0, self.append_message, "system", line)
                        else:
                            self.root.after(0, self.append_message, "incoming", line)
            except Exception:
                break

        if self.is_connected:
            self.root.after(0, self._handle_server_disconnect)

    def _handle_server_disconnect(self):
        self.is_connected = False
        self.status_badge.config(text="● Koneksi terputus dari server", bg="#7f1d1d", fg="#f87171")
        self.btn_connect.config(text="Hubungkan", bg="#0284c7")
        self.entry_host.config(state="normal")
        self.entry_port.config(state="normal")
        self.entry_msg.config(state="disabled")
        self.btn_send.config(state="disabled")
        self.append_message("system", "*** Koneksi ke server terputus secara mendadak ***")

    def send_message(self):
        if not self.is_connected:
            return
        text = self.entry_msg.get().strip()
        if not text:
            return

        self.entry_msg.delete(0, tk.END)

        try:
            payload = (text + "\n").encode("utf-8")
            self.client_socket.sendall(payload)
            self.append_message("outgoing", f"[Saya]: {text}")
        except Exception as e:
            self.append_message("system", f"[ERROR] Gagal mengirim pesan: {e}")
            self.disconnect_from_server()

    def quick_send(self, text):
        if self.is_connected:
            self.entry_msg.delete(0, tk.END)
            self.entry_msg.insert(0, text)
            self.send_message()

    def on_closing(self):
        if self.is_connected:
            self.disconnect_from_server()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ChatClientGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

