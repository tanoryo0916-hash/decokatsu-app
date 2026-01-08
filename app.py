import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import time

# ==========================================
#  1. 設定＆デザイン（GIGA端末向け最適化）
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活ポケット",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS設定 ---
st.markdown("""
<style>
    /* 全体のフォント設定 */
    html, body, [class*="css"] {
        font-family: 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
    }
    /* ボタンのスタイル：大きく押しやすく */
    .stButton>button {
        width: 100%;
        height: 80px;
        font-size: 20px !important;
        border-radius: 15px;
        font-weight: bold;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        border: 2px solid #f0f2f6;
    }
    .stButton>button:active {
        box-shadow: none;
        transform: translateY(2px);
    }
    /* 入力欄の文字サイズ調整 */
    .stSelectbox label, .stNumberInput label, .stTextInput label {
        font-size: 16px !important;
        font-weight: bold;
    }
    /* 成功メッセージ */
    .stToast {
        font-size: 18px;
        background-color: #E8F5E9;
    }
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

def fetch_user_data(school, grade, u_class, number):
    client = get_connection()
    if not client: return None, None, 0

    try:
        sheet = client.open("decokatsu_db").sheet1
        records = sheet.get_all_records()
        
        # ID生成：入力された学校名をそのまま使うため、空白除去だけ行う
        clean_school = school.strip()
        user_id = f"{clean_school}_{grade}_{u_class}_{number}"
        
        total_co2 = 0
        nickname = ""
        
        for row in records:
            if str(row.get('ID')) == user_id:
                try:
                    val = int(row.get('CO2削減量', 0))
                    total_co2 += val
                except:
                    pass
                if row.get('ニックネーム'):
                    nickname = row.get('ニックネーム')
        
        return user_id, nickname, total_co2

    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return None, None, 0

def save_action(user_id, nickname, action, co2_val):
    client = get_connection()
    if not client: return False

    try:
        sheet = client.open("decokatsu_db").sheet1
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sheet.append_row([now, user_id, nickname, action, co2_val])
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
    st.image("https://placehold.jp/3d4070/ffffff/800x300.png?text=DecoKatsu", use_column_width=True)
    st.markdown("### 🏫 デコ活ポケット ログイン")
    st.info("学校名と、自分の「年・組・番号」を入れてスタート！")

    with st.form("login_form"):
        # --- 変更箇所：学校名を自由入力に変更 ---
        school_input = st.text_input("小学校の名前", placeholder="例：倉敷小学校（毎回おなじ名前を入れてね）")
        
        col1, col2 = st.columns(2)
        with col1:
            grade = st.selectbox("学年", ["1年", "2年", "3年", "4年", "5年", "6年"])
            u_class = st.number_input("組（クラス）", min_value=1, max_value=10, step=1)
        with col2:
            number = st.number_input("出席番号", min_value=1, max_value=50, step=1)
            # レイアウト調整のための空要素
            st.write("") 
        
        nickname_input = st.text_input("ニックネーム（ひらがな）", placeholder="例：たろう")

        submit = st.form_submit_button("スタート！", type="primary")

        if submit:
            # 入力チェック
            if not school_input:
                st.warning("小学校の名前を入れてね！")
                return
            if not nickname_input:
                st.warning("ニックネームを入れてね！")
                return

            with st.spinner("データを読み込んでいます..."):
                # 入力された学校名でデータを検索
                user_id, saved_name, total = fetch_user_data(school_input, grade, u_class, number)
                
                final_name = saved_name if saved_name else nickname_input
                
                st.session_state.user_info = {
                    'id': user_id,
                    'name': final_name,
                    'total_co2': total,
                    'school': school_input
                }
                st.rerun()

def main_screen():
    user = st.session_state.user_info
    
    st.markdown(f"**👋 {user['name']} さんのチャレンジ**")
    
    # 目標設定
    GOAL = 3000
    current = user['total_co2']
    
    col_m1, col_m2 = st.columns([2, 1])
    with col_m1:
        st.metric(label="現在のCO2削減量", value=f"{current} g")
    with col_m2:
        st.write(f"目標まで\nあと {max(0, GOAL - current)} g")

    progress_val = min(current / GOAL, 1.0)
    st.progress(progress_val)
    
    if progress_val >= 1.0:
        st.balloons()
        st.success("🎉 おめでとう！目標達成！")

    st.markdown("---")
    st.markdown("### 👇 やったことをタップ！")

    col1, col2 = st.columns(2)

    def create_action_btn(col, label, point, icon, color_msg):
        with col:
            btn_label = f"{icon} {label}\n(+{point}g)"
            if st.button(btn_label):
                with st.spinner('記録中...'):
                    if save_action(user['id'], user['name'], label, point):
                        st.session_state.user_info['total_co2'] += point
                        st.toast(f"{color_msg}！ +{point}g", icon="✨")
                        time.sleep(1)
                        st.rerun()

    create_action_btn(col1, "電気を消す", 50, "💡", "ナイス")
    create_action_btn(col1, "水を止める", 30, "🚰", "いいね")
    create_action_btn(col1, "徒歩・自転車", 100, "🚲", "すごい")

    create_action_btn(col2, "残さず食べる", 100, "🍚", "えらい")
    create_action_btn(col2, "ゴミ分別", 80, "♻️", "さすが")
    create_action_btn(col2, "家族と話す", 50, "👨‍👩‍👧", "すてき")

    st.markdown("---")
    
    tab1, tab2 = st.tabs(["📅 イベント情報", "🎟 ガラポン参加証"])
    
    with tab1:
        st.subheader("🎉 おかやまデコ活フェス2026")
        st.info("**日時:** 6月6日(土)・7日(日) 10:00〜16:00\n\n**場所:** イオンモール倉敷 1F")
        st.markdown("* ✨ EV車展示 / ガラポン抽選会 / スタンプラリー")
    
    with tab2:
        st.subheader("会場でガラポン！")
        if user['total_co2'] > 0:
            st.success("この画面を会場の受付で見せてね！")
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={user['id']}"
            st.image(qr_url, width=200)
            st.caption(f"ID: {user['id']}")
        else:
            st.warning("まずはポイントを貯めよう！")
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("ログアウト"):
        st.session_state.user_info = None
        st.rerun()

# ==========================================
#  メイン実行
# ==========================================
if __name__ == "__main__":
    if st.session_state.user_info is None:
        login_screen()
    else:
        main_screen()
