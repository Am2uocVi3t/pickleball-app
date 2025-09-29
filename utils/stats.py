# utils/stats.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
# from utils.member import load_members
from utils.gsheets import load_sheet
from utils.input_info import load_sheet

def get_stats(df_matches, members_df):
    if df_matches.empty:
        return pd.DataFrame(), 0
    
    # Tạo map giá thua
    gia_map = dict(zip(members_df["Tên"], members_df["Giá thua"]))

    rows = []
    for _, row in df_matches.iterrows():
        ngay = row["Ngày"]
        gia = int(row.get("Giá", -1))
        # Tách tên từ cột "Trận thua" (có thể ngăn cách bằng dấu phẩy hoặc khoảng trắng)
        names = [n.strip() for n in row["Trận thua"].replace(",", " ").split() if n.strip()]
        for name in names:
            fee = gia if gia > 0 else gia_map.get(name, 5000)
            rows.append({
                "Tên": name,
                "Số trận thua": 1,
                "Tổng tiền": fee,
                "Ngày": ngay
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
    return df_stats, total

def show_stats_page():
    st.markdown("<h2 style='text-align: center;'>BẢNG THỐNG KÊ THÁNG</h2>", unsafe_allow_html=True)

    st.subheader("Bảng thống kê")
    df_matches = load_sheet("matches")
    df_funds = load_sheet("funds")

    # --- Matches ---
    if df_matches.empty and df_funds.empty:
        st.info("Chưa có dữ liệu.")
        return

    # Nếu cả hai rỗng -> không có dữ liệu
    if (df_matches is None or df_matches.empty) and (df_funds is None or df_funds.empty):
        st.info("Chưa có dữ liệu.")
        return

    # Chuẩn hoá cột Ngày và tạo cột Ngày_dt cho cả 2 bảng (an toàn ngay cả khi rỗng)
    if df_matches is None:
        df_matches = pd.DataFrame(columns=["Ngày", "Trận thua", "Giá"])
    df_matches["Ngày"] = df_matches.get("Ngày", "").astype(str)
    df_matches["Ngày_dt"] = pd.to_datetime(df_matches["Ngày"], format="%d/%m/%Y", errors="coerce")

    if df_funds is None:
        df_funds = pd.DataFrame(columns=["Ngày", "Ghi chú", "Giá"])
    df_funds["Ngày"] = df_funds.get("Ngày", "").astype(str)
    df_funds["Ngày_dt"] = pd.to_datetime(df_funds["Ngày"], format="%d/%m/%Y", errors="coerce")

    # Chọn tháng/năm
    months = list(range(1,13))
    month = st.selectbox("Chọn tháng", months, index=pd.Timestamp.now().month-1)

    # Chọn tháng/năm dựa trên dữ liệu có sẵn ở matches hoặc funds
    years_matches = df_matches["Ngày_dt"].dropna().dt.year.unique().tolist() if not df_matches.empty else []
    years_funds = df_funds["Ngày_dt"].dropna().dt.year.unique().tolist() if not df_funds.empty else []
    years = sorted(set(years_matches) | set(years_funds))
    if not years:
        st.info("Chưa có dữ liệu năm nào để chọn.")
        return
    
    # Lọc theo tháng/năm
    year = st.selectbox("Chọn năm", years, index=max(0, len(years)-1))
    
    # Lọc matches theo tháng/năm (an toàn nếu df_matches rỗng)
    if not df_matches.empty:
        df_filtered = df_matches[
            (df_matches["Ngày_dt"].dt.month == month) &
            (df_matches["Ngày_dt"].dt.year == year)
        ].copy()
    else:
        df_filtered = pd.DataFrame(columns=df_matches.columns)

    # Lấy thống kê từ matches (get_stats trả về df_stats, total)
    members_df = load_sheet("members") if load_sheet is not None else pd.DataFrame()
    if not df_filtered.empty:
        df_stats, total = get_stats(df_filtered, members_df)
    else:
        df_stats, total = pd.DataFrame(), 0

    if not df_stats.empty:
        st.dataframe(df_stats.reset_index(drop=True), use_container_width=True, hide_index=True)
        # st.markdown(f"###  Tổng tiền trận thua: **{total:,}**")
    else:
        st.info(f"Không có dữ liệu trận thua cho {month}/{year}.")
        total = 0

    # --- Funds ---
    if not df_funds.empty:
        df_f_month = df_funds[
            (df_funds["Ngày_dt"].dt.month == month) &
            (df_funds["Ngày_dt"].dt.year == year)
        ]
        if not df_f_month.empty:
            st.subheader("Thu/Chi Quỹ")
            df_f_month = df_f_month.copy()
            df_f_month["Giá"] = pd.to_numeric(df_f_month["Giá"], errors="coerce").fillna(0).astype(int)
            df_f_month["Số tiền"] = df_f_month["Giá"].apply(lambda x: f"{x:+,}")
            df_manual = df_f_month[~df_f_month["Ghi chú"].str.startswith("Tổng thu quỹ tháng")]
            st.dataframe(df_manual[["Ngày", "Ghi chú", "Số tiền"]].reset_index(drop=True), use_container_width=True, hide_index=True)
            total_funds = df_manual["Giá"].sum()
        else:
            total_funds = 0
            st.info("Không có dữ liệu thu chi trong tháng này.")
    else:
        total_funds = 0

    # --- Tổng kết ---
    final_total = total + total_funds
    st.markdown("###  Tổng kết cuối tháng")
    st.write(f"- Tổng tiền thua các trận: **{total:,}**")
    st.write(f"- Tổng thu chi: **{total_funds:+,}**")
    st.markdown(f"<h2 style='text-align: center; color: #009900; font-weight: bold;'>TỔNG CỘNG: {final_total:,}</h2>", unsafe_allow_html=True)

    
    # Biểu đồ
    # member_names = set(members_df["Tên"].astype(str).str.strip().tolist())
    # colors = ["#1f77b4" if name in member_names else "#ff7f0e" for name in df_stats["Tên"]]
    if not df_stats.empty:
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
        
        ax.set_xticks(range(len(df_stats["Tên"])))
        ax.set_xticklabels(df_stats["Tên"], rotation=0, ha="center")

        ax.grid(True, axis="y")
        st.pyplot(fig)

