import streamlit as st
import pandas as pd
from utils.member import show_members_page
from utils.input_info import show_match_page
from utils.details import show_detail_page
from utils.stats import show_stats_page
from utils.funds import show_fund_page
from utils.charts import show_charts_page


st.set_page_config(
    page_title="Pickleball App", 
    page_icon="https://img.freepik.com/premium-vector/pickleball-paddles-logo-pickleball-club-icon-vector_854827-129.jpg?w=2000", 
    layout="centered"
    )
# ======================
# 🎨 CSS CHO SIDEBAR
# ======================
st.markdown("""
<style>
/* 🎾 Toàn bộ sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f9fafb, #f1f5f9);
    padding-top: 2rem;
    box-shadow: 2px 0 8px rgba(0,0,0,0.08);
    font-family: 'Segoe UI', Roboto, sans-serif;
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* 🏓 Logo */
[data-testid="stSidebar"]::before {
    content: "";
    display: block;
    height: 80px;
    width: 80px;
    margin: 0 auto 20px auto;
    border-radius: 50%;
    background-image: url("https://img.freepik.com/premium-vector/pickleball-paddles-logo-pickleball-club-icon-vector_854827-129.jpg?w=2000");
    background-size: cover;
    background-position: center;
    box-shadow: 0 0 6px rgba(0,0,0,0.15);
}

/* 🚫 Ẩn chữ "Menu" ở sidebar */
[data-testid="stSidebar"] > div > div:first-child > h2 {
    display: none;
}

/* 📦 Các mục menu: làm dạng khối vuông */
div[role="radiogroup"] {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.6rem;
    width: 100%;
}

div[role="radiogroup"] > label {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 160px;       
    height: 60px;       
    border: 2px solid #cbd5e1;
    border-radius: 12px;
    background-color: #ffffff;
    color: #1e293b !important;
    font-weight: 500;
    text-align: center;
    transition: all 0.2s ease-in-out;
    cursor: pointer;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

/* 🖱️ Hover */
div[role="radiogroup"] > label:hover {
    background-color: #e0f2fe;
    border-color: #38bdf8;
    color: #0c4a6e !important;
    transform: translateY(-2px);
}

/* ✅ Mục được chọn — dùng aria-checked thay cho :has */
div[role="radiogroup"] > label[data-baseweb="radio"][aria-checked="true"] {
    background-color: #a7f3d0; /* Xanh nhạt */
    border-color: #10b981;
    color: #065f46 !important;
    font-weight: 600;
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
    transform: scale(1.05);
}

/* Ẩn radio tròn mặc định */
div[role="radiogroup"] input[type="radio"] {
    display: none;
}
</style>
""", unsafe_allow_html=True)
# st.markdown(
#     """
#     <div style="position: absolute; top: 1rem; right: 1rem; z-index: 100;">
#         <img src="https://img.freepik.com/premium-vector/pickleball-paddles-logo-pickleball-club-icon-vector_854827-129.jpg?w=2000" width="60" style="border-radius: 50%;">
#     </div>
#     """,
#     unsafe_allow_html=True
# )
menu = st.sidebar.radio(
    "", 
    ["Nhập thông tin", "Bảng chi tiết", "Thống kê", "Quỹ nhóm", "Hội viên", "Biểu đồ"]
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
elif menu == "Biểu đồ":
    show_charts_page()