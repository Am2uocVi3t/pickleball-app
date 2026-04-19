import streamlit as st
import pandas as pd
from utils.gsheets import load_sheet, save_sheet
from utils.input_info import load_matches
from utils.stats import get_stats
import datetime


FUND_SHEET = "funds"

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

def update_fund():
       # --- Lưu tổng tiền thua của tất cả các tháng vào quỹ ---
    df_funds = load_funds()
    df_matches = load_matches()
    members_df = load_sheet("members")

    # Chuyển đổi cột Ngày và chỉ giữ các dòng ngày hợp lệ để group
    df_matches["Ngày_dt"] = pd.to_datetime(df_matches["Ngày"], format="%d/%m/%Y", errors="coerce")
    df_matches_valid = df_matches.dropna(subset=["Ngày_dt"]).copy()
    if df_matches_valid.empty:
        return

    # Lấy tất cả (năm, tháng) có trận
    month_years = df_matches_valid.groupby(
        [df_matches_valid["Ngày_dt"].dt.year, df_matches_valid["Ngày_dt"].dt.month]
    )
    
    today = pd.Timestamp.now().normalize()
    for (y, m), group in month_years:
        df_stats, total = get_stats(group, members_df)
        if total == 0:  
            continue  # không có gì thì bỏ qua

        # Ép kiểu để tránh lỗi Timestamp khi y/m là kiểu không mong muốn
        y = int(y)
        m = int(m)

        # format ngày cuối tháng
        ngay_cuoi_thang = pd.Timestamp(year=y, month=m, day=1) + pd.offsets.MonthEnd(0)
        ngay_cuoi_str = ngay_cuoi_thang.strftime("%d/%m/%Y")
        
        # Ghi chú có cả tháng và năm để phân biệt
        ghi_chu = f"Tổng thu quỹ tháng {m}/{y}"

        # Kiểm tra xem tháng đã qua chưa
        if today > ngay_cuoi_thang:
            # Tháng đã qua - chuẩn hóa chỉ còn 1 dòng/tháng với ngày cuối tháng.
            # Tránh trường hợp trước đó có cùng "Ghi chú" nhưng ngày khác (vd: 28/03),
            # khi sang tháng mới bị thêm tiếp 31/03 thành 2 dòng.
            mask = df_funds["Ghi chú"] == ghi_chu
            df_funds = df_funds[~mask]
            new_row = pd.DataFrame([{
                "Ngày": ngay_cuoi_str,
                "Ghi chú": ghi_chu,
                "Giá": total
            }])
            df_funds = pd.concat([df_funds, new_row], ignore_index=True)
            continue  # bỏ qua update tháng cũ
        
        # Tháng hiện tại - cập nhật mỗi lần
        # Xoá dòng cũ nếu có (tìm theo ghi chú vì ngày có thể thay đổi)
        mask = df_funds["Ghi chú"] == ghi_chu
        df_funds = df_funds[~mask]
        
        # Thêm dòng mới với ngày hôm nay (để hiển thị khi lọc)
        ngay_hom_nay_str = today.strftime("%d/%m/%Y")
        new_row = pd.DataFrame([{
            "Ngày": ngay_hom_nay_str,
            "Ghi chú": ghi_chu,
            "Giá": total
        }])
        df_funds = pd.concat([df_funds, new_row], ignore_index=True)

    # Lưu lại tất cả
    save_funds(df_funds)

