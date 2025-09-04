# utils/input_info.py
import streamlit as st
import pandas as pd
import os
# from utils.member import load_members
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

def show_match_page():
    st.header("Nhập thông tin trận thua")

    # Chọn ngày
    ngay_chon = st.date_input("Chọn ngày", format="DD/MM/YYYY")

    # Form nhập
    with st.form("match_form", clear_on_submit=True):
        tran_thua = st.text_input("Trận thua (ngăn cách bằng dấu ,)")
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
            st.warning("Vui lòng nhập Trận thua!")
        else:
            ngay_str = ngay_chon.strftime("%d/%m/%Y")
            items = [item.strip() for item in tran_thua.split(",") if item.strip()]
            new_rows = []
            team = []
            for it in items:
                name = it.split()
                team.append(name)
            for name in team:
                num_player = len(name)
                if gia_input > 1:
                    fee = int(gia_input / num_player)
                else:
                    fee = -1
                    
                new_rows.append({
                "Ngày": ngay_str,
                "Cặp thua": " ".join(name),
                "Ghi chú": ghichu if ghichu.strip() else "",
                "Giá": fee
                })

            df_all = load_matches()
            df_all = pd.concat([df_all, pd.DataFrame(new_rows)], ignore_index=True)
            save_matches(df_all)
            st.success(f"Đã lưu {len(items)} trận thua (ngày {ngay_str}).")

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

    # Tạo DataFrame gọn hơn
    df_show = df_filtered.copy()
    df_show = df_show[["Ngày", "Cặp thua", "Ghi chú", "Giá"]]
    df_show["Giá/người"] = df_show["Giá"].apply(lambda x: f"{x:,} VNĐ" if x > 0 else "")

    st.dataframe(df_show[["Ngày", "Cặp thua", "Ghi chú", "Giá/người"]], use_container_width=True)

    # Toggle ẩn/hiện danh sách xoá
    if "show_delete_list" not in st.session_state:
        st.session_state.show_delete_list = False

    col1, col2 = st.columns([8, 2])
    with col1:
        st.subheader("Xoá trận")
    with col2:
        if st.button("👁", key="toggle_show_list"):
            st.session_state.show_delete_list = not st.session_state.show_delete_list

    if st.session_state.show_delete_list:
        # 👉 Nút xoá tất cả trước khi liệt kê từng dòng
        if st.button("Xoá tất cả trong ngày", key=f"delete_all_{ngay_str}"):
            df_all = load_matches()
            df_all = df_all[df_all["Ngày"] != ngay_str].reset_index(drop=True)
            save_matches(df_all)
            st.success(f"Đã xoá toàn bộ dữ liệu ngày {ngay_str}.")
            st.rerun()

        # Liệt kê từng dòng để xoá riêng
        for idx, row in df_filtered.iterrows():
            col1, col2 = st.columns([6,1])
            col1.write(f"{row['Ngày']} - {row['Cặp thua']}")
            if col2.button("❌", key=f"del_{ngay_str}_{idx}"):
                df_all = load_matches()
                if idx in df_all.index:
                    df_all = df_all.drop(idx).reset_index(drop=True)
                    save_matches(df_all)
                    st.success("Đã xóa 1 dòng.")
                    st.rerun()
