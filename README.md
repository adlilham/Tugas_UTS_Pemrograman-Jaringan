# Proyek Praktikum Jaringan Komputer: Aplikasi Chat Server & Client TCP Multithreaded

Proyek ini mengimplementasikan aplikasi **Chat Server dan Client berbasis TCP** menggunakan bahasa pemrograman **Python 3** murni (hanya menggunakan modul bawaan `socket` tingkat rendah dan `threading`, tanpa framework/library eksternal).

---

## Identitas Pengembang
- **Nama**        : Aidil Ilham Werfete
- **NIM**         : 2322105052
- **No. Absen**   : 42
- **Kelas**       : 4TI01
- **Kampus**      : Universitas Cendekia Abditama
- **Mata Kuliah** : Praktikum Jaringan Komputer

---

## Struktur Berkas Proyek

```text
chat-tcp/
├── server.py         # Program utama TCP Chat Server (CLI Multithreaded)
├── client.py         # Program TCP Chat Client (CLI Terminal interaktif)
├── gui_server.py     # Aplikasi Desktop GUI Server Dashboard (Tkinter Native)
├── gui_client.py     # Aplikasi Desktop GUI Klien Chat (Tkinter Native)
├── simulator.html    # Simulator Web Enterprise v3.0 (Wireshark Sniffer + Canvas + Cetak Laporan)
├── test_scenario.py  # Skrip pengujian otomatis (3 skenario pengujian)
└── README.md         # Dokumentasi lengkap, cara penggunaan, dan arsitektur
```

---

## Arsitektur & Prinsip Kerja Sistem

Aplikasi ini dirancang mengikuti prinsip sistem jaringan terdistribusi berbasis **Client-Server** dengan protokol transport **TCP (Transmission Control Protocol)**:

### 1. TCP Socket Tingkat Rendah
- Menggunakan socket bertipe `socket.AF_INET` (IPv4) dan `socket.SOCK_STREAM` (koneksi stream berorientasi byte yang andal, berurutan, dan bebas duplikasi).
- Server mengaktifkan opsi socket `SO_REUSEADDR` (`setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)`) agar port dapat segera digunakan kembali tanpa tertahan dalam status `TIME_WAIT`.

### 2. Konkurensi Multithreading
- **Server**:
  - Thread Utama (*Main Thread*): Menjalankan loop penerima koneksi (`server_socket.accept()`).
  - Worker Thread: Setiap ada klien baru yang terhubung, server membuat dan menjalankan thread khusus (`threading.Thread(target=handle_client, daemon=True)`) yang bertugas menjalankan read loop (`recv()`) dari klien tersebut secara independen tanpa memblokir klien lain.
- **Client**:
  - Receiver Thread (`daemon=True`): Menjalankan loop pembacaan pesan secara asynchronous dari server (`receive_messages`) dan mencetaknya ke konsol secara *real-time*.
  - Main Thread: Membaca input ketikan pengguna dari keyboard (`input("> ")`) dan mengirimkannya ke server (`sendall`).

### 3. Connection Pool & Thread Synchronization (Lock)
- Seluruh socket klien yang aktif disimpan dalam struktur data dictionary (*Connection Pool*):
  ```python
  clients = { client_socket: (ip, port) }
  ```
- Karena dictionary ini diakses dan dimodifikasi secara bersamaan oleh banyak worker thread (saat registrasi klien, pengiriman broadcast, dan penghapusan klien), seluruh operasi kritis dilindungi menggunakan objek pengunci `threading.Lock()` (`clients_lock`) guna mencegah *race condition*.

### 4. Protokol Pembatasan Pesan (Line-Delimited Framing)
- Karena TCP adalah protokol *byte-stream* tanpa batas pesan alami (*packet boundary*), pesan dapat terpecah (*fragmentation*) atau menyatu (*concatenation*).
- Sistem ini menerapkan *message framing* sederhana dengan karakter *newline* (`\n`) sebagai pemisah pesan serta encoding `UTF-8`. Setiap data yang diterima diakumulasi ke dalam buffer lokal sebelum dipecah menjadi baris-baris pesan yang utuh.

