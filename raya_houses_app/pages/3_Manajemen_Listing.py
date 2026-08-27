from datetime import date
import pandas as pd
import streamlit as st

import db
import style
import auth

st.set_page_config(page_title="Raya Houses | Manajemen Listing", page_icon="🏘️", layout="wide")
db.init_db()
style.inject()
style.header("Manajemen Listing", "Kelola data listing properti perusahaan.")
auth.sidebar_user_box()

user = auth.require_login(allowed_roles=["Admin", "Manager", "Agent"])
is_owner_role = user["role"] in ("Admin", "Manager")

tab_list, tab_add = st.tabs(["📋 Daftar Listing", "➕ Tambah Listing Baru"])

# ---------------------------------------------------------------------------
# Tab: Daftar & Edit
# ---------------------------------------------------------------------------
with tab_list:
    colf1, colf2, colf3 = st.columns(3)
    f_type = colf1.selectbox("Filter Tipe", ["Semua"] + db.PROPERTY_TYPES)
    f_status = colf2.selectbox("Filter Status", ["Semua"] + db.LISTING_STATUSES)
    f_city = colf3.selectbox("Filter Kota", ["Semua"] + db.distinct_cities())

    filters = {
        "type": None if f_type == "Semua" else f_type,
        "status": None if f_status == "Semua" else f_status,
        "city": None if f_city == "Semua" else f_city,
    }
    if not is_owner_role:
        filters["agent_id"] = user["staff_id"]

    listings = db.list_listings(filters)
    if not listings:
        st.info("Tidak ada listing yang cocok.")
    else:
        df = pd.DataFrame(listings)[[
            "id", "title", "type", "status", "price", "city", "agent_name", "views", "created_date"
        ]]
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("### ✏️ Edit / Hapus Listing")
        options = {f"#{l['id']} - {l['title']}": l["id"] for l in listings}
        chosen_label = st.selectbox("Pilih listing", list(options.keys()))
        chosen_id = options[chosen_label]
        listing = db.get_listing(chosen_id)

        can_edit = is_owner_role or listing["agent_id"] == user["staff_id"]
        if not can_edit:
            st.warning("Anda hanya dapat mengubah listing yang ditugaskan kepada Anda.")
        else:
            agents = db.list_staff(role="Agent", status="Aktif")
            agent_options = {a["name"]: a["id"] for a in agents}
            agent_names = list(agent_options.keys())
            current_agent_name = next((n for n, i in agent_options.items() if i == listing["agent_id"]), agent_names[0] if agent_names else None)

            with st.form("edit_listing_form"):
                c1, c2 = st.columns(2)
                title = c1.text_input("Judul", value=listing["title"])
                ptype = c2.selectbox("Tipe", db.PROPERTY_TYPES, index=db.PROPERTY_TYPES.index(listing["type"]))
                status = c1.selectbox("Status", db.LISTING_STATUSES, index=db.LISTING_STATUSES.index(listing["status"]))
                price = c2.number_input("Harga (Rp)", value=float(listing["price"]), step=1_000_000.0, format="%.0f")
                address = c1.text_input("Alamat", value=listing["address"] or "")
                city = c2.text_input("Kota", value=listing["city"])
                province = c1.text_input("Provinsi", value=listing["province"] or "")
                bedrooms = c2.number_input("Kamar Tidur", value=int(listing["bedrooms"]), min_value=0)
                bathrooms = c1.number_input("Kamar Mandi", value=int(listing["bathrooms"]), min_value=0)
                building_area = c2.number_input("Luas Bangunan (m²)", value=float(listing["building_area"]), min_value=0.0)
                land_area = c1.number_input("Luas Tanah (m²)", value=float(listing["land_area"]), min_value=0.0)
                agent_name = c2.selectbox(
                    "Agent Penanggung Jawab", agent_names,
                    index=agent_names.index(current_agent_name) if current_agent_name in agent_names else 0,
                    disabled=not is_owner_role,
                )
                description = st.text_area("Deskripsi", value=listing["description"] or "")

                save_col, del_col = st.columns([3, 1])
                submitted = save_col.form_submit_button("💾 Simpan Perubahan", use_container_width=True)
                deleted = del_col.form_submit_button("🗑️ Hapus", use_container_width=True, disabled=not is_owner_role)

                if submitted:
                    updates = dict(
                        title=title, type=ptype, status=status, price=price, address=address,
                        city=city, province=province, bedrooms=bedrooms, bathrooms=bathrooms,
                        building_area=building_area, land_area=land_area, description=description,
                    )
                    if status == "Terjual" and listing["status"] != "Terjual":
                        updates["sold_date"] = date.today().strftime("%Y-%m-%d")
                    if is_owner_role:
                        updates["agent_id"] = agent_options.get(agent_name)
                    db.update_listing(chosen_id, **updates)
                    st.success("Listing berhasil diperbarui.")
                    st.rerun()

                if deleted:
                    db.delete_listing(chosen_id)
                    st.success("Listing dihapus.")
                    st.rerun()

# ---------------------------------------------------------------------------
# Tab: Tambah Baru
# ---------------------------------------------------------------------------
with tab_add:
    agents = db.list_staff(role="Agent", status="Aktif")
    if not agents:
        st.warning("Belum ada agent aktif. Tambahkan agent terlebih dahulu di menu Staff & Agent.")
    else:
        agent_options = {a["name"]: a["id"] for a in agents}
        default_agent = user["staff_name"] if user["role"] == "Agent" and user["staff_name"] in agent_options else list(agent_options.keys())[0]

        with st.form("add_listing_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            title = c1.text_input("Judul Listing*")
            ptype = c2.selectbox("Tipe Properti*", db.PROPERTY_TYPES)
            price = c1.number_input("Harga (Rp)*", min_value=0.0, step=1_000_000.0, format="%.0f")
            price_unit = c2.selectbox("Jenis Harga", ["Jual", "Sewa/Tahun"])
            city = c1.text_input("Kota*")
            province = c2.text_input("Provinsi")
            address = c1.text_input("Alamat")
            status = c2.selectbox("Status Awal", db.LISTING_STATUSES)
            bedrooms = c1.number_input("Kamar Tidur", min_value=0, value=2)
            bathrooms = c2.number_input("Kamar Mandi", min_value=0, value=1)
            land_area = c1.number_input("Luas Tanah (m²)", min_value=0.0, value=100.0)
            building_area = c2.number_input("Luas Bangunan (m²)", min_value=0.0, value=80.0)
            agent_name = st.selectbox(
                "Agent Penanggung Jawab*", list(agent_options.keys()),
                index=list(agent_options.keys()).index(default_agent) if default_agent in agent_options else 0,
            )
            description = st.text_area("Deskripsi")

            submitted = st.form_submit_button("➕ Tambahkan Listing", use_container_width=True)
            if submitted:
                if not title or not city:
                    st.error("Judul dan Kota wajib diisi.")
                else:
                    new_id = db.add_listing(dict(
                        title=title, type=ptype, status=status, price=price, price_unit=price_unit,
                        address=address, city=city, province=province, bedrooms=bedrooms,
                        bathrooms=bathrooms, land_area=land_area, building_area=building_area,
                        description=description, agent_id=agent_options[agent_name],
                        created_date=date.today().strftime("%Y-%m-%d"),
                    ))
                    st.success(f"Listing baru berhasil ditambahkan dengan ID #{new_id}.")
