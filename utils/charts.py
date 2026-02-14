# charts.py
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import datetime
from utils.gsheets import load_sheet
from utils.stats import get_stats
import matplotlib.patheffects as path_effects



def show_charts_page():
    st.markdown("<h2 style='text-align: center;'>BIỂU ĐỒ THỐNG KÊ</h2>", unsafe_allow_html=True)

    df_matches = load_sheet("matches")
    df_funds = load_sheet("funds")
    members_df = load_sheet("members")

    if df_matches is None or df_matches.empty:
        st.info("Chưa có dữ liệu trận để vẽ biểu đồ.")
        return

    # Chuẩn hoá cột ngày
    df_matches["Ngày"] = df_matches["Ngày"].astype(str)
    df_matches["Ngày_dt"] = pd.to_datetime(df_matches["Ngày"], format="%d/%m/%Y", errors="coerce")

    # --- Bộ lọc ngày ---
    today = datetime.datetime.today()
    default_start = today.replace(day=1).strftime("%d/%m/%Y")  # Đầu tháng này
    default_end = today.strftime("%d/%m/%Y")                   # Hôm nay

    # Dùng session_state để lưu bộ lọc
    if "chart_filter" not in st.session_state:
        st.session_state.chart_filter = {
            "start_str": default_start,
            "end_str": default_end
        }

    with st.form("chart_filter_form"):
        col1, col2 = st.columns(2)
        with col1:
            start_str = st.text_input("Từ ngày", st.session_state.chart_filter["start_str"])
        with col2:
            end_str = st.text_input("Đến ngày", st.session_state.chart_filter["end_str"])
        
        filter_submit = st.form_submit_button("Lọc dữ liệu")
        
        if filter_submit:
            st.session_state.chart_filter = {
                "start_str": start_str,
                "end_str": end_str
            }
    
    # Lấy giá trị từ session_state
    start_str = st.session_state.chart_filter["start_str"]
    end_str = st.session_state.chart_filter["end_str"]

    # Kiểm tra và chuyển đổi
    try:
        start_date = pd.to_datetime(start_str, format="%d/%m/%Y")
        end_date = pd.to_datetime(end_str, format="%d/%m/%Y")
    except Exception:
        st.error("Vui lòng nhập đúng định dạng dd/mm/yyyy.")
        return

    # Lọc dữ liệu
    df_filtered = df_matches[
        (df_matches["Ngày_dt"] >= start_date) &
        (df_matches["Ngày_dt"] <= end_date)
    ]

    if df_filtered.empty:
        st.warning("Không có dữ liệu trận trong khoảng này.")
        return

    # --- Tính stats ---
    df_stats, _ = get_stats(df_filtered, members_df)

    if df_stats.empty:
        st.info("Không có thống kê để vẽ biểu đồ.")
        return

    df_stats = df_stats.sort_values("Tổng tiền", ascending=False)

    # ================================================================
    #  BIỂU ĐỒ 1 — Leaderboard tổng tiền
    # ================================================================
    st.subheader("Biểu đồ tổng tiền")

    fig1, ax1 = plt.subplots()
    bars = ax1.bar(df_stats["Tên"], df_stats["Tổng tiền"])

    for bar in bars:
        height = bar.get_height()
        ax1.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:,}",
            ha="center", va="bottom", fontsize=9
        )

    ax1.set_ylabel("Tổng tiền (VND)")
    # ax1.set_title(f"Biểu đồ từ {start_str} đến {end_str}")
    ax1.set_xticks(range(len(df_stats["Tên"])))
    ax1.set_xticklabels(df_stats["Tên"], rotation=0)
    ax1.grid(True, axis="y")

    st.pyplot(fig1)

    # ================================================================
    #  BIỂU ĐỒ 2 — Tỉ lệ thua (%)
    # ================================================================
    st.subheader("Biểu đồ tỉ lệ thua")

    df_ratio = df_stats.copy()
    df_ratio["Tỉ lệ thua (%)"] = (
        df_ratio["Số trận thua"] * 100 /
        (df_ratio["Số trận thắng"] + df_ratio["Số trận thua"]).replace(0, 1)
    ).round(1)

    df_ratio = df_ratio.sort_values("Tỉ lệ thua (%)", ascending=False)

    fig2, ax2 = plt.subplots()
    bars2 = ax2.bar(df_ratio["Tên"], df_ratio["Tỉ lệ thua (%)"], color="orange")

    for bar in bars2:
        height = bar.get_height()
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            height,
            f"{height:.1f}%",
            ha="center", va="bottom", fontsize=9
        )

    ax2.set_ylabel("Tỉ lệ thua (%)")
    # ax2.set_title(f"Biểu đồ từ {start_str} đến {end_str}")
    ax2.set_xticks(range(len(df_ratio["Tên"])))
    ax2.set_xticklabels(df_ratio["Tên"], rotation=0)
    ax2.grid(True, axis="y")

    st.pyplot(fig2)

    # ================================================================
    #  BIỂU ĐỒ 3 — Heatmap tỉ lệ thua theo cặp (sửa: tính cả đội thắng)
    # ================================================================
    st.subheader("Biểu đồ tỉ lệ thua các cặp")

    def parse_team_names(team_raw):
        """Những chỗ trước bạn dùng .split() đơn giản — giữ nguyên cách làm nhưng loại bỏ ký tự ngoặc và dấu phẩy."""
        if pd.isna(team_raw):
            return []
        s = str(team_raw)
        # Thay , ( ) bằng khoảng trắng rồi split — phù hợp với format hiện tại của bạn
        s = s.replace(",", " ").replace("(", " ").replace(")", " ")
        names = [t.strip() for t in s.split() if t.strip()]
        return names

    # Danh sách người chơi từ df_stats
    member_list = sorted(df_stats["Tên"].tolist())
    idx_map = {name: i for i, name in enumerate(member_list)}
    n = len(member_list)

    # Ma trận: số trận thua chung và tổng trận cùng xuất hiện trong 1 đội (thắng hoặc thua)
    pair_loss = [[0]*n for _ in range(n)]
    pair_total = [[0]*n for _ in range(n)]

    for _, row in df_filtered.iterrows():
        winners = parse_team_names(row.get("Đội thắng", ""))
        losers = parse_team_names(row.get("Đội thua", ""))

        # --- Cập nhật pair_total cho đội thắng (nếu 2 người cùng 1 đội thắng, hoặc 1 người) ---
        if winners:
            for a in winners:
                if a in idx_map:
                    ia = idx_map[a]
                    for b in winners:
                        if b in idx_map:
                            ib = idx_map[b]
                            pair_total[ia][ib] += 1

        # --- Cập nhật pair_total cho đội thua ---
        if losers:
            for a in losers:
                if a in idx_map:
                    ia = idx_map[a]
                    for b in losers:
                        if b in idx_map:
                            ib = idx_map[b]
                            pair_total[ia][ib] += 1

        # --- Cập nhật pair_loss: chỉ khi họ là đội thua chung ---
        if len(losers) == 2:
            a, b = losers
            if a in idx_map and b in idx_map:
                ia, ib = idx_map[a], idx_map[b]
                pair_loss[ia][ib] += 1
                pair_loss[ib][ia] += 1
        elif len(losers) == 1:
            a = losers[0]
            if a in idx_map:
                ia = idx_map[a]
                pair_loss[ia][ia] += 1
                # pair_total[ia][ia] đã được cộng ở trên

    # Tính phần trăm thua: losses / total * 100
    percent_matrix = [
        [
            (pair_loss[i][j] / pair_total[i][j] * 100) if pair_total[i][j] > 0 else 0
            for j in range(n)
        ]
        for i in range(n)
    ]

    # Vẽ heatmap
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(percent_matrix, cmap="OrRd", vmin=0, vmax=100)

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(member_list, rotation=45, ha="right", fontsize=18)
    ax.set_yticklabels(member_list, fontsize=18)

    # Ghi text: "xx% (tổng trận)"
    for i in range(n):
        for j in range(n):
            pct = percent_matrix[i][j]
            losses = pair_loss[i][j]
            total = pair_total[i][j]
            if total > 0:
                txt = ax.text(
                    j, i,
                    f"{pct:.0f}%\n{losses}/{total} trận",
                    ha="center", va="center",
                    fontsize=12, color="black",
                )
                # txt.set_path_effects([
                # path_effects.Stroke(linewidth=1.5, foreground='white'),  # viền trắng
                # path_effects.Normal()
                # ])

    # ax.set_title(f"Biểu đồ từ {start_str} đến {end_str}", fontsize=20)
    fig.colorbar(im)
    st.pyplot(fig)
