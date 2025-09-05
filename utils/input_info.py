# utils/input_info.py
import streamlit as st
import pandas as pd
import os
# from utils.member import load_members
from utils.gsheets import load_sheet, save_sheet

FUND_SHEET = "funds"
SHEET_NAME = "matches"


# -------- Matches ----------
def load_matches():
    df = load_sheet(SHEET_NAME)
    if df.empty:
        df = pd.DataFrame(columns=["Ngày", "Trận thua", "Giá"])
    df = df.replace("nan", "", regex=False).fillna("")
    df["Ngày"] = df["Ngày"].astype(str).str.strip()
    df["Trận thua"] = df["Trận thua"].astype(str).str.strip()
    df["Giá"] = pd.to_numeric(df["Giá"], errors="coerce").fillna(-1).astype(int)
    return df

def save_matches(df: pd.DataFrame):
    save_sheet(SHEET_NAME, df)


# -------- Funds ----------
def load_funds():
    df = load_sheet(FUND_SHEET)
    if df.empty:
        df = pd.DataFrame(columns=["Ngày", "Ghi chú", "Giá"])
    df = df.fillna("")
    df["Ngày"] = df["Ngày"].astype(str).str.strip()
    df["Ghi chú"] = df["Ghi chú"].astype(str).str.strip()
    df["Giá"] = pd.to_numeric(df["Giá"], errors="coerce").fillna(0).astype(int)
    return df

def save_funds(df: pd.DataFrame):
    save_sheet(FUND_SHEET, df)


# -------- UI ----------
def show_match_page():
    st.markdown("<h2 style='text-align: center;'>BẢNG NHẬP THÔNG TIN</h2>", unsafe_allow_html=True)
    
    st.subheader("Thông tin trận thua")
    # Chọn ngày
    ngay_chon = st.date_input("Chọn ngày", format="DD/MM/YYYY")

    # Form nhập
    with st.form("match_form", clear_on_submit=True):
        tran_thua = st.text_input("Trận thua")
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
                "Trận thua": " ".join(name),
                "Giá": fee
                })

            df_all = load_matches()
            df_all = pd.concat([df_all, pd.DataFrame(new_rows)], ignore_index=True)
            save_matches(df_all)
            st.success(f"Đã lưu {len(items)} trận thua (ngày {ngay_str}).")



    # Hiển thị danh sách trận thua theo ngày
    st.subheader("Danh sách trận thua")
    df = load_matches()
    if df.empty:
        st.info("Chưa có dữ liệu.")
        return

    ngay_str = ngay_chon.strftime("%d/%m/%Y")
    df_filtered = df[df["Ngày"] == ngay_str]

    if df_filtered.empty:
        st.info("Không có trận thua cho ngày đã chọn.")
    else:
        # Tạo DataFrame gọn hơn
        df_show = df_filtered.copy()
        # st.dataframe(df_show[["Ngày", "Trận thua", "Giá"]], use_container_width=True)
        df_show["Giá mới/người"] = df_show["Giá"].apply(lambda x: f"{x:,} VNĐ" if x > 0 else "")
        st.dataframe(df_show[["Ngày", "Trận thua", "Giá mới/người"]], use_container_width=True)

        st.subheader("Xóa trận")
        if st.button("Xoá tất cả trong ngày", key=f"delete_all_{ngay_str}"):
            df_all = load_matches()
            df_all = df_all[df_all["Ngày"] != ngay_str].reset_index(drop=True)
            save_matches(df_all)
            st.success(f"Đã xoá toàn bộ dữ liệu ngày {ngay_str}.")
            st.rerun()

        # Liệt kê từng dòng để xoá riêng
        for idx, row in df_filtered.iterrows():
            col1, col2 = st.columns([6,1])
            col1.write(f"{row['Ngày']} - {row['Trận thua']}")
            if col2.button("❌", key=f"del_{ngay_str}_{idx}"):
                df_all = load_matches()
                if idx in df_all.index:
                    df_all = df_all.drop(idx).reset_index(drop=True)
                    save_matches(df_all)
                    st.success("Đã xóa 1 dòng.")
                    st.rerun()

    # -------- Funds (Trích/Thu) ----------
    st.subheader("Thu chi quỹ (Nếu có)")

    with st.form("fund_form", clear_on_submit=True):
        note = st.text_input("Ghi chú")
        fund_value = st.number_input("Số tiền", step=1000, value=0)
        fund_submit = st.form_submit_button("Lưu")

    if fund_submit:
        if fund_value != 0: 
            df_funds = load_funds()
            new_row = pd.DataFrame([{"Ngày": ngay_str, "Ghi chú": note, "Giá": int(fund_value)}])
            df_funds = pd.concat([df_funds, new_row], ignore_index=True)
            save_funds(df_funds)
            st.success(f"Đã lưu vào quỹ {'thu' if fund_value>0 else 'chi'} {abs(fund_value):,} VNĐ")

    # -------- Danh sách quỹ ----------
    st.subheader("Danh sách thu chi quỹ")
    df_funds = load_funds()
    df_f_today = df_funds[df_funds["Ngày"] == ngay_str]

    if df_f_today.empty:
        st.info("Không có thu chi cho ngày này.")
    else:
        df_f_today = df_f_today.copy()
        df_f_today["Giá"] = df_f_today["Giá"].apply(lambda x: f"{x:+,} VNĐ")
        st.dataframe(df_f_today[["Ngày", "Ghi chú", "Giá"]], use_container_width=True)

        # Nút xoá tất cả trong ngày
        if st.button("Xoá tất cả quỹ trong ngày", key=f"del_fund_all_{ngay_str}"):
            df_all = load_funds()
            df_all = df_all[df_all["Ngày"] != ngay_str].reset_index(drop=True)
            save_funds(df_all)
            st.success(f"Đã xoá toàn bộ thu chi quỹ ngày {ngay_str}.")
            st.rerun()

        # Nút xoá từng dòng
        for idx, row in df_f_today.iterrows():
            col1, col2 = st.columns([6,1])
            col1.write(f"{row['Ngày']} - {row['Ghi chú']} ({row['Giá']})")
            if st.button("❌", key=f"del_fund_{ngay_str}_{idx}"):
                df_all = load_funds()
                if idx in df_all.index:
                    df_all = df_all.drop(idx).reset_index(drop=True)
                    save_funds(df_all)
                    st.success("Đã xoá 1 dòng quỹ.")
                    st.rerun()