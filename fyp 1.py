import streamlit as st
import pandas as pd
import sqlite3
import os
import time
from datetime import date, datetime, timedelta

# 1. KONFIGURASI PAGE
st.set_page_config(page_title="Sistem Pinjaman Alat Ukur PUO", layout="wide", page_icon="🏗️")

DB_FILE = "sistem_pinjaman.db"
LIMIT_JAM = 3 

STAFF_USER = "admin"
STAFF_PASS = "puo123"

# 2. FUNGSI DATABASE (AUTO-REPAIR VERSION)
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # --- PEMBERSIHAN KHAS (Jika Table Sejarah Tiada) ---
    # Kod ini akan paksa bina table sejarah jika ia tak wujud lagi
    c.execute('''CREATE TABLE IF NOT EXISTS sejarah (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alat TEXT,
                    nama TEXT,
                    kelas TEXT,
                    aksi TEXT,
                    waktu TEXT
                )''')
    
    # Bina table alatan jika belum ada
    c.execute('''CREATE TABLE IF NOT EXISTS alatan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alat TEXT UNIQUE,
                    status TEXT,
                    peminjam TEXT,
                    kelas TEXT,
                    tarikh TEXT,
                    masa_tamat TEXT,
                    disahkan INTEGER DEFAULT 0
                )''')
    
    # Check kolom 'disahkan' - Kalau tak wujud, tambah sekarang!
    try:
        c.execute("SELECT disahkan FROM alatan LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE alatan ADD COLUMN disahkan INTEGER DEFAULT 0")
        conn.commit()

    # Masukkan data master jika kosong
    c.execute("SELECT COUNT(*) FROM alatan")
    if c.fetchone()[0] == 0:
        alatan_master = [
            "TS141", "TS741", "TS140", "TS WAKAF", "PRISM 1", "PRISM 2", "PRISM 3", "PRISM 4", 
            "PRISM 5", "PRISM 6", "PRISM 7", "PRISM 8", "TRIPOD 100", "TRIPOD 84", "TRIPOD 24", 
            "TRIPOD 60", "TRIPOD 67", "TRIPOD 97", "TRIPOD 10", "TRIPOD 38", "TRIPOD 27", 
            "SUN FILTER 1", "SUN FILTER 2", "SUN FILTER 3", "SUN FILTER 4", "STAFF 1", "STAFF 2", "STAFF 3"
        ]
        for alat in alatan_master:
            c.execute("INSERT INTO alatan (alat, status, peminjam, kelas, tarikh, masa_tamat, disahkan) VALUES (?, ?, ?, ?, ?, ?, ?)",
                      (alat, "Tersedia", "-", "-", "-", "-", 0))
    
    conn.commit()
    conn.close()

# --- PENTING: Kena panggil init_db dulu sebelum buat benda lain ---
init_db()

# Sambung dengan fungsi get_data_from_db dan lain-lain...
