import streamlit as st
import pandas as pd
import os
from utils.member import load_members   
from utils.gsheets import load_sheet
import datetime

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

def get_detail_df(df_matches, start_date, end_date):
    if df_matches.empty:
        return pd.DataFrame()

    members_df = load_members()
    gia_map = dict(zip(members_df["Tên"], members_df["Giá thua"]))

    df_matches["Ngày_dt"] = pd.to_datetime(df_matches["Ngày"], format="%d/%m/%Y", errors="coerce")
    df_filtered = df_matches[
        (df_matches["Ngày_dt"] >= start_date) &
        (df_matches["Ngày_dt"] <= end_date)
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

    # # Chọn khoảng ngày bằng text_input với định dạng dd/mm/yyyy
    # min_date = pd.to_datetime(df_matches["Ngày"], format="%d/%m/%Y", errors="coerce").min()
    # max_date = pd.to_datetime(df_matches["Ngày"], format="%d/%m/%Y", errors="coerce").max()

    today = datetime.datetime.today()
    default_start = today.replace(day=1).strftime("%d/%m/%Y")  # Đầu tháng này
    default_end = today.strftime("%d/%m/%Y")                   # Hôm nay

    col1, col2 = st.columns(2)
    with col1:
        start_str = st.text_input("Từ ngày", default_start)
    with col2:
        end_str = st.text_input("Đến ngày", default_end)

    # Kiểm tra và chuyển đổi
    try:
        start_date = pd.to_datetime(start_str, format="%d/%m/%Y")
        end_date = pd.to_datetime(end_str, format="%d/%m/%Y")
    except Exception:
        st.error("Vui lòng nhập đúng định dạng dd/mm/yyyy.")
        return


    df_detail = get_detail_df(df_matches, pd.to_datetime(start_date), pd.to_datetime(end_date))
    if df_detail.empty:
        st.info(f"Không có dữ liệu trong khoảng {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}.")
        return
    st.dataframe(df_detail.reset_index(drop=True), use_container_width=True, hide_index=True)

    # --- Tổng thu ---
    st.subheader("Tổng tiền từng người")
    df_simple = (
        df_detail.groupby(["Ngày", "Tên"], as_index=False)["Tổng tiền"].sum()
        .sort_values(["Ngày", "Tên"])
        .reset_index(drop=True)
    )
    st.dataframe(df_simple.reset_index(drop=True), use_container_width=True, hide_index=True)

     # --- Quỹ (Funds) ---
    st.subheader("Danh sách thu chi quỹ")
    df_funds = load_funds()
    if df_funds.empty:
        st.info("Chưa có dữ liệu quỹ.")
    else:
        # Lọc theo khoảng ngày
        df_funds["Ngày_dt"] = pd.to_datetime(df_funds["Ngày"], format="%d/%m/%Y", errors="coerce")
        df_f_month = df_funds[
            (df_funds["Ngày_dt"] >= pd.to_datetime(start_date)) &
            (df_funds["Ngày_dt"] <= pd.to_datetime(end_date))
        ]
        if df_f_month.empty:
            st.info("Không có dữ liệu trích thu trong tháng này.")
        else:
            df_f_month = df_f_month.copy()
            df_f_month["Quỹ"] = df_f_month["Giá"].apply(lambda x: f"{x:+,}")
            st.dataframe(df_f_month[["Ngày", "Ghi chú", "Quỹ"]].reset_index(drop=True), use_container_width=True, hide_index=True)