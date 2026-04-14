import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# 1. KONFIGURASI HALAMAN
st.set_page_config(
    page_title="Dashboard Monitoring Gempa RI Terpadu",
    layout="wide",
    page_icon="🌋"
)

# Fitur Auto-Refresh setiap 10 menit (600,000 ms)
st_autorefresh(interval=600000, key="datarefresh")

# 2. FUNGSI PENGAMBILAN DATA (MULTI-SOURCE API)
@st.cache_data(ttl=600)
def get_combined_data():
    try:
        # Sumber 1: Gempa M > 5.0
        res5 = requests.get("https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json").json()
        df5 = pd.DataFrame(res5['Infogempa']['gempa'])
        df5['Kategori'] = "M > 5.0"
        
        # Sumber 2: Gempa Dirasakan
        resD = requests.get("https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json").json()
        dfD = pd.DataFrame(resD['Infogempa']['gempa'])
        dfD['Kategori'] = "Dirasakan"
        
        # Penggabungan Data
        df = pd.concat([df5, dfD], ignore_index=True)
        
        # Pembersihan Koordinat
        coords = df['Coordinates'].str.split(',', expand=True)
        df['Lat'] = pd.to_numeric(coords[0], errors='coerce')
        df['Lon'] = pd.to_numeric(coords[1], errors='coerce')
        
        # Pembersihan Magnitudo & Kedalaman
        df['Magnitude'] = pd.to_numeric(df['Magnitude'], errors='coerce')
        df['Kedalaman'] = df['Kedalaman'].astype(str).str.replace(' km', '').str.replace('km', '').str.strip()
        df['Kedalaman'] = pd.to_numeric(df['Kedalaman'], errors='coerce')
        
        # Menghapus duplikat dan data kosong
        df = df.dropna(subset=['Magnitude', 'Kedalaman', 'Lat', 'Lon'])
        return df.drop_duplicates(subset=['DateTime', 'Coordinates'])
    except Exception as e:
        st.error(f"Gagal memuat data dari BMKG: {e}")
        return pd.DataFrame()

# Inisialisasi Data
df_all = get_combined_data()

# 3. SIDEBAR (KONTROL PANEL)
st.sidebar.title("🧭 Navigasi & Filter")
st.sidebar.markdown("Dashboard ini memperbarui data secara otomatis dari server BMKG setiap 10 menit.")

if not df_all.empty:
    kategori_pilihan = st.sidebar.multiselect(
        "Pilih Kategori Gempa:",
        options=["M > 5.0", "Dirasakan"],
        default=["M > 5.0", "Dirasakan"]
    )
    
    mag_min = float(df_all['Magnitude'].min())
    mag_max = float(df_all['Magnitude'].max())
    min_mag = st.sidebar.slider("Minimal Magnitudo (M):", mag_min, mag_max, 4.0, step=0.1)

    # Proses Filtering
    df_filtered = df_all[
        (df_all['Magnitude'] >= min_mag) & 
        (df_all['Kategori'].isin(kategori_pilihan))
    ].copy()

    # 4. TAMPILAN UTAMA
    st.title("🛡️ Dashboard Pemantauan Seismik Nasional")
    st.markdown(f"Menganalisis **{len(df_filtered)}** kejadian gempa bumi terbaru di wilayah Indonesia.")

    # Barisan Metrik (KPI)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Gempa Terkuat", f"{df_filtered['Magnitude'].max()} M")
    m2.metric("Rerata Kedalaman", f"{int(df_filtered['Kedalaman'].mean())} km")
    m3.metric("Wilayah Teraktif", df_filtered['Wilayah'].mode()[0].split(',')[0])
    m4.metric("Status Data", "Real-Time")

    st.divider()

    # Layout Kolom untuk Peta dan Grafik
    col_left, col_right = st.columns([2, 1])

    with col_left:
        st.subheader("📍 Peta Sebaran Episentrum")
        fig_map = px.scatter_mapbox(
            df_filtered, lat="Lat", lon="Lon", 
            color="Kedalaman", size="Magnitude",
            hover_name="Wilayah", 
            color_continuous_scale='RdYlGn_r', # Merah = Dangkal, Hijau = Dalam
            zoom=3.5, height=600,
            mapbox_style="carto-darkmatter"
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with col_right:
        st.subheader("📉 Korelasi Magnitudo & Kedalaman")
        fig_corr = px.scatter(
            df_filtered, x="Magnitude", y="Kedalaman",
            color="Kategori", size="Magnitude",
            hover_name="Wilayah", template="plotly_dark",
            labels={"Kedalaman": "Kedalaman (km)", "Magnitude": "Magnitudo (M)"}
        )
        fig_corr.update_yaxes(autorange="reversed") # Sesuai profil kerak bumi
        st.plotly_chart(fig_corr, use_container_width=True)
        
        st.subheader("📋 Log Kejadian")
        st.dataframe(df_filtered[['Tanggal', 'Magnitude', 'Kategori', 'Wilayah']].head(20), hide_index=True)

    # 5. MODUL INTERPRETASI OTOMATIS (INSIGHT)
    st.divider()
    st.subheader("🧠 Analisis & Interpretasi Otomatis")
    
    # Logika Analisis
    gempa_dangkal = df_filtered[df_filtered['Kedalaman'] <= 50]
    persen_dangkal = (len(gempa_dangkal) / len(df_filtered) * 100) if len(df_filtered) > 0 else 0

    c_ins1, c_ins2 = st.columns(2)
    
    with c_ins1:
        if persen_dangkal > 50:
            st.warning(f"⚠️ **Peringatan Risiko Kedalaman:**\n\nSekitar **{persen_dangkal:.1f}%** gempa yang terdeteksi adalah **Gempa Dangkal** (≤ 50 km). "
                       "Gempa dangkal memiliki daya rusak yang lebih besar pada infrastruktur bangunan di permukaan bumi.")
        else:
            st.success("✅ **Informasi Kedalaman:**\n\nMayoritas gempa berada pada kedalaman menengah hingga dalam. Energi guncangan biasanya lebih teredam saat mencapai permukaan.")

    with c_ins2:
        st.info(f"💡 **Tips Mitigasi:**\n\nUntuk wilayah **{df_filtered['Wilayah'].mode()[0].split(',')[0]}** yang menunjukkan aktivitas tinggi, "
                "disarankan untuk melakukan pengecekan struktur bangunan secara berkala dan memahami jalur evakuasi mandiri.")

    st.write("---")
    st.caption("Data Sumber: Portal Open Data BMKG (Badan Meteorologi, Klimatologi, dan Geofisika) Indonesia.")

else:
    st.error("Gagal mendapatkan data. Periksa koneksi internet atau status server BMKG.")
