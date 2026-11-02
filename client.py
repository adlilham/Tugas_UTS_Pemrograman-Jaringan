# ==============================================================================
# Nama       : Aidil Ilham Werfete
# NIM        : 2322105052
# No. Absen  : 42
# Kelas      : 4TI01
# Kampus     : Universitas Cendekia Abditama
# Mata Kuliah: Jaringan Komputer (Praktikum)
# Deskripsi  : Klien Chat TCP Berbasis Socket Tingkat Rendah dengan Multithreading
# ==============================================================================

import socket
import threading
import sys
import os

# Default host dan port server
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8080

# Event untuk mengoordinasikan penghentian thread
stop_event = threading.Event()


def receive_messages(sock: socket.socket):
    """
    Fungsi thread penerima: menerima byte stream dari server secara terus-menerus,
    merangkai pecahan buffer berbasis newline (\n), dan mencetak pesan secara real-time.
    """
    buffer = ""
    try:
        while not stop_event.is_set():
            data = sock.recv(4096)
            if not data:
                # Server menutup koneksi secara normal
                if not stop_event.is_set():
                    print("\n[INFO] Koneksi ditutup oleh server.", flush=True)
                break

            buffer += data.decode("utf-8", errors="replace")

            # Memisahkan pesan per baris (\n)
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip("\r")
                if line:
                    # Cetak pesan yang diterima apa adanya (format sudah diatur server)
                    # Jika terminal interaktif, bersihkan baris prompt dan tampilkan pesan lalu prompt kembali
                    if sys.stdout.isatty():
                        print(f"\r{line}\n> ", end="", flush=True)
                    else:
                        print(f"{line}", flush=True)

    except (ConnectionResetError, BrokenPipeError, OSError):
        if not stop_event.is_set():
            print("\n[INFO] Koneksi ke server terputus.", flush=True)
    finally:
        stop_event.set()


def main():
    # Parsing argumen baris perintah: python client.py [HOST] [PORT]
    host = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_HOST
    port = DEFAULT_PORT
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"[ERROR] Port tidak valid: {sys.argv[2]}")
            sys.exit(1)

    # Membuat socket TCP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f"[*] Menghubungi server chat di {host}:{port}...")
    try:
        client_socket.connect((host, port))
    except (ConnectionRefusedError, OSError) as err:
        print(f"[GAGAL] Tidak dapat terhubung ke server: {err}")
        sys.exit(1)

    local_ip, local_port = client_socket.getsockname()
    print("===========================================================")
    print("                APLIKASI CHAT CLIENT TCP                   ")
    print("===========================================================")
    print(" Nama       : Aidil Ilham Werfete")
    print(" NIM        : 2322105052")
    print(" No. Absen  : 42")
    print(" Kelas      : 4TI01")
    print(" Kampus     : Universitas Cendekia Abditama")
    print("===========================================================")
    print(f" Status     : TERHUBUNG KE SERVER CHAT")
    print(f" Alamat Server : {host}:{port}")
    print(f" Alamat Lokal  : {local_ip}:{local_port}")
    print(" Petunjuk:")
    print("  - Ketik pesan lalu tekan Enter untuk mengirim.")
    print("  - Ketik '/quit' atau tekan Ctrl+C untuk keluar.")
    print("===========================================================")

    # Menjalankan thread penerima pesan (daemon=True)
    receiver_thread = threading.Thread(
        target=receive_messages,
        args=(client_socket,),
        daemon=True
    )
    receiver_thread.start()

    # Loop utama (main thread) untuk membaca input pengguna dari keyboard
    try:
        while not stop_event.is_set():
            try:
                # Tampilkan prompt input jika masih berjalan
                msg = input("> ")
            except EOFError:
                # Input pipe berakhir
                break
            except KeyboardInterrupt:
                # Tangani Ctrl+C di terminal klien
                print("\n[INFO] Mengakhiri sesi chat...")
                break

            if stop_event.is_set():
                break

            pesan_bersih = msg.strip()

            # Tangani perintah keluar /quit
            if pesan_bersih == "/quit":
                try:
                    client_socket.sendall(b"/quit\n")
                except OSError:
                    pass
                break

            # Kirim pesan jika tidak kosong
            if pesan_bersih:
                try:
                    payload = (pesan_bersih + "\n").encode("utf-8")
                    client_socket.sendall(payload)
                except (ConnectionResetError, BrokenPipeError, OSError):
                    print("[ERROR] Gagal mengirim pesan. Server mungkin telah terputus.")
                    break

    finally:
        # Tandai penghentian dan bersihkan socket
        stop_event.set()
        try:
            client_socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            client_socket.close()
        except OSError:
            pass
        print("[INFO] Klien telah keluar. Sesi selesai.")


if __name__ == "__main__":
    main()

