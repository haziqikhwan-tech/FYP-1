import streamlit as st
import pandas as pd
import os
import time
from datetime import date, datetime, timedelta

# Konfigurasi Page
st.set_page_config(page_title="Sistem Pinjaman Alat Ukur PUO", layout="centered")

DB_FILE = "status_alatan.csv"
LIMIT_JAM = 3 

ALATAN_MASTER = [
    "TS141", "TS741", "TS140", "TS WAKAF", "PRISM 1", "PRISM 2", "PRISM 3", "PRISM 4", 
    "PRISM 5", "PRISM 6", "PRISM 7", "PRISM 8", "TRIPOD 100", "TRIPOD 84", "TRIPOD 24", 
    "TRIPOD 60", "TRIPOD 67", "TRIPOD 97", "TRIPOD 10", "TRIPOD 38", "TRIPOD 27", 
    "SUN FILTER 1", "SUN FILTER 2", "SUN FILTER 3", "SUN FILTER 4", "STAFF 1", "STAFF 2", "STAFF 3"
]

def init_database():
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame({
            "Alat": ALATAN_MASTER, 
            "Status": "Tersedia", 
            "Peminjam": "-", 
            "Kelas": "-", 
            "Tarikh": "-",
            "Masa_Tamat": "-" 
        })
        df.to_csv(DB_FILE, index=False)

def get_data():
    return pd.read_csv(DB_FILE)

def save_data(df):
    df.to_csv(DB_FILE, index=False)

# FUNGSI BARU: Proses Pemulangan
def proses_pulang(nama_alat):
    data_sekarang = get_data()
    data_sekarang.loc[data_sekarang['Alat'] == nama_alat, ['Status', 'Peminjam', 'Kelas', 'Tarikh', 'Masa_Tamat']] = \
        ['Tersedia', '-', '-', '-', '-']
    save_data(data_sekarang)
    st.toast(f"Alat {nama_alat} telah dipulangkan!")

init_database()
df = get_data()

st.title("🏗️ Sistem Pinjaman Alat Ukur PUO")
st.markdown("---")

menu = st.sidebar.selectbox("MENU NAVIGASI", ["UTAMA", "BORANG PINJAMAN", "STATUS & TIMER"])

if menu == "UTAMA":
    st.subheader("Selamat Datang!")
    tersedia = len(df[df['Status'] == 'Tersedia'])
    st.metric(label="Alat Tersedia", value=f"{tersedia} Alat")

elif menu == "BORANG PINJAMAN":
    st.subheader("📝 Borang Pinjaman Multi-Alat")
    senarai_tersedia = df[df['Status'] == 'Tersedia']['Alat'].tolist()
    
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
                    for alat in pilihan_alat:
                        df.loc[df['Alat'] == alat, ['Status', 'Peminjam', 'Kelas', 'Tarikh', 'Masa_Tamat']] = \
                            ['Dipinjam', nama, kelas, date.today().strftime("%d/%m/%Y"), waktu_tamat.strftime("%Y-%m-%d %H:%M:%S")]
                    save_data(df)
                    st.success("Pinjaman Berjaya!")
                    st.rerun()
    else:
        st.error("Tiada alat tersedia.")

elif menu == "STATUS & TIMER":
    st.subheader("⏳ Status & Baki Masa")
    waktu_sekarang = datetime.now()
    
    # Kita buat list alat yang dipinjam sahaja
    dipinjam_df = df[df['Status'] == "Dipinjam"]
    
    if dipinjam_df.empty:
        st.write("Tiada alat yang sedang dipinjam.")
    else:
        for index, row in dipinjam_df.iterrows():
            col1, col2, col3 = st.columns([2, 3, 2])
            
            with col1:
                st.write(f"**{row['Alat']}**")
                st.caption(f"Peminjam: {row['Peminjam']}")
            
            with col2:
                t_tamat = datetime.strptime(row['Masa_Tamat'], "%Y-%m-%d %H:%M:%S")
                baki_masa = t_tamat - waktu_sekarang
                
                if baki_masa.total_seconds() > 0:
                    m, s = divmod(int(baki_masa.total_seconds()), 60)
                    h, m = divmod(m, 60)
                    st.warning(f"{h:d}j {m:02d}m {s:02d}s")
                else:
                    # Auto return
                    proses_pulang(row['Alat'])
                    st.rerun()
            
            with col3:
                # Guna on_click supaya aksi lebih 'pantas' dari rerun
                st.button("RETURN", key=f"btn_{row['Alat']}", on_click=proses_pulang, args=(row['Alat'],))
            
            st.divider()

    # Refresh timer setiap 2 saat (kurangkan beban CPU)
    time.sleep(2)
    st.rerun()