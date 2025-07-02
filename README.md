
# 🗳️ Blockchain E-Voting App (Python + Flask + Blockchain)

Aplikasi e-voting berbasis **blockchain** yang dibangun menggunakan Python, Flask, SQLite, dan WebSocket (Flask-SocketIO). Sistem ini memungkinkan proses pemilihan dilakukan secara **transparan**, **aman**, dan **terverifikasi**.

---

## 🚀 Fitur Utama

✅ Registrasi Mahasiswa  
✅ Login Admin & Mahasiswa  
✅ Voting calon ketua jurusan  
✅ Transaksi dicatat di blockchain  
✅ Verifikasi transaksi menggunakan hash  
✅ Hasil voting real-time  
✅ Socket.IO untuk notifikasi langsung  
✅ Tampilan web user-friendly (HTML/CSS)

---

## 🧪 Setup Environment (Virtualenv)

### 1. 📂 Siapkan Folder Proyek

Pastikan kamu memiliki file berikut dalam satu folder:

```
├── app.py
├── blockchain.py
├── database.py
└── templates/
```

### 2. 🔐 Buat Virtual Environment

```bash
python -m venv venv
```

### 3. ▶️ Aktifkan Virtual Environment

- **Windows**:
  ```bash
  venv\Scripts\activate
  ```
- **Linux/macOS**:
  ```bash
  source venv/bin/activate
  ```

### 4. 📦 Install Dependencies

```bash
pip install flask flask-socketio eventlet
```

Untuk menyimpan dependencies:

```bash
pip freeze > requirements.txt
```

---

## 🧭 Jalankan Aplikasi

```bash
python app.py
```

Jika berhasil, akan muncul:

```
🚀 Starting Modern E-Voting Blockchain Application...
📱 Access: http://localhost:5000
👨‍💼 Admin: http://localhost:5000/admin (admin/admin123)
```

---

## 🌐 Akses Aplikasi

| Peran        | URL                         | Info Login        |
|--------------|-----------------------------|-------------------|
| Mahasiswa    | http://localhost:5000       | Registrasi dulu   |
| Admin Panel  | http://localhost:5000/admin | admin / admin123  |

> Ubah username & password admin di bagian awal `app.py`.

---

## 📁 Struktur Folder

| File/Folder         | Fungsi Utama                                      |
|---------------------|---------------------------------------------------|
| `app.py`            | Server Flask utama                                |
| `blockchain.py`     | Logika blockchain (Block, Transaction, Validasi)  |
| `database.py`       | Akses SQLite (voters, candidates, sessions)       |
| `templates/`        | HTML halaman (login, vote, admin, hasil)          |
| `evoting.db`        | Database SQLite otomatis                          |
| `blockchain.dat`    | File rantai blockchain disimpan                   |
| `voters.dat`        | Data NIM pemilih yang sudah voting                |

---

## 🔄 Real-Time & Blockchain

- Semua voting disimpan sebagai transaksi di blockchain.
- Hash transaksi bisa diverifikasi melalui endpoint `/api/verify_tx`.
- Socket.IO digunakan untuk:
  - Update data kandidat
  - Notifikasi suara masuk
  - Statistik realtime di admin panel

---

## 🧼 Reset Data (Opsional)

Jika ingin memulai ulang dari awal (hapus semua data):

```bash
deactivate
del evoting.db blockchain.dat voters.dat
```

Atau di Linux/macOS:

```bash
rm evoting.db blockchain.dat voters.dat
```

---

## 📝 Contoh Template Wajib

Kamu perlu membuat beberapa file HTML di folder `templates/`, misalnya:

- `index.html` → Halaman awal
- `login.html` → Form login pemilih
- `register.html` → Registrasi mahasiswa
- `vote.html` → Tampilan pemungutan suara
- `admin.html` → Panel admin
- `vote-confirmed.html` → Konfirmasi berhasil memilih

---

## 📋 Dependencies (minimal)

Isi `requirements.txt` jika ingin dibagikan:

```
flask
flask-socketio
eventlet
```

Install via:

```bash
pip install -r requirements.txt
```

---

## 📄 Lisensi

Proyek ini dibuat untuk pembelajaran dan penelitian dalam pengembangan sistem e-voting berbasis blockchain. Bebas digunakan dan dimodifikasi sesuai kebutuhan.

---

## 📌 Rangkuman Teknologi yang Digunakan

| Komponen       | Fungsi                               |
| -------------- | ------------------------------------ |
| Flask          | Web framework utama                  |
| Flask-SocketIO | Komunikasi real-time                 |
| SQLite         | Database mahasiswa dan kandidat      |
| Blockchain     | Mencatat suara sebagai transaksi     |
| Pickle         | Simpan blockchain ke file lokal      |
| SHA-256 Hash   | Mengamankan data suara & blok        |
| Proof of Work  | Validasi penambahan blok baru        |
| HTML + Jinja2  | Antarmuka pengguna                   |
| WebSocket      | Notifikasi real-time (via Socket.IO) |
| Session Flask  | Manajemen login user & admin         |

---
