import streamlit as st
import pandas as pd
import os
from utils.member import load_members   
from utils.gsheets import load_sheet


def load_matches():
    # Đọc từ Google Sheets
    df = load_sheet("matches")
    if df.empty:
        df = pd.DataFrame(columns=["Ngày","Trận thua","Giá"])

    # Chuẩn hóa dữ liệu
    df = df.replace("nan", "", regex=False).fillna("")
    df["Ngày"] = df["Ngày"].astype(str).str.strip()
    df["Trận thua"] = df["Trận thua"].astype(str).str.strip()

    if "Giá" not in df.columns:
        df["Giá"] = -1
    df["Giá"] = df["Giá"].fillna(-1).astype(int)
    return df

def load_funds():
    df = load_sheet("funds")
    if df.empty:
        df = pd.DataFrame(columns=["Ngày", "Ghi chú", "Giá"])
    df = df.fillna("")
    df["Ngày"] = df["Ngày"].astype(str).str.strip()
    df["Ghi chú"] = df["Ghi chú"].astype(str).str.strip()
    df["Giá"] = pd.to_numeric(df["Giá"], errors="coerce").fillna(0).astype(int)
    return df

def get_detail_df(df_matches, month, year):
    if df_matches.empty:
        return pd.DataFrame()

    members_df = load_members()
    gia_map = dict(zip(members_df["Tên"], members_df["Giá thua"]))

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
        pair = row["Trận thua"]
        gia = int(row.get("Giá", -1))

        names = [n.strip() for n in pair.split() if n.strip()]
        for name in names:
            fee = gia if gia > 0 else int(gia_map.get(name, 5000))
            records.append({
                "Ngày": ngay,
                "Tên": name,
                "Số trận thua": 1,
                "Giá": fee
            })
    if not records:
        return pd.DataFrame()
    
    df_detail = pd.DataFrame(records)
    df_detail = df_detail.groupby(["Ngày","Tên","Giá"], as_index=False).agg({
        "Số trận thua": "sum",
    }).sort_values(["Ngày", "Tên", "Giá"]).reset_index(drop=True)

    df_detail["Tổng tiền"] = df_detail["Số trận thua"] * df_detail["Giá"]
    return df_detail


def show_detail_page():
    st.markdown("<h2 style='text-align: center;'>BẢNG CHI TIẾT TỪNG NGÀY</h2>", unsafe_allow_html=True)

    st.subheader("Bảng chi tiết từng giá")
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

    # --- Tổng thu ---
    st.subheader("Tổng tiền từng người")
    df_simple = (
        df_detail.groupby(["Ngày", "Tên"], as_index=False)["Tổng tiền"].sum()
        .sort_values(["Ngày", "Tên"])
        .reset_index(drop=True)
    )
    st.dataframe(df_simple, use_container_width=True)

     # --- Quỹ (Funds) ---
    st.subheader("Danh sách thu chi quỹ")
    df_funds = load_funds()
    if df_funds.empty:
        st.info("Chưa có dữ liệu quỹ.")
    else:
        # Lọc theo tháng/năm
        df_funds["Ngày_dt"] = pd.to_datetime(df_funds["Ngày"], format="%d/%m/%Y", errors="coerce")
        df_f_month = df_funds[
            (df_funds["Ngày_dt"].dt.month == month) &
            (df_funds["Ngày_dt"].dt.year == year)
        ]
        if df_f_month.empty:
            st.info("Không có dữ liệu trích thu trong tháng này.")
        else:
            df_f_month = df_f_month.copy()
            df_f_month["Quỹ"] = df_f_month["Giá"].apply(lambda x: f"{x:+,} VNĐ")
            st.dataframe(df_f_month[["Ngày", "Ghi chú", "Quỹ"]], use_container_width=True)