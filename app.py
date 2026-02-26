import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import io

# ==========================================
# 1. SETUP FOLDER "CLOUD" LOKAL
# ==========================================
MASTER_DIR = "master pendataan cukai rokok 2025"
RESULT_DIR = "hasil_input_user"

for d in[MASTER_DIR, RESULT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

st.set_page_config(page_title="Sistem Cukai 2025", layout="wide")

# ==========================================
# 2. HIDE STREAMLIT MENU & GITHUB ICON (KEAMANAN)
# ==========================================
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            /* Menyembunyikan Toolbar atas kanan termasuk logo GitHub */
            [data-testid="stToolbar"] {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# ==========================================
# 3. BACA DATA UNTUK DASHBOARD PROGRESS
# ==========================================
master_path = os.path.join(MASTER_DIR, "master_data.xlsx")
total_toko_master = 0
df_master = None

# Coba baca file master jika sudah ada
if os.path.exists(master_path):
    try:
        df_master = pd.read_excel(master_path)
        
        # Rapikan kolom agar standar
        col_names = list(df_master.columns.astype(str).str.strip().str.upper())
        for i, col in enumerate(col_names):
            if col == 'NAMA' and i > 2:  
                col_names[i] = 'NAMA TOKO'
            elif col == 'NAMA.1':
                col_names[i] = 'NAMA TOKO'
        df_master.columns = col_names
        
        # Bersihkan master dari baris kosong
        df_master = df_master.dropna(subset=['KODE TOKO'])
        df_master['KODE TOKO'] = df_master['KODE TOKO'].astype(str).str.strip().str.upper()
        df_master['NAMA TOKO'] = df_master['NAMA TOKO'].astype(str).str.strip()
        df_master = df_master[df_master['KODE TOKO'] != 'NAN']
        
        # Hitung Total Toko (Unik)
        total_toko_master = df_master['KODE TOKO'].nunique()
    except:
        pass

# Hitung Toko Sudah Input (Dari nama file hasil input)
all_files =[f for f in os.listdir(RESULT_DIR) if f.endswith('.csv')]
toko_sudah_input_list = set([f.split('_')[0] for f in all_files])
jumlah_sudah_input = len(toko_sudah_input_list)

# Hitung Belum Input
jumlah_belum_input = total_toko_master - jumlah_sudah_input
if jumlah_belum_input < 0: 
    jumlah_belum_input = 0

# ==========================================
# 4. TAMPILAN HOMEPAGE (DASHBOARD PROGRESS)
# ==========================================
st.title("📊 Progress Pendataan Sisa Cukai 2025")

# Menampilkan metrik dalam 3 kolom
col_prog1, col_prog2, col_prog3 = st.columns(3)
col_prog1.metric("Total Toko Pendataan", f"{total_toko_master} Toko")
col_prog2.metric("Toko Sudah Input", f"{jumlah_sudah_input} Toko")
col_prog3.metric("Toko Belum Input", f"{jumlah_belum_input} Toko")

st.divider()

# ==========================================
# 5. MENU UTAMA (DALAM SATU HALAMAN PAKAI TABS)
# ==========================================
# Ini menggantikan Sidebar, posisinya persis di bawah Dashboard Progress
tab1, tab2 = st.tabs(["📝 Form Input User", "🔒 Menu Admin"])

# ------------------------------------------
# TAB 1: FORM INPUT USER
# ------------------------------------------
with tab1:
    st.subheader("Form Pengisian Data")
    
    if st.session_state.get('show_success'):
        st.success(f"✅ Data berhasil disimpan! (Waktu Submit: {st.session_state['waktu_submit']})")
        st.session_state['show_success'] = False
        
    if df_master is None:
        st.warning("⚠️ File Master belum di-upload oleh Admin. Sistem belum bisa digunakan.")
    else:
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
            
            btn_simpan = st.button("💾 Simpan Pendataan", type="primary", use_container_width=True)
            
            if btn_simpan:
                if edited_df["QTY SISA CUKAI 2025"].isnull().any():
                    st.error("masih ada kolom yang belum diinput")
                else:
                    # FIX TIMESTAMP: Menggunakan Waktu Indonesia (UTC+8 / WITA)
                    waktu_indonesia = datetime.utcnow() + timedelta(hours=8)
                    timestamp_lengkap = waktu_indonesia.strftime("%Y-%m-%d %H:%M:%S")
                    
                    final_data = edited_df.copy()
                    final_data.insert(0, "KODE TOKO", st.session_state['toko_valid'])
                    final_data.insert(0, "JABATAN", st.session_state['jabatan'])
                    final_data.insert(0, "NIK", st.session_state['nik_user'])
                    final_data.insert(0, "NAMA KARYAWAN", st.session_state['nama_user'])
                    final_data.insert(4, "NAMA TOKO", st.session_state['nama_toko']) 
                    final_data["TIMESTAMP"] = timestamp_lengkap
                    
                    tanggal_hari_ini = waktu_indonesia.strftime("%Y-%m-%d")
                    file_name = f"{st.session_state['toko_valid']}_{tanggal_hari_ini}.csv"
                    file_path = os.path.join(RESULT_DIR, file_name)
                    
                    if os.path.exists(file_path):
                        final_data.to_csv(file_path, mode='a', header=False, index=False)
                    else:
                        final_data.to_csv(file_path, index=False)
                        
                    st.session_state['show_success'] = True
                    st.session_state['waktu_submit'] = timestamp_lengkap
                    del st.session_state['toko_valid'] 
                    st.rerun()

# ------------------------------------------
# TAB 2: MENU ADMIN
# ------------------------------------------
with tab2:
    st.subheader("Halaman Administrator")
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "icnbr034":
        st.success("Login Berhasil!")
        
        # 1. UPLOAD MASTER
        st.write("### 📁 1. Upload Master File")
        file_master = st.file_uploader("Upload File Master Excel Anda", type=["xlsx"])
        if file_master:
            master_path = os.path.join(MASTER_DIR, "master_data.xlsx")
            with open(master_path, "wb") as f:
                f.write(file_master.getbuffer())
            st.success("✅ File Master berhasil di-upload! Halaman akan memuat ulang...")
            st.rerun()
                
        st.divider()
        
        # 2. DOWNLOAD HASIL
        st.write("### 📥 2. Download Rekap Input User")
        if len(all_files) == 0:
            st.warning("Belum ada data yang disubmit oleh user.")
        else:
            if st.button("Download Semua Hasil (Jadikan 1 Excel)"):
                all_data =
