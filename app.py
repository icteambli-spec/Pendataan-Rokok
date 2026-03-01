import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz
import json
import gspread
from google.oauth2.service_account import Credentials
import io

# ==========================================
# 1. SETUP CLOUD LOKAL (Hanya untuk Master Data)
# ==========================================
MASTER_DIR = "master pendataan cukai rokok 2025"
if not os.path.exists(MASTER_DIR):
    os.makedirs(MASTER_DIR)

st.set_page_config(page_title="Pendataan Cukai 2025", layout="wide")

# ==========================================
# 2. HIDE HEADER & GITHUB LOGO
# ==========================================
hide_st_style = """
            <style>
            header {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 3. KONEKSI KE GOOGLE SHEETS
# ==========================================
# Ganti tulisan di bawah dengan LINK Google Sheets Anda
LINK_GSHEETS = "https://docs.google.com/spreadsheets/d/1Bhy2fR3sX79G1BJZcQDwbLKdB4oLvkdAE6kpi4R021s/edit?gid=0#gid=0" 

@st.cache_resource
def init_connection():
    try:
        creds_json = json.loads(st.secrets["google_credentials"])
        scopes =[
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_json, scopes=scopes)
        client = gspread.authorize(creds)
        
        # PERUBAHANNYA ADA DI SINI: Kita gunakan open_by_url
        return client.open_by_url(LINK_GSHEETS).sheet1
        
    except Exception as e:
        st.error(f"❌ Gagal terhubung ke Google Sheets. Detail: {e}")
        st.stop()

# ==========================================
# 4. BACA DATA (MASTER EXCEL & GOOGLE SHEETS)
# ==========================================
master_path = os.path.join(MASTER_DIR, "master_data.xlsx")
df_master = pd.DataFrame()
total_toko_master = 0
list_kode_toko_master =[]

# Baca Master Excel (Acuan Admin)
if os.path.exists(master_path):
    try:
        df_master = pd.read_excel(master_path)
        col_names = list(df_master.columns.astype(str).str.strip().str.upper())
        for i, col in enumerate(col_names):
            if col == 'NAMA' and i > 2:
                col_names[i] = 'NAMA TOKO'
            elif col == 'NAMA.1':
                col_names[i] = 'NAMA TOKO'
        df_master.columns = col_names
        df_master = df_master.dropna(subset=['KODE TOKO'])
        df_master['KODE TOKO'] = df_master['KODE TOKO'].astype(str).str.strip().str.upper()
        df_master['NAMA TOKO'] = df_master['NAMA TOKO'].astype(str).str.strip()
        df_master = df_master[df_master['KODE TOKO'] != 'NAN']
        list_kode_toko_master = df_master['KODE TOKO'].unique().tolist()
        total_toko_master = len(list_kode_toko_master)
    except Exception as e:
        st.error(f"Gagal membaca master data: {e}")

# Hitung Progress dari Google Sheets
jumlah_sudah_input = 0
all_values =[]
try:
    all_values = sheet.get_all_values()
    if len(all_values) > 1: # Ada data selain Header
        df_gsheets = pd.DataFrame(all_values[1:], columns=all_values[0])
        if 'KODE TOKO' in df_gsheets.columns:
            toko_sudah_input = set(df_gsheets['KODE TOKO'].astype(str).unique())
            jumlah_sudah_input = len(toko_sudah_input)
except Exception as e:
    pass 

jumlah_belum_input = total_toko_master - jumlah_sudah_input
if jumlah_belum_input < 0: jumlah_belum_input = 0

# ==========================================
# 5. TAMPILAN DASHBOARD PROGRESS
# ==========================================
st.title("📊 Dashboard Pendataan Cukai Rokok 2025")
col_prog1, col_prog2, col_prog3 = st.columns(3)
with col_prog1:
    st.metric(label="🏢 Total Toko Pendataan", value=f"{total_toko_master} Toko")
with col_prog2:
    st.metric(label="✅ Toko Sudah Input", value=f"{jumlah_sudah_input} Toko")
with col_prog3:
    st.metric(label="⏳ Toko Belum Input", value=f"{jumlah_belum_input} Toko")

st.divider()

# ==========================================
# 6. MENU TABS
# ==========================================
tab_input, tab_admin = st.tabs(["📝 Form Input User", "🔒 Menu Admin"])

# ------------------------------------------
# TAB 1: FORM INPUT USER
# ------------------------------------------
with tab_input:
    if df_master.empty:
        st.warning("⚠️ File Master belum di-upload oleh Admin. Sistem belum bisa digunakan.")
    else:
        if st.session_state.get('show_success'):
            st.success(f"✅ Data berhasil dikirim ke Google Sheets! (Waktu Submit: {st.session_state['waktu_submit']})")
            st.session_state['show_success'] = False
            
        st.write("### 1. Identitas Penginput")
        col1, col2, col3 = st.columns(3)
        with col1:
            nama_user = st.text_input("NAMA KARYAWAN")
        with col2:
            nik_user = st.text_input("NIK", max_chars=10)
        with col3:
            jabatan = st.selectbox("JABATAN",["", "COS", "SSL", "SJL", "SCG", "SCB"])
            
        st.write("### 2. Pencarian Toko")
        col_toko, col_btn = st.columns([3, 1])
        with col_toko:
            kode_toko = st.text_input("KODE TOKO").upper().strip()
        with col_btn:
            st.write("") 
            st.write("") 
            btn_cari = st.button("🔍 Cari Toko", use_container_width=True)
            
        if btn_cari:
            if not nama_user or not nik_user or jabatan == "" or not kode_toko:
                st.error("ada data yang masih kosong atau belum diisi")
            elif len(nik_user) != 10 or not nik_user.isdigit():
                st.error("ada data yang masih kosong atau belum diisi (Periksa NIK: Wajib 10 digit angka)")
            else:
                df_subset = df_master[df_master['KODE TOKO'] == kode_toko]
                if df_subset.empty:
                    st.error("❌ Kode Toko tidak ditemukan di Master Data!")
                    if 'toko_valid' in st.session_state:
                        del st.session_state['toko_valid']
                else:
                    st.session_state['toko_valid'] = kode_toko
                    st.session_state['nama_user'] = nama_user
                    st.session_state['nik_user'] = nik_user
                    st.session_state['jabatan'] = jabatan
                    st.session_state['nama_toko'] = df_subset.iloc[0]['NAMA TOKO']
                    st.session_state['produk_toko'] = df_subset[['PLU', 'DESC']].dropna().to_dict('records')

        if st.session_state.get('toko_valid'):
            st.divider()
            st.info(f"📍 **NAMA TOKO:** {st.session_state['nama_toko']}")
            st.write("💡 **jika tidak ada fisik input nol (0)**")
            
            df_input = pd.DataFrame(st.session_state['produk_toko'])
            df_input["QTY SISA CUKAI 2025"] = None 
            
            edited_df = st.data_editor(
                df_input,
                disabled=["PLU", "DESC"],
                hide_index=True,
                use_container_width=True,
                column_config={
                    "QTY SISA CUKAI 2025": st.column_config.NumberColumn(
                        "QTY SISA CUKAI 2025",
                        help="Hanya bisa diisi angka",
                        min_value=0,
                        step=1
                    )
                }
            )
            
            btn_simpan = st.button("💾 Simpan ke Google Sheets", type="primary", use_container_width=True)
            
            if btn_simpan:
                if edited_df["QTY SISA CUKAI 2025"].isnull().any():
                    st.error("masih ada kolom yang belum diinput")
                else:
                    tz_indonesia = pytz.timezone('Asia/Makassar')
                    timestamp_lengkap = datetime.now(tz_indonesia).strftime("%Y-%m-%d %H:%M:%S")
                    
                    final_data = edited_df.copy()
                    final_data.insert(0, "KODE TOKO", st.session_state['toko_valid'])
                    final_data.insert(0, "JABATAN", st.session_state['jabatan'])
                    final_data.insert(0, "NIK", st.session_state['nik_user'])
                    final_data.insert(0, "NAMA KARYAWAN", st.session_state['nama_user'])
                    final_data.insert(4, "NAMA TOKO", st.session_state['nama_toko']) 
                    final_data["TIMESTAMP"] = timestamp_lengkap
                    
                    final_data = final_data.fillna("")
                    
                    if len(all_values) == 0:
                        sheet.append_row(final_data.columns.tolist())
                    
                    sheet.append_rows(final_data.values.tolist())
                        
                    st.session_state['show_success'] = True
                    st.session_state['waktu_submit'] = timestamp_lengkap
                    del st.session_state['toko_valid']
                    st.rerun()

# ------------------------------------------
# TAB 2: MENU ADMIN
# ------------------------------------------
with tab_admin:
    st.write("### 🔒 Halaman Administrator")
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "icnbr034":
        st.success("Login Berhasil!")
        
        # 1. Upload Master (Acuan)
        st.subheader("📁 1. Upload Master File")
        file_master = st.file_uploader("Upload File Master Excel Anda", type=["xlsx"])
        if file_master:
            with open(os.path.join(MASTER_DIR, "master_data.xlsx"), "wb") as f:
                f.write(file_master.getbuffer())
            st.success("✅ File Master berhasil di-upload! Halaman akan dimuat ulang.")
            st.rerun()
                
        st.divider()
        
        # 2. Download Hasil Excel (Gabungan Sudah & Belum Input)
        st.subheader("📥 2. Download Rekap Keseluruhan")
        
        if df_master.empty:
            st.warning("⚠️ File Master belum di-upload. Sistem tidak bisa mengetahui daftar seluruh toko.")
        else:
            st.info("Laporan ini akan menggabungkan data toko yang **Sudah Input** (dari Google Sheets) dan **Belum Input** (dari File Master).")
            
            if st.button("Download Rekap Lengkap (Excel)", type="primary"):
                # A. Siapkan data yang SUDAH input
                if len(all_values) > 1:
                    df_sudah = pd.DataFrame(all_values[1:], columns=all_values[0])
                    list_toko_sudah = df_sudah['KODE TOKO'].astype(str).unique().tolist()
                else:
                    df_sudah = pd.DataFrame()
                    list_toko_sudah =[]
                
                # B. Siapkan data yang BELUM input dari Master Data
                df_belum = df_master[~df_master['KODE TOKO'].isin(list_toko_sudah)].copy()
                if not df_belum.empty:
                    df_belum['NAMA KARYAWAN'] = "-"
                    df_belum['NIK'] = "-"
                    df_belum['JABATAN'] = "-"
                    df_belum['QTY SISA CUKAI 2025'] = "" # Kosongkan QTY agar mudah ditotal
                    df_belum['TIMESTAMP'] = "BELUM INPUT"
                
                # C. Gabungkan Keduanya
                if not df_sudah.empty:
                    df_final = pd.concat([df_sudah, df_belum], ignore_index=True)
                else:
                    df_final = df_belum
                
                # D. Rapikan Susunan Kolom
                kolom_rapi =["KODE TOKO", "NAMA TOKO", "NAMA KARYAWAN", "NIK", "JABATAN", "PLU", "DESC", "QTY SISA CUKAI 2025", "TIMESTAMP"]
                for col in kolom_rapi:
                    if col not in df_final.columns:
                        df_final[col] = ""
                
                # Posisikan kolom utama di depan, sisanya (jika ada) di belakang
                kolom_tambahan =[c for c in df_final.columns if c not in kolom_rapi]
                df_final = df_final[kolom_rapi + kolom_tambahan]
                
                # E. Ekspor ke Excel File
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_final.to_excel(writer, index=False, sheet_name='Rekap_Pendataan')
                
                tz_indonesia = pytz.timezone('Asia/Makassar')
                waktu_sekarang = datetime.now(tz_indonesia).strftime('%d%m%Y_%H%M')
                
                st.download_button(
                    label="📥 KLIK UNTUK DOWNLOAD EXCEL LENGKAP",
                    data=output.getvalue(),
                    file_name=f"Rekap_Cukai_Lengkap_{waktu_sekarang}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
        st.divider()
        
        # 3. Fitur Hapus Semua Data (Reset)
        st.subheader("⚠️ 3. Zona Bahaya: Reset Data")
        st.error("PERHATIAN: Pastikan Anda sudah Mendownload Excel di atas sebelum melakukan ini. Menekan tombol hapus akan mengosongkan file Google Sheets Anda!")
        
        konfirmasi = st.text_input("Ketik kata 'KONFIRMASI' untuk membuka tombol hapus:")
        if konfirmasi == "KONFIRMASI":
            if st.button("🗑️ Hapus Semua Data di Google Sheets"):
                try:
                    sheet.clear() 
                    st.success("✅ Seluruh data di Google Sheets berhasil dibersihkan! Halaman akan dimuat ulang.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Terjadi kesalahan saat menghapus data: {e}")

    elif password != "":
        st.error("❌ Password Salah!")
