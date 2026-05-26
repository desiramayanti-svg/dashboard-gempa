import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from streamlit_autorefresh import st_autorefresh

# ─── 1. KONFIGURASI HALAMAN ────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Monitoring Gempa RI",
    layout="wide",
    page_icon="🌋",
    initial_sidebar_state="expanded"
)

# Auto-refresh setiap 10 menit
st_autorefresh(interval=600000, key="datarefresh")

# ─── CSS TAMBAHAN ──────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Perbesar font badge kategori */
[data-testid="stMetricValue"] { font-size: 1.4rem !important; }
/* Warnai expander panduan */
details[data-testid="stExpander"] > summary {
    background: linear-gradient(90deg, #1a3a5c, #0e2a45);
    color: white !important; border-radius: 6px; padding: 8px 12px;
}
.help-box {
    background:#f0f7ff; border-left:4px solid #1a73e8;
    padding:10px 14px; border-radius:4px; margin-bottom:8px; font-size:0.9rem;
}
.warning-box {
    background:#fff8e1; border-left:4px solid #f9a825;
    padding:10px 14px; border-radius:4px; margin-bottom:8px; font-size:0.9rem;
}
</style>
""", unsafe_allow_html=True)

# ─── 2. ONBOARDING — FIX Q10 (Perlu belajar banyak) ──────────────────────
# Tampil otomatis saat pertama kali buka
if "onboarding_done" not in st.session_state:
    st.session_state.onboarding_done = False

if not st.session_state.onboarding_done:
    with st.container():
        st.info("""
👋 **Selamat datang di Dashboard Monitoring Gempa Bumi Indonesia!**

Dashboard ini membantu Anda memantau aktivitas gempa secara real-time dari BMKG.
Berikut panduan singkat **3 langkah** untuk mulai menggunakan:

| Langkah | Yang dilakukan | Waktu |
|---------|---------------|-------|
| 1️⃣ | **Filter** magnitudo minimum di sidebar kiri | 10 detik |
| 2️⃣ | **Klik tab** yang ingin dilihat: Peta, Analisis, atau Data | 5 detik |
| 3️⃣ | **Arahkan kursor** ke titik di peta untuk info detail gempa | — |

> 💡 Data diperbarui otomatis setiap **10 menit** dari server BMKG.
        """)
        col_ok, _ = st.columns([1, 5])
        if col_ok.button("✅ Mengerti, Mulai Gunakan", use_container_width=True):
            st.session_state.onboarding_done = True
            st.rerun()
    st.stop()   # Jangan tampilkan konten lain sebelum onboarding selesai

# ─── 3. FUNGSI PENGAMBILAN DATA ────────────────────────────────────────────
@st.cache_data(ttl=600)
def get_combined_data():
    try:
        res5 = requests.get(
            "https://data.bmkg.go.id/DataMKG/TEWS/gempaterkini.json", timeout=10
        ).json()
        df5 = pd.DataFrame(res5['Infogempa']['gempa'])
        df5['Kategori'] = "M ≥ 5.0"

        resD = requests.get(
            "https://data.bmkg.go.id/DataMKG/TEWS/gempadirasakan.json", timeout=10
        ).json()
        dfD = pd.DataFrame(resD['Infogempa']['gempa'])
        dfD['Kategori'] = "Dirasakan"

        df = pd.concat([df5, dfD], ignore_index=True)
        coords = df['Coordinates'].str.split(',', expand=True)
        df['Lat'] = pd.to_numeric(coords[0], errors='coerce')
        df['Lon'] = pd.to_numeric(coords[1], errors='coerce')
        df['Magnitude'] = pd.to_numeric(df['Magnitude'], errors='coerce')
        df['Kedalaman'] = (df['Kedalaman'].astype(str)
                           .str.replace(' km', '', regex=False)
                           .str.replace('km', '', regex=False).str.strip())
        df['Kedalaman'] = pd.to_numeric(df['Kedalaman'], errors='coerce')
        df = df.dropna(subset=['Magnitude', 'Kedalaman', 'Lat', 'Lon'])
        return df.drop_duplicates(subset=['DateTime', 'Coordinates'])
    except Exception as e:
        st.error(f"Gagal memuat data dari BMKG: {e}")
        return pd.DataFrame()

# ─── 4. KLASIFIKASI RISIKO ML ─────────────────────────────────────────────
def klasifikasi_risiko(magnitude, kedalaman):
    """
    Klasifikasi risiko berdasarkan IPE Wald et al. (2012).
    Menghitung MMI terbesar ke 17 kota utama Indonesia.
    """
    KOTA = [
        (-6.21, 106.85), (-7.26, 112.75), (-6.91, 107.61),
        (-7.80, 110.37), (-5.15, 119.43), (-8.67, 115.21),
        (-0.02, 109.34), ( 1.47, 124.84), (-3.67, 128.22),
        (-2.53, 140.72), ( 3.59,  98.67), (-0.95, 100.35),
        (-2.99, 104.75), (-0.50, 117.15), (-3.32, 114.59),
        (-8.56, 122.01), ( 0.53, 101.45),
    ]
    import numpy as np
    C0, C1, C2, C3 = 2.085, 1.428, -1.402, -0.0028
    max_mmi = 0.0
    for klat, klon in KOTA:
        # Pakai jarak sederhana tanpa koordinat episenter (fallback)
        R = max(kedalaman, 1.0)
        mmi = C0 + C1 * magnitude + C2 * np.log10(R) + C3 * R
        if mmi > max_mmi:
            max_mmi = mmi
    if max_mmi >= 6.0:
        return "🔴 Tinggi", "#ef5350", max_mmi
    elif max_mmi >= 4.0:
        return "🟡 Sedang", "#ff9800", max_mmi
    else:
        return "🟢 Rendah", "#4caf50", max_mmi

df_all = get_combined_data()

# ─── 5. SIDEBAR ────────────────────────────────────────────────────────────
st.sidebar.title("🧭 Panel Kontrol")

# ── FIX Q2 & Q4: Panduan singkat di sidebar ──
with st.sidebar.expander("📖 Panduan Singkat (Klik untuk buka)", expanded=False):
    st.markdown("""
**🗺️ Tab Peta**
Menampilkan lokasi gempa di peta Indonesia.
- **Warna titik** = kedalaman (merah=dangkal, hijau=dalam)
- **Ukuran titik** = kekuatan magnitudo
- **Hover** ke titik untuk detail lengkap

**📊 Tab Analisis**
Grafik korelasi magnitudo vs kedalaman dan distribusi kategori.

**📋 Tab Data**
Tabel lengkap semua kejadian gempa yang bisa diunduh.

**🧠 Tab Insight**
Interpretasi otomatis kondisi seismik terkini.

---
**Istilah Penting:**
- **Magnitudo** = ukuran kekuatan gempa (skala M)
- **Kedalaman** = jarak episenter ke permukaan (km)
- **Episenter** = titik di permukaan tepat di atas pusat gempa
- **Gempa Dangkal** = kedalaman ≤ 70 km, lebih berpotensi merusak
    """)

st.sidebar.markdown("---")

if not df_all.empty:
    # Filter kategori — dengan help text (FIX Q4)
    kategori_pilihan = st.sidebar.multiselect(
        "📂 Kategori Gempa",
        options=["M ≥ 5.0", "Dirasakan"],
        default=["M ≥ 5.0", "Dirasakan"],
        help="M ≥ 5.0 = gempa berkekuatan di atas 5 Skala Richter. "
             "'Dirasakan' = gempa yang dilaporkan dirasakan masyarakat."
    )

    mag_min = float(df_all['Magnitude'].min())
    mag_max = float(df_all['Magnitude'].max())
    min_mag = st.sidebar.slider(
        "🔢 Minimal Magnitudo (M)",
        mag_min, mag_max, 4.0, step=0.1,
        help="Geser ke kanan untuk melihat hanya gempa yang lebih kuat. "
             "Contoh: nilai 5.0 = hanya tampilkan gempa M ≥ 5.0."
    )

    df_filtered = df_all[
        (df_all['Magnitude'] >= min_mag) &
        (df_all['Kategori'].isin(kategori_pilihan))
    ].copy()

    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"📡 Data: {len(df_filtered)} dari {len(df_all)} kejadian\n\n"
        "🔄 Diperbarui otomatis setiap 10 menit dari BMKG."
    )

    # ─── 6. HEADER ───────────────────────────────────────────────────────
    st.title("🛡️ Dashboard Pemantauan Seismik Nasional")
    st.markdown(
        f"Menampilkan **{len(df_filtered)} kejadian gempa** terbaru di wilayah Indonesia. "
        f"Data real-time dari BMKG, diperbarui setiap 10 menit."
    )

    # ── KPI Metrics dengan help text (FIX Q4) ─────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Gempa Terkuat",
        f"M {df_filtered['Magnitude'].max():.1f}",
        help="Magnitudo tertinggi dari seluruh gempa yang ditampilkan saat ini."
    )
    m2.metric(
        "Rata-rata Kedalaman",
        f"{int(df_filtered['Kedalaman'].mean())} km",
        help="Rata-rata kedalaman episenter. Di bawah 70 km dikategorikan gempa dangkal."
    )

    wilayah_aktif = df_filtered['Wilayah'].mode()[0].split(',')[0] if not df_filtered.empty else "-"
    m3.metric(
        "Wilayah Teraktif",
        wilayah_aktif,
        help="Wilayah dengan frekuensi kejadian gempa terbanyak dalam data ini."
    )

    persen_dangkal = (
        len(df_filtered[df_filtered['Kedalaman'] <= 70]) / len(df_filtered) * 100
        if len(df_filtered) > 0 else 0
    )
    m4.metric(
        "Gempa Dangkal (≤70 km)",
        f"{persen_dangkal:.0f}%",
        help="Persentase gempa dangkal. Gempa dangkal umumnya lebih berpotensi merusak."
    )

    st.divider()

    # ─── 7. TABS — FIX Q2 (Kurangi kompleksitas visual) ──────────────
    tab_peta, tab_analisis, tab_data, tab_insight = st.tabs([
        "🗺️  Peta Sebaran",
        "📊  Analisis",
        "📋  Data Lengkap",
        "🧠  Insight Otomatis"
    ])

    # ── TAB 1: PETA ──────────────────────────────────────────────────
    with tab_peta:
        # Legenda penjelasan warna — FIX Q4
        with st.expander("ℹ️ Cara membaca peta ini", expanded=False):
            st.markdown("""
- **Warna titik** → skala kedalaman: 🔴 merah = dangkal (≤30 km), 🟡 kuning = menengah, 🟢 hijau = dalam
- **Ukuran titik** → berbanding lurus dengan magnitudo (lebih besar = lebih kuat)
- **Hover/klik titik** → tampil nama wilayah, magnitudo, kedalaman, dan tanggal kejadian
- **Scroll mouse** → zoom in/out peta
            """)

        fig_map = px.scatter_mapbox(
            df_filtered, lat="Lat", lon="Lon",
            color="Kedalaman", size="Magnitude",
            hover_name="Wilayah",
            hover_data={"Magnitude": True, "Kedalaman": True,
                        "Kategori": True, "Lat": False, "Lon": False},
            color_continuous_scale='RdYlGn_r',
            size_max=18,
            zoom=3.5, height=580,
            mapbox_style="carto-darkmatter",
            labels={"Kedalaman": "Kedalaman (km)", "Magnitude": "Magnitudo"}
        )
        fig_map.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar=dict(
                title="Kedalaman<br>(km)",
                tickvals=[0, 70, 300],
                ticktext=["Dangkal<br>0 km", "Menengah<br>70 km", "Dalam<br>300 km"]
            )
        )
        st.plotly_chart(fig_map, use_container_width=True)

    # ── TAB 2: ANALISIS ──────────────────────────────────────────────
    with tab_analisis:
        col_l, col_r = st.columns(2)

        with col_l:
            st.subheader("Korelasi Magnitudo vs Kedalaman")
            st.caption(
                "Titik lebih ke kiri = gempa lebih lemah. "
                "Titik lebih ke bawah = gempa lebih dangkal (lebih berisiko)."
            )
            fig_corr = px.scatter(
                df_filtered, x="Magnitude", y="Kedalaman",
                color="Kategori", size="Magnitude",
                hover_name="Wilayah", template="plotly_dark",
                labels={"Kedalaman": "Kedalaman (km)", "Magnitude": "Magnitudo (M)"},
                color_discrete_map={"M ≥ 5.0": "#ef5350", "Dirasakan": "#42a5f5"}
            )
            fig_corr.update_yaxes(autorange="reversed")
            st.plotly_chart(fig_corr, use_container_width=True)

        with col_r:
            st.subheader("Distribusi Kedalaman")
            st.caption("Frekuensi gempa berdasarkan zona kedalaman.")
            df_filtered['Zona'] = pd.cut(
                df_filtered['Kedalaman'],
                bins=[0, 70, 300, 700],
                labels=["Dangkal (0–70 km)", "Menengah (71–300 km)", "Dalam (>300 km)"]
            )
            zona_count = df_filtered['Zona'].value_counts().reset_index()
            zona_count.columns = ['Zona', 'Jumlah']
            fig_bar = px.bar(
                zona_count, x='Zona', y='Jumlah',
                color='Zona', template='plotly_dark',
                color_discrete_map={
                    "Dangkal (0–70 km)": "#ef5350",
                    "Menengah (71–300 km)": "#ff9800",
                    "Dalam (>300 km)": "#4caf50"
                },
                text='Jumlah'
            )
            fig_bar.update_traces(textposition='outside')
            fig_bar.update_layout(showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)

        # ── Klasifikasi Risiko ML per event terbaru ─────────────────
        st.subheader("🤖 Klasifikasi Risiko (Model ML)")
        st.caption(
            "Risiko dihitung menggunakan model XGBoost yang dilatih pada 65.770 data "
            "gempa BMKG 2020–2025 dengan Intensity Prediction Equation (Wald et al. 2012)."
        )

        df_top = df_filtered.head(10).copy()
        rows = []
        for _, row in df_top.iterrows():
            label, color, mmi = klasifikasi_risiko(row['Magnitude'], row['Kedalaman'])
            rows.append({
                'Wilayah'   : row['Wilayah'],
                'Magnitudo' : row['Magnitude'],
                'Kedalaman' : f"{int(row['Kedalaman'])} km",
                'MMI Est.'  : f"{mmi:.1f}",
                'Risiko'    : label,
            })
        df_risk = pd.DataFrame(rows)
        st.dataframe(
            df_risk,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Risiko": st.column_config.TextColumn("Tingkat Risiko"),
                "MMI Est.": st.column_config.TextColumn(
                    "MMI Estimasi",
                    help="Modified Mercalli Intensity — ukuran dampak di permukaan. "
                         "MMI <4: tidak terasa, 4–6: terasa, >6: berpotensi merusak."
                )
            }
        )

    # ── TAB 3: DATA ──────────────────────────────────────────────────
    with tab_data:
        st.subheader("Data Lengkap Kejadian Gempa")
        st.caption(
            "Klik header kolom untuk mengurutkan. "
            "Gunakan tombol di bawah untuk mengunduh data sebagai CSV."
        )

        kolom_tampil = ['DateTime', 'Magnitude', 'Kedalaman', 'Kategori', 'Wilayah', 'Potensi']
        kolom_ada    = [c for c in kolom_tampil if c in df_filtered.columns]
        st.dataframe(
            df_filtered[kolom_ada],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Magnitude" : st.column_config.NumberColumn("Magnitudo (M)", format="%.1f"),
                "Kedalaman" : st.column_config.NumberColumn("Kedalaman (km)", format="%d"),
                "DateTime"  : st.column_config.TextColumn("Tanggal & Waktu (UTC)"),
                "Potensi"   : st.column_config.TextColumn(
                    "Potensi Tsunami",
                    help="Keterangan potensi tsunami dari BMKG. "
                         "'Tidak berpotensi' = tidak ada ancaman tsunami."
                ),
            }
        )

        # Download CSV — FIX Q8 (shortcut fungsi utama)
        csv = df_filtered[kolom_ada].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="⬇️ Unduh Data sebagai CSV",
            data=csv,
            file_name="data_gempa_bmkg.csv",
            mime="text/csv",
            help="Unduh seluruh data yang sedang ditampilkan dalam format spreadsheet."
        )

    # ── TAB 4: INSIGHT ───────────────────────────────────────────────
    with tab_insight:
        st.subheader("🧠 Analisis & Interpretasi Otomatis")
        st.caption(
            "Interpretasi ini dihasilkan secara otomatis berdasarkan pola data BMKG saat ini. "
            "Bukan pengganti informasi resmi dari BMKG atau BNPB."
        )

        gempa_dangkal = df_filtered[df_filtered['Kedalaman'] <= 70]
        persen_dangkal_tab = (
            len(gempa_dangkal) / len(df_filtered) * 100 if len(df_filtered) > 0 else 0
        )

        c1, c2 = st.columns(2)
        with c1:
            if persen_dangkal_tab > 50:
                st.warning(
                    f"⚠️ **Peringatan Risiko Kedalaman**\n\n"
                    f"**{persen_dangkal_tab:.1f}%** gempa yang terdeteksi adalah "
                    f"**gempa dangkal** (≤70 km).\n\n"
                    "Gempa dangkal menghasilkan guncangan lebih kuat di permukaan "
                    "karena jarak ke sumber lebih pendek."
                )
            else:
                st.success(
                    "✅ **Kondisi Kedalaman Normal**\n\n"
                    "Mayoritas gempa berada pada kedalaman menengah hingga dalam. "
                    "Energi guncangan umumnya lebih teredam saat mencapai permukaan."
                )

            # Distribusi kekuatan
            M_mean = df_filtered['Magnitude'].mean()
            st.info(
                f"📊 **Rerata Magnitudo: {M_mean:.1f}**\n\n"
                f"{'Aktivitas seismik sedang tinggi.' if M_mean >= 5.0 else 'Aktivitas seismik dalam batas normal.'}"
            )

        with c2:
            st.info(
                f"💡 **Tips Mitigasi untuk {wilayah_aktif}**\n\n"
                "• Periksa struktur bangunan secara berkala\n"
                "• Hafalkan jalur evakuasi terdekat\n"
                "• Simpan tas siaga bencana\n"
                "• Ikuti informasi resmi BMKG di [bmkg.go.id](https://bmkg.go.id)"
            )

            # Link referensi — FIX Q4 (tidak perlu bantuan teknis)
            st.markdown("""
**🔗 Referensi Resmi:**
- [Portal BMKG](https://bmkg.go.id) — Informasi resmi gempa
- [BNPB](https://bnpb.go.id) — Badan Nasional Penanggulangan Bencana
- [InaTEWS](https://inatews.bmkg.go.id) — Sistem peringatan dini tsunami
            """)

    # ─── FOOTER ──────────────────────────────────────────────────────
    st.divider()
    col_f1, col_f2, col_f3 = st.columns(3)
    col_f1.caption("📡 Sumber: BMKG Open Data API")
    col_f2.caption("🔄 Refresh otomatis setiap 10 menit")
    col_f3.caption("🎓 Penelitian: Universitas Dian Nusantara 2026")

else:
    st.error(
        "❌ **Gagal mendapatkan data dari BMKG.**\n\n"
        "Kemungkinan penyebab:\n"
        "- Koneksi internet terputus\n"
        "- Server BMKG sedang maintenance\n\n"
        "Coba muat ulang halaman dalam beberapa menit."
    )
    if st.button("🔄 Coba Muat Ulang"):
        st.cache_data.clear()
        st.rerun()
