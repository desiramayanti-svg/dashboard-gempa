import streamlit as st
import pandas as pd
import plotly.express as px

import db
import style
import auth

st.set_page_config(page_title="Raya Houses | Beranda", page_icon="🏠", layout="wide")
db.init_db()
style.inject()
style.header("Beranda", "Partner properti terpercaya untuk jual, beli, dan sewa rumah impian Anda.")
auth.sidebar_user_box()

listings = db.list_listings(order_by="views DESC")
df = pd.DataFrame(listings)

# ---------------------------------------------------------------------------
# Ringkasan cepat
# ---------------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
total_listing = len(df)
tersedia = int((df["status"] == "Tersedia").sum()) if not df.empty else 0
terjual = int((df["status"] == "Terjual").sum()) if not df.empty else 0
agents = db.list_staff(role="Agent", status="Aktif")

c1.metric("🏘️ Total Listing", total_listing)
c2.metric("✅ Tersedia", tersedia)
c3.metric("🤝 Terjual", terjual)
c4.metric("🧑‍💼 Agent Aktif", len(agents))

st.markdown("---")

# ---------------------------------------------------------------------------
# Listing unggulan (paling banyak dilihat, status tersedia)
# ---------------------------------------------------------------------------
st.subheader("⭐ Listing Unggulan")
featured = [l for l in listings if l["status"] == "Tersedia"][:6]

if not featured:
    st.info("Belum ada listing tersedia saat ini.")
else:
    cols = st.columns(3)
    for idx, l in enumerate(featured):
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div class="rh-card">
                    <h4>{l['title']}</h4>
                    {style.status_badge(l['status'])}
                    <span class="rh-badge" style="background:#2b2b2b;color:#ddd;">{l['type']}</span>
                    <p>📍 {l['city']}, {l['province']}</p>
                    <p class="rh-price">{style.format_rupiah(l['price'])}{' / thn' if l['price_unit']=='Sewa/Tahun' else ''}</p>
                    <p>🛏️ {l['bedrooms']} KT &nbsp; 🛁 {l['bathrooms']} KM &nbsp; 📐 {l['building_area']:.0f} m²</p>
                    <p>👁️ {l['views']} dilihat &nbsp;|&nbsp; Agent: {l['agent_name'] or '-'}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

st.markdown("---")
st.subheader("📊 Sebaran Tipe Properti yang Tersedia")
if not df.empty:
    avail = df[df["status"] == "Tersedia"]
    if not avail.empty:
        fig = px.pie(avail, names="type", title="Komposisi Tipe Properti Tersedia", hole=0.45,
                      color_discrete_sequence=px.colors.sequential.Oranges_r)
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption(
    "Gunakan menu di sidebar: **Cari Properti** untuk melihat semua listing publik, "
    "atau **Login Staff** untuk mengakses panel manajemen internal "
    "(Manajemen Listing, Staff & Agent, Keuangan, Statistik Penjualan, Statistik Wilayah)."
)
