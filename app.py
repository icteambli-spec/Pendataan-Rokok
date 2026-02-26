import streamlit as st
import pandas as pd
import os
from datetime import datetime
import pytz
import io

# ==========================================
# 1. SETUP FOLDER "CLOUD" LOKAL
# ==========================================
MASTER_DIR = "master pendataan cukai rokok 2025"
RESULT_DIR = "hasil_input_user"

for d in [MASTER_DIR, RESULT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Konfigurasi Halaman
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
# 3. BACA DATA MASTER
# ==========================================
master_path = os.path.join(MASTER_DIR, "master_data.xlsx")
df_master = pd.DataFrame()
total_toko_master = 0

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
        
        total_toko_master = len(df_master['KODE TOKO'].unique())
    except Exception as e:
        st.error(f"Gagal membaca master data: {e}")

# Hitung Progress
all_files = [f for f in os.listdir(RESULT_DIR) if f.endswith('.csv')]
toko_sudah_input = set([f.split('_')[0] for f in all_files])
jumlah_sudah_input = len(toko_sudah_input)
jumlah_belum_input = max(0, total_toko_master - jumlah_sudah_input)

# ==========================================
# 4. DASHBOARD
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
# 5. MENU TABS
# ==========================================
tab_input, tab_admin = st.tabs(["📝 Form Input User", "🔒 Menu Admin"])

with tab_input:
    if df_master.empty:
        st.warning("⚠️ File Master belum di-upload oleh Admin.")
    else:
        if st.session_state.get('show_success'):
            st.success(f"✅ Data berhasil disimpan! (Waktu: {st.session_state['waktu_submit']})")
            st.session_state['show_success'] = False
            
        st.write("### 1. Identitas Penginput")
        c1, c2, c3 = st.columns(3)
        nama_user = c1.text_input("NAMA KARYAWAN")
        nik_user = c2.text_input("NIK", max_chars=10)
        jabatan = c3.selectbox("JABATAN", ["", "COS", "SSL", "SJL", "SCG", "SCB"])
            
        st.write("### 2. Pencarian Toko")
        col_toko, col_btn = st.columns([3, 1])
        kode_toko = col_toko.text_input("KODE TOKO").upper().strip()
        btn_cari = col_btn.button("🔍 Cari Toko", use_container_width=True)
            
        if btn_cari:
            if not nama_user or not nik_user or jabatan == "" or not kode_toko:
                st.error("Ada data yang masih kosong")
            elif len(nik_user) != 10 or not nik_user.isdigit():
                st.error("NIK Wajib 10 digit angka")
            else:
                df_subset = df_master[df_master['KODE TOKO'] == kode_toko]
                if df_subset.empty:
                    st.error("❌ Kode Toko tidak ditemukan!")
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
            df_input = pd.DataFrame(st.session_state['produk_toko'])
            df_input["QTY SISA CUKAI 2025"] = None 
            
            edited_df = st.data_editor(
                df_input,
                disabled=["PLU", "DESC"],
                hide_index=True,
                use_container_width=True,
                column_config={"QTY SISA CUKAI 2025": st.column_config.NumberColumn(min_value=0, step=1)}
            )
            
            if st.button("💾 Simpan Pendataan", type="primary", use_container_width=True):
                if edited_df["QTY SISA CUKAI 2025"].isnull().any():
                    st.error("Masih ada kolom yang kosong")
                else:
                    tz_indo = pytz.timezone('Asia/Makassar')
                    waktu_skrg = datetime.now(tz_indo)
                    
                    final_data = edited_df.copy()
                    final_data.insert(0, "KODE TOKO", st.session_state['toko_valid'])
                    final_data.insert(0, "JABATAN", st.session_state['jabatan'])
                    final_data.insert(0, "NIK", st.session_state['nik_user'])
                    final_data.insert(0, "NAMA KARYAWAN", st.session_state['nama_user'])
                    final_data.insert(4, "NAMA TOKO", st.session_state['nama_toko']) 
                    final_data["TIMESTAMP"] = waktu_skrg.strftime("%Y-%m-%d %H:%M:%S")
                    
                    f_name = f"{st.session_state['toko_valid']}_{waktu_skrg.strftime('%Y%m%d')}.csv"
                    final_data.to_csv(os.path.join(RESULT_DIR, f_name), index=False)
                        
                    st.session_state['show_success'] = True
                    st.session_state['waktu_submit'] = waktu_skrg.strftime("%H:%M:%S")
                    del st.session_state['toko_valid']
                    st.rerun()

with tab_admin:
    st.write("### 🔒 Halaman Administrator")
    pwd = st.text_input("Masukkan Password Admin:", type="password")
    
    if pwd == "icnbr034":
        st.success("Login Berhasil!")
        
        # 1. Upload Master
        st.subheader("📁 1. Upload Master File")
        file_m = st.file_uploader("Upload File Master Excel", type=["xlsx"])
        if file_m:
            with open(os.path.join(MASTER_DIR, "master_data.xlsx"), "wb") as f:
                f.write(file_m.getbuffer())
            st.success("Master berhasil di-upload!")
            st.rerun()
                
        st.divider()
        
        # 2. Download Hasil (Mapping ke Kolom A, B, C secara eksklusif)
        st.subheader("📥 2. Download Rekap Seluruh Toko")
        if st.button("🚀 Generate Rekap (Semua Toko Master)"):
            if df_master.empty:
                st.error("Master data tidak ditemukan.")
            else:
                # Baca semua file hasil input user
                list_df_hasil = []
                for f in all_files:
                    try:
                        list_df_hasil.append(pd.read_csv(os.path.join(RESULT_DIR, f)))
                    except: pass
                
                # Gunakan salinan struktur master asli
                df_final_rekap = df_master.copy()
                
                if list_df_hasil:
                    df_semua_input = pd.concat(list_df_hasil, ignore_index=True)
                    # Sortir untuk mengambil input paling baru berdasarkan PLU dan Kode Toko
                    df_semua_input = df_semua_input.sort_values("TIMESTAMP").drop_duplicates(subset=['KODE TOKO', 'PLU'], keep='last')
                    
                    # Gabungkan data input ke template master
                    df_final_rekap = df_final_rekap.merge(
                        df_semua_input[['KODE TOKO', 'PLU', 'NAMA KARYAWAN', 'NIK', 'JABATAN', 'QTY SISA CUKAI 2025', 'TIMESTAMP']], 
                        on=['KODE TOKO', 'PLU'], 
                        how='left',
                        suffixes=('', '_temp')
                    )
                    
                    # MAPPING DATA KE KOLOM ASLI MASTER
                    # Kolom A (NAMA) diisi dari data Nama Karyawan yang menginput
                    df_final_rekap['NAMA'] = df_final_rekap['NAMA KARYAWAN_temp']
                    # Kolom B (NIK)
                    df_final_rekap['NIK'] = df_final_rekap['NIK_temp']
                    # Kolom C (JABATAN)
                    df_final_rekap['JABATAN'] = df_final_rekap['JABATAN_temp']
                    # Kolom H (QTY SISA CUKAI 2025)
                    df_final_rekap['QTY SISA CUKAI 2025'] = df_final_rekap['QTY SISA CUKAI 2025_temp']
                    # Kolom K (TIMESTAMP) tetap di paling kanan sesuai urutan master
                    df_final_rekap['TIMESTAMP'] = df_final_rekap['TIMESTAMP_temp']

                    # HAPUS SEMUA KOLOM SEMENTARA HASIL MERGE
                    # Ini memastikan tidak ada kolom "NAMA KARYAWAN" tambahan di sebelah kanan
                    kolom_temp = [c for c in df_final_rekap.columns if '_temp' in c]
                    df_final_rekap.drop(columns=kolom_temp, inplace=True)
                    
                    # Pastikan kolom "NAMA KARYAWAN" hasil join yang tidak sengaja terbawa juga dibuang
                    if 'NAMA KARYAWAN' in df_final_rekap.columns:
                        df_final_rekap.drop(columns=['NAMA KARYAWAN'], inplace=True)

                # Proses Download ke Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_final_rekap.to_excel(writer, index=False, sheet_name='REKAP_CUKAI_2025')
                
                st.download_button(
                    label="📥 Klik Download Hasil Rekap",
                    data=output.getvalue(),
                    file_name=f"HASIL_PENDATAAN_CUKAI_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

