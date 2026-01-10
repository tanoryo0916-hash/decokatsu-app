import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import time
import uuid

# ==========================================
#  1. 設定＆デザイン
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活宣言",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS設定（スマホ最適化・チケット風デザイン） ---
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
        color: #333;
    }
    /* ボタン */
    .stButton>button {
        width: 100%;
        height: 60px;
        font-size: 20px !important;
        border-radius: 30px;
        font-weight: bold;
        background: linear-gradient(135deg, #43A047 0%, #66BB6A 100%);
        color: white;
        border: none;
        box-shadow: 0 4px 10px rgba(67, 160, 71, 0.3);
    }
    /* ヘッダー画像エリア */
    .header-area {
        background-color: #E8F5E9;
        padding: 20px;
        border-radius: 0 0 20px 20px;
        text-align: center;
        margin-bottom: 20px;
        border-bottom: 4px solid #C8E6C9;
    }
    .main-title {
        font-size: 24px;
        font-weight: 900;
        color: #2E7D32;
        margin-bottom: 5px;
    }
    /* 完了チケット */
    .ticket-card {
        background: linear-gradient(135deg, #FFF9C4 0%, #FFF176 100%);
        border: 4px dashed #FBC02D;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        position: relative;
    }
    .ticket-title {
        font-size: 22px;
        font-weight: 900;
        color: #E65100;
        border-bottom: 2px solid #E65100;
        display: inline-block;
        margin-bottom: 10px;
    }
    .ticket-name {
        font-size: 28px;
        font-weight: bold;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
#  2. Google Sheets 接続設定
# ==========================================
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

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
        st.error(f"接続エラー: {e}")
        return None

def save_declaration(nickname, action_text):
    client = get_connection()
    if not client: return False

    try:
        sheet = client.open("decokatsu_db").sheet1
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 一般参加用のID生成 (VISitor_日時_ランダム)
        user_id = f"VIS_{datetime.datetime.now().strftime('%H%M%S')}_{str(uuid.uuid4())[:4]}"
        
        # 保存 (学校名は「一般参加」とする)
        # 列順: [日時, ID, 名前, 対象日付, 項目, ポイント, メモ, q1, q2, q3]
        sheet.append_row([now, user_id, nickname, "一般来場", "デコ活宣言", 0, action_text, "", "", ""])
        return True
    except Exception as e:
        st.error(f"送信エラー: {e}")
        return False

# ==========================================
#  3. 画面構成
# ==========================================

# セッション状態の管理（画面更新してもチケットを消さないため）
if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False
if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

# --- ヘッダー ---
st.markdown("""
<div class="header-area">
    <div class="main-title">🌿 おかやまデコ活宣言</div>
    <div style="font-size:14px; font-weight:bold;">みんなで地球にいいこと、始めよう！</div>
</div>
""", unsafe_allow_html=True)

# --- メイン処理 ---
if st.session_state['submitted']:
    # === 送信完了画面（抽選チケット） ===
    st.balloons()
    st.markdown(f"""
    <div class="ticket-card">
        <div class="ticket-title">🎟 ガラポン参加チケット</div>
        <p style="font-weight:bold; margin-top:10px;">デコ活宣言 ありがとう！</p>
        <div class="ticket-name">{st.session_state['user_name']} 様</div>
        <div style="font-size:14px; margin-top:10px;">
            この画面をスタッフに見せて<br>ガラポン抽選に参加してね！
        </div>
        <div style="font-size:12px; color:#555; margin-top:15px;">
            {datetime.date.today().strftime('%Y年%m月%d日')} 発行
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("戻る（新しい人が入力する）"):
        st.session_state['submitted'] = False
        st.session_state['user_name'] = ""
        st.rerun()

else:
    # === 入力フォーム ===
    st.info("👇 ここに入力すると、ガラポン抽選に参加できるよ！")

    with st.form("visitor_form"):
        nickname = st.text_input("お名前（ニックネーム）", placeholder="例：ももたろう")
        
        # 宣言の選択肢
        options = [
            "エコバッグを持ち歩きます",
            "食べ残しをしません",
            "こまめに電気を消します",
            "冷房は28℃、暖房は20℃にします",
            "なるべく歩いて移動します",
            "マイボトルを使います",
            "水を大切に使います",
            "その他（自由入力）"
        ]
        declaration = st.selectbox("あなたの「デコ活宣言」を選んでね", options)
        
        # その他を選んだ場合
        custom_text = ""
        if declaration == "その他（自由入力）":
            custom_text = st.text_input("宣言したいことを書いてね")
        
        submitted = st.form_submit_button("宣言して ガラポンに参加！")

        if submitted:
            if not nickname:
                st.warning("お名前を入力してね！")
            else:
                final_action = custom_text if custom_text else declaration
                
                with st.spinner("送信中..."):
                    if save_declaration(nickname, final_action):
                        st.session_state['submitted'] = True
                        st.session_state['user_name'] = nickname
                        st.rerun()

# フッター
st.markdown("""
<div style="text-align:center; margin-top:50px; font-size:10px; color:#999;">
    © 2026 おかやまデコ活フェス
</div>
""", unsafe_allow_html=True)
