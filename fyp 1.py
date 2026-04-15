import streamlit as st
import pandas as pd
import sqlite3
import os
import time
from datetime import date, datetime, timedelta

# 1. KONFIGURASI PAGE
st.set_page_config(page_title="Sistem Pinjaman Alat Ukur PUO", layout="wide", page_icon="🏗️")

# NAMA DATABASE BARU (Guna v5 supaya fresh terus)
DB_FILE = "sistem_puo_v5.db"
LIMIT_JAM = 3 

STAFF_USER = "admin"
STAFF_PASS = "puo123"

# 2. FUNGSI DATABASE
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Table Utama
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
    # Table Sejarah
    c.execute('''CREATE TABLE IF NOT EXISTS sejarah (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alat TEXT,
                    nama TEXT,
                    kelas TEXT,
                    aksi TEXT,
                    waktu TEXT
                )''')
    
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

def get_data(table="alatan"):
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
    conn.close()
    return df

def rekod_sejarah(alat, nama, kelas, aksi):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    waktu = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    c.execute("INSERT INTO sejarah (alat, nama, kelas, aksi, waktu) VALUES (?, ?, ?, ?, ?)",
              (alat, nama, kelas, aksi, waktu))
    conn.commit()
    conn.close()

def hantar_permohonan(alat_list, nama, kelas):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    tarikh_hari_ini = date.today().strftime("%d/%m/%Y")
    for alat in alat_list:
        c.execute("UPDATE alatan SET status='Menunggu Pengesahan', peminjam=?, kelas=?, tarikh=?, disahkan=0 WHERE alat=?", 
                  (nama, kelas, tarikh_hari_ini, alat))
        rekod_sejarah(alat, nama, kelas, "MINTA PINJAM")
    conn.commit()
    conn.close()

def sahkan_oleh_admin(alat):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    masa_tamat = (datetime.now() + timedelta(hours=LIMIT_JAM)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE alatan SET status='Dipinjam', disahkan=1, masa_tamat=? WHERE alat=?", (masa_tamat, alat))
    conn.commit()
    conn.close()
    rekod_sejarah(alat, "-", "-", "DISAHKAN ADMIN")

def pulangkan_alat(alat):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT peminjam, kelas FROM alatan WHERE alat=?", (alat,))
    res = c.fetchone()
    p_nama = res[0] if res else "-"
    p_kelas = res[1] if res else "-"
    rekod_sejarah(alat, p_nama, p_kelas, "PULANG")
    c.execute("UPDATE alatan SET status='Tersedia', peminjam='-', kelas='-', tarikh='-', masa_tamat='-', disahkan=0 WHERE alat=?", (alat,))
    conn.commit()
    conn.close()

# INITIALIZE
init_db()

# 3. SIDEBAR
st.sidebar.title("NAVIGASI")
menu = st.sidebar.selectbox("Pilih Halaman", ["🏠 UTAMA", "📝 PINJAM ALAT", "⏳ TIMER", "🔐 AKSES STAF"])

# 4. UTAMA
if menu == "🏠 UTAMA":
    st.title("🏗️ Sistem Pinjaman Alat Ukur PUO")
    df = get_data()
    st.subheader("Status Semasa Alatan")
    st.dataframe(df[['alat', 'status', 'peminjam', 'kelas']], use_container_width=True, hide_index=True)

# 5. PINJAM (STUDENT)
elif menu == "📝 PINJAM ALAT":
    st.title("📝 Borang Pinjaman Student")
    df = get_data()
    senarai_tersedia = df[df['status'] == 'Tersedia']['alat'].tolist()
    
    with st.form("pinjam_form", clear_on_submit=True):
        nama = st.text_input("Nama Penuh").upper()
        kelas = st.text_input("Kelas (DGU)").upper()
        pilihan = st.multiselect("Pilih Alat", senarai_tersedia)
        if st.form_submit_button("HANTAR PERMOHONAN"):
            if nama and kelas and pilihan:
                hantar_permohonan(pilihan, nama, kelas)
                st.warning("Permohonan dihantar. Sila jumpa Admin untuk 'Tick' (✔️) pengesahan.")
                time.sleep(1); st.rerun()
            else: st.error("Sila isi semua maklumat!")

# 6. TIMER
elif menu == "⏳ TIMER":
    st.title("⏳ Masa Pinjaman (Timer)")
    df = get_data()
    aktif = df[df['disahkan'] == 1]
    if aktif.empty: 
        st.info("Tiada alat yang sedang dipinjam secara sah.")
    else:
        for _, row in aktif.iterrows():
            c1, c2, c3 = st.columns([2,2,1])
            c1.write(f"**{row['alat']}**")
            c1.caption(f"👤 {row['peminjam']} ({row['kelas']})")
            
            # Logik kira baki masa
            tamat = datetime.strptime(row['masa_tamat'], "%Y-%m-%d %H:%M:%S")
            baki = tamat - datetime.now()
            
            if baki.total_seconds() > 0:
                # Format baki masa HH:MM:SS
                m, s = divmod(int(baki.total_seconds()), 60)
                h, m = divmod(m, 60)
                c2.warning(f"⏱️ {h:02d}:{m:02d}:{s:02d}")
            else:
                pulangkan_alat(row['alat']); st.rerun()
                
            if c3.button("PULANG", key=f"btn_{row['alat']}"):
                pulangkan_alat(row['alat']); st.rerun()
            st.divider()
    time.sleep(5); st.rerun()

# 7. AKSES STAF
elif menu == "🔐 AKSES STAF":
    st.title("🔐 Panel Kawalan Admin")
    user = st.text_input("User Admin")
    pw = st.text_input("Password Admin", type="password")
    
    if user == STAFF_USER and pw == STAFF_PASS:
        st.success("Login Berjaya")
        t1, t2, t3 = st.tabs(["✅ PENGESAHAN (TICK)", "📜 HISTORY", "📊 DATABASE"])
        
        with t1:
            st.subheader("Senarai Menunggu Pengesahan")
            df = get_data()
            tunggu = df[df['status'] == "Menunggu Pengesahan"]
            if tunggu.empty: 
                st.info("Tiada permohonan pinjaman baru.")
            else:
                for _, row in tunggu.iterrows():
                    col1, col2, col3 = st.columns([2, 4, 1])
                    col1.write(f"**{row['alat']}**")
                    col2.write(f"Oleh: {row['peminjam']} ({row['kelas']})")
                    if col3.button("✔️", key=f"tick_{row['alat']}"):
                        sahkan_oleh_admin(row['alat'])
                        st.success(f"{row['alat']} telah disahkan!")
                        time.sleep(0.5); st.rerun()
                    st.divider()
        
        with t2:
            st.subheader("Rekod Sejarah Keseluruhan")
            st.dataframe(get_data("sejarah").sort_values(by='id', ascending=False), use_container_width=True, hide_index=True)
            
        with t3:
            st.subheader("Data Inventori Mentah")
            st.dataframe(get_data(), use_container_width=True, hide_index=True)
            
    elif user or pw: 
        st.error("Kredential Salah!")
