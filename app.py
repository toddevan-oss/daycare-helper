import streamlit as st
import json
import os
import io
from datetime import date

from main import generate_pdf

CONFIG_FILE = os.path.join(os.path.dirname(__file__), "config.json")

DEFAULT_CONFIG = {
    "baby_name": "",
    "parent_contact": "",
    "feeding_instructions": [
        "Warm breast milk bottles in warm water for 2 minutes — do not microwave",
        "Shake gently before feeding",
        "Discard any unused milk after 1 hour of feeding"
    ]
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            return json.load(f)
    return DEFAULT_CONFIG.copy()


def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)


# ---- Page setup ----
st.set_page_config(page_title="Daycare Instructions", page_icon="👶", layout="centered")
st.title("Daycare Instruction Sheet")

config = load_config()

# ---- Tabs ----
tab_daily, tab_settings = st.tabs(["Daily Sheet", "Settings"])


# ==============================================================
# DAILY SHEET TAB
# ==============================================================
with tab_daily:

    # Date
    sheet_date = st.date_input("Date", value=date.today())
    st.divider()

    # ---- Nap Schedule ----
    st.subheader("Nap Schedule")

    if "naps" not in st.session_state:
        st.session_state.naps = [{"start": "", "duration": ""}]

    for i, nap in enumerate(st.session_state.naps):
        col1, col2, col3 = st.columns([2, 2, 0.5])
        with col1:
            st.session_state.naps[i]["start"] = st.text_input(
                f"Nap {i+1} start time", value=nap["start"],
                placeholder="e.g. 9:30am", key=f"nap_start_{i}"
            )
        with col2:
            st.session_state.naps[i]["duration"] = st.text_input(
                f"Target duration", value=nap["duration"],
                placeholder="e.g. 1h 30min", key=f"nap_dur_{i}"
            )
        with col3:
            st.write("")
            st.write("")
            if len(st.session_state.naps) > 1:
                if st.button("✕", key=f"remove_nap_{i}"):
                    st.session_state.naps.pop(i)
                    st.rerun()

    if st.button("+ Add Nap"):
        st.session_state.naps.append({"start": "", "duration": ""})
        st.rerun()

    st.divider()

    # ---- Feeding Schedule ----
    st.subheader("Feeding Schedule")

    if "feedings" not in st.session_state:
        st.session_state.feedings = [{"time": "", "amount": "", "type": "breast milk"}]

    for i, feeding in enumerate(st.session_state.feedings):
        col1, col2, col3, col4 = st.columns([2, 1.5, 2, 0.5])
        with col1:
            st.session_state.feedings[i]["time"] = st.text_input(
                f"Feeding {i+1} time", value=feeding["time"],
                placeholder="e.g. 7:00am", key=f"feed_time_{i}"
            )
        with col2:
            st.session_state.feedings[i]["amount"] = st.text_input(
                f"Amount", value=feeding["amount"],
                placeholder="e.g. 4oz", key=f"feed_amt_{i}"
            )
        with col3:
            st.session_state.feedings[i]["type"] = st.text_input(
                f"Type", value=feeding["type"],
                placeholder="e.g. breast milk", key=f"feed_type_{i}"
            )
        with col4:
            st.write("")
            st.write("")
            if len(st.session_state.feedings) > 1:
                if st.button("✕", key=f"remove_feed_{i}"):
                    st.session_state.feedings.pop(i)
                    st.rerun()

    if st.button("+ Add Feeding"):
        st.session_state.feedings.append({"time": "", "amount": "", "type": "breast milk"})
        st.rerun()

    st.divider()

    # ---- Notes ----
    st.subheader("Notes for Today")
    notes = st.text_area("Notes", placeholder="e.g. Rough night, may be extra tired. Teething.", label_visibility="collapsed")

    st.divider()

    # ---- Generate PDF ----
    if st.button("Generate PDF", type="primary", use_container_width=True):
        naps = [
            {"num": i+1, "start": n["start"], "duration": n["duration"] or "—"}
            for i, n in enumerate(st.session_state.naps)
            if n["start"].strip()
        ]
        feedings = [
            {"time": f["time"], "amount": f["amount"] or "—", "type": f["type"] or "breast milk"}
            for f in st.session_state.feedings
            if f["time"].strip()
        ]
        formatted_date = sheet_date.strftime("%B %d, %Y")
        pdf = generate_pdf(config, formatted_date, naps, feedings, notes)

        buf = io.BytesIO()
        pdf.output(buf)
        buf.seek(0)

        filename = f"daycare_{sheet_date.strftime('%Y-%m-%d')}.pdf"
        st.download_button(
            label="Download PDF",
            data=buf,
            file_name=filename,
            mime="application/pdf",
            use_container_width=True
        )
        st.success(f"Ready! Click Download PDF above.")


# ==============================================================
# SETTINGS TAB
# ==============================================================
with tab_settings:
    st.subheader("Baby Info")

    baby_name = st.text_input("Baby's name", value=config.get("baby_name", ""))
    parent_contact = st.text_input("Parent contact (phone/email)", value=config.get("parent_contact", ""))

    st.subheader("Feeding Instructions")
    st.caption("These print on every sheet. One instruction per line.")

    instructions_text = st.text_area(
        "Feeding instructions",
        value="\n".join(config.get("feeding_instructions", [])),
        height=150,
        label_visibility="collapsed"
    )

    if st.button("Save Settings", type="primary"):
        instructions = [line.strip() for line in instructions_text.splitlines() if line.strip()]
        new_config = {
            "baby_name": baby_name,
            "parent_contact": parent_contact,
            "feeding_instructions": instructions
        }
        save_config(new_config)
        config.update(new_config)
        st.success("Settings saved!")
