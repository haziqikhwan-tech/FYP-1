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

# ID & Password untuk Staf (Boleh tukar di sini)
STAFF_USER = "admin"
STAFF_PASS = "puo123"

# 2. FUNGSI DATABASE
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS alatan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alat TEXT UNIQUE,
                    status TEXT,
                    peminjam TEXT,
                    kelas TEXT,
                    tarikh TEXT,
                    masa_tamat TEXT
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
            c.execute("INSERT INTO alatan (alat, status, peminjam, kelas, tarikh, masa_tamat) VALUES (?, ?, ?, ?, ?, ?)",
                      (alat, "Tersedia", "-", "-", "-", "-"))
    conn.commit()
    conn.close()

def get_data_from_db():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM alatan", conn)
    conn.close()
    return df

def proses_update_db(alat_list, status, peminjam="-", kelas="-", tarikh="-", masa_tamat="-"):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    for alat in alat_list:
        c.execute('''UPDATE alatan SET status=?, peminjam=?, kelas=?, tarikh=?, masa_tamat=? 
                     WHERE alat=?''', (status, peminjam, kelas, tarikh, masa_tamat, alat))
    conn.commit()
    conn.close()

init_db()
df = get_data_from_db()

# 3. SIDEBAR
st.sidebar.header("MENU NAVIGASI")
menu = st.sidebar.selectbox("Pilih Halaman", ["🏠 UTAMA", "📝 BORANG PINJAMAN", "⏳ STATUS & TIMER"])

# 4. HALAMAN UTAMA
if menu == "🏠 UTAMA":
    st.title("🏗️ Sistem Pinjaman Alat Ukur PUO")
    tersedia = len(df[df['status'] == 'Tersedia'])
    dipinjam = len(df[df['status'] == 'Dipinjam'])
    
    col1, col2 = st.columns(2)
    col1.metric("Alat Tersedia", f"{tersedia}")
    col2.metric("Sedang Dipinjam", f"{dipinjam}")
    
    st.markdown("---")
    st.subheader("📁 Senarai Inventori & Status Semasa")
    st.dataframe(df, use_container_width=True, hide_index=True)

# 5. HALAMAN BORANG (KEMASKINI: STUDENT/STAF)
elif menu == "📝 BORANG PINJAMAN":
    st.title("📝 Borang Pinjaman Peralatan")
    
    # Pilihan Kategori
    kategori = st.radio("Sila Pilih Kategori Anda:", ["STUDENT", "STAF"], horizontal=True)
    
    senarai_tersedia = df[df['status'] == 'Tersedia']['alat'].tolist()
    
    if senarai_tersedia:
        with st.form("form_pinjam"):
            # Bahagian Login jika Staf
            if kategori == "STAF":
                st.warning("Akses Staf: Sila masukkan kredential")
                user_input = st.text_input("Username")
                pass_input = st.text_input("Password", type="password")
            
            # Maklumat Peminjam
            nama = st.text_input("Nama Penuh").upper()
            
            if kategori == "STUDENT":
                matrik = st.text_input("No. Matrik")
                identiti = st.text_input("Kelas (e.g. DGU5A)").upper()
            else:
                matrik = "STAF"
                identiti = st.text_input("Jabatan/Unit").upper()
            
            pilihan_alat = st.multiselect("Pilih Alat", senarai_tersedia)
            submit = st.form_submit_button("SAHKAN PINJAMAN")
            
            if submit:
                # Validasi Login Staf
                login_ok = True
                if kategori == "STAF":
                    if user_input != STAFF_USER or pass_input != STAFF_PASS:
                        st.error("Username atau Password Staf SALAH!")
                        login_ok = False
                
                # Validasi Maklumat Kosong
                if not nama or not identiti or not pilihan_alat:
                    st.error("Sila lengkapkan semua maklumat!")
                    login_ok = False
                
                if login_ok:
                    waktu_tamat = datetime.now() + timedelta(hours=LIMIT_JAM)
                    t_str = waktu_tamat.strftime("%Y-%m-%d %H:%M:%S")
                    d_str = date.today().strftime("%d/%m/%Y")
                    
                    proses_update_db(pilihan_alat, "Dipinjam", nama, identiti, d_str, t_str)
                    st.success(f"Pinjaman berjaya direkodkan sebagai {kategori}.")
                    st.balloons()
                    time.sleep(1)
                    st.rerun()
    else:
        st.error("Tiada alat tersedia.")

# 6. STATUS & TIMER
elif menu == "⏳ STATUS & TIMER":
    st.title("⏳ Pemantauan Baki Masa")
    waktu_sekarang = datetime.now()
    dipinjam_df = df[df['status'] == "Dipinjam"]
    
    if dipinjam_df.empty:
        st.write("Tiada alat sedang dipinjam.")
    else:
        for index, row in dipinjam_df.iterrows():
            col1, col2, col3 = st.columns([2, 3, 2])
            with col1:
                st.write(f"**{row['alat']}**")
                st.caption(f"👤 {row['peminjam']} ({row['kelas']})")
            with col2:
                t_tamat = datetime.strptime(row['masa_tamat'], "%Y-%m-%d %H:%M:%S")
                baki = t_tamat - waktu_sekarang
                if baki.total_seconds() > 0:
                    m, s = divmod(int(baki.total_seconds()), 60)
                    h, m = divmod(m, 60)
                    st.warning(f"⏱️ {h:d}j {m:02d}m {s:02d}s")
                else:
                    proses_update_db([row['alat']], "Tersedia")
                    st.rerun()
            with col3:
                st.button("PULANG", key=f"btn_{row['alat']}", on_click=proses_update_db, args=([row['alat']], "Tersedia"))
            st.divider()
    
    time.sleep(5)
    st.rerun()
