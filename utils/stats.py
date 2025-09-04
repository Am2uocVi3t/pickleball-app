# utils/stats.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.member import load_members
from utils.gsheets import load_sheet  # load từ Google Sheets

def get_stats(df_matches, members_df):
    if df_matches.empty:
        return pd.DataFrame(), 0, pd.DataFrame()
    
    # Tạo map giá thua
    gia_map = dict(zip(members_df["Tên"], members_df["Giá thua"]))

    rows = []
    for _, row in df_matches.iterrows():
        ngay = row["Ngày"]
        ghi_chu = row.get("Ghi chú", "")
        gia = int(row.get("Giá", -1))
        # Tách tên từ cột "Cặp thua" (có thể ngăn cách bằng dấu phẩy hoặc khoảng trắng)
        names = [n.strip() for n in row["Trận thua"].replace(",", " ").split() if n.strip()]
        for name in names:
            fee = gia if gia > 0 else gia_map.get(name, 5000)
            rows.append({
                "Tên": name,
                "Số trận thua": 1,
                "Tổng tiền": fee,
                "Ngày": ngay,
                "Ghi chú": ghi_chu
            })

    df = pd.DataFrame(rows)
    df["Số trận thua"] = pd.to_numeric(df["Số trận thua"], errors="coerce").fillna(0).astype(int)
    df["Tổng tiền"] = pd.to_numeric(df["Tổng tiền"], errors="coerce").fillna(0).astype(int)
    # Gom theo tên
    df_stats = df.groupby("Tên", as_index=False).agg({
        "Số trận thua": "sum",
        "Tổng tiền": "sum"
    })

    total = int(df_stats["Tổng tiền"].sum())
    return df_stats, total, df

def show_stats_page():
    st.subheader("Bảng thống kê")

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
    st.markdown(f"###  Tổng thu: **{total:,}** VND")

    # Lấy ghi chú theo tháng (1 ngày 1 ghi chú)
    notes = {}
    for _, row in df_for_notes.iterrows():
        note = str(row.get("Ghi chú","")).strip()
        if note:
            notes[row["Ngày"]] = note

    if notes:
        st.markdown("###  Các ghi chú trong tháng:")
        for ngay, note in sorted(notes.items()):
            st.markdown(f"{ngay}: {note}")

    # Biểu đồ
    # member_names = set(members_df["Tên"].astype(str).str.strip().tolist())
    # colors = ["#1f77b4" if name in member_names else "#ff7f0e" for name in df_stats["Tên"]]

    fig, ax = plt.subplots()
    df_stats = df_stats.sort_values("Tổng tiền", ascending=False)
    bars = ax.bar(df_stats["Tên"], df_stats["Tổng tiền"])

    # Hiển thị số trên mỗi cột
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:,}",       # format có dấu phẩy
            ha="center", va="bottom", fontsize=9
        )
    ax.set_ylabel("Tổng tiền (VND)")
    ax.set_title("Bảng xếp hạng")
    ax.set_xticklabels(df_stats["Tên"], rotation=0, ha="right")
    ax.grid(True, axis="y")
    st.pyplot(fig)
