import streamlit as st
import pandas as pd
from utils.member import show_members_page
from utils.input_info import show_match_page
from utils.details import show_detail_page
from utils.stats import show_stats_page
from utils.funds import show_fund_page


st.set_page_config(page_title="Pickleball App", page_icon="https://img.freepik.com/premium-vector/pickleball-paddles-logo-pickleball-club-icon-vector_854827-129.jpg?w=2000", layout="centered")

menu = st.sidebar.radio(
    "Menu", 
    ["Nhập thông tin", "Bảng chi tiết", "Thống kê", "Quỹ nhóm", "Hội viên"]
)

if menu == "Hội viên":
    show_members_page()
elif menu == "Nhập thông tin":
    show_match_page()
elif menu == "Thống kê":
    show_stats_page()
elif menu == "Bảng chi tiết":
    show_detail_page()
elif menu == "Quỹ nhóm":
    show_fund_page()