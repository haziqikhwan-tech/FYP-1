import streamlit as st
import pandas as pd
import sqlite3
import os
import time
from datetime import date, datetime, timedelta

# Konfigurasi Page
st.set_page_config(page_title="Sistem Pinjaman Alat Ukur PUO", layout="centered")

DB_FILE = "sistem_pinjaman.db"
LIMIT_JAM = 3 

# --- FUNGSI DATABASE (SQLITE) ---
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    # Cipta table kalau belum ada
    c.execute('''CREATE TABLE IF NOT EXISTS alatan (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alat TEXT UNIQUE,
                    status TEXT,
                    peminjam TEXT,
                    kelas TEXT,
                    tarikh TEXT,
                    masa_tamat TEXT
                )''')
    
    # Masukkan senarai alat master kalau table masih kosong
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

# --- UI SISTEM ---
init_db()
df = get_data_from_db()

st.title("🏗️ Sistem Pinjaman PUO (.db Mode)")
st.markdown("---")

menu = st.sidebar.selectbox("MENU NAVIGASI", ["UTAMA", "BORANG PINJAMAN", "STATUS & TIMER"])

if menu == "UTAMA":
    st.subheader("Selamat Datang!")
    tersedia = len(df[df['status'] == 'Tersedia'])
    st.metric(label="Alat Tersedia", value=f"{tersedia} Alat")

elif menu == "BORANG PINJAMAN":
    st.subheader("📝 Borang Pinjaman Multi-Alat")
    senarai_tersedia = df[df['status'] == 'Tersedia']['alat'].tolist()
    
    if senarai_tersedia:
        with st.form("borang_pinjam"):
            nama = st.text_input("Nama Penuh").upper()
            matrik = st.text_input("No. Matrik")
            kelas = st.text_input("Kelas").upper()
            pilihan_alat = st.multiselect("Pilih Alat", senarai_tersedia)
            submit = st.form_submit_button("SAHKAN PINJAMAN")
            
            if submit:
                if nama and matrik and kelas and pilihan_alat:
                    waktu_tamat = datetime.now() + timedelta(hours=LIMIT_JAM)
                    t_str = waktu_tamat.strftime("%Y-%m-%d %H:%M:%S")
                    d_str = date.today().strftime("%d/%m/%Y")
                    
                    proses_update_db(pilihan_alat, "Dipinjam", nama, kelas, d_str, t_str)
                    st.success("Pinjaman Berjaya!")
                    st.rerun()
    else:
        st.error("Tiada alat tersedia.")

elif menu == "STATUS & TIMER":
    st.subheader("⏳ Status & Baki Masa")
    waktu_sekarang = datetime.now()
    dipinjam_df = df[df['status'] == "Dipinjam"]
    
    if dipinjam_df.empty:
        st.write("Tiada alat yang sedang dipinjam.")
    else:
        for index, row in dipinjam_df.iterrows():
            col1, col2, col3 = st.columns([2, 3, 2])
            with col1:
                st.write(f"**{row['alat']}**")
                st.caption(f"Peminjam: {row['peminjam']}")
            with col2:
                t_tamat = datetime.strptime(row['masa_tamat'], "%Y-%m-%d %H:%M:%S")
                baki_masa = t_tamat - waktu_sekarang
                if baki_masa.total_seconds() > 0:
                    m, s = divmod(int(baki_masa.total_seconds()), 60)
                    h, m = divmod(m, 60)
                    st.warning(f"{h:d}j {m:02d}m {s:02d}s")
                else:
                    proses_update_db([row['alat']], "Tersedia")
                    st.rerun()
            with col3:
                if st.button("RETURN", key=f"btn_{row['alat']}"):
                    proses_update_db([row['alat']], "Tersedia")
                    st.rerun()
            st.divider()

    # Tengok data mentah database .db
    if st.checkbox("Tunjuk Data Penuh Database"):
        st.dataframe(df)

    time.sleep(2)
    st.rerun()
