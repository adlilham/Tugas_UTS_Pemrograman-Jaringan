# ==============================================================================
# Nama       : Aidil Ilham Werfete
# NIM        : 2322105052
# No. Absen  : 42
# Kelas      : 4TI01
# Kampus     : Universitas Cendekia Abditama
# Mata Kuliah: Jaringan Komputer (Praktikum)
# Deskripsi  : Desktop GUI Server Dashboard TCP Chat (Tkinter - Native Python)
# ==============================================================================

import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import datetime

HOST = "0.0.0.0"
PORT = 8080


class ChatServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TCP Chat Server Controller - Aidil Ilham Werfete (4TI01)")
        self.root.geometry("820x680")
        self.root.minsize(700, 550)
        self.root.configure(bg="#0b1120")

        self.server_socket = None
        self.server_running = False
        self.clients = {}  # {client_socket: (ip, port, fd, connected_at)}
        self.clients_lock = threading.Lock()
        self.total_packets = 0

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _build_ui(self):
        # 1. Header Identitas Banner
        header = tk.Frame(self.root, bg="#1e293b", padx=16, pady=12)
        header.pack(fill=tk.X, side=tk.TOP)

        top_row = tk.Frame(header, bg="#1e293b")
        top_row.pack(fill=tk.X)

        tk.Label(
            top_row,
            text="TCP CHAT SERVER DASHBOARD",
            bg="#1e293b",
            fg="#38bdf8",
            font=("Segoe UI", 14, "bold")
        ).pack(side=tk.LEFT)

        self.lbl_server_status = tk.Label(
            top_row,
            text="STATUS: STOPPED",
            bg="#334155",
            fg="#f87171",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=2
        )
        self.lbl_server_status.pack(side=tk.RIGHT)

        info_text = (
            "Nama: Aidil Ilham Werfete | NIM: 2322105052 | No. Absen: 42 | Kelas: 4TI01 | "
            "Universitas Cendekia Abditama"
        )
        tk.Label(
            header,
            text=info_text,
            bg="#1e293b",
            fg="#94a3b8",
            font=("Segoe UI", 8)
        ).pack(anchor="w", pady=(4, 0))

        # 2. Controls & Metrics Bar
        ctrl_bar = tk.Frame(self.root, bg="#0b1120", padx=16, pady=10)
        ctrl_bar.pack(fill=tk.X)

        tk.Label(ctrl_bar, text="Bind Host:", bg="#0b1120", fg="#94a3b8", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.entry_host = tk.Entry(ctrl_bar, width=12, bg="#1e293b", fg="white", font=("Segoe UI", 9), relief="flat")
        self.entry_host.insert(0, HOST)
        self.entry_host.pack(side=tk.LEFT, padx=(4, 10))

        tk.Label(ctrl_bar, text="Port:", bg="#0b1120", fg="#94a3b8", font=("Segoe UI", 9)).pack(side=tk.LEFT)
        self.entry_port = tk.Entry(ctrl_bar, width=6, bg="#1e293b", fg="white", font=("Segoe UI", 9), relief="flat")
        self.entry_port.insert(0, str(PORT))
        self.entry_port.pack(side=tk.LEFT, padx=(4, 15))

        self.btn_toggle_server = tk.Button(
            ctrl_bar,
            text="Jalankan Server",
            command=self.toggle_server,
            bg="#10b981",
            fg="white",
            activebackground="#059669",
            activeforeground="white",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=14,
            cursor="hand2"
        )
        self.btn_toggle_server.pack(side=tk.LEFT)

        # Metrics on right
        self.lbl_metric_clients = tk.Label(
            ctrl_bar,
            text="Active Clients: 0",
            bg="#1e293b",
            fg="#38bdf8",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4
        )
        self.lbl_metric_clients.pack(side=tk.RIGHT, padx=4)

        self.lbl_metric_packets = tk.Label(
            ctrl_bar,
            text="Packets: 0",
            bg="#1e293b",
            fg="#34d399",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=4
        )
        self.lbl_metric_packets.pack(side=tk.RIGHT, padx=4)

        # 3. Active Sockets Treeview (Connection Pool)
        pool_frame = tk.LabelFrame(
            self.root,
            text=" Active Socket Connection Pool (Dictionary/List) ",
            bg="#0b1120",
            fg="#cbd5e1",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8
        )
        pool_frame.pack(fill=tk.BOTH, expand=False, padx=16, pady=(0, 10))

        cols = ("fd", "endpoint", "status", "connected_at")
        self.tree_pool = ttk.Treeview(pool_frame, columns=cols, show="headings", height=4)
        self.tree_pool.heading("fd", text="Socket FD")
        self.tree_pool.heading("endpoint", text="Client IP:Port")
        self.tree_pool.heading("status", text="TCP State")
        self.tree_pool.heading("connected_at", text="Connected At")

        self.tree_pool.column("fd", width=90, anchor="center")
        self.tree_pool.column("endpoint", width=180, anchor="w")
        self.tree_pool.column("status", width=110, anchor="center")
        self.tree_pool.column("connected_at", width=120, anchor="center")
        self.tree_pool.pack(fill=tk.X, side=tk.LEFT, expand=True)

        # Disconnect selected button
        btn_kick = tk.Button(
            pool_frame,
            text="Kick\nClient",
            command=self.kick_selected_client,
            bg="#ef4444",
            fg="white",
            activebackground="#dc2626",
            activeforeground="white",
            font=("Segoe UI", 8, "bold"),
            relief="flat",
            padx=8,
            cursor="hand2"
        )
        btn_kick.pack(side=tk.RIGHT, fill=tk.Y, padx=(8, 0))

        # 4. Server Console Log (ScrolledText)
        console_frame = tk.LabelFrame(
            self.root,
            text=" Server Activity & Socket Event Console ",
            bg="#0b1120",
            fg="#cbd5e1",
            font=("Segoe UI", 9, "bold"),
            padx=10,
            pady=8
        )
        console_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(0, 10))

        self.console_box = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            bg="#050811",
            fg="#e2e8f0",
            font=("Consolas", 9),
            relief="flat",
            state="disabled"
        )
        self.console_box.pack(fill=tk.BOTH, expand=True)

        self.console_box.tag_config("info", foreground="#94a3b8")
        self.console_box.tag_config("connect", foreground="#10b981", font=("Consolas", 9, "bold"))
        self.console_box.tag_config("disconnect", foreground="#f43f5e", font=("Consolas", 9, "bold"))
        self.console_box.tag_config("msg", foreground="#38bdf8")
        self.console_box.tag_config("system", foreground="#fbbf24")

        # 5. Broadcast System Message Row
        bcast_bar = tk.Frame(self.root, bg="#1e293b", padx=16, pady=8)
        bcast_bar.pack(fill=tk.X, side=tk.BOTTOM)

        tk.Label(bcast_bar, text="Server Broadcast:", bg="#1e293b", fg="#cbd5e1", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.entry_bcast = tk.Entry(bcast_bar, bg="#0f172a", fg="white", font=("Segoe UI", 9), relief="flat")
        self.entry_bcast.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), ipady=4)
        self.entry_bcast.bind("<Return>", lambda e: self.send_system_broadcast())

        tk.Button(
            bcast_bar,
            text="Siarkan Notifikasi",
            command=self.send_system_broadcast,
            bg="#f59e0b",
            fg="black",
            activebackground="#d97706",
            activeforeground="black",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            cursor="hand2"
        ).pack(side=tk.RIGHT)

    def log(self, tag, text):
        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        self.console_box.config(state="normal")
        self.console_box.insert(tk.END, f"[{now_str}] ", "info")
        self.console_box.insert(tk.END, f"{text}\n", tag)
        self.console_box.config(state="disabled")
        self.console_box.yview(tk.END)

    def toggle_server(self):
        if not self.server_running:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        host = self.entry_host.get().strip()
        try:
            port = int(self.entry_port.get().strip())
        except ValueError:
            messagebox.showerror("Error Port", "Port harus berupa angka!")
            return

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((host, port))
            self.server_socket.listen()
            self.server_running = True

            self.lbl_server_status.config(text=f"STATUS: RUNNING ({host}:{port})", bg="#064e3b", fg="#34d399")
            self.btn_toggle_server.config(text="Hentikan Server", bg="#e11d48")
            self.entry_host.config(state="disabled")
            self.entry_port.config(state="disabled")

            self.log("info", f"[INFO] Socket Server diinisialisasi pada {host}:{port}")
            self.log("info", f"[INFO] Listening TCP Connections... Menunggu klien terhubung.")

            threading.Thread(target=self._accept_loop, daemon=True).start()

        except Exception as e:
            messagebox.showerror("Gagal Start", f"Tidak dapat menjalankan server:\n{e}")
            self.server_running = False

    def stop_server(self):
        self.server_running = False
        with self.clients_lock:
            for s in list(self.clients.keys()):
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except Exception:
                    pass
                try:
                    s.close()
                except Exception:
                    pass
            self.clients.clear()

        if self.server_socket:
            try:
                self.server_socket.close()
            except Exception:
                pass

        self.lbl_server_status.config(text="STATUS: STOPPED", bg="#334155", fg="#f87171")
        self.btn_toggle_server.config(text="Jalankan Server", bg="#10b981")
        self.entry_host.config(state="normal")
        self.entry_port.config(state="normal")
        self.log("disconnect", "[SHUTDOWN] Server telah dihentikan.")
        self._update_pool_tree()

    def _accept_loop(self):
        while self.server_running:
            try:
                sock, addr = self.server_socket.accept()
            except Exception:
                break

            ip, port = addr
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            fd = sock.fileno() if hasattr(sock, "fileno") else "?"

            with self.clients_lock:
                self.clients[sock] = (ip, port, fd, now_str)

            self.root.after(0, self.log, "connect", f"[CONNECTED] Klien terhubung dari {ip}:{port}")
            self.root.after(0, self._update_pool_tree)

            threading.Thread(target=self._client_read_loop, args=(sock, addr), daemon=True).start()

    def _client_read_loop(self, sock, addr):
        ip, port = addr
        buffer = ""
        while self.server_running:
            try:
                data = sock.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip("\r")
                    if not line:
                        continue
                    if line == "/quit":
                        return

                    self.total_packets += 1
                    self.root.after(0, self.log, "msg", f"[MESSAGE] {ip}:{port}: {line}")
                    self.root.after(0, self.lbl_metric_packets.config, {"text": f"Packets: {self.total_packets}"})
                    self._broadcast(f"[{ip}:{port}]: {line}", sender=sock)

            except Exception:
                break

        self._remove_client(sock)

    def _broadcast(self, msg, sender=None):
        encoded = (msg + "\n").encode("utf-8")
        dead = []
        with self.clients_lock:
            recipients = list(self.clients.keys())

        for s in recipients:
            if s != sender:
                try:
                    s.sendall(encoded)
                except Exception:
                    dead.append(s)

        for d in dead:
            self._remove_client(d)

    def _remove_client(self, sock):
        info = None
        with self.clients_lock:
            if sock in self.clients:
                info = self.clients.pop(sock)

        if info:
            ip, port, fd, _ = info
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            try:
                sock.close()
            except Exception:
                pass

            self.root.after(0, self.log, "disconnect", f"[DISCONNECTED] Klien {ip}:{port} memutuskan koneksi")
            self.root.after(0, self._update_pool_tree)

            sys_msg = f"*** SISTEM: Klien {ip}:{port} telah meninggalkan obrolan ***"
            self._broadcast(sys_msg, sender=None)

    def _update_pool_tree(self):
        for item in self.tree_pool.get_children():
            self.tree_pool.delete(item)

        with self.clients_lock:
            active_count = len(self.clients)
            for sock, (ip, port, fd, connected_at) in self.clients.items():
                self.tree_pool.insert("", tk.END, iid=str(id(sock)), values=(f"FD {fd}", f"{ip}:{port}", "ESTABLISHED", connected_at))

        self.lbl_metric_clients.config(text=f"Active Clients: {active_count}")

    def kick_selected_client(self):
        selected = self.tree_pool.selection()
        if not selected:
            messagebox.showinfo("Pilih Klien", "Silakan klik salah satu baris klien di tabel terlebih dahulu.")
            return

        sock_id = selected[0]
        with self.clients_lock:
            target_sock = None
            for s in self.clients:
                if str(id(s)) == sock_id:
                    target_sock = s
                    break

        if target_sock:
            self._remove_client(target_sock)

    def send_system_broadcast(self):
        text = self.entry_bcast.get().strip()
        if not text:
            return
        self.entry_bcast.delete(0, tk.END)

        msg = f"*** SISTEM (PENGUMUMAN SERVER): {text} ***"
        self.log("system", msg)
        self._broadcast(msg, sender=None)

    def on_closing(self):
        if self.server_running:
            self.stop_server()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ChatServerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

