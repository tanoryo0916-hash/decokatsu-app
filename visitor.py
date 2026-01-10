import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import time
import uuid

# ==========================================
#  1. 設定＆デザイン（スマホ特化・ミッション風）
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活フェス2026",
    page_icon="🎪",
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
        background-color: #FFF3E0; /* 背景：薄いオレンジ */
    }

    /* ストリームリットの標準余白調整（ヘッダー見切れ防止・強化版） */
    .block-container {
        padding-top: 3.5rem !important; /* ★ここを大幅に増やしました（約56px確保） */
        padding-bottom: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max_width: 100% !important;
    }

    /* --- 🎪 ヘッダーエリア --- */
    .header-area {
        background: linear-gradient(135deg, #FF6F00 0%, #FFCA28 100%);
        padding: 30px 20px 40px 20px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        color: white;
        position: relative;
        overflow: hidden;
    }
    .header-area::before { content: '🎪'; font-size: 30px; position: absolute; top: 20px; left: 20px; opacity: 0.5; }
    .header-area::after { content: '🎁'; font-size: 30px; position: absolute; bottom: 20px; right: 20px; opacity: 0.5; }

    .event-title-main {
        font-size: 28px; font-weight: 900; margin-bottom: 5px;
        text-shadow: 2px 2px 0px rgba(0,0,0,0.2); letter-spacing: 1px;
    }
    .event-title-sub {
        font-size: 16px; font-weight: bold; background-color: rgba(255,255,255,0.2);
        padding: 5px 15px; border-radius: 20px; display: inline-block; margin-bottom: 10px;
    }

    /* --- 📜 ミッションカード --- */
    .mission-card {
        background-color: #ffffff;
        padding: 20px 15px;
        border-radius: 15px;
        box-shadow: 0 4px 0px #E0E0E0;
        border: 2px solid #fff;
        margin-bottom: 25px;
        position: relative;
    }
    
    /* ミッションバッジ */
    .mission-badge {
        background: linear-gradient(90deg, #D32F2F, #FF5252);
        color: white;
        padding: 5px 15px;
        border-radius: 5px 5px 5px 0;
        font-weight: 900;
        font-size: 14px;
        position: absolute;
        top: -10px;
        left: -5px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }
    .mission-badge::before {
        content: ""; position: absolute; bottom: -5px; left: 0;
        border-top: 5px solid #8B0000; border-left: 5px solid transparent;
    }

    .mission-title {
        margin-top: 15px; font-size: 18px; font-weight: bold; color: #333;
        border-bottom: 2px dashed #FFCC80; padding-bottom: 5px; margin-bottom: 15px;
    }

    /* 矢印 */
    .next-arrow {
        text-align: center; font-size: 30px; color: #FF9800; margin: -15px 0 10px 0; font-weight: bold;
    }

    /* 入力フィールド調整 */
    div[data-baseweb="input"], div[data-baseweb="textarea"], div[data-baseweb="select"] { 
        font-size: 16px !important; background-color: #FAFAFA; 
    }
    
    /* ラジオボタン＆チェックボックス調整 */
    div[role="radiogroup"] label, div[data-baseweb="checkbox"] label {
        background-color: #FAFAFA; padding: 10px; border-radius: 8px; margin-bottom: 5px;
        border: 1px solid #EEEEEE; width: 100%;
    }
    div[data-baseweb="checkbox"] {
        margin-bottom: 8px;
    }

    /* --- コンプリートボタン --- */
    .stButton>button {
        width: 100%; height: 75px; font-size: 20px !important; border-radius: 35px;
        font-weight: 900; background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%);
        color: white; border: none; box-shadow: 0 6px 0px #1B5E20; /* 立体ボタン */
        margin-top: 10px; position: relative; top: 0; transition: all 0.1s;
    }
    .stButton>button:active {
        top: 6px; box-shadow: 0 0 0 #1B5E20; /* 押した時の沈み込み */
    }

    /* --- 完了チケット --- */
    .ticket-card {
        background: linear-gradient(135deg, #FFF9C4 0%, #FFF59D 100%);
        border: 4px dashed #FBC02D;
        border-radius: 20px;
        padding: 30px 20px;
        text-align: center;
        margin-top: 15px;
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        color: #5D4037;
        animation: popUp 0.5s ease-out;
    }
    @keyframes popUp {
        0% { transform: scale(0.8); opacity: 0; }
        100% { transform: scale(1); opacity: 1; }
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

# ★ここに実際のブース名を記入してください★
BOOTH_LIST = [
    "次世代EV車展示",
    "ソーラーカー工作",
    "古着リメイク",
    "地元野菜マルシェ",
    "省エネ家電クイズ",
    "廃油キャンドル",
    "海洋プラゴミ展示",
    "水素エネルギー体験",
    "フードドライブ",
    "企業ブースA",
    "企業ブースB",
    "その他"
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
        st.error(f"接続エラー: {e}")
        return None

def save_visitor_data(nickname, gender, age, location, action_text, visited_booths_str, q1_score, q2_text):
    client = get_connection()
    if not client: return False

    try:
        sheet = client.open("decokatsu_db").sheet1
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_id = f"VIS_{datetime.datetime.now().strftime('%H%M%S')}_{str(uuid.uuid4())[:4]}"
        
        # メモ欄に属性と宣言を集約
        memo_content = f"【属性】{age}/{gender}/{location}\n【宣言】{action_text}"
        
        # 保存
        sheet.append_row([now, user_id, nickname, "一般来場", "ミッションコンプリート", 0, memo_content, q1_score, q2_text, visited_booths_str])
        return True
    except Exception as e:
        st.error(f"送信エラー: {e}")
        return False

# ==========================================
#  3. 画面構成
# ==========================================

if 'submitted' not in st.session_state: st.session_state['submitted'] = False
if 'user_name' not in st.session_state: st.session_state['user_name'] = ""

# --- 🎪 ヘッダー表示 ---
if not st.session_state['submitted']:
    st.markdown("""
    <div class="header-area">
        <div class="event-title-main">おかやま<br>デコ活フェス2026</div>
        <div class="event-title-sub">会場限定ミッション</div>
        <div style="font-size:14px; font-weight:bold; color:rgba(255,255,255,0.9); line-height:1.5;">
            4つのミッションをクリアして<br>
            <strong>🎁 ガラポン抽選券</strong> を手に入れよう！
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- メイン処理 ---
if st.session_state['submitted']:
    # === 送信完了画面 ===
    st.balloons()
    st.markdown("""
    <div class="header-area" style="background: linear-gradient(135deg, #4CAF50 0%, #2E7D32 100%); padding-bottom:40px;">
        <div class="event-title-main">🎉 ミッション<br>コンプリート！</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="ticket-card" style="margin-top:-40px; position:relative; z-index:1;">
        <div style="font-size:22px; font-weight:900; color:#E65100; border-bottom:3px solid #E65100; display:inline-block; margin-bottom:15px;">
            🎟 ガラポン参加チケット
        </div>
        <div style="font-size:14px; font-weight:bold;">完全制覇おめでとう！</div>
        <div class="ticket-name">{st.session_state['user_name']} 様</div>
        <div style="background-color:white; padding:15px; border-radius:10px; display:inline-block; font-weight:bold; font-size:15px; margin-top:10px; color:#333; box-shadow:0 2px 5px rgba(0,0,0,0.1);">
            この画面をスタッフに見せて<br>ガラポンを回してね！
        </div>
        <div style="font-size:12px; color:#888; margin-top:20px;">
            発行日: {datetime.date.today().strftime('%Y年%m月%d日')}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("戻る（新しい人が挑戦する）"):
        st.session_state['submitted'] = False
        st.session_state['user_name'] = ""
        st.rerun()

else:
    # === 入力フォーム ===
    with st.form("visitor_form"):
        # MISSION 1
        st.markdown("""
        <div class="mission-card">
            <div class="mission-badge">MISSION 1</div>
            <div class="mission-title">📝 ヒーロー登録をせよ！</div>
        """, unsafe_allow_html=True)
        st.markdown("**お名前（ニックネーム）**")
        nickname = st.text_input("名前", placeholder="例：ももたろう", label_visibility="collapsed")
        st.markdown("**年代**")
        age = st.radio("年代", ["小学生未満", "小学生", "中学生", "高校生", "18〜19歳", "20代", "30代", "40代", "50代", "60代", "70代以上"], index=None, label_visibility="collapsed")
        st.markdown("**お住まい**")
        location = st.radio("お住まい", ["倉敷市", "岡山市", "総社市", "玉野市", "笠岡市", "井原市", "浅口市", "高梁市", "新見市", "備前市", "瀬戸内市", "赤磐市", "真庭市", "美作市", "津山市", "その他の県内", "県外"], index=None, label_visibility="collapsed")
        st.markdown("**性別**")
        gender = st.radio("性別", ["男性", "女性", "その他・無回答"], horizontal=True, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="next-arrow">▼</div>', unsafe_allow_html=True)

        # MISSION 2
        st.markdown("""
        <div class="mission-card">
            <div class="mission-badge">MISSION 2</div>
            <div class="mission-title">📢 デコ活宣言をせよ！</div>
            <p style="font-size:13px; color:#555; line-height:1.5;">
                会場のパネルを見て、<strong>「これなら自分もできそう！」</strong>と思ったことをここに宣言してね。
            </p>
        """, unsafe_allow_html=True)
        declaration_text = st.text_area("宣言内容", placeholder="（例）パネルにあった「食品ロス削減」を見て、今日からご飯を残さず食べようと思いました！", height=100, label_visibility="collapsed")
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="next-arrow">▼</div>', unsafe_allow_html=True)

        # MISSION 3 (ブース選択・チェックボックス形式)
        st.markdown("""
        <div class="mission-card">
            <div class="mission-badge">MISSION 3</div>
            <div class="mission-title">👣 ブースを4つ回れ！</div>
            <p style="font-size:13px; color:#555; line-height:1.5;">
                回ったブースにチェックを入れてね。<br>
                <strong>4つ以上チェック</strong>するとクリアだよ！
            </p>
        """, unsafe_allow_html=True)
        
        # チェックボックスを2列で配置
        selected_booths = []
        cols = st.columns(2)
        for i, booth_name in enumerate(BOOTH_LIST):
            if cols[i % 2].checkbox(booth_name, key=f"booth_{i}"):
                selected_booths.append(booth_name)
        
        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
        booth_count = len(selected_booths)
        if booth_count >= 4:
            st.markdown(f"✅ **{booth_count}個** 回った！ <span style='color:green; font-weight:bold;'>条件クリア！</span>", unsafe_allow_html=True)
        elif booth_count > 0:
            st.markdown(f"あと **{4 - booth_count}個** でクリアだよ！", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('<div class="next-arrow">▼</div>', unsafe_allow_html=True)

        # MISSION 4 (アンケート)
        st.markdown("""
        <div class="mission-card">
            <div class="mission-badge">MISSION 4</div>
            <div class="mission-title">💌 最後にアンケート！</div>
        """, unsafe_allow_html=True)
        
        st.markdown("<p style='font-weight:bold; font-size:14px; margin-bottom:5px;'>Q1. フェスは楽しかったですか？</p>", unsafe_allow_html=True)
        q1 = st.radio("Q1", ["5：とても楽しかった！", "4：楽しかった", "3：ふつう", "2：あまり...", "1：よくなかった"], label_visibility="collapsed")
        
        st.markdown("<p style='font-weight:bold; font-size:14px; margin-top:10px; margin-bottom:5px;'>Q2. ご感想・気づいたこと</p>", unsafe_allow_html=True)
        q2 = st.text_area("Q2", height=80, placeholder="自由記述", label_visibility="collapsed")
        
        st.markdown('</div>', unsafe_allow_html=True)

        # コンプリートボタン
        submitted = st.form_submit_button("ミッションコンプリート！\n（抽選券ゲット）")

        if submitted:
            if not nickname: st.warning("MISSION 1：お名前を入力してね！")
            elif not age: st.warning("MISSION 1：年代を選択してね！")
            elif not location: st.warning("MISSION 1：お住まいを選択してね！")
            elif not declaration_text: st.warning("MISSION 2：宣言を書いてね！")
            elif len(selected_booths) < 4: st.error(f"MISSION 3：ブースがあと{4-len(selected_booths)}個足りないよ！")
            else:
                with st.spinner("データ送信中..."):
                    booth_str = ", ".join(selected_booths)
                    if save_visitor_data(nickname, gender, age, location, declaration_text, booth_str, q1, q2):
                        st.session_state['submitted'] = True
                        st.session_state['user_name'] = nickname
                        st.rerun()

# フッター
st.markdown("""
<div style="text-align:center; margin-top:30px; font-size:10px; color:#999; padding-bottom:20px;">
    © 2026 おかやまデコ活フェス
</div>
""", unsafe_allow_html=True)
