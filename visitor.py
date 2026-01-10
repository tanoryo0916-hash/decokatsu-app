import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import time
import uuid

# ==========================================
#  1. 設定＆デザイン（スマホ特化・オシャレ版）
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活フェス2026",
    page_icon="🌿",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS設定 ---
st.markdown("""
<style>
    /* ベースフォント設定 */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        color: #333;
        background-color: #F1F8E9; /* 背景：薄い黄緑 */
    }

    /* ストリームリットの標準余白削除 */
    .block-container {
        padding-top: 0 !important; /* ヘッダーを上までくっつける */
        padding-bottom: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max_width: 100% !important;
    }

    /* --- ✨ 新しいオシャレなヘッダーエリア --- */
    .header-area {
        /* エコ(緑)＆フェス(オレンジ)の明るいグラデーション */
        background: linear-gradient(135deg, #66BB6A 0%, #FFB74D 100%);
        padding: 35px 20px 30px 20px;
        border-radius: 0 0 30px 30px; /* 下だけ丸く */
        text-align: center;
        margin: 0 -1rem 25px -1rem; /* 画面端まで広げる */
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        color: white;
        position: relative;
        overflow: hidden;
    }

    /* 背景の装飾（キラキラ） */
    .header-area::before {
        content: '🌿 ✨'; font-size: 24px; position: absolute; top: 15px; left: 20px; opacity: 0.6;
    }
    .header-area::after {
        content: '✨ 🍑'; font-size: 24px; position: absolute; bottom: 15px; right: 20px; opacity: 0.6;
    }

    /* メインタイトル（フェス名） */
    .event-title-main {
        font-size: 32px;
        font-weight: 900;
        margin-bottom: 5px;
        text-shadow: 2px 2px 5px rgba(0,0,0,0.3); /* 文字をくっきりさせる影 */
        letter-spacing: 1px;
        line-height: 1.2;
    }

    /* サブタイトル（デコ活宣言） */
    .event-title-sub {
        font-size: 18px;
        font-weight: bold;
        display: inline-block;
        background-color: rgba(255,255,255,0.25); /* 半透明の白背景 */
        padding: 6px 20px;
        border-radius: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        backdrop-filter: blur(5px); /* すりガラス効果 */
    }

    /* 説明文 */
    .header-description {
        font-size: 14px;
        font-weight: bold;
        line-height: 1.6;
        color: rgba(255,255,255,0.95);
    }

    /* --- カードデザイン --- */
    .step-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 6px solid #43A047;
        margin-bottom: 15px;
    }
    /* ステップバッジ */
    .step-badge {
        background-color: #43A047; color: white; padding: 3px 10px; border-radius: 15px;
        font-weight: bold; font-size: 12px; display: inline-block; margin-bottom: 8px; vertical-align: middle;
    }
    .step-title {
        font-size: 18px; font-weight: bold; color: #2E7D32; margin-left: 5px; vertical-align: middle;
    }
    /* 入力フィールド調整 */
    div[data-baseweb="input"], div[data-baseweb="textarea"] { font-size: 16px !important; background-color: #FAFAFA; }
    /* ラジオボタン調整 */
    div[role="radiogroup"] label {
        background-color: #FAFAFA; padding: 10px 15px; border-radius: 8px; margin-bottom: 5px;
        border: 1px solid #EEEEEE; width: 100%;
    }
    div[role="radiogroup"] label:hover { background-color: #F1F8E9; border-color: #C5E1A5; }
    /* 送信ボタン */
    .stButton>button {
        width: 100%; height: 65px; font-size: 20px !important; border-radius: 15px;
        font-weight: 900; background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%);
        color: white; border: none; box-shadow: 0 4px 10px rgba(245, 124, 0, 0.3); margin-top: 10px;
    }
    .stButton>button:active { transform: scale(0.98); }

    /* --- 完了チケット（ヘッダーに合わせて少しリッチに） --- */
    .ticket-card {
        background: linear-gradient(135deg, #FFF9C4 0%, #FFF59D 100%);
        border: 4px dashed #FBC02D;
        border-radius: 20px;
        padding: 30px 20px;
        text-align: center;
        margin-top: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        color: #5D4037;
    }
    .ticket-name {
        font-size: 30px; font-weight: 900; margin: 15px 0; color: #E65100; word-break: break-all;
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

def save_visitor_data(nickname, gender, age, location, action_text, q1_score, q2_text):
    client = get_connection()
    if not client: return False

    try:
        sheet = client.open("decokatsu_db").sheet1
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_id = f"VIS_{datetime.datetime.now().strftime('%H%M%S')}_{str(uuid.uuid4())[:4]}"
        memo_content = f"【属性】{age}/{gender}/{location}\n【宣言】{action_text}"
        sheet.append_row([now, user_id, nickname, "一般来場", "デコ活宣言・アンケート", 0, memo_content, q1_score, q2_text, ""])
        return True
    except Exception as e:
        st.error(f"送信エラー: {e}")
        return False

# ==========================================
#  3. 画面構成
# ==========================================

# セッション状態
if 'submitted' not in st.session_state: st.session_state['submitted'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""

# --- ✨ 新しいヘッダー表示 ---
if not st.session_state['submitted']:
    st.markdown("""
    <div class="header-area">
        <div class="event-title-main">おかやま<br>デコ活フェス2026</div>
        <div class="event-title-sub">🌿 デコ活宣言＆アンケート</div>
        <div class="header-description">
            3つのステップを入力して<br>
            <strong>ガラポン抽選</strong> に参加しよう！
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- メイン処理 ---
if st.session_state['submitted']:
    # === 送信完了画面（チケット） ===
    st.balloons()
    st.markdown("""
    <div class="header-area" style="background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); padding-bottom:40px;">
        <div class="event-title-main">🎉 送信完了！</div>
        <div class="header-description">ご協力ありがとうございました。</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="ticket-card" style="margin-top:-30px; position:relative; z-index:1;">
        <div style="font-size:22px; font-weight:900; color:#E65100; border-bottom:3px solid #E65100; display:inline-block; margin-bottom:15px;">
            🎟 ガラポン参加チケット
        </div>
        <div class="ticket-name">{st.session_state['user_name']} 様</div>
        <div style="background-color:rgba(255,255,255,0.8); padding:12px; border-radius:10px; display:inline-block; font-weight:bold; font-size:15px; margin-top:10px; color:#333;">
            この画面をスタッフに見せてね！
        </div>
        <div style="font-size:12px; color:#888; margin-top:20px;">
            発行日: {datetime.date.today().strftime('%Y年%m月%d日')}
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
    with st.form("visitor_form"):
        # STEP 1
        st.markdown("""
        <div class="step-card"><span class="step-badge">STEP 1</span><span class="step-title">あなたについて</span>
        """, unsafe_allow_html=True)
        st.markdown("**お名前（ニックネーム）**")
        nickname = st.text_input("名前", placeholder="例：ももたろう", label_visibility="collapsed")
        st.markdown("**性別**")
        gender = st.radio("性別", ["男性", "女性", "その他・無回答"], horizontal=True, label_visibility="collapsed")
        st.markdown("**年代**")
        age = st.radio("年代", ["小学生未満", "小学生", "中学生", "高校生", "18〜19歳", "20代", "30代", "40代", "50代", "60代", "70代以上"], index=None, label_visibility="collapsed")
        st.markdown("**お住まい**")
        location = st.radio("お住まい", ["倉敷市", "岡山市", "総社市", "玉野市", "笠岡市", "井原市", "浅口市", "高梁市", "新見市", "備前市", "瀬戸内市", "赤磐市", "真庭市", "美作市", "津山市", "その他の県内", "県外"], index=None, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        # STEP 2
        st.markdown("""
        <div class="step-card"><span class="step-badge">STEP 2</span><span class="step-title">デコ活宣言</span>
            <p style="font-size:13px; color:#555; margin-top:5px; line-height:1.4;">
                パネルをヒントに、<strong>「これなら自分もできそう！」</strong>と思ったことを宣言してね。
            </p>
        """, unsafe_allow_html=True)
        declaration_text = st.text_area("宣言内容", placeholder="（例）パネルの「食品ロス削減」を見て、今日からご飯を残さず食べようと思いました！", height=100, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        # STEP 3
        st.markdown("""
        <div class="step-card"><span class="step-badge">STEP 3</span><span class="step-title">感想</span>
        """, unsafe_allow_html=True)
        st.markdown("<p style='font-weight:bold; font-size:14px; margin-bottom:5px;'>Q1. ブースは楽しかったですか？</p>", unsafe_allow_html=True)
        q1 = st.radio("Q1", ["5：とても楽しかった！", "4：楽しかった", "3：ふつう", "2：あまり...", "1：よくなかった"], label_visibility="collapsed")
        st.markdown("<p style='font-weight:bold; font-size:14px; margin-top:10px; margin-bottom:5px;'>Q2. ご感想（自由記述）</p>", unsafe_allow_html=True)
        q2 = st.text_area("Q2", height=80, placeholder="気づいたことなどあれば教えてください", label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)

        # 送信ボタン
        submitted = st.form_submit_button("送信して ガラポンに参加！")

        if submitted:
            if not nickname: st.warning("お名前を入れてね！")
            elif not age: st.warning("年代を選んでね！")
            elif not location: st.warning("お住まいを選んでね！")
            elif not declaration_text: st.warning("宣言を書いてね！")
            else:
                with st.spinner("送信中..."):
                    if save_visitor_data(nickname, gender, age, location, declaration_text, q1, q2):
                        st.session_state['submitted'] = True
                        st.session_state['user_name'] = nickname
                        st.rerun()

# フッター
st.markdown("""
<div style="text-align:center; margin-top:30px; font-size:10px; color:#999; padding-bottom:20px;">
    © 2026 おかやまデコ活フェス
</div>
""", unsafe_allow_html=True)
