from datetime import date
import pandas as pd
import streamlit as st

import db
import style
import auth

st.set_page_config(page_title="Raya Houses | Staff & Agent", page_icon="👥", layout="wide")
db.init_db()
style.inject()
style.header("Manajemen Staff & Agent", "Kelola data pegawai dan agent properti.")
auth.sidebar_user_box()

user = auth.require_login(allowed_roles=["Admin", "Manager"])

tab_list, tab_add, tab_perf = st.tabs(["📋 Daftar Staff", "➕ Tambah Staff/Agent", "📈 Performa Agent"])

with tab_list:
    f_role = st.selectbox("Filter Role", ["Semua"] + db.STAFF_ROLES)
    staff = db.list_staff(role=None if f_role == "Semua" else f_role)
    if not staff:
        st.info("Belum ada data staff.")
    else:
        df = pd.DataFrame(staff)[["id", "name", "role", "phone", "email", "join_date", "status"]]
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("### ✏️ Edit Status / Data Staff")
        options = {f"#{s['id']} - {s['name']} ({s['role']})": s["id"] for s in staff}
        chosen_label = st.selectbox("Pilih staff", list(options.keys()))
        chosen_id = options[chosen_label]
        s = db.get_staff(chosen_id)

        with st.form("edit_staff_form"):
            c1, c2 = st.columns(2)
            name = c1.text_input("Nama", value=s["name"])
            role = c2.selectbox("Role", db.STAFF_ROLES, index=db.STAFF_ROLES.index(s["role"]))
            phone = c1.text_input("Telepon", value=s["phone"] or "")
            email = c2.text_input("Email", value=s["email"] or "")
            status = c1.selectbox("Status", ["Aktif", "Nonaktif"], index=0 if s["status"] == "Aktif" else 1)
            notes = st.text_area("Catatan", value=s["notes"] or "")
            submitted = st.form_submit_button("💾 Simpan Perubahan", use_container_width=True)
            if submitted:
                db.update_staff(chosen_id, name=name, role=role, phone=phone, email=email, status=status, notes=notes)
                st.success("Data staff berhasil diperbarui.")
                st.rerun()

with tab_add:
    with st.form("add_staff_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        name = c1.text_input("Nama Lengkap*")
        role = c2.selectbox("Role*", db.STAFF_ROLES)
        phone = c1.text_input("Telepon")
        email = c2.text_input("Email")
        join_date = st.date_input("Tanggal Bergabung", value=date.today())
        notes = st.text_area("Catatan")

        st.markdown("**Akun login (opsional)** — kosongkan jika staff ini tidak perlu login ke sistem.")
        c3, c4 = st.columns(2)
        username = c3.text_input("Username")
        password = c4.text_input("Password", type="password")

        submitted = st.form_submit_button("➕ Tambahkan Staff", use_container_width=True)
        if submitted:
            if not name:
                st.error("Nama wajib diisi.")
            elif username and db.username_exists(username):
                st.error("Username sudah digunakan, pilih username lain.")
            else:
                new_id = db.add_staff(name, role, phone, email, join_date.strftime("%Y-%m-%d"), notes)
                if username and password:
                    db.create_user(username, password, new_id, role)
                st.success(f"Staff baru '{name}' berhasil ditambahkan (ID #{new_id}).")

with tab_perf:
    agents = db.list_staff(role="Agent")
    if not agents:
        st.info("Belum ada agent.")
    else:
        rows = []
        for a in agents:
            listings = db.list_listings({"agent_id": a["id"]})
            terjual = [l for l in listings if l["status"] == "Terjual"]
            total_revenue = sum(l["price"] for l in terjual)
            rows.append({
                "Agent": a["name"],
                "Status": a["status"],
                "Total Listing": len(listings),
                "Terjual": len(terjual),
                "Total Nilai Terjual": total_revenue,
            })
        perf_df = pd.DataFrame(rows).sort_values("Total Nilai Terjual", ascending=False)
        perf_df["Total Nilai Terjual (Rp)"] = perf_df["Total Nilai Terjual"].apply(style.format_rupiah)
        st.dataframe(
            perf_df[["Agent", "Status", "Total Listing", "Terjual", "Total Nilai Terjual (Rp)"]],
            use_container_width=True, hide_index=True,
        )
