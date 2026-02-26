import streamlit as st
import pandas as pd
import os
from datetime import datetime
import io

# ==========================================
# 1. KONFIGURASI "CLOUD" (FOLDER PENYIMPANAN)
# ==========================================
MASTER_DIR = "master pendataan cukai rokok 2025"
RESULT_DIR = "hasil_input_user"

# Otomatis membuat folder jika belum ada
for d in [MASTER_DIR, RESULT_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

# Konfigurasi Halaman Web
st.set_page_config(page_title="Sistem Cukai 2025", layout="wide")

# ==========================================
# 2. MENU NAVIGASI (SIDEBAR)
# ==========================================
st.sidebar.title("Navigasi Sistem")
menu = st.sidebar.radio("Pilih Akses:", ["📝 Form Input User", "🔒 Menu Admin"])

# ==========================================
# 3. MENU ADMIN
# ==========================================
if menu == "🔒 Menu Admin":
    st.title("🔒 Halaman Administrator")
    
    # Sistem Password Admin
    password = st.text_input("Masukkan Password Admin:", type="password")
    
    if password == "icnbr034":
        st.success("Login Berhasil!")
        st.divider()
        
        # Fitur 1: Upload Master Data
        st.subheader("📁 1. Upload Master File (Acuan Input User)")
        st.info("Pastikan file Excel memiliki kolom: **KODE TOKO, NAMA TOKO, PLU, DESC**")
        file_master = st.file_uploader("Upload File Master Excel", type=["xlsx"])
        
        if file_master:
            master_path = os.path.join(MASTER_DIR, "master_data.xlsx")
            with open(master_path, "wb") as f:
                f.write(file_master.getbuffer())
            st.success(f"✅ File Master berhasil di-upload ke cloud '{MASTER_DIR}'!")
            
            # Tampilkan Preview Excel yang diupload
            try:
                df_preview = pd.read_excel(master_path)
                st.write("Preview Master Data:")
                st.dataframe(df_preview.head(), use_container_width=True)
            except Exception as e:
                st.error("Gagal membaca file. Pastikan formatnya benar.")
                
        st.divider()
        
        # Fitur 2: Download Hasil Input
        st.subheader("📥 2. Download Rekap Input User")
        all_files = [f for f in os.listdir(RESULT_DIR) if f.endswith('.csv')]
        
        if len(all_files) == 0:
            st.warning("Belum ada data yang disubmit oleh user.")
        else:
            st.write(f"Terdapat **{len(all_files)}** file hasil input dari berbagai toko.")
            
            # Tombol untuk menggabungkan semua CSV menjadi 1 file Excel rapi
            if st.button("Download Semua Hasil (Jadikan 1 Excel)"):
                all_data =[]
                for file in all_files:
                    df_temp = pd.read_csv(os.path.join(RESULT_DIR, file))
                    all_data.append(df_temp)
                    
                if all_data:
                    df_final = pd.concat(all_data, ignore_index=True)
                    
                    # Proses konversi ke Excel in-memory
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        df_final.to_excel(writer, index=False, sheet_name='Rekap_Hasil')
                    
                    # Generate File Download
                    st.download_button(
                        label="📥 KLIK UNTUK DOWNLOAD EXCEL",
                        data=output.getvalue(),
                        file_name=f"Rekap_Sisa_Cukai_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )

    elif password != "":
        st.error("❌ Password Salah!")

# ==========================================
# 4. MENU USER (FORM INPUT DINAMIS)
# ==========================================
elif menu == "📝 Form Input User":
    st.title("📋 Pendataan QTY Sisa Cukai 2025")
    
    master_path = os.path.join(MASTER_DIR, "master_data.xlsx")
    
    # Cek apakah Admin sudah upload master
    if not os.path.exists(master_path):
        st.warning("⚠️ File Master belum di-upload. Sistem belum bisa digunakan. Silakan hubungi Admin.")
    else:
        try:
            # Membaca Data Master
            df_master = pd.read_excel(master_path)
            # Menyeragamkan nama kolom (antisipasi jika admin mengetik 'TOKO' alih-alih 'KODE TOKO')
            df_master.columns = df_master.columns.str.strip().str.upper()
            if 'TOKO' in df_master.columns and 'KODE TOKO' not in df_master.columns:
                df_master.rename(columns={'TOKO': 'KODE TOKO'}, inplace=True)
            if 'NAMA' in df_master.columns and 'NAMA TOKO' not in df_master.columns:
                df_master.rename(columns={'NAMA': 'NAMA TOKO'}, inplace=True)
            
            # Membuat kamus (dictionary) Kode Toko -> Nama Toko
            df_toko = df_master[['KODE TOKO', 'NAMA TOKO']].drop_duplicates().dropna()
            dict_toko = dict(zip(df_toko['KODE TOKO'].astype(str), df_toko['NAMA TOKO'].astype(str)))
            
            # Membuat list PLU dan DESC
            df_produk = df_master[['PLU', 'DESC']].drop_duplicates().dropna()
            list_produk = df_produk.to_dict('records')
            
        except Exception as e:
            st.error("❌ Terjadi kesalahan membaca File Master. Pastikan Admin sudah mengunggah file dengan format kolom yang benar.")
            st.stop()
            
        # ==========================================
        # BAGIAN INPUT USER
        # ==========================================
        col1, col2, col3 = st.columns(3)
        with col1:
            nama_user = st.text_input("NAMA KARYAWAN")
        with col2:
            nik_user = st.text_input("NIK")
        with col3:
            jabatan = st.selectbox("JABATAN",["", "COS", "SSL", "SJL", "SCB", "SCG"])
            
        st.divider()
        
        # Validasi Kode Toko
        col_toko1, col_toko2 = st.columns([1, 2])
        with col_toko1:
            kode_toko = st.text_input("KODE TOKO", max_chars=4, help="Masukkan maksimal 4 digit").upper()
            
        nama_toko = ""
        with col_toko2:
            if len(kode_toko) == 4:
                if kode_toko in dict_toko:
                    nama_toko = dict_toko[kode_toko]
                    st.success(f"NAMA TOKO: {nama_toko}")
                else:
                    st.error("❌ Kode Toko tidak ditemukan di Master Data!")
            elif len(kode_toko) > 0:
                st.warning("⏳ Ketik 4 digit kode toko untuk memunculkan nama toko...")
                
        # Jika kode toko valid, munculkan tabel input QTY
        if nama_toko != "":
            st.divider()
            st.info("💡 **INFO:** Jika fisik di toko tidak ada, isi kolom dengan angka **0 (nol)**")
            
            # Siapkan Data Tabel Produk dari Master
            df_input = pd.DataFrame(list_produk)
            df_input["QTY SISA CUKAI 2025"] = None # Awal blank (kosong)
            
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
            
            # ==========================================
            # VALIDASI & SUBMIT
            # ==========================================
            if st.button("💾 Simpan Pendataan", type="primary"):
                # Cek Header
                if not nama_user or not nik_user or jabatan == "":
                    st.error("⚠️ Lengkapi NAMA, NIK, dan JABATAN terlebih dahulu!")
                else:
                    # Cek jika masih ada sel QTY yang belum diketik
                    if edited_df["QTY SISA CUKAI 2025"].isnull().any():
                        st.error("❌ ada kolom yang belum diisi")
                    else:
                        # 1. Ambil Waktu saat tombol submit ditekan
                        waktu_sekarang = datetime.now()
                        tanggal_submit = waktu_sekarang.strftime("%Y-%m-%d")
                        timestamp_lengkap = waktu_sekarang.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 2. Rangkai Data Akhir
                        final_data = edited_df.copy()
                        # Tambahkan kolom TIMESTAMP di paling ujung
                        final_data["TIMESTAMP"] = timestamp_lengkap
                        
                        # Tambahkan kolom identitas di urutan paling kiri (insert 0)
                        final_data.insert(0, "NAMA TOKO", nama_toko)
                        final_data.insert(0, "KODE TOKO", kode_toko)
                        final_data.insert(0, "JABATAN", jabatan)
                        final_data.insert(0, "NIK", nik_user)
                        final_data.insert(0, "NAMA", nama_user)
                        
                        # 3. Penamaan File Sesuai Permintaan (kode toko_tanggal submit.csv)
                        file_name = f"{kode_toko}_{tanggal_submit}.csv"
                        file_path = os.path.join(RESULT_DIR, file_name)
                        
                        # 4. Save file ke Cloud Lokal
                        # Jika di hari yang sama user input ulang (update), data akan ditambahkan ke bawahnya (append)
                        if os.path.exists(file_path):
                            final_data.to_csv(file_path, mode='a', header=False, index=False)
                        else:
                            final_data.to_csv(file_path, index=False)
                            
                        st.success(f"✅ Data berhasil disimpan! (Nama File di server: {file_name})")