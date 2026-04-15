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

# 2. FUNGSI DATABASE
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Tambah kolom 'disahkan' (0 = Belum, 1 = Ya)
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

def get_data_from_db(table="alatan"):
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

def sahkan_alat(alat):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Set masa tamat bermula dari SEKARANG bila staf sahkan
    waktu_tamat = (datetime.now() + timedelta(hours=LIMIT_JAM)).strftime("%Y-%m-%d %H:%M:%S")
    c.execute("UPDATE alatan SET disahkan=1, masa_tamat=? WHERE alat=?", (waktu_tamat, alat))
    conn.commit()
    conn.close()
    rekod_sejarah(alat, "-", "-", "DISAHKAN OLEH STAF")

def proses_update_db(alat_list, status, peminjam="-", kelas="-", tarikh="-", masa_tamat="-", aksi=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for alat in alat_list:
        if aksi == "PULANG":
            c.execute("SELECT peminjam, kelas FROM alatan WHERE alat=?", (alat,))
            res = c.fetchone()
            rekod_sejarah(alat, res[0], res[1], "PULANG")
            c.execute("UPDATE alatan SET status=?, peminjam=?, kelas=?, tarikh=?, masa_tamat=?, disahkan=0 WHERE alat=?", 
                     (status, peminjam, kelas, tarikh, masa_tamat, alat))
        else:
            # Student pinjam: status tukar tapi disahkan=0 (tunggu staf)
            c.execute("UPDATE alatan SET status=?, peminjam=?, kelas=?, tarikh=?, masa_tamat=?, disahkan=0 WHERE alat=?", 
                     (status, peminjam, kelas, tarikh, masa_tamat, alat))
            if aksi == "PINJAM":
                rekod_sejarah(alat, peminjam, kelas, "PERMOHONAN PINJAM")
    conn.commit()
    conn.close()

init_db()
df = get_data_from_db()

# 3. SIDEBAR
st.sidebar.header("MENU NAVIGASI")
menu = st.sidebar.selectbox("Pilih Halaman", ["🏠 UTAMA", "📝 BORANG PINJAMAN", "⏳ STATUS & TIMER", "🔐 AKSES STAF"])

# 4. UTAMA
if menu == "🏠 UTAMA":
    st.title("🏗️ Sistem Pinjaman Alat Ukur PUO")
    st.dataframe(df, use_container_width=True, hide_index=True)

# 5. BORANG (STUDENT)
elif menu == "📝 BORANG PINJAMAN":
    st.title("📝 Borang Pinjaman Student")
    senarai_tersedia = df[df['status'] == 'Tersedia']['alat'].tolist()
    with st.form("form_pinjam", clear_on_submit=True):
        nama = st.text_input("Nama Penuh").upper()
        matrik = st.text_input("No. Matrik")
        kelas = st.text_input("Kelas").upper()
        pilihan = st.multiselect("Pilih Alat", senarai_tersedia)
        if st.form_submit_button("HANTAR PERMOHONAN"):
            if nama and matrik and kelas and pilihan:
                proses_update_db(pilihan, "Menunggu Pengesahan", nama, kelas, date.today().strftime("%d/%m/%Y"), "-", aksi="PINJAM")
                st.warning("Permohonan dihantar! Sila jumpa staf untuk pengesahan alat.")
                time.sleep(1); st.rerun()

# 6. STATUS (Hanya tunjuk yang dah DISAHKAN)
elif menu == "⏳ STATUS & TIMER":
    st.title("⏳ Pemantauan Baki Masa")
    waktu_sekarang = datetime.now()
    # Hanya tunjuk alat yang status dipinjam DAN sudah disahkan
    dipinjam_df = df[(df['status'] == "Dipinjam") | (df['disahkan'] == 1)]
    if dipinjam_df.empty:
        st.write("Tiada alat yang sedang digunakan.")
    else:
        for index, row in dipinjam_df.iterrows():
            if row['masa_tamat'] != "-":
                col1, col2, col3 = st.columns([2, 3, 2])
                with col1:
                    st.write(f"**{row['alat']}**")
                    st.caption(f"👤 {row['peminjam']}")
                with col2:
                    t_tamat = datetime.strptime(row['masa_tamat'], "%Y-%m-%d %H:%M:%S")
                    baki = t_tamat - waktu_sekarang
                    if baki.total_seconds() > 0:
                        m, s = divmod(int(baki.total_seconds()), 60); h, m = divmod(m, 60)
                        st.warning(f"⏱️ {h:d}j {m:02d}m {s:02d}s")
                    else:
                        proses_update_db([row['alat']], "Tersedia", aksi="PULANG"); st.rerun()
                with col3:
                    if st.button("PULANG", key=f"p_{row['alat']}"):
                        proses_update_db([row['alat']], "Tersedia", aksi="PULANG"); st.rerun()
                st.divider()
    time.sleep(5); st.rerun()

# 7. AKSES STAF (LOGIN UNTUK SAHKAN & HISTORY)
elif menu == "🔐 AKSES STAF":
    st.title("🔐 Panel Kawalan Staf")
    user_in = st.text_input("Username Admin")
    pass_in = st.text_input("Password Admin", type="password")
    
    if user_in == STAFF_USER and pass_in == STAFF_PASS:
        tab1, tab2, tab3 = st.tabs(["✅ PENGESAHAN ALAT", "📜 SEJARAH", "📁 DATABASE"])
        
        with tab1:
            st.subheader("Semakan Alat Keluar")
            # Cari alat yang statusnya Menunggu Pengesahan
            tunggu_df = df[df['status'] == "Menunggu Pengesahan"]
            if tunggu_df.empty:
                st.info("Tiada permohonan pinjaman baru.")
            else:
                for index, row in tunggu_df.iterrows():
                    c1, c2, c3 = st.columns([3, 3, 1])
                    c1.write(f"**{row['alat']}**")
                    c2.write(f"Peminjam: {row['peminjam']} ({row['kelas']})")
                    if c3.button("✔️", key=f"ok_{row['alat']}"):
                        # Bila staf tekan, status jadi 'Dipinjam' dan timer mula
                        proses_update_db([row['alat']], "Dipinjam")
                        sahkan_alat(row['alat'])
                        st.success(f"{row['alat']} Disahkan!")
                        time.sleep(0.5); st.rerun()
                    st.divider()

        with tab2:
            st.dataframe(get_data_from_db("sejarah").sort_values(by='id', ascending=False), use_container_width=True, hide_index=True)
        
        with tab3:
            st.dataframe(df, use_container_width=True)
            with open(DB_FILE, "rb") as f:
                st.download_button("📥 Backup DB", f, file_name="survey_puo.db")
    elif user_in or pass_in:
        st.error("Salah password!")
