# utils/stats.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import datetime
# from utils.member import load_members
from utils.gsheets import load_sheet
# from utils.input_info import load_sheet

def get_stats(df_matches, members_df):
    if df_matches.empty:
        return pd.DataFrame(), 0
    
    # Tạo map giá thua
    gia_map = dict(zip(members_df["Tên"], members_df["Giá thua"]))

    rows = []
    for _, row in df_matches.iterrows():
        ngay = row["Ngày"]
        gia = int(row.get("Giá", -1))

        # Đội thắng
        winners = [n.strip() for n in str(row["Đội thắng"]).replace(",", " ").split() if n.strip()]

        # Đội thua & kiểm tra ăn trắng
        doi_thua_raw = str(row["Đội thua"])
        if "(" in doi_thua_raw and ")" in doi_thua_raw:
            # Trường hợp ăn trắng: "Hạnh Thành (Ty Triều)"
            doi_thua, doi_an_trang = doi_thua_raw.split("(")
            doi_thua = [n.strip() for n in doi_thua.split() if n.strip()]
            doi_an_trang = doi_an_trang.replace(")", "").strip()
            doi_an_trang = [n.strip() for n in doi_an_trang.split() if n.strip()]
        else:
            doi_thua = [n.strip() for n in doi_thua_raw.replace(",", " ").split() if n.strip()]
            doi_an_trang = []

        # Đội thua: cộng tiền, nếu bị ăn trắng thì cộng gấp đôi
        for name in doi_thua:
            if gia > 0:
                fee = int(gia)
            else:
                fee = int(gia_map.get(name, 5000))
            if doi_an_trang:
                total_fee = fee * 2
            else:
                total_fee = fee
            rows.append({
                "Tên": name,
                "Số trận thắng": 0,
                "Số trận thua": 1,
                "Tổng tiền": total_fee,
                "Ngày": ngay
            })

        # Đội thắng: nếu ăn trắng thì có thể trừ tiền (tuỳ quy định, ví dụ trừ lệ phí)
        for name in winners:
            if gia > 0:
                fee = int(gia)
            else:
                fee = int(gia_map.get(name, 5000))
            if name in doi_an_trang:
                # Ăn trắng: trừ tiền
                rows.append({
                    "Tên": name,
                    "Số trận thắng": 1,
                    "Số trận thua": 0,
                    "Tổng tiền": -fee,
                    "Ngày": ngay
                })
            else:
                # Thắng bình thường: không cộng/trừ tiền
                rows.append({
                    "Tên": name,
                    "Số trận thắng": 1,
                    "Số trận thua": 0,
                    "Tổng tiền": 0,
                    "Ngày": ngay
                })


    df = pd.DataFrame(rows)
    df["Số trận thua"] = pd.to_numeric(df["Số trận thua"], errors="coerce").fillna(0).astype(int)
    df["Tổng tiền"] = pd.to_numeric(df["Tổng tiền"], errors="coerce").fillna(0).astype(int)
    df["Số trận thắng"] = pd.to_numeric(df["Số trận thắng"], errors="coerce").fillna(0).astype(int)

    # Gom theo tên
    df_stats = df.groupby("Tên", as_index=False).agg({
        "Số trận thua": "sum",
        "Số trận thắng": "sum",
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
    if df_matches is None or df_matches.empty:
        df_matches = pd.DataFrame(columns=["Ngày", "Đội thắng", "Đội thua", "Giá"])
    else:
        df_matches["Ngày"] = df_matches["Ngày"].astype(str)
    df_matches["Ngày_dt"] = pd.to_datetime(df_matches["Ngày"], format="%d/%m/%Y", errors="coerce")

    if df_funds is None:
        df_funds = pd.DataFrame(columns=["Ngày", "Ghi chú", "Giá"])
    df_funds["Ngày"] = df_funds.get("Ngày", "").astype(str)
    df_funds["Ngày_dt"] = pd.to_datetime(df_funds["Ngày"], format="%d/%m/%Y", errors="coerce")

    # Chọn khoảng ngày
    today = datetime.datetime.today()
    default_start = today.replace(day=1).strftime("%d/%m/%Y")  # Đầu tháng này
    default_end = today.strftime("%d/%m/%Y")                   # Hôm nay

    # Dùng session_state để lưu bộ lọc
    if "stats_filter" not in st.session_state:
        st.session_state.stats_filter = {
            "start_str": default_start,
            "end_str": default_end
        }

    with st.form("stats_filter_form"):
        col1, col2 = st.columns(2)
        with col1:
            start_str = st.text_input("Từ ngày", st.session_state.stats_filter["start_str"])
        with col2:
            end_str = st.text_input("Đến ngày", st.session_state.stats_filter["end_str"])
        
        filter_submit = st.form_submit_button("Lọc dữ liệu")
        
        if filter_submit:
            st.session_state.stats_filter = {
                "start_str": start_str,
                "end_str": end_str
            }
    
    # Lấy giá trị từ session_state
    start_str = st.session_state.stats_filter["start_str"]
    end_str = st.session_state.stats_filter["end_str"]

    # Kiểm tra và chuyển đổi
    try:
        start_date = pd.to_datetime(start_str, format="%d/%m/%Y")
        end_date = pd.to_datetime(end_str, format="%d/%m/%Y")
    except Exception:
        st.error("Vui lòng nhập đúng định dạng dd/mm/yyyy.")
        return
    
    # Lọc matches theo khoảng ngày
    if not df_matches.empty:
        df_filtered = df_matches[
            (df_matches["Ngày_dt"] >= start_date) &
            (df_matches["Ngày_dt"] <= end_date)
        ].copy()
    else:
        df_filtered = pd.DataFrame(columns=df_matches.columns)

    # Lọc funds theo khoảng ngày
    if not df_funds.empty:
        df_f_month = df_funds[
            (df_funds["Ngày_dt"] >= start_date) &
            (df_funds["Ngày_dt"] <= end_date)
        ]
    else:
        df_f_month = pd.DataFrame(columns=df_funds.columns)

    # Lấy thống kê từ matches (get_stats trả về df_stats, total)
    members_df = load_sheet("members") if load_sheet is not None else pd.DataFrame()
    if not df_filtered.empty:
        df_stats, total = get_stats(df_filtered, members_df)
    else:
        df_stats, total = pd.DataFrame(), 0

    if not df_stats.empty:
    # Tô màu cho cột Số trận thắng (xanh) và Số trận thua (đỏ nhạt)
        def highlight_stats(val, col_name):
            if col_name == "Số trận thắng":
                color = "#d4edda"  # xanh nhạt
            elif col_name == "Số trận thua":
                color = "#f8d7da"  # đỏ nhạt
            else:
                color = ""
            return f"background-color: {color}"

        styled_df = df_stats.style.apply(
            lambda col: [highlight_stats(v, col.name) for v in col],
            axis=0
        ).format({
            "Tổng tiền": lambda x: f"{x:+,}"
        })

        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        # st.dataframe(df_stats.reset_index(drop=True), use_container_width=True, hide_index=True)
        # st.markdown(f"###  Tổng tiền trận thua: **{total:,}**")
    else:
        st.info(f"Không có dữ liệu trận thua cho khoảng {start_str} - {end_str}.")
        total = 0

    # --- Funds ---
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
        st.info("Không có dữ liệu thu chi trong khoảng này.")


    # --- Tổng kết ---
    final_total = total + total_funds
    st.markdown("###  Tổng kết cuối tháng")
    st.write(f"- Tổng tiền thua các trận: **{total:,}**")
    st.write(f"- Tổng thu chi: **{total_funds:+,}**")
    color = "#009900" if final_total >= 0 else "#FF0000"
    st.markdown(
        f"<h5 style='text-align: center; color: {color}; font-weight: bold;'>TỔNG CỘNG: {final_total:,}</h5>", 
        unsafe_allow_html=True
    )

    
    # # Biểu đồ
    # # member_names = set(members_df["Tên"].astype(str).str.strip().tolist())
    # # colors = ["#1f77b4" if name in member_names else "#ff7f0e" for name in df_stats["Tên"]]
    # if not df_stats.empty:
    #     fig, ax = plt.subplots()
    #     df_stats = df_stats.sort_values("Tổng tiền", ascending=False)
    #     bars = ax.bar(df_stats["Tên"], df_stats["Tổng tiền"])

    #     # Hiển thị số trên mỗi cột
    #     for bar in bars:
    #         height = bar.get_height()
    #         ax.text(
    #             bar.get_x() + bar.get_width() / 2,
    #             height,
    #             f"{height:,}",       # format có dấu phẩy
    #             ha="center", va="bottom", fontsize=9
    #         )
    #     ax.set_ylabel("Tổng tiền (VND)")
    #     ax.set_title("Bảng xếp hạng")
        
    #     ax.set_xticks(range(len(df_stats["Tên"])))
    #     ax.set_xticklabels(df_stats["Tên"], rotation=0, ha="center")

    #     ax.grid(True, axis="y")
    #     st.pyplot(fig)

    # if not df_stats.empty:
    #     df_ratio = df_stats.copy()
    #     df_ratio["Tỉ lệ thua (%)"] = (
    #         df_ratio["Số trận thua"] * 100 /
    #         (df_ratio["Số trận thắng"] + df_ratio["Số trận thua"]).replace(0, 1)
    #     ).round(1)

    #     df_ratio = df_ratio.sort_values("Tỉ lệ thua (%)", ascending=False)

    #     fig2, ax2 = plt.subplots()
    #     bars2 = ax2.bar(df_ratio["Tên"], df_ratio["Tỉ lệ thua (%)"], color="orange")

    #     for bar in bars2:
    #         height = bar.get_height()
    #         ax2.text(bar.get_x() + bar.get_width()/2, height,
    #                 f"{height:.1f}%", ha="center", va="bottom", fontsize=9)

    #     ax2.set_ylabel("Tỉ lệ thua (%)")
    #     ax2.set_title("Tỉ lệ thua")
    #     ax2.set_xticks(range(len(df_ratio["Tên"])))
    #     ax2.set_xticklabels(df_ratio["Tên"], rotation=0, ha="center")
    #     ax2.grid(True, axis="y")
    #     st.pyplot(fig2)