### 5. Penanganan Disconnect & Toleransi Kesalahan (Fault Tolerance)
- Server menangani pemutusan koneksi secara halus (saat `recv()` mengembalikan `b""` atau klien mengirim perintah `/quit`), maupun pemutusan paksa (*crash*/Ctrl+C) yang memicu exception `ConnectionResetError`, `BrokenPipeError`, atau `OSError`.
- Fungsi `remove_client()` menghapus socket dari pool, menutup socket, memperbarui hitungan klien aktif, dan menyiarkan notifikasi ke seluruh klien lain:
  ```text
  *** SISTEM: Klien <IP>:<PORT> telah meninggalkan obrolan ***
  ```
- Jika terjadi kegagalan `sendall()` ke satu klien saat proses *broadcast*, server tidak akan mengalami *crash*; klien yang gagal tersebut akan ditandai dan dibersihkan dari pool secara aman.

---

## Panduan Menjalankan Aplikasi

### Kebutuhan Sistem
- Python 3.8 atau lebih baru.
- Tidak memerlukan instalasi paket tambahan (cukup bawaan Python).

### Menjalankan Server
Buka terminal dan jalankan:
```bash
python server.py
```
*(Opsional: Anda dapat menentukan nomor port kustom, misalnya `python server.py 9000`)*

### Menjalankan Klien
Buka 3 terminal terpisah untuk menguji komunikasi multi-klien:

- **Terminal Klien 1**:
  ```bash
  python client.py
  ```
- **Terminal Klien 2**:
  ```bash
  python client.py
  ```
- **Terminal Klien 3**:
  ```bash
  python client.py
  ```
*(Opsional: Anda dapat menyambung ke host dan port tertentu, misalnya `python client.py 127.0.0.1 8080`)*

---

## Skenario Pengujian & Contoh Output

### Pengujian 1: Inisialisasi & Multi-Client
- **Langkah**: Jalankan 1 server dan 3 klien pada terminal berbeda.
- **Hasil di Server**:
  ```text
  [CONNECTED] Klien terhubung dari 127.0.0.1:49812
  [INFO] Klien aktif: 1
  [CONNECTED] Klien terhubung dari 127.0.0.1:49813
  [INFO] Klien aktif: 2
  [CONNECTED] Klien terhubung dari 127.0.0.1:49814
  [INFO] Klien aktif: 3
  ```

### Pengujian 2: Broadcast Pesan
- **Langkah**: Klien 1 mengetik pesan:
  ```text
  > Halo kawan-kawan, ini pesan uji broadcast dari Klien 1!
  ```
- **Hasil di Konsol Server**:
  ```text
  [MESSAGE] 127.0.0.1:49812: Halo kawan-kawan, ini pesan uji broadcast dari Klien 1!
  ```
- **Hasil di Klien 2 & Klien 3**:
  ```text
  [127.0.0.1:49812]: Halo kawan-kawan, ini pesan uji broadcast dari Klien 1!
  ```
- **Hasil di Klien 1**:
  Pesan tidak dipantulkan kembali ke pengirim.

### Pengujian 3: Disconnect & Recovery
- **Langkah**: Klien 2 ditutup mendadak (Ctrl+C atau tutup jendela terminal).
- **Hasil di Konsol Server**:
  ```text
  [DISCONNECTED] Klien 127.0.0.1:49813 memutuskan koneksi
  [INFO] Klien aktif: 2
  ```
- **Hasil di Klien 1 & Klien 3**:
  ```text
  *** SISTEM: Klien 127.0.0.1:49813 telah meninggalkan obrolan ***
  ```
- **Uji Komunikasi Lanjutan**:
  Klien 3 mengirim pesan:
  ```text
  > Klien 1, apakah kamu masih bisa mendengar saya?
  ```
  Klien 1 menerima:
  ```text
  [127.0.0.1:49814]: Klien 1, apakah kamu masih bisa mendengar saya?
  ```

---

## Pengujian Otomatis (`test_scenario.py`)

Untuk memvalidasi seluruh spesifikasi dan kriteria secara otomatis tanpa membuka banyak terminal manual:

```bash
python test_scenario.py
```

Skrip ini akan menjalankan server sebagai *subprocess*, menghubungkan 3 klien secara konkuren, menguji pengiriman pesan dan pemutusan mendadak dengan paket TCP RST, serta memvalidasi kesesuaian format log dan pesan menggunakan *Regular Expression* (Regex).

