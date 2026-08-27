import streamlit as st
import db
import style
import auth

st.set_page_config(page_title="Raya Houses | Cari Properti", page_icon="🔎", layout="wide")
db.init_db()
style.inject()
style.header("Cari Properti", "Temukan rumah, apartemen, tanah, ruko, atau villa impian Anda.")
auth.sidebar_user_box()

if "selected_listing_id" not in st.session_state:
    st.session_state["selected_listing_id"] = None
if "viewed_listings" not in st.session_state:
    st.session_state["viewed_listings"] = set()

# ---------------------------------------------------------------------------
# Filter sidebar
# ---------------------------------------------------------------------------
st.sidebar.header("🔍 Filter Pencarian")
keyword = st.sidebar.text_input("Kata kunci (judul/alamat/kota)")
ptype = st.sidebar.selectbox("Tipe Properti", ["Semua"] + db.PROPERTY_TYPES)
city = st.sidebar.selectbox("Kota", ["Semua"] + db.distinct_cities())
status = st.sidebar.selectbox("Status", ["Semua"] + db.LISTING_STATUSES, index=1)
price_range = st.sidebar.slider("Rentang Harga (Rp Miliar)", 0.0, 10.0, (0.0, 10.0), step=0.1)
min_bed = st.sidebar.selectbox("Minimal Kamar Tidur", [0, 1, 2, 3, 4, 5], index=0)

filters = {
    "keyword": keyword or None,
    "type": None if ptype == "Semua" else ptype,
    "city": None if city == "Semua" else city,
    "status": None if status == "Semua" else status,
    "min_price": price_range[0] * 1e9,
    "max_price": price_range[1] * 1e9,
    "min_bedrooms": min_bed if min_bed > 0 else None,
}

listings = db.list_listings(filters)
st.write(f"Menampilkan **{len(listings)}** properti")

# ---------------------------------------------------------------------------
# Detail view (jika ada listing terpilih)
# ---------------------------------------------------------------------------
selected_id = st.session_state["selected_listing_id"]
if selected_id:
    listing = db.get_listing(selected_id)
    if listing:
        if selected_id not in st.session_state["viewed_listings"]:
            db.increment_view(selected_id)
            st.session_state["viewed_listings"].add(selected_id)
            listing["views"] += 1

        if st.button("⬅️ Kembali ke daftar"):
            st.session_state["selected_listing_id"] = None
            st.rerun()

        st.markdown(
            f"""
            <div class="rh-card">
                <h2>{listing['title']}</h2>
                {style.status_badge(listing['status'])}
                <span class="rh-badge" style="background:#2b2b2b;color:#ddd;">{listing['type']}</span>
                <p class="rh-price">{style.format_rupiah(listing['price'])}{' / tahun' if listing['price_unit']=='Sewa/Tahun' else ''}</p>
                <p>📍 {listing['address']}, {listing['city']}, {listing['province']}</p>
                <p>🛏️ {listing['bedrooms']} Kamar Tidur &nbsp; 🛁 {listing['bathrooms']} Kamar Mandi</p>
                <p>📐 Luas Tanah: {listing['land_area']:.0f} m² &nbsp; | &nbsp; Luas Bangunan: {listing['building_area']:.0f} m²</p>
                <p>👁️ {listing['views']} kali dilihat</p>
                <hr>
                <p>{listing['description']}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.subheader("📞 Hubungi Agent Penanggung Jawab")
        st.markdown(
            f"""
            <div class="rh-card">
                <p><b>🧑‍💼 {listing['agent_name'] or 'Belum ditugaskan'}</b></p>
                <p>📱 {listing['agent_phone'] or '-'}</p>
                <p>✉️ {listing['agent_email'] or '-'}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("Listing tidak ditemukan.")
        st.session_state["selected_listing_id"] = None

else:
    if not listings:
        st.info("Tidak ada properti yang cocok dengan filter Anda.")
    cols = st.columns(3)
    for idx, l in enumerate(listings):
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
                    <p>Agent: {l['agent_name'] or '-'}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Lihat Detail", key=f"detail_{l['id']}", use_container_width=True):
                st.session_state["selected_listing_id"] = l["id"]
                st.rerun()
