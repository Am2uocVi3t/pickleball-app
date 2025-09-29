import streamlit as st
import pandas as pd
from utils.gsheets import load_sheet, save_sheet
from utils.input_info import load_matches
from utils.stats import get_stats


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

    # Chuyển đổi cột Ngày
    df_matches["Ngày_dt"] = pd.to_datetime(df_matches["Ngày"], format="%d/%m/%Y", errors="coerce")

    # Lấy tất cả (năm, tháng) có trận
    month_years = df_matches.dropna(subset=["Ngày_dt"]).groupby([df_matches["Ngày_dt"].dt.year,
                                                                df_matches["Ngày_dt"].dt.month])

    for (y, m), group in month_years:
        df_stats, total = get_stats(group, members_df)

        if total == 0:  
            continue  # không có gì thì bỏ qua

        # format ngày cuối tháng
        ngay_cuoi_thang = pd.Timestamp(year=y, month=m, day=1) + pd.offsets.MonthEnd(0)
        ngay_str = ngay_cuoi_thang.strftime("%d/%m/%Y")

        # xoá nếu đã có để tránh trùng
        mask = (df_funds["Ghi chú"] == f"Tổng thu quỹ tháng {m}") & (df_funds["Ngày"] == ngay_str)
        df_funds = df_funds[~mask]

        # thêm dòng mới
        new_row = pd.DataFrame([{
            "Ngày": ngay_str,
            "Ghi chú": f"Tổng thu quỹ tháng {m}",
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

    # --- Lọc theo tháng/năm ---
    df = load_funds()
    if df.empty:
        st.info("Chưa có dữ liệu thu/chi quỹ.")
        return

    st.subheader("Danh sách thu chi quỹ")

    # Tách cột tháng/năm từ "Ngày"
    df["Ngày_dt"] = pd.to_datetime(df["Ngày"], format="%d/%m/%Y", errors="coerce")
    df["Tháng"] = df["Ngày_dt"].dt.month
    df["Năm"] = df["Ngày_dt"].dt.year

    col1, col2 = st.columns(2)
    month = col1.selectbox("Chọn tháng", list(range(1, 13)), index=pd.Timestamp.now().month-1)
    year = col2.selectbox("Chọn năm", sorted(df["Năm"].dropna().unique()), 
                          index=len(sorted(df["Năm"].dropna().unique()))-1)

    df_month = df[(df["Tháng"] == month) & (df["Năm"] == year)]

    if df_month.empty:
        st.info("Không có thu chi trong tháng này.")
    else:
        df_month_show = df_month.copy()
        df_month_show["Giá"] = df_month_show["Giá"].apply(lambda x: f"{x:+,}")
        st.dataframe(df_month_show[["Ngày", "Ghi chú", "Giá"]].reset_index(drop=True), use_container_width=True, hide_index=True)

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
    st.markdown(f"<h2 style='text-align: center; color: #009900; font-weight: bold;'>QUỸ HIỆN TẠI: {tong_quy:,}</h2>", unsafe_allow_html=True)
