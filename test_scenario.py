# ==============================================================================
# Nama       : Aidil Ilham Werfete
# NIM        : 2322105052
# No. Absen  : 42
# Kelas      : 4TI01
# Kampus     : Universitas Cendekia Abditama
# Mata Kuliah: Jaringan Komputer (Praktikum)
# Deskripsi  : Skrip Pengujian Otomatis Server & Klien Chat TCP (3 Skenario)
# ==============================================================================

import socket
import subprocess
import threading
import time
import queue
import re
import sys
import os
import struct

def find_free_port():
    """Mencari port TCP lokal yang sedang bebas agar tidak bentrok dengan server lain."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

TEST_HOST = "127.0.0.1"
TEST_PORT = find_free_port()


class TestChatClient:
    """
    Klien pembantu untuk pengujian otomatis yang memiliki thread penerima
    dan queue penampung pesan masuk.
    """
    def __init__(self, host=TEST_HOST, port=TEST_PORT, name="Klien"):
        self.host = host
        self.port = port
        self.name = name
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))
        self.local_ip, self.local_port = self.sock.getsockname()
        
        self.incoming_messages = queue.Queue()
        self.running = True
        self.receiver_thread = threading.Thread(target=self._read_loop, daemon=True)
        self.receiver_thread.start()

    def _read_loop(self):
        buffer = ""
        while self.running:
            try:
                data = self.sock.recv(4096)
                if not data:
                    break
                buffer += data.decode("utf-8", errors="replace")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip("\r")
                    if line:
                        self.incoming_messages.put(line)
            except OSError:
                break

    def send(self, message: str):
        payload = (message + "\n").encode("utf-8")
        self.sock.sendall(payload)

    def get_message(self, timeout=2.0):
        try:
            return self.incoming_messages.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self):
        """Penutupan normal (graceful shutdown)."""
        self.running = False
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass

    def abort(self):
        """
        Simulasi crash mendadak (abrupt kill) dengan mengirim paket TCP RST
        melalui SO_LINGER bernilai 0.
        """
        self.running = False
        try:
            # Set linger off: l_onoff=1, l_linger=0 (kirim RST)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_LINGER, struct.pack('ii', 1, 0))
        except OSError:
            pass
        try:
            self.sock.close()
        except OSError:
            pass


def read_server_stdout(process, server_lines_queue):
    """Membaca output server baris per baris secara real-time."""
    for line in iter(process.stdout.readline, ''):
        clean_line = line.strip()
        if clean_line:
            server_lines_queue.put(clean_line)


def run_tests():
    print("==================================================================")
    print("      PENGUJIAN OTOMATIS APLIKASI CHAT SERVER & CLIENT TCP       ")
    print("==================================================================")
    print(f"[*] Mahasiswa  : Aidil Ilham Werfete (NIM: 2322105052 / Absen: 42)")
    print(f"[*] Kelas      : 4TI01 - Universitas Cendekia Abditama")
    print("==================================================================\n")

    # Jalankan server.py sebagai subprocess
    server_script = os.path.join(os.path.dirname(__file__), "server.py")
    server_process = subprocess.Popen(
        [sys.executable, "-u", server_script, str(TEST_PORT)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    server_lines = queue.Queue()
    reader_thread = threading.Thread(
        target=read_server_stdout,
        args=(server_process, server_lines),
        daemon=True
    )
    reader_thread.start()

    # Beri waktu sebentar bagi server untuk bind & listen
    time.sleep(0.8)

    test_results = {}

    try:
        # ======================================================================
        # PENGUJIAN 1: Inisialisasi & Multi-Client (3 Klien Bersamaan)
        # ======================================================================
        print(">>> Menjalankan Pengujian 1: Inisialisasi & Multi-Client...")
        c1 = TestChatClient(name="Klien 1")
        time.sleep(0.2)
        c2 = TestChatClient(name="Klien 2")
        time.sleep(0.2)
        c3 = TestChatClient(name="Klien 3")
        time.sleep(0.5)

        # Kumpulkan log dari server
        connected_logs = []
        timeout = time.time() + 2.0
        while time.time() < timeout and len(connected_logs) < 3:
            try:
                line = server_lines.get(timeout=0.3)
                if "[CONNECTED]" in line:
                    connected_logs.append(line)
            except queue.Empty:
                pass

        print(f"    - Alamat Klien 1 : {c1.local_ip}:{c1.local_port}")
        print(f"    - Alamat Klien 2 : {c2.local_ip}:{c2.local_port}")
        print(f"    - Alamat Klien 3 : {c3.local_ip}:{c3.local_port}")
        print("    - Log server terdeteksi:")
        for log in connected_logs:
            print(f"      {log}")

        # Validasi log format persis: [CONNECTED] Klien terhubung dari IP:PORT
        pattern_connected = re.compile(r"^\[CONNECTED\] Klien terhubung dari (?:127\.0\.0\.1|0\.0\.0\.0|\d+\.\d+\.\d+\.\d+):(\d+)$")
        ports_logged = set()
        all_formats_valid = True

        for log in connected_logs:
            match = pattern_connected.match(log)
            if match:
                ports_logged.add(int(match.group(1)))
            else:
                all_formats_valid = False

        expected_ports = {c1.local_port, c2.local_port, c3.local_port}
        test1_pass = (
            len(connected_logs) == 3 and
            all_formats_valid and
            ports_logged == expected_ports and
            len(ports_logged) == 3
        )

        test_results["Pengujian 1"] = test1_pass
        if test1_pass:
            print("[PASS] Pengujian 1: Berhasil melayani 3 klien bersamaan dengan IP/Port berbeda.")
        else:
            print(f"[FAIL] Pengujian 1: Gagal memverifikasi 3 koneksi klien. Terdeteksi: {connected_logs}")

        print("-" * 66)

        # ======================================================================
        # PENGUJIAN 2: Broadcast Pesan
        # ======================================================================
        print(">>> Menjalankan Pengujian 2: Broadcast Pesan...")
        pesan_uji = "Halo kawan-kawan, ini pesan uji broadcast dari Klien 1!"
        c1.send(pesan_uji)

        # Klien 2 dan 3 harus menerima pesan, Klien 1 TIDAK boleh menerima pesan
        msg_c2 = c2.get_message(timeout=2.0)
        msg_c3 = c3.get_message(timeout=2.0)
        msg_c1 = c1.get_message(timeout=0.5)  # Harusnya None

        expected_broadcast = f"[{c1.local_ip}:{c1.local_port}]: {pesan_uji}"
        pattern_broadcast = re.compile(rf"^\[(?:127\.0\.0\.1|\d+\.\d+\.\d+\.\d+):{c1.local_port}\]: {re.escape(pesan_uji)}$")

        print(f"    - Pesan dikirim Klien 1 : '{pesan_uji}'")
        print(f"    - Diterima oleh Klien 2 : {msg_c2}")
        print(f"    - Diterima oleh Klien 3 : {msg_c3}")
        print(f"    - Diterima oleh Klien 1 : {msg_c1} (harus None)")

        test2_pass = (
            msg_c2 is not None and pattern_broadcast.match(msg_c2) is not None and
            msg_c3 is not None and pattern_broadcast.match(msg_c3) is not None and
            msg_c1 is None
        )

        test_results["Pengujian 2"] = test2_pass
        if test2_pass:
            print("[PASS] Pengujian 2: Broadcast berhasil. Format pesan persis sesuai spesifikasi dan tidak dipantulkan ke pengirim.")
        else:
            print("[FAIL] Pengujian 2: Format broadcast tidak cocok atau pesan tidak terdistribusi dengan benar.")

        print("-" * 66)

        # ======================================================================
        # PENGUJIAN 3: Disconnect & Recovery
        # ======================================================================
        print(">>> Menjalankan Pengujian 3: Disconnect & Recovery...")
        c2_ip = c2.local_ip
        c2_port = c2.local_port
        
        # Putus Klien 2 secara mendadak (abrupt / crash)
        c2.abort()
        time.sleep(0.5)

        # Tangkap notifikasi sistem di Klien 1 dan Klien 3
        sys_msg_c1 = c1.get_message(timeout=2.0)
        sys_msg_c3 = c3.get_message(timeout=2.0)

        expected_system_msg = f"*** SISTEM: Klien {c2_ip}:{c2_port} telah meninggalkan obrolan ***"
        pattern_system = re.compile(rf"^\*\*\* SISTEM: Klien (?:127\.0\.0\.1|\d+\.\d+\.\d+\.\d+):{c2_port} telah meninggalkan obrolan \*\*\*$")

        print(f"    - Klien 2 diputus paksa ({c2_ip}:{c2_port})")
        print(f"    - Notifikasi di Klien 1 : {sys_msg_c1}")
        print(f"    - Notifikasi di Klien 3 : {sys_msg_c3}")

        # Periksa log server untuk DISCONNECTED dan jumlah klien aktif
        disconnected_log_found = False
        active_count_found = False
        timeout = time.time() + 1.5
        while time.time() < timeout:
            try:
                line = server_lines.get(timeout=0.2)
                if f"[DISCONNECTED] Klien {c2_ip}:{c2_port} memutuskan koneksi" in line:
                    disconnected_log_found = True
                if "[INFO] Klien aktif: 2" in line:
                    active_count_found = True
            except queue.Empty:
                pass

        print(f"    - Log server DISCONNECTED : {'Ditemukan' if disconnected_log_found else 'Tidak Ditemukan'}")
        print(f"    - Log server Klien aktif: 2: {'Ditemukan' if active_count_found else 'Tidak Ditemukan'}")

        # Uji pengiriman pesan antara Klien 3 dan Klien 1 untuk membuktikan server tetap bekerja
        pesan_recovery = "Klien 1, apakah kamu masih bisa mendengar saya?"
        c3.send(pesan_recovery)
        recovery_recv_c1 = c1.get_message(timeout=2.0)
        expected_recovery = f"[{c3.local_ip}:{c3.local_port}]: {pesan_recovery}"
        print(f"    - Uji komunikasi sisa (Klien 3 -> Klien 1): {recovery_recv_c1}")

        server_alive = (server_process.poll() is None)

        test3_pass = (
            server_alive and
            sys_msg_c1 is not None and pattern_system.match(sys_msg_c1) is not None and
            sys_msg_c3 is not None and pattern_system.match(sys_msg_c3) is not None and
            disconnected_log_found and
            active_count_found and
            recovery_recv_c1 == expected_recovery
        )

        test_results["Pengujian 3"] = test3_pass
        if test3_pass:
            print("[PASS] Pengujian 3: Server pulih dari crash klien. Pool diperbarui dan klien tersisa tetap dapat berkomunikasi.")
        else:
            print("[FAIL] Pengujian 3: Kegagalan pada verifikasi disconnect/recovery.")

        # Bersihkan klien yang tersisa
        c1.close()
        c3.close()

    finally:
        # Matikan server subprocess
        try:
            server_process.terminate()
            server_process.wait(timeout=2)
        except Exception:
            server_process.kill()

    print("\n==================================================================")
    print("                      RINGKASAN HASIL PENGUJIAN                   ")
    print("==================================================================")
    all_passed = True
    for test_name, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        print(f" {test_name.ljust(25)} : {status}")
        if not result:
            all_passed = False

    print("==================================================================")
    if all_passed:
        print(" SEMUA TEST CASE LOLOS (100% SUKSES) ")
    else:
        print(" TERDAPAT TEST CASE YANG GAGAL ")
    print("==================================================================")

    return all_passed


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

