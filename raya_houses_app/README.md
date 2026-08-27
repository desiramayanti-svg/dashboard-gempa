# Raya Houses — Aplikasi Website & Manajemen Property Agent

Aplikasi web internal + publik untuk perusahaan property agent **Raya Houses**, dibangun dengan
[Streamlit](https://streamlit.io) (Python) dan database SQLite bawaan (tanpa perlu setup database
server terpisah).

## ✨ Fitur

**Publik (tanpa login):**
- **Beranda** — ringkasan perusahaan, listing unggulan, sebaran tipe properti.
- **Cari Properti** — jelajahi & filter listing (tipe, kota, harga, kamar tidur, status), lihat
  detail properti lengkap dengan kontak agent penanggung jawab.

**Internal (butuh login staff):**
- **Login Staff** — otentikasi berbasis username/password dengan role (Admin, Manager, Agent,
  Finance, Marketing).
- **Manajemen Listing** — tambah, ubah, hapus, dan tugaskan listing ke agent. Agent hanya dapat
  mengubah listing miliknya sendiri; Admin/Manager dapat mengelola semua listing.
- **Manajemen Staff & Agent** — kelola data pegawai/agent, status aktif/nonaktif, serta lihat
  ringkasan performa penjualan tiap agent.
- **Keuangan** — catat transaksi (penjualan, sewa, komisi agent, pengeluaran operasional), lihat
  ringkasan arus kas bulanan dan laba bersih.
- **Statistik Penjualan** — tren penjualan bulanan, tingkat konversi, peringkat agent, performa per
  tipe properti.
- **Statistik Wilayah** — wilayah/kota paling aktif, rata-rata harga per wilayah, tipe properti
  paling **dicari** (berdasarkan jumlah dilihat), paling **laku** (unit terjual), dan **terbanyak**
  (jumlah listing).

## 🚀 Menjalankan aplikasi

```bash
pip install -r ../requirements.txt
cd raya_houses_app
streamlit run Home.py
```

Database SQLite (`raya_houses_app/data/raya_houses.db`) akan dibuat otomatis beserta data contoh
(dummy) saat pertama kali dijalankan.

## 🔑 Akun demo

| Username     | Password    | Role    |
|--------------|-------------|---------|
| admin        | admin123    | Admin   |
| manager      | manager123  | Manager |
| finance      | finance123  | Finance |
| agent.andi   | agent123    | Agent   |

⚠️ Ganti seluruh password ini sebelum digunakan di lingkungan produksi. Hashing password saat ini
menggunakan SHA-256 + pepper statis — cukup untuk MVP internal, namun untuk produksi sesungguhnya
sebaiknya diganti dengan bcrypt/argon2 dan salt unik per pengguna.

## 🗂️ Struktur proyek

```
raya_houses_app/
├── Home.py                 # Halaman beranda (entry point)
├── db.py                   # Lapisan data (SQLite) + seed data contoh
├── auth.py                 # Login, session, dan kontrol akses berbasis role
├── style.py                # Branding & styling bersama (warna emas/hitam Raya Houses)
├── data/                   # Lokasi file database (dibuat otomatis, tidak di-commit)
└── pages/
    ├── 1_Cari_Properti.py
    ├── 2_Login_Staff.py
    ├── 3_Manajemen_Listing.py
    ├── 4_Staff_dan_Agent.py
    ├── 5_Keuangan.py
    ├── 6_Statistik_Penjualan.py
    └── 7_Statistik_Wilayah.py
```

## 🎨 Branding

Warna utama mengikuti identitas logo Raya Houses: emas (`#F2A93B`) di atas latar gelap. Untuk
menampilkan logo asli (file gambar), tambahkan file logo ke folder ini dan referensikan di
`style.py`/`Home.py` — saat ini header memakai representasi teks/CSS sebagai placeholder karena
belum ada file logo yang di-commit ke repository.
