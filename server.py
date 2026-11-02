# ==============================================================================
# Nama       : Aidil Ilham Werfete
# NIM        : 2322105052
# No. Absen  : 42
# Kelas      : 4TI01
# Kampus     : Universitas Cendekia Abditama
# Mata Kuliah: Jaringan Komputer (Praktikum)
# Deskripsi  : Server Chat TCP Berbasis Socket Tingkat Rendah dengan Multithreading
# ==============================================================================

import socket
import threading
import sys

# Konstanta konfigurasi jaringan server
HOST = "0.0.0.0"
PORT = 8080

# Connection pool untuk menyimpan klien yang terhubung:
# Format dictionary: { client_socket: (ip, port) }
clients = {}

# Lock untuk sinkronisasi thread saat mengakses connection pool
clients_lock = threading.Lock()

# Status operasional server
server_running = True


def broadcast(message: str, sender_socket=None):
    """
    Mengirimkan pesan ke seluruh klien aktif kecuali socket pengirim (sender_socket).
    Jika pengiriman ke salah satu klien gagal (misal koneksi putus mendadak),
    klien yang bermasalah akan dicatat untuk dihapus dari pool tanpa menghentikan
    proses broadcast ke klien lain yang masih sehat.
    """
    # Pastikan pesan diakhiri newline sebagai pembatas protokol (line delimiter)
    if not message.endswith("\n"):
        message += "\n"
    encoded_message = message.encode("utf-8")

    dead_clients = []

    # Salin daftar klien di dalam lock agar thread-safe
    with clients_lock:
        active_recipients = list(clients.items())

    for client_sock, client_addr in active_recipients:
        # Jangan kirimkan kembali ke pengirim pesan
        if client_sock != sender_socket:
            try:
                client_sock.sendall(encoded_message)
            except (ConnectionResetError, BrokenPipeError, OSError):
                # Tandai socket yang gagal kirim untuk dibersihkan
                dead_clients.append(client_sock)

    # Bersihkan klien yang gagal saat proses broadcast
    for dead_sock in dead_clients:
        remove_client(dead_sock, notify=True)


def remove_client(client_socket, notify=True):
    """
    Menghapus socket klien dari connection pool, menutup koneksi socket,
    mencetak log pemutusan koneksi, serta menyiarkan pesan sistem ke klien lain.
    """
    client_addr = None
    with clients_lock:
        if client_socket in clients:
            client_addr = clients.pop(client_socket)
            remaining_count = len(clients)

    # Jika klien memang ada di pool sebelum dihapus
    if client_addr:
        ip, port = client_addr
        
        # Log konsol server persis sesuai spesifikasi
        print(f"[DISCONNECTED] Klien {ip}:{port} memutuskan koneksi", flush=True)
        print(f"[INFO] Klien aktif: {remaining_count}", flush=True)

        # Tutup socket dengan aman
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            client_socket.close()
        except OSError:
            pass

        # Siarkan notifikasi bahwa klien telah keluar
        if notify:
            system_msg = f"*** SISTEM: Klien {ip}:{port} telah meninggalkan obrolan ***"
            broadcast(system_msg, sender_socket=None)


def handle_client(client_socket, client_address):
    """
    Fungsi worker thread untuk menangani siklus baca pesan dari satu klien.
    Menggunakan buffer berbasis baris (\n) untuk menangani pemecahan/penggabungan paket TCP.
    """
    ip, port = client_address
    buffer = ""

    try:
        while server_running:
            # Membaca data byte stream dari socket
            data = client_socket.recv(4096)
            if not data:
                # b"" menandakan klien menutup koneksi secara normal (graceful EOF)
                break

            # Decode data dengan toleransi karakter
            buffer += data.decode("utf-8", errors="replace")

            # Ekstrak seluruh pesan lengkap berdasarkan delimiter newline '\n'
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip("\r")
                
                # Abaikan baris kosong
                if not line:
                    continue

                # Tangani perintah khusus keluar jika klien mengirimkan /quit
                if line == "/quit":
                    return

                # Log pesan di konsol server persis sesuai spesifikasi
                print(f"[MESSAGE] {ip}:{port}: {line}", flush=True)

                # Broadcast ke semua klien lain persis sesuai format spesifikasi
                broadcast(f"[{ip}:{port}]: {line}", sender_socket=client_socket)

    except (ConnectionResetError, BrokenPipeError, OSError):
        # Klien terputus paksa (misal Ctrl+C atau koneksi putus)
        pass
    finally:
        # Bersihkan resource klien
        remove_client(client_socket, notify=True)


def start_server(host=HOST, port=PORT):
    """
    Inisialisasi socket server TCP, bind, listen, dan menjalankan accept loop.
    """
    global server_running

    # Membuat socket TCP IPv4
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Mengaktifkan SO_REUSEADDR agar port dapat langsung digunakan kembali
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        server_socket.bind((host, port))
        server_socket.listen()
        print("===========================================================", flush=True)
        print("                APLIKASI CHAT SERVER TCP                   ", flush=True)
        print("===========================================================", flush=True)
        print(" Nama       : Aidil Ilham Werfete", flush=True)
        print(" NIM        : 2322105052", flush=True)
        print(" No. Absen  : 42", flush=True)
        print(" Kelas      : 4TI01", flush=True)
        print(" Kampus     : Universitas Cendekia Abditama", flush=True)
        print("===========================================================", flush=True)
        print(f" Status     : AKTIF", flush=True)
        print(f" Alamat     : {host}:{port}", flush=True)
        print(f" Menunggu koneksi klien...", flush=True)
        print("===========================================================", flush=True)

        while server_running:
            try:
                client_socket, client_address = server_socket.accept()
            except OSError:
                # Terjadi saat server_socket ditutup saat shutdown
                break

            ip, port_client = client_address

            # Daftarkan klien ke connection pool dengan pengamanan lock
            with clients_lock:
                clients[client_socket] = (ip, port_client)
                active_count = len(clients)

            # Log koneksi baru persis sesuai spesifikasi
            print(f"[CONNECTED] Klien terhubung dari {ip}:{port_client}", flush=True)
            print(f"[INFO] Klien aktif: {active_count}", flush=True)

            # Buat thread baru (daemon=True) untuk menangani komunikasi klien tersebut
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address),
                daemon=True
            )
            client_thread.start()

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Menerima sinyal Ctrl+C, mematikan server...", flush=True)
    finally:
        server_running = False

        # Tutup seluruh socket klien yang masih tersambung
        with clients_lock:
            all_sockets = list(clients.keys())
            clients.clear()

        for sock in all_sockets:
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                sock.close()
            except OSError:
                pass

        # Tutup socket utama server
        try:
            server_socket.close()
        except OSError:
            pass

        print("[SHUTDOWN] Server berhasil dimatikan dengan rapi.", flush=True)


if __name__ == "__main__":
    # Izinkan override port melalui argumen command line jika diberikan
    port_arg = PORT
    if len(sys.argv) > 1:
        try:
            port_arg = int(sys.argv[1])
        except ValueError:
            print(f"[WARN] Argumen port '{sys.argv[1]}' tidak valid, menggunakan default {PORT}")
    
    start_server(HOST, port_arg)

