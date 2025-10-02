# utils/input_info.py
import streamlit as st
import pandas as pd
import os
# from utils.member import load_members
from utils.gsheets import load_sheet, save_sheet


FUND_SHEET = "funds"
SHEET_NAME = "matches"

# -------- Matches ----------
def load_matches():
    df = load_sheet(SHEET_NAME)
    if df.empty:
        df = pd.DataFrame(columns=["Ngày", "Đội thắng", "Đội thua", "Giá"])
    df = df.replace("nan", "", regex=False).fillna("")
    df["Ngày"] = df["Ngày"].astype(str).str.strip()
    df["Đội thắng"] = df["Đội thắng"].astype(str).str.strip()
    df["Đội thua"] = df["Đội thua"].astype(str).str.strip()
    df["Giá"] = pd.to_numeric(df["Giá"], errors="coerce").fillna(-1).astype(int)
    return df


def save_matches(df: pd.DataFrame):
    save_sheet(SHEET_NAME, df)


# -------- UI ----------
def show_match_page():
    st.markdown("<h2 style='text-align: center;'>BẢNG NHẬP THÔNG TIN</h2>", unsafe_allow_html=True)
    
    st.subheader("Nhập thông tin trận thua")
    # Chọn ngày
    ngay_chon = st.date_input("Chọn ngày", format="DD/MM/YYYY")

    # Form nhập
    with st.form("match_form", clear_on_submit=True):
        doi_thang = st.text_input("Đội thắng")
        doi_thua = st.text_input("Đội thua")
        gia_input = st.number_input(
            "Giá mới (nếu có giá khác)",
            min_value=0,
            step=1000,
            value=0
        )
        submitted = st.form_submit_button("Lưu")

    if submitted:
        if (not doi_thua or not doi_thua.strip()) or (not doi_thang or not doi_thang.strip()):
            st.warning("Vui lòng nhập đầy đủ thông tin Đội thắng và Đội thua.")
        else:            
            # items = [item.strip() for item in doi_thua.split(",") if item.strip()]
            # new_rows = []
            # team = []
            # for it in items:
            #     name = it.split()
            #     team.append(name)
            # for name in team:
            #     num_player = len(name)
            #     if gia_input > 1:
            #         fee = int(gia_input / num_player)
            #     else:
            #         fee = -1
                    
            #     new_rows.append({
            #     "Ngày": ngay_str,
            #     "Đội thắng": doi_thang,
            #     "Đội thua": " ".join(name),
            #     "Giá": fee
            #     })

            winner = [n.strip() for n in doi_thang.split(",") if n.strip()]
            loser = [n.strip() for n in doi_thua.split(",") if n.strip()]
            if len(winner) != len(loser):
                st.warning("Số người trong Đội thắng và Đội thua phải bằng nhau.")
                return
            
            ngay_str = ngay_chon.strftime("%d/%m/%Y")
            new_rows = []
            for w_team, l_team in zip(winner, loser):
                num_player = len(l_team.split())
                if gia_input > 1:
                    fee = int(gia_input / num_player)
                else:
                    fee = -1

                new_rows.append({
                    "Ngày": ngay_str,
                    "Đội thắng": w_team,
                    "Đội thua": l_team,
                    "Giá": fee
                })

            if new_rows:
                df_all = load_matches()
                df_all = pd.concat([df_all, pd.DataFrame(new_rows)], ignore_index=True)
                save_matches(df_all)
                st.success(f"Đã lưu: {len(new_rows)} trận (ngày {ngay_str}).")
            else: 
                st.info("Không có dữ liệu để lưu.")

    # Hiển thị danh sách trận thua theo ngày
    st.subheader("Danh sách trận thua")
    df = load_matches()
    if df.empty:
        st.info("Chưa có dữ liệu.")
        return

    ngay_str = ngay_chon.strftime("%d/%m/%Y")
    df_filtered = df[df["Ngày"] == ngay_str]

    if df_filtered.empty:
        st.info("Không có dữ liệu cho ngày đã chọn.")
    else:
        # Tạo DataFrame gọn hơn
        df_show = df_filtered.copy()
        # st.dataframe(df_show[["Ngày", "Trận thua", "Giá"]], use_container_width=True)
        df_show["Giá mới/người"] = df_show["Giá"].apply(lambda x: f"{x:,} VNĐ" if x > 0 else "")
        st.dataframe(df_show[["Ngày", "Đội thắng", "Đội thua", "Giá mới/người"]].reset_index(drop=True), use_container_width=True, hide_index=True)

        # st.subheader("Xóa trận")
        # if st.button("Xoá tất cả trong ngày", key=f"delete_all_{ngay_str}"):
        #     df_all = load_matches()
        #     df_all = df_all[df_all["Ngày"] != ngay_str].reset_index(drop=True)
        #     save_matches(df_all)
        #     st.success(f"Đã xoá toàn bộ dữ liệu ngày {ngay_str}.")
        #     st.rerun()

        # # Liệt kê từng dòng để xoá riêng
        # for idx, row in df_filtered.iterrows():
        #     col1, col2 = st.columns([6,1])
        #     col1.write(f"{row['Ngày']} - {row['Trận thua']}")
        #     if col2.button("❌", key=f"del_{ngay_str}_{idx}"):
        #         df_all = load_matches()
        #         if idx in df_all.index:
        #             df_all = df_all.drop(idx).reset_index(drop=True)
        #             save_matches(df_all)
        #             st.success("Đã xóa 1 dòng.")
        #             st.rerun()
