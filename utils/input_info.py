# utils/input_info.py
import streamlit as st
import pandas as pd
import os
from utils.member import load_members
from utils.gsheets import load_sheet, save_sheet


SHEET_NAME = "matches"

def load_matches():
    df = load_sheet(SHEET_NAME)
    if df.empty:
        df = pd.DataFrame(columns=["Ngày", "Cặp thua", "Ghi chú", "Giá"])
    df = df.replace("nan", "", regex=False).fillna("")
    df["Ngày"] = df["Ngày"].astype(str).str.strip()
    df["Cặp thua"] = df["Cặp thua"].astype(str).str.strip()
    df["Ghi chú"] = df["Ghi chú"].astype(str).str.strip()
    df["Giá"] = pd.to_numeric(df["Giá"], errors="coerce").fillna(-1).astype(int)
    return df

def save_matches(df: pd.DataFrame):
    save_sheet(SHEET_NAME, df)

def format_team_name(s: str) -> str:
    """Viết hoa chữ cái đầu mỗi từ, giữ nguyên phần còn lại."""
    parts = [p for p in s.strip().split() if p]
    res = []
    for w in parts:
        if len(w) == 0:
            continue
        res.append(w[0].upper() + w[1:])
    return " ".join(res)

def show_match_page():
    st.header("Nhập thông tin trận thua")

    # Chọn ngày
    ngay_chon = st.date_input("Chọn ngày", format="DD/MM/YYYY")

    # Form nhập
    with st.form("match_form", clear_on_submit=True):
        tran_thua = st.text_input("Cặp thua (ngăn cách bằng dấu ,)")
        ghichu = st.text_input("Ghi chú")
        gia_input = st.number_input(
            "Giá mới (nếu có giá khác hãy nhập giá 1 trận)",
            min_value=0,
            step=1000,
            value=0
        )
        submitted = st.form_submit_button("Lưu")

    if submitted:
        if not tran_thua or not tran_thua.strip():
            st.warning("Vui lòng nhập Cặp thua!")
        else:
            members_df = load_members()
            items = [item.strip() for item in tran_thua.split(",") if item.strip()]
            formatted = [format_team_name(it) for it in items]

            ngay_str = ngay_chon.strftime("%d/%m/%Y")
            new_rows = []
            for name in formatted:
                if gia_input > 0:
                    fee = int(gia_input / 2)
                else:
                    if name in members_df["Tên"].values:
                        fee = 5000
                    else:
                        fee = -1
                new_rows.append({
                    "Ngày": ngay_str,
                    "Cặp thua": name,
                    "Ghi chú": ghichu if ghichu.strip() else "",
                    "Giá": fee
                })

            df_all = load_matches()
            df_all = pd.concat([df_all, pd.DataFrame(new_rows)], ignore_index=True)
            save_matches(df_all)
            st.success(f"Đã lưu {len(formatted)} cặp thua (ngày {ngay_str}).")

    # Toggle ẩn/hiện danh sách
    if "show_list" not in st.session_state:
        st.session_state.show_list = True

    st.subheader("Danh sách trận thua")
    col_h, col_btn = st.columns([8,1])
    with col_h:
        st.write("")
    with col_btn:
        if st.button("👁"):
            st.session_state.show_list = not st.session_state.show_list

    if not st.session_state.show_list:
        return

    # Hiển thị danh sách trận thua theo ngày
    df = load_matches()
    if df.empty:
        st.info("Chưa có dữ liệu.")
        return

    ngay_str = ngay_chon.strftime("%d/%m/%Y")
    df_filtered = df[df["Ngày"] == ngay_str]

    if df_filtered.empty:
        st.info("Không có trận thua cho ngày đã chọn.")
        return

    # Header
    h1, h2, h3, h4, h5 = st.columns([2,3,3,3,1])
    h1.markdown("**Ngày**")
    h2.markdown("**Tên**")
    h3.markdown("**Ghi chú**")
    h4.markdown("**Giá**")
    h5.markdown("**Xóa**")

    for idx, row in df_filtered.iterrows():
        c1, c2, c3, c4, c5 = st.columns([2,3,3,3,1])
        c1.write(row["Ngày"])
        c2.write(row["Cặp thua"])
        c3.write(row["Ghi chú"] if row["Ghi chú"] else "")


        if int(row["Giá"]) > 0:
        # Nếu có giá nhập từ form thì hiển thị gấp đôi (giá cặp)
            c4.write(f"{int(row['Giá']) * 2:,} VNĐ")
        else:
            # Nếu không có giá override thì để trống
            c4.write("")

        if c5.button("❌", key=f"del_{idx}"):
            df_all = load_matches()
            if idx in df_all.index:
                df_all = df_all.drop(idx).reset_index(drop=True)
                save_matches(df_all)
                st.success("Đã xóa 1 dòng.")
                st.rerun()
                return
            else:
                st.warning("Không tìm thấy dòng để xóa.")
                return