def show_monthly_summary():
    df = load_funds()
    if df.empty:
        st.info("Chưa có dữ liệu quỹ.")
        return
    
    # Chuyển đổi Ngày thành datetime
    df["Ngày_dt"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")
    df = df.dropna(subset=["Ngày_dt"])
    
    # Gom theo tháng/năm
    df["Tháng"] = df["Ngày_dt"].dt.month
    df["Năm"] = df["Ngày_dt"].dt.year
    monthly_summary = df.groupby(["Năm", "Tháng"])["Giá"].sum().reset_index()
    monthly_summary = monthly_summary.sort_values(["Năm", "Tháng"])
    
    # Format cột hiển thị
    monthly_summary["Tháng/Năm"] = monthly_summary["Tháng"].astype(str) + "/" + monthly_summary["Năm"].astype(str)
    monthly_summary["Tổng"] = monthly_summary["Giá"].apply(lambda x: f"{x:+,}")
    
    st.subheader("Tổng thu chi theo tháng")
    st.dataframe(monthly_summary[["Tháng/Năm", "Tổng"]].reset_index(drop=True), use_container_width=True, hide_index=True)


def show_fund_page():
    update_fund()
    st.markdown("<h2 style='text-align: center;'>QUỸ NHÓM</h2>", unsafe_allow_html=True)
    st.subheader("Nhập thông tin thu chi quỹ")
    ngay_chon = st.date_input("Chọn ngày", format="DD/MM/YYYY")
    ngay_str = ngay_chon.strftime("%d/%m/%Y")
    df = load_funds()
    if df.empty:
        st.info("Chưa có dữ liệu thu/chi quỹ.")
        return
    
    # -------- Funds (Trích/Thu) ----------
    st.subheader("Thu chi quỹ")

    with st.form("fund_form", clear_on_submit=True):
        note = st.text_input("Ghi chú")
        fund_value = st.number_input("Số tiền (+ : thu | - : chi)", step=1000, value=0)
        fund_submit = st.form_submit_button("Lưu")

    if fund_submit:
        if fund_value != 0: 
            df_funds = load_funds()
            new_row = pd.DataFrame([{"Ngày": ngay_str, "Ghi chú": note, "Giá": int(fund_value)}])
            df_funds = pd.concat([df_funds, new_row], ignore_index=True)
            save_funds(df_funds)
            st.success(f"Đã lưu vào quỹ {'thu' if fund_value>0 else 'chi'} {abs(fund_value):,}")

    # --- Lọc theo khoảng ngày ---
    df = load_funds()
    if df.empty:
        st.info("Chưa có dữ liệu thu/chi quỹ.")
        return

    st.subheader("Danh sách thu chi quỹ")

    # Tách cột ngày
    df["Ngày_dt"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")

    today = datetime.datetime.today()
    default_start = today.replace(day=1).strftime("%d/%m/%Y")  # Đầu tháng này
    default_end = today.strftime("%d/%m/%Y")                   # Hôm nay

    # Dùng session_state để lưu bộ lọc
    if "fund_filter" not in st.session_state:
        st.session_state.fund_filter = {
            "start_str": default_start,
            "end_str": default_end
        }

    with st.form("fund_filter_form"):
        col1, col2 = st.columns(2)
        with col1:
            start_str = st.text_input("Từ ngày", st.session_state.fund_filter["start_str"])
        with col2:
            end_str = st.text_input("Đến ngày", st.session_state.fund_filter["end_str"])
        
        filter_submit = st.form_submit_button("Lọc dữ liệu")
        
        if filter_submit:
            st.session_state.fund_filter = {
                "start_str": start_str,
                "end_str": end_str
            }
    
    # Lấy giá trị từ session_state
    start_str = st.session_state.fund_filter["start_str"]
    end_str = st.session_state.fund_filter["end_str"]

    # Kiểm tra và chuyển đổi
    try:
        start_date = pd.to_datetime(start_str, format="%d/%m/%Y")
        end_date = pd.to_datetime(end_str, format="%d/%m/%Y")
    except Exception:
        st.error("Vui lòng nhập đúng định dạng dd/mm/yyyy.")
        return

    df_month = df[
        (df["Ngày_dt"] >= start_date) &
        (df["Ngày_dt"] <= end_date)
    ]
    if df_month.empty:
        st.info(f"Không có thu chi trong khoảng {start_str} - {end_str}.")
    else:
        df_month_show = df_month.copy()
        df_month_show["Giá"] = df_month_show["Giá"].apply(lambda x: f"{x:+,}")
        df_month_show = df_month_show.sort_values("Ngày_dt")
        st.dataframe(
            df_month_show[["Ngày", "Ghi chú", "Giá"]].reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )
        tong_thuchi = df_month["Giá"].sum()
        color = "#009900" if tong_thuchi >= 0 else "#FF0000"
        st.markdown(
            f"<h5 style='text-align: right; color: {color}; font-weight: bold;'>TỔNG: {tong_thuchi:,} VNĐ</h5>",
            unsafe_allow_html=True
        )

        # # --- Nút xoá ---
        # st.markdown("### Xoá dữ liệu thu chi")

        # # Xoá toàn bộ trong tháng đã chọn
        # if st.button(f"Xoá tất cả", key=f"del_fund_month_{month}_{year}"):
        #     df_all = load_funds()
        #     # chuyển ngày sang datetime để lọc an toàn
        #     df_all["Ngày_dt"] = pd.to_datetime(df_all["Ngày"], format="%d/%m/%Y", errors="coerce")
        #     df_all = df_all[~((df_all["Ngày_dt"].dt.month == month) & (df_all["Ngày_dt"].dt.year == year))]
        #     df_all = df_all.reset_index(drop=True)
        #     save_funds(df_all)
        #     st.success(f"Đã xoá toàn bộ thu/chi trong tháng {month}/{year}.")
        #     st.rerun()

        # # Hiện từng ngày và cho xóa từng dòng
        # for ngay, group in df_month.groupby("Ngày"):
        #     st.markdown(f"**Ngày {ngay}**")
        #     for _, row in group.iterrows():
        #         col1, col2 = st.columns([6, 1])
        #         col1.write(f"{row['Ghi chú']} ({row['Giá']:+,} VNĐ)")
        #         # dùng row.name làm key để giữ unique, khi xóa thì tìm và xoá hàng tương ứng trong sheet
        #         if col2.button("❌", key=f"del_fund_{ngay}_{row.name}"):
        #             df_all = load_funds()
        #             # tìm index đầu tiên khớp (Ngày, Ghi chú, Giá) để tránh sai index
        #             cond = (
        #                 (df_all["Ngày"] == row["Ngày"]) &
        #                 (df_all["Ghi chú"] == row["Ghi chú"]) &
        #                 (pd.to_numeric(df_all["Giá"], errors="coerce").fillna(0).astype(int) == int(row["Giá"]))
        #             )
        #             idxs = df_all[cond].index.tolist()
        #             if idxs:
        #                 df_all = df_all.drop(idxs[0]).reset_index(drop=True)
        #                 save_funds(df_all)
        #                 st.success("Đã xoá 1 dòng quỹ.")
        #                 st.rerun()
        #             else:
        #                 st.warning("Không tìm thấy dòng tương ứng để xóa.")

    show_monthly_summary()

    # --- Quỹ hiện tại (tổng tất cả các dòng) ---
    tong_quy = df["Giá"].sum()
    color = "#009900" if tong_quy >= 0 else "#FF0000"
    st.markdown(
        f"<h2 style='text-align: center; color: {color}; font-weight: bold;'>QUỸ HIỆN TẠI: {tong_quy:,}</h2>",
        unsafe_allow_html=True
    )
