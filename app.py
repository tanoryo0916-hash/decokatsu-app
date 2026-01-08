import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import time
import pandas as pd

# ==========================================
#  1. 設定＆デザイン
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活チャレンジ",
    page_icon="🌏",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS設定 ---
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
    }
    /* チェックボックス（トグル）周り */
    .stToggle {
        background-color: #f0f8ff;
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        border: 1px solid #dcdcdc;
    }
    .stToggle label {
        font-size: 18px !important;
        font-weight: bold;
        color: #2e8b57;
    }
    /* 送信ボタン */
    .stButton>button {
        width: 100%;
        height: 70px;
        font-size: 20px !important;
        border-radius: 30px;
        font-weight: bold;
        background-color: #FF9800;
        color: white;
        border: none;
    }
    .stButton>button:hover {
        color: white;
        background-color: #F57C00;
    }
    .school-suffix {
        font-size: 20px;
        font-weight: bold;
        padding-top: 35px;
        color: #333;
    }
    /* スペシャルミッション用の枠 */
    .special-mission {
        background-color: #e0f7fa;
        padding: 20px;
        border-radius: 15px;
        border: 2px dashed #00bcd4;
        text-align: center;
        margin-bottom: 20px;
    }
    /* 表のデザイン調整 */
    thead tr th:first-child { display:none }
    tbody th { display:none }
    .dataframe { font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
#  2. Google Sheets 接続設定
# ==========================================
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_connection():
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPE
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error("システムエラー: 設定を確認してください")
        return None

def fetch_user_data(school_full_name, grade, u_class, number):
    client = get_connection()
    if not client: return None, None, 0, []

    try:
        sheet = client.open("decokatsu_db").sheet1
        records = sheet.get_all_records()
        
        user_id = f"{school_full_name}_{grade}_{u_class}_{number}"
        
        total_co2 = 0
        nickname = ""
        history = [] 
        
        for row in records:
            if str(row.get('ID')) == user_id:
                try:
                    val = int(row.get('CO2削減量', 0))
                    total_co2 += val
                except:
                    pass
                if row.get('ニックネーム'):
                    nickname = row.get('ニックネーム')
                if row.get('対象日付') and row.get('実施項目'):
                    history.append({
                        'date': row.get('対象日付'),
                        'actions': str(row.get('実施項目'))
                    })
        
        return user_id, nickname, total_co2, history

    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return None, None, 0, []

def save_daily_challenge(user_id, nickname, target_date, actions_done, total_points, memo):
    client = get_connection()
    if not client: return False

    try:
        sheet = client.open("decokatsu_db").sheet1
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        actions_str = ", ".join(actions_done)
        sheet.append_row([now, user_id, nickname, target_date, actions_str, total_points, memo])
        return True
    except Exception as e:
        st.error(f"保存失敗: {e}")
        return False

# ==========================================
#  3. セッション管理
# ==========================================
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# ==========================================
#  4. 画面コンポーネント
# ==========================================

def login_screen():
    st.image("https://placehold.jp/3d4070/ffffff/800x200.png?text=DecoKatsu%20Login", use_column_width=True)
    st.markdown("### 🏫 チャレンジシートをはじめよう！")
    st.info("学校名と、自分の「年・組・番号」を入れてね。")

    with st.form("login_form"):
        st.markdown("**小学校の名前**")
        col_sch1, col_sch2 = st.columns([3, 1])
        with col_sch1:
            school_core = st.text_input("小学校名", placeholder="例：倉敷", label_visibility="collapsed")
        with col_sch2:
            st.markdown('<div class="school-suffix">小学校</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            grade = st.selectbox("学年", ["1年", "2年", "3年", "4年", "5年", "6年"])
            u_class = st.text_input("組（クラス）", placeholder="例：1、A、松")
        with col2:
            number = st.number_input("出席番号", min_value=1, max_value=50, step=1)
            
        nickname_input = st.text_input("ニックネーム（ひらがな）", placeholder="例：でこかつたろう")

        submit = st.form_submit_button("スタート！", type="primary")

        if submit:
            if not school_core or not nickname_input or not u_class:
                st.warning("すべて入力してね！")
                return

            with st.spinner("データを読み込んでいます..."):
                full_school_name = f"{school_core}小学校"
                
                user_id, saved_name, total, history = fetch_user_data(full_school_name, grade, u_class, number)
                final_name = saved_name if saved_name else nickname_input
                
                st.session_state.user_info = {
                    'id': user_id,
                    'name': final_name,
                    'total_co2': total,
                    'school': full_school_name,
                    'history': history
                }
                st.rerun()

def main_screen():
    user = st.session_state.user_info
    
    st.markdown(f"**👋 こんにちは、{user['name']} さん！**")
    
    # --- メーター ---
    GOAL = 3000
    current = user['total_co2']
    st.progress(min(current / GOAL, 1.0))
    st.caption(f"現在のCO2削減パワー: **{current} g** / 目標 {GOAL} g")
