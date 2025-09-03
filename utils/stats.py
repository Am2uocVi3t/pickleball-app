# utils/stats.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.member import load_members
from utils.gsheets import load_sheet  # load từ Google Sheets

def get_stats(df_matches, members_df):
    if df_matches.empty:
        return pd.DataFrame(), 0

    # Tạo map giá của hội viên
    gia_map = dict(zip(members_df["Tên"], members_df["Giá thua"]))

    rows = []
    for _, row in df_matches.iterrows():
        ngay = row["Ngày"]
        ghi_chu = row.get("Ghi chú", "")
        gia = int(row.get("Giá", -1))
        names = [n.strip() for n in row["Cặp thua"].replace(",", " ").split() if n.strip()]
        for name in names:
            fee = gia if gia > 0 else gia_map.get(name, 5000)
            rows.append({
                "Tên": name,
                "Số trận thua": 1,
                "Giá": fee,
                "Ngày": ngay,
                "Ghi chú": ghi_chu
            })

    df = pd.DataFrame(rows)
    df_stats = df.groupby("Tên", as_index=False).agg({
        "Số trận thua": "sum",
        "Giá": "first"
    })
    df_stats["Tổng tiền"] = df_stats["Số trận thua"] * df_stats["Giá"]

    total = int(pd.to_numeric(df_stats["Tổng tiền"], errors="coerce").fillna(0).sum())
    return df_stats, total, df  # trả cả df gốc để lấy ghi chú theo tháng

def show_stats_page():
    st.subheader("📊 Bảng thống kê")

    df_matches = load_sheet("matches")
    if df_matches.empty:
        st.info("Chưa có dữ liệu.")
        return

    df_matches["Ngày_dt"] = pd.to_datetime(df_matches["Ngày"], format="%d/%m/%Y", errors="coerce")

    # Chọn tháng/năm
    months = list(range(1,13))
    month = st.selectbox("Chọn tháng", months, index=pd.Timestamp.now().month-1)
    years = sorted(df_matches["Ngày_dt"].dropna().dt.year.unique())
    year = st.selectbox("Chọn năm", years, index=0)

    # Lọc theo tháng/năm
    df_filtered = df_matches[
        (df_matches["Ngày_dt"].dt.month == month) &
        (df_matches["Ngày_dt"].dt.year == year)
    ]

    members_df = load_sheet("members")
    df_stats, total, df_for_notes = get_stats(df_filtered, members_df)

    if df_stats.empty:
        st.info(f"Không có dữ liệu cho {month}/{year}.")
        return

    st.dataframe(df_stats, use_container_width=True)
    st.markdown(f"### 💰 Tổng thu: **{total:,}** VND")

    # Lấy ghi chú theo tháng (1 ngày 1 ghi chú)
    notes = {}
    for _, row in df_for_notes.iterrows():
        note = str(row.get("Ghi chú","")).strip()
        if note:
            notes[row["Ngày"]] = note

    if notes:
        st.markdown("### 📝 Các ghi chú trong tháng:")
        for ngay, note in sorted(notes.items()):
            st.markdown(f"{ngay}: {note}")

    # Biểu đồ
    member_names = set(members_df["Tên"].astype(str).str.strip().tolist())
    colors = ["#1f77b4" if name in member_names else "#ff7f0e" for name in df_stats["Tên"]]

    fig, ax = plt.subplots()
    df_stats = df_stats.sort_values("Tổng tiền", ascending=False)
    ax.bar(df_stats["Tên"], df_stats["Tổng tiền"], color=colors)
    ax.set_ylabel("Tổng tiền (VND)")
    ax.set_title("Thống kê thu theo từng người")
    ax.set_xticklabels(df_stats["Tên"], rotation=45, ha="right")
    ax.grid(True, axis="y")
    st.pyplot(fig)
