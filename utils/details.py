# utils/details.py
import streamlit as st
import pandas as pd
import os
from utils.member import load_members   # để lấy DS hội viên
from utils.gsheets import load_sheet


def load_matches():
    # Đọc từ Google Sheets
    df = load_sheet("matches")
    if df.empty:
        df = pd.DataFrame(columns=["Ngày","Cặp thua","Ghi chú","Giá"])

    # Chuẩn hóa dữ liệu
    df = df.replace("nan", "", regex=False).fillna("")
    df["Ngày"] = df["Ngày"].astype(str).str.strip()
    df["Cặp thua"] = df["Cặp thua"].astype(str).str.strip()
    df["Ghi chú"] = df["Ghi chú"].astype(str).str.strip()

    if "Giá" not in df.columns:
        df["Giá"] = -1
    df["Giá"] = df["Giá"].fillna(-1).astype(int)
    return df

def get_detail_df(df_matches, month, year):
    if df_matches.empty:
        return pd.DataFrame()

    # Load DS hội viên
    members_df = load_members()
    gia_map = dict(zip(members_df["Tên"], members_df["Giá thua"]))

    # Chuyển sang datetime để lọc tháng/năm
    df_matches["Ngày_dt"] = pd.to_datetime(df_matches["Ngày"], format="%d/%m/%Y", errors="coerce")
    df_filtered = df_matches[
        (df_matches["Ngày_dt"].dt.month == month) &
        (df_matches["Ngày_dt"].dt.year == year)
    ]
    if df_filtered.empty:
        return pd.DataFrame()

    records = []
    for _, row in df_filtered.iterrows():
        ngay = row["Ngày"]
        pair = row["Cặp thua"]
        ghi_chu = row.get("Ghi chú", "")
        gia = int(row.get("Giá", -1))

        # Tách tên trong cặp thua
        names = [n.strip() for n in pair.split() if n.strip()]
        for name in names:
            # Nếu không nhập giá override → lấy theo DS hội viên
            if gia <= 0:
                fee = gia_map.get(name, 5000)  # vãng lai = 5000
            else:
                fee = gia
            records.append({
                "Ngày": ngay,
                "Tên": name,
                "Số trận thua": 1,
                "Giá": fee,
                "Ghi chú": ghi_chu
            })

    df_detail = pd.DataFrame(records)
    df_detail = df_detail.groupby(["Ngày","Tên","Ghi chú"], as_index=False).agg({
        "Số trận thua": "sum",
        "Giá": "first"
    })

    # 👉 Thêm cột Tổng tiền
    df_detail["Tổng tiền"] = df_detail["Số trận thua"] * df_detail["Giá"]

    return df_detail


def show_detail_page():
    st.subheader("Bảng chi tiết")

    df_matches = load_matches()
    if df_matches.empty:
        st.info("Chưa có dữ liệu trận thua nào.")
        return

    months = list(range(1,13))
    month = st.selectbox("Chọn tháng", months, index=pd.Timestamp.now().month-1)
    years = sorted(df_matches["Ngày"].apply(lambda x: int(x.split("/")[2].strip())).unique())
    year = st.selectbox("Chọn năm", years, index=0)

    df_detail = get_detail_df(df_matches, month, year)
    if df_detail.empty:
        st.info(f"Không có dữ liệu cho {month}/{year}.")
        return

    st.dataframe(df_detail, use_container_width=True)
