# members.py
import streamlit as st
import pandas as pd
import os
from utils.gsheets import load_sheet, save_sheet

# Hàm load & save
SHEET_NAME = "members"

def load_members():
    df = load_sheet(SHEET_NAME)
    if df.empty:
        df = pd.DataFrame(columns=["Tên", "Giá thua"])
    df["Tên"] = df["Tên"].astype(str).str.strip()
    df["Giá thua"] = pd.to_numeric(df["Giá thua"], errors="coerce").fillna(0).astype(int)
    return df

def save_members(df: pd.DataFrame):
    save_sheet(SHEET_NAME, df)

# Hàm hiển thị giao diện hội viên
def show_members_page():
    st.markdown("<h2 style='text-align: center;'>QUẢN LÝ HỘI VIÊN</h2>", unsafe_allow_html=True)

    # Load dữ liệu
    members_df = load_members()

    # Thêm hội viên
    # st.subheader("Thêm hội viên")
    # with st.form("add_member_form", clear_on_submit=True):
    #     name = st.text_input("Tên hội viên").strip()
    #     fee = st.number_input("Giá thua (VNĐ)", min_value=5000, step=1000)
    #     submit = st.form_submit_button("Thêm")

    #     if submit and name:
    #         if name in members_df["Tên"].values:
    #             st.warning(f"{name} đã tồn tại trong danh sách.")
    #         else:
    #             new_row = pd.DataFrame([[name, fee]], columns=["Tên", "Giá thua"])
    #             members_df = pd.concat([members_df, new_row], ignore_index=True)
    #             save_members(members_df)
    #             st.success(f"Đã thêm {name} với giá thua {fee:,} VNĐ")

    # Danh sách hội viên
    st.subheader("Danh sách hội viên")
    if not members_df.empty:
        st.dataframe(members_df, use_container_width=True)

        # # Chỉnh sửa hội viên
        # st.subheader("Chỉnh sửa hội viên")
        # member_to_edit = st.selectbox("Chọn hội viên", members_df["Tên"].tolist(), key="edit_member")

        # # Lấy dữ liệu cũ
        # old_name = member_to_edit
        # old_fee = int(members_df.loc[members_df["Tên"] == old_name, "Giá thua"].values[0])

        # # Nhập tên và giá mới
        # new_name = st.text_input("Tên mới", value=old_name, key="edit_name").strip()
        # new_fee = st.number_input(
        #     "Giá thua mới (VNĐ)",
        #     min_value=5000,
        #     step=1000,
        #     value=old_fee,
        #     key="edit_fee"
        # )

        # if st.button("Cập nhật"):
        #     # Kiểm tra tên mới có bị trùng không (trừ chính nó)
        #     if new_name != old_name and new_name in members_df["Tên"].values:
        #         st.warning(f"Tên {new_name} đã tồn tại trong danh sách.")
        #     else:
        #         members_df.loc[members_df["Tên"] == old_name, "Tên"] = new_name
        #         members_df.loc[members_df["Tên"] == new_name, "Giá thua"] = new_fee
        #         save_members(members_df)
        #         st.success(f"Đã cập nhật {old_name} → {new_name}, giá thua {new_fee:,} VNĐ")
        #         st.rerun()
        # # Xóa hội viên
        # st.subheader("Xóa hội viên")
        # member_to_delete = st.selectbox("Chọn hội viên để xóa", members_df["Tên"].tolist(), key="delete_member")
        # if st.button("Xóa"):
        #     members_df = members_df[members_df["Tên"] != member_to_delete]
        #     save_members(members_df)
        #     st.success(f"Đã xóa {member_to_delete}")
        #     st.rerun()
    else:
        st.info("Chưa có hội viên nào. Hãy thêm mới!")
