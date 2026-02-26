import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# ==========================================
# 1. SETUP FOLDER "CLOUD" LOKAL
# ==========================================
MASTER_DIR = "master pendataan cukai rokok 2025"
RESULT_DIR = "hasil_input_user"

for d in [MASTER_DIR, RESULT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

st.set_page_config(page_title="Sistem Cukai 2025", layout="wide")

# ==========================================
# 2. MENU NAVIGASI
# ==========================================
st.sidebar.title("Navigasi")
menu = st.sidebar.radio("Pilih Akses:", ["📝 Form Input User", "🔒 Menu Admin"])

# ==========================================
# 3. MENU ADMIN
# ==========================================
if menu == "🔒 Menu Admin":
    st.title("🔒 Halaman Administrator")
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "icnbr034":
        st.success("Login Berhasil!")
        st.divider()
        
        # Upload Master
        st.subheader("📁 1. Upload Master File (Acuan)")
        file_master = st.file_uploader("Upload File Master Excel Anda", type=["xlsx"])
        
        if file_master:
            master_path = os.path.join(MASTER_DIR, "master_data.xlsx")
            with open(master_path, "wb") as f:
                f.write(file_master.getbuffer())
            
            try:
                df_preview = pd.read_excel(master_path)
                st.success("✅ File Master berhasil di-upload dan terbaca oleh sistem!")
                st.write("Preview Data Master:")
                st.dataframe(df_preview.head(), use_container_width=True)
            except Exception as e:
                st.error(f"❌ Gagal membaca file: {e}")
                
        st.divider()
        
        # Download Hasil
        st.subheader("📥 2. Download Rekap Input User")
        all_files =[f for f in os.listdir(RESULT_DIR) if f.endswith('.csv')]
        
        if len(all_files) == 0:
            st.warning("Belum ada data yang disubmit oleh user.")
        else:
            if st.button("Download Semua Hasil (Jadikan 1 Excel)"):
                all_data =[]
                for file in all_files:
                    try:
                        df_temp = pd.read_csv(os.path.join(RESULT_DIR, file))
                        all_data.append(df_temp)
                    except:
                        continue
                    
                if all_data:
                    df_final = pd.concat(all_data, ignore_index=True)
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_final.to_excel(writer, index=False, sheet_name='Rekap_Hasil')
                    
                    st.download_button(
                        label="📥 KLIK UNTUK DOWNLOAD REKAP",
                        data=output.getvalue(),
                        file_name=f"Rekap_Sisa_Cukai_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )

    elif password != "":
        st.error("❌ Password Salah!")

# ==========================================
# 4. MENU USER (FORM INPUT UTAMA)
# ==========================================
elif menu == "📝 Form Input User":
    st.title("📋 Pendataan QTY Sisa Cukai 2025")
    
    # --- PESAN SUKSES JIKA BARU SAJA SUBMIT ---
    if st.session_state.get('show_success'):
        st.success(f"✅ Data berhasil disimpan! (Waktu Submit: {st.session_state['waktu_submit']})")
        st.session_state['show_success'] = False # Reset agar tidak muncul terus
    
    master_path = os.path.join(MASTER_DIR, "master_data.xlsx")
    
    if not os.path.exists(master_path):
        st.warning("⚠️ File Master belum di-upload. Sistem belum bisa digunakan.")
    else:
        try:
            # BACA MASTER DATA
            df_master = pd.read_excel(master_path)
            
            # Rapikan Kolom & Deteksi 2 kolom "NAMA" seperti format Excel Anda
            col_names = list(df_master.columns.astype(str).str.strip().str.upper())
            for i, col in enumerate(col_names):
                if col == 'NAMA' and i > 2:  # Mengubah kolom NAMA(Toko) ke-2 jadi NAMA TOKO
                    col_names[i] = 'NAMA TOKO'
                elif col == 'NAMA.1':
                    col_names[i] = 'NAMA TOKO'
            df_master.columns = col_names
            
            # Buang baris kosong yang tidak punya KODE TOKO
            df_master = df_master.dropna(subset=['KODE TOKO'])
            df_master['KODE TOKO'] = df_master['KODE TOKO'].astype(str).str.strip().str.upper()
            df_master['NAMA TOKO'] = df_master['NAMA TOKO'].astype(str).str.strip()
            df_master = df_master[df_master['KODE TOKO'] != 'NAN']

        except Exception as e:
            st.error(f"❌ Terjadi kesalahan membaca File Master: {e}")
            st.stop()
            
        # ==========================================
        # TAHAP 1: FORM DATA DIRI
        # ==========================================
        st.write("### 1. Identitas Penginput")
        col1, col2, col3 = st.columns(3)
        with col1:
            nama_user = st.text_input("NAMA KARYAWAN")
        with col2:
            nik_user = st.text_input("NIK", max_chars=10)
        with col3:
            jabatan = st.selectbox("JABATAN",["", "COS", "SSL", "SJL", "SCG", "SCB"])
            
        # ==========================================
        # TAHAP 2: PENCARIAN KODE TOKO
        # ==========================================
        st.write("### 2. Pencarian Toko")
        col_toko, col_btn = st.columns([3, 1])
        with col_toko:
            kode_toko = st.text_input("KODE TOKO").upper().strip()
        with col_btn:
            st.write("") # Spacer biar sejajar
            st.write("") # Spacer
            btn_cari = st.button("🔍 Cari Toko", use_container_width=True)
            
        # LOGIKA TOMBOL CARI DITEKAN
        if btn_cari:
            # 1. Validasi Kosong
            if not nama_user or not nik_user or jabatan == "" or not kode_toko:
                st.error("ada data yang masih kosong atau belum diisi")
            # 2. Validasi NIK wajib 10 Digit
            elif len(nik_user) != 10 or not nik_user.isdigit():
                st.error("ada data yang masih kosong atau belum diisi (Periksa NIK: Wajib 10 digit angka)")
            else:
                # 3. Pencarian di Master
                df_subset = df_master[df_master['KODE TOKO'] == kode_toko]
                
                if df_subset.empty:
                    st.error("❌ Kode Toko tidak ditemukan di Master Data!")
                    # Hapus memori pencarian sebelumnya jika ada
                    if 'toko_valid' in st.session_state:
                        del st.session_state['toko_valid']
                else:
                    # SIMPAN KE MEMORI (Session State) agar tabel muncul
                    st.session_state['toko_valid'] = kode_toko
                    st.session_state['nama_user'] = nama_user
                    st.session_state['nik_user'] = nik_user
                    st.session_state['jabatan'] = jabatan
                    st.session_state['nama_toko'] = df_subset.iloc[0]['NAMA TOKO']
                    
                    # Ambil daftar produk khusus toko ini saja dari master
                    produk_list = df_subset[['PLU', 'DESC']].dropna().to_dict('records')
                    st.session_state['produk_toko'] = produk_list

        # ==========================================
        # TAHAP 3 & 4: TABEL PRODUK & SIMPAN (Muncul jika "Cari" berhasil)
        # ==========================================
        if st.session_state.get('toko_valid'):
            st.divider()
            
            # Label NAMA TOKO persis sesuai permintaan
            st.info(f"📍 **NAMA TOKO:** {st.session_state['nama_toko']}")
            
            # Keterangan Acuan
            st.write("💡 **jika tidak ada fisik input nol (0)**")
            
            # Siapkan Tabel
            df_input = pd.DataFrame(st.session_state['produk_toko'])
            df_input["QTY SISA CUKAI 2025"] = None  # Setup awal blank
            
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
            
            # Tombol Simpan
            btn_simpan = st.button("💾 Simpan Pendataan", type="primary", use_container_width=True)
            
            if btn_simpan:
                # Validasi jika ada sel QTY yang masih kosong (blank/null)
                if edited_df["QTY SISA CUKAI 2025"].isnull().any():
                    st.error("masih ada kolom yang belum diinput")
                else:
                    # CREATE TIMESTAMP!
                    timestamp_lengkap = datetime.now().strfti
