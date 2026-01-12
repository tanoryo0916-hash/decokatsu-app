import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import time
import os
import base64
import random

# --- 真っ白画面回避のための安全策 ---
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# ==========================================
#  1. 設定＆デザイン
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活チャレンジ",
    page_icon="🍑",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS設定（スマホ最適化＆ヘッダー見切れ修正版） ---
st.markdown("""
<style>
    /* 全体のフォント設定 */
    html, body, [class*="css"] {
        font-family: 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
        color: #333;
    }

    /* --- 📱 Streamlit標準の余白調整（ヘッダー見切れ防止・強化版） --- */
    .block-container {
        padding-top: 3.5rem !important;
        padding-bottom: 3rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max_width: 100% !important;
    }

    /* --- 🍑 ボタンのデザイン --- */
    .stButton>button {
        width: 100%;
        height: 70px;
        font-size: 20px !important;
        border-radius: 35px;
        font-weight: 900;
        border: none;
        color: white;
        background: linear-gradient(135deg, #FF9800 0%, #FF5722 100%);
        box-shadow: 0 4px 15px rgba(255, 87, 34, 0.4);
        transition: all 0.3s ease;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(255, 87, 34, 0.6);
        color: white;
    }
    .stButton>button:active {
        transform: translateY(1px);
        box-shadow: 0 2px 10px rgba(255, 87, 34, 0.4);
    }

    /* --- 🏫 ログインフォームのカード化 --- */
    div[data-testid="stForm"] {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        border: 2px solid #FFF3E0;
    }

    /* 入力フィールドのデザイン */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        border-radius: 12px;
        background-color: #FAFAFA;
        border: 2px solid #EEEEEE;
        transition: border-color 0.3s;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within, div[data-baseweb="textarea"]:focus-within {
        border-color: #FF9800;
        background-color: #fff;
    }

    .school-suffix {
        font-size: 18px;
        font-weight: bold;
        padding-top: 35px;
        color: #555;
    }

    /* --- 🏆 ユーザー用 認定証カード --- */
    .hero-card {
        background: linear-gradient(135deg, #FFD54F, #FFECB3);
        border: 4px solid #FFA000;
        border-radius: 20px;
        padding: 25px;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        color: #5D4037;
        position: relative;
        overflow: hidden;
    }
    .hero-card::before {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255,255,255,0.8) 0%, rgba(255,255,255,0) 60%);
        transform: rotate(30deg);
        opacity: 0.3;
        pointer-events: none;
    }
    .hero-title {
        font-size: 26px;
        font-weight: bold;
        margin-bottom: 10px;
        text-shadow: 1px 1px 0px rgba(255,255,255,0.8);
        color: #E65100;
    }
    .hero-name {
        font-size: 32px;
        font-weight: 900;
        border-bottom: 3px dashed #5D4037;
        display: inline-block;
        margin: 15px 0;
        padding-bottom: 5px;
    }

    /* --- 👑 ログイン画面：認定ヒーロー数 --- */
    @keyframes shine {
        0% { background-position: -100px; }
        40%, 100% { background-position: 300px; }
    }
    .special-hero-stats {
        background: linear-gradient(135deg, #FFC107 0%, #FFECB3 50%, #FF8F00 100%);
        border: 4px solid #FFFFFF;
        border-radius: 20px;
        padding: 20px;
        text-align: center;
        margin-bottom: 15px;
        box-shadow: 0 10px 25px rgba(255, 143, 0, 0.4);
        position: relative;
        overflow: hidden;
    }
    .special-hero-stats::after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.6) 50%, rgba(255,255,255,0) 100%);
        background-repeat: no-repeat;
        background-size: 50px 100%;
        transform: skewX(-20deg);
        animation: shine 4s infinite linear;
    }
    .special-hero-label {
        font-size: 16px;
        font-weight: bold;
        color: #5D4037;
        letter-spacing: 1px;
        margin-bottom: 5px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 5px;
    }
    .special-hero-num {
        font-size: 60px;
        font-weight: 900;
        color: #BF360C;
        text-shadow: 3px 3px 0px #FFFFFF, 5px 5px 10px rgba(0,0,0,0.2);
        margin: 0;
        line-height: 1;
        font-family: 'Arial', sans-serif;
    }
    .special-hero-unit {
        font-size: 20px;
        color: #5D4037;
        margin-left: 5px;
        text-shadow: none;
    }

    /* --- 📊 ログイン画面：サブ統計 --- */
    .sub-stats-container {
        display: flex;
        gap: 15px;
        margin-bottom: 15px;
    }
    .sub-stat-box {
        flex: 1;
        background: linear-gradient(145deg, #37474F, #263238);
        color: white;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        border: 1px solid #546E7A;
    }
    .sub-stat-label {
        font-size: 12px;
        opacity: 0.8;
        margin-bottom: 5px;
        font-weight: bold;
        color: #B0BEC5;
    }
    .sub-stat-num {
        font-size: 22px;
        font-weight: bold;
        color: #81D4FA;
    }

    /* --- ⚽ サッカーボール換算 --- */
    .soccer-visual {
        background-color: #E8F5E9;
        border: 2px dashed #66BB6A;
        border-radius: 15px;
        padding: 15px;
        text-align: center;
        margin-bottom: 30px;
        color: #2E7D32;
    }
    .soccer-text {
        font-size: 14px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .soccer-count {
        font-size: 24px;
        font-weight: 900;
        color: #1B5E20;
    }

    /* --- 📌 ログイン注意事項ボックス --- */
    .login-guide {
        background-color: #FFEBEE;
        border: 2px solid #FFCDD2;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 20px;
        color: #B71C1C;
        font-size: 14px;
    }
    .login-guide strong {
        color: #D32F2F;
        font-weight: 900;
    }

    /* --- 🎉 イベント告知ボックス --- */
    .event-promo-box {
        background: linear-gradient(135deg, #F8BBD0 0%, #F48FB1 100%);
        border: 4px solid #EC407A;
        border-radius: 20px;
        padding: 25px 20px;
        text-align: center;
        margin-top: 40px;
        margin-bottom: 20px;
        color: #880E4F;
        box-shadow: 0 8px 16px rgba(233, 30, 99, 0.2);
    }
    .event-title {
        font-size: 24px;
        font-weight: 900;
        margin-bottom: 10px;
        color: #C2185B;
        text-shadow: 1px 1px 0px rgba(255,255,255,0.8);
    }
    .event-date {
        background-color: white;
        color: #EC407A;
        font-weight: bold;
        padding: 8px 15px;
        border-radius: 20px;
        display: inline-block;
        margin-bottom: 15px;
        font-size: 18px;
        line-height: 1.5;
    }

    /* --- ℹ️ ミッション説明ボックス --- */
    .mission-box {
        background-color: #FFF8E1;
        border-left: 6px solid #FFAB00;
        border-radius: 8px;
        padding: 15px 20px;
        margin-bottom: 20px;
        color: #333;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .mission-header {
        font-size: 20px;
        font-weight: bold;
        color: #E65100;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* --- 📈 メーターコンテナ --- */
    .metric-container {
        padding: 15px;
        background-color: #F1F8E9;
        border-radius: 15px;
        border: 2px solid #C5E1A5;
        text-align: center;
        margin-bottom: 10px;
    }

    /* --- 🍑 タイトルデザイン（PC標準） --- */
    .main-title {
        text-align: center;
        font-size: 32px;
        font-weight: 900;
        color: #2E7D32;
        margin-bottom: 20px;
        text-shadow: 1px 1px 0 #fff, -1px -1px 0 #fff, 2px 2px 0 rgba(0,0,0,0.1);
    }

    /* --- 🦶 フッター --- */
    .footer-container {
        margin-top: 60px;
        padding-top: 30px;
        border-top: 1px solid #EEEEEE;
        text-align: center;
        font-size: 12px;
        color: #90A4AE;
    }
    .footer-label {
        font-weight: bold;
        margin-bottom: 5px;
        color: #546E7A;
        font-size: 13px;
    }

    /* --- 📚 デコ活説明コーナー --- */
    .decokatsu-intro {
        background-color: #E3F2FD;
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 20px;
        border: 2px solid #BBDEFB;
    }
    .intro-header {
        color: #1976D2;
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 15px;
        border-bottom: 2px dashed #90CAF9;
        padding-bottom: 8px;
        text-align: center;
    }
    .kids-action {
        background-color: #FFFDE7;
        border: 3px dashed #FDD835;
        padding: 15px;
        border-radius: 15px;
        text-align: center;
        margin-bottom: 20px;
        font-weight: bold;
        color: #5D4037;
        font-size: 18px;
    }
    .parent-memo {
        background-color: #fff;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #E0E0E0;
        font-size: 14px;
        margin-top: 15px;
        color: #555;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }

    /* --- タブのデザイン強化 --- */
    div[data-baseweb="tab-list"] {
        gap: 8px;
        margin-bottom: 10px;
        flex-wrap: wrap;
    }
    button[data-baseweb="tab"] {
        background-color: #FFF3E0;
        border: 1px solid #FFE0B2;
        border-radius: 20px 20px 0 0;
        font-weight: bold;
        color: #EF6C00;
        padding: 12px 10px;
        font-size: 14px;
        transition: all 0.2s;
        flex-grow: 1;
    }
    button[data-baseweb="tab"]:hover {
        background-color: #FFE0B2;
        padding-top: 10px;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background-color: #FF9800 !important;
        color: white !important;
        border: none;
        box-shadow: 0 -2px 5px rgba(0,0,0,0.1);
    }

    /* =========================================
       📱 スマホ用レスポンシブ対応 (画面幅600px以下)
       ========================================= */
    @media only screen and (max-width: 600px) {
        .main-title { font-size: 24px !important; }
        .hero-name { font-size: 24px !important; }
        .stat-num { font-size: 24px !important; }
        .special-hero-num { font-size: 40px !important; }
        div[data-testid="stForm"] { padding: 15px !important; }
        .hero-card, .mission-box, .decokatsu-intro { padding: 15px !important; }
        .custom-header { height: 180px !important; }
        .header-title-main { font-size: 28px !important; }
        .header-title-sub { font-size: 12px !important; padding: 5px 10px !important; }
        .stButton>button { font-size: 18px !important; height: 60px !important; }
        .school-suffix { font-size: 14px; padding-top: 40px; }
        .event-title { font-size: 20px !important; }
        .event-date { font-size: 14px !important; }
        
        /* 表の文字サイズ調整 */
        div[data-testid="stDataEditor"] { font-size: 12px !important; }
        th, td { padding: 5px !important; }
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
#  2. データ定義
# ==========================================

OKAYAMA_PRAISE_LIST = [
    "ぼっけぇ すごいが！",
    "でーれー がんばったな！",
    "さすがじゃ！ そのちょうし！",
    "おめぇは ほんまに えらい！",
    "地球（ちきゅう）が よろこびょーるで！",
    "すごいが！ ヒーローじゃな！",
    "明（あ）したも がんばられー！"
]

ECO_TRIVIA_LIST = [
    "シャワーを 1分（ぷん） とめるだけで、ペットボトル 200本（ぽん）ぶんの 水（みず）が せつやく できるんで！",
    "テレビを 1時間（じかん） けすと、風船（ふうせん） 400個（こ）ぶんの CO2（シーオーツー）が へらせるんよ。",
    "岡山県（おかやまけん）は 「晴（は）れの国（くに）」 じゃけど、 水（みず）は とっても 大切（たいせつ）なんよ。",
    "ごはんを のこさず 食べると、ゴミも へるし 体（からだ）も 元気（げんき）に なるで！",
    "冷房（れいぼう）の 温度（おんど）を 1℃（ど） かえるだけで、電気（でんき）代（だい）が 安（やす）く なるんよ。",
    "リサイクル できない ゴミを もやすと、たくさんの CO2（シーオーツー）が でてしまうんよ。",
    "近（ちか）くの お店（みせ）には、車（くるま）じゃなくて 歩（ある）いていくのが かっこいい！"
]

# ==========================================
#  3. Google Sheets 接続設定
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
        st.error("システムエラー: 設定(Secrets)を確認してください")
        return None

def display_pdf(file_path):
    try:
        with open(file_path, "rb") as f:
            base64_pdf = base64.b64encode(f.read()).decode('utf-8')
        pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="600" type="application/pdf"></iframe>'
        st.markdown(pdf_display, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"PDF表示エラー: {e}")

@st.cache_data(ttl=60)
def fetch_global_stats():
    client = get_connection()
    if not client: return 0, 0, 0

    try:
        sheet = client.open("decokatsu_db").sheet1
        if HAS_PANDAS:
            data = sheet.get_all_records()
            if not data: return 0, 0, 0
            df = pd.DataFrame(data)
            
            total_co2 = pd.to_numeric(df['CO2削減量'], errors='coerce').sum()
            total_participants = df['ID'].nunique()
            
            hero_df = df[df['実施項目'].astype(str).str.contains("環境の日アンケート", na=False)]
            total_heroes = hero_df['ID'].nunique()
            
            return int(total_co2), int(total_heroes), int(total_participants)
        else:
            return 0, 0, 0
    except Exception as e:
        return 0, 0, 0

def fetch_user_data(school_full_name, grade, u_class, number):
    client = get_connection()
    if not client: return None, None, 0, {}

    try:
        sheet = client.open("decokatsu_db").sheet1
        records = sheet.get_all_records()
        
        user_id = f"{school_full_name}_{grade}_{u_class}_{number}"
        
        total_co2 = 0
        nickname = ""
        history_dict = {} 
        
        for row in records:
            if str(row.get('ID')) == user_id:
                try:
                    val = int(row.get('CO2削減量', 0))
                    total_co2 += val
                except:
                    pass
                if row.get('ニックネーム'):
                    nickname = row.get('ニックネーム')
                
                r_date = row.get('対象日付')
                r_actions = row.get('実施項目')
                if r_date:
                    history_dict[r_date] = str(r_actions).split(", ") if r_actions else []
        
        return user_id, nickname, total_co2, history_dict

    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return None, None, 0, {}

def save_daily_challenge(user_id, nickname, target_date, actions_done, total_points, memo, q1="", q2="", q3=""):
    client = get_connection()
    if not client: return False

    try:
        sheet = client.open("decokatsu_db").sheet1
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        actions_str = ", ".join(actions_done)
        
        sheet.append_row([now, user_id, nickname, target_date, actions_str, total_points, memo, q1, q2, q3])
        fetch_global_stats.clear()
        return True
    except Exception as e:
        st.error(f"保存失敗: {e}")
        return False

# ★ イベント誘導（チラシ表示）関数（日程・会場変更反映）
def show_event_promo():
    st.markdown("""
    <div class="event-promo-box">
        <div class="event-title">🎉 おかやまデコ活フェス2026 🎉</div>
        <div class="event-date">6月7日(日) 10:00〜19:00<br>イオンモール倉敷 ノースコートにて</div>
        <p><strong>特別（とくべつ）ミッションを クリアしたら、<br>会場（かいじょう）へ あそびにきてね！</strong></p>
        <p style="font-size:14px; background-color:white; padding:10px; border-radius:10px; display:inline-block;">
        受付（うけつけ）で<strong>「学校名」と「名前」</strong>を言うだけで<br>ガラポン抽選（ちゅうせん）に参加できるよ！
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    img_path = "fes_flyer.jpg"
    if os.path.exists(img_path):
        st.image(img_path, caption="おかやまデコ活フェス2026 チラシ", use_column_width=True)
    else:
        st.info("※ここに「フェスのチラシ画像」が表示されます")

def show_footer():
    st.markdown("""
    <div class="footer-container">
        <div class="footer-section">
            <div class="footer-label">主催</div>
            <div>日本青年会議所 中国地区 岡山ブロック協議会<br>環境未来デザイン委員会</div>
        </div>
        <div class="footer-section">
            <div class="footer-label">後援</div>
            <div>（ここに後援団体名が入ります）</div>
        </div>
        <div class="footer-section">
            <div class="footer-label">協賛</div>
            <div>（ここに協賛企業名が入ります）</div>
        </div>
        <div style="margin-top:20px; font-size:10px;">
            © 2026 Okayama Decokatsu Challenge
        </div>
    </div>
    """, unsafe_allow_html=True)

# ==========================================
#  4. セッション管理
# ==========================================
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# ==========================================
#  5. 画面コンポーネント
# ==========================================

import time
import random
import json
import os
import base64
import datetime
import streamlit as st

# --- 🎮 激闘！分別マスター（BGM微音・クリア時停止版） ---
def show_sorting_game():
    
    # 📁 設定：ファイル名
    DATA_FILE = "ranking_log.json"
    FILES = {
        "bgm": "bgm.mp3",
        "correct": "correct.mp3",
        "wrong": "wrong.mp3",
        "clear": "clear.mp3"
    }

    # --- 🛠️ 音声再生関数 ---
    def get_audio_html(filename, loop=False, volume=0.5):
        file_path = os.path.abspath(filename)
        
        if not os.path.exists(file_path):
            return ""

        try:
            with open(file_path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode()
            mime_type = "audio/mpeg"
        except Exception:
            return ""

        rnd_id = random.randint(0, 1000000)
        loop_attr = "loop" if loop else ""
        
        # volume変数をJSに渡して制御
        return f"""
            <div style="width:0; height:0; overflow:hidden;">
                <audio id="audio_{rnd_id}" {loop_attr} autoplay>
                    <source src="data:{mime_type};base64,{b64}" type="audio/mp3">
                </audio>
                <script>
                    var audio = document.getElementById("audio_{rnd_id}");
                    audio.volume = {volume};
                    var playPromise = audio.play();
                    if (playPromise !== undefined) {{
                        playPromise.catch(error => {{
                            console.log("Auto-play blocked");
                        }});
                    }}
                </script>
            </div>
        """

    # --- 🛠️ データ保存・読込 ---
    def load_logs():
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_log(name, school, score_time):
        logs = load_logs()
        today_str = datetime.date.today().isoformat()
        new_record = {
            "name": name,
            "school": school,
            "time": score_time,
            "date": today_str
        }
        logs.append(new_record)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    # --- 🛠️ ランキング集計 ---
    def get_rankings(mode="all"):
        logs = load_logs()
        if not logs: return []
        
        today_str = datetime.date.today().isoformat()
        best_records = {} 

        for record in logs:
            if mode == "daily" and record["date"] != today_str:
                continue
            key = f"{record['school']}_{record['name']}"
            if key not in best_records:
                best_records[key] = record
            else:
                if record["time"] < best_records[key]["time"]:
                    best_records[key] = record
        
        ranking_list = list(best_records.values())
        ranking_list.sort(key=lambda x: x["time"])
        return ranking_list

    # --- 🛠️ ユーザー情報・自己ベスト ---
    def get_user_info():
        info = st.session_state.get('user_info', {})
        return info.get('name', 'ゲスト'), info.get('school', '体験入学校')

    def get_personal_best():
        name, school = get_user_info()
        for r in get_rankings(mode="all"):
            if r['name'] == name and r['school'] == school:
                return r['time']
        return None

    # --- 🎨 デザインCSS ---
    st.markdown("""
    <style>
        .game-header {
            background-color:#FFF3E0; padding:15px; border-radius:15px; 
            border:3px solid #FF9800; text-align:center; margin-bottom:10px;
        }
        .question-box {
            text-align:center; padding:20px; background-color:#FFFFFF; 
            border-radius:15px; margin:20px 0; border:4px solid #607D8B;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            min-height: 120px;
            display: flex; align-items: center; justify-content: center;
        }
        .feedback-overlay {
            position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
            z-index: 9999; padding: 30px; border-radius: 20px; text-align: center;
            width: 80%; max-width: 350px; box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            background-color: white;
            animation: popIn 0.2s ease-out;
        }
        @keyframes popIn {
            0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0; }
            100% { transform: translate(-50%, -50%) scale(1); opacity: 1; }
        }
        .personal-best {
            text-align: right; font-size: 14px; color: #555; 
            background-color: #f0f2f6; padding: 5px 10px; border-radius: 5px;
            margin-top: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- 1. データ定義 ---
    garbage_data = [
        {"name": "🍌 バナナの皮", "type": 0}, {"name": "🤧 使ったティッシュ", "type": 0},
        {"name": "🥢 汚れた割り箸", "type": 0}, {"name": "🧸 古いぬいぐるみ", "type": 0},
        {"name": "🍂 落ち葉", "type": 0}, {"name": "👕 汚れたTシャツ", "type": 0},
        {"name": "🧾 レシート", "type": 0}, {"name": "🐟 魚の骨", "type": 0},
        {"name": "😷 使い捨てマスク", "type": 0}, {"name": "🥚 卵の殻", "type": 0},
        {"name": "🥤 ペットボトル", "type": 1}, {"name": "🥫 空き缶", "type": 1},
        {"name": "🍾 空き瓶", "type": 1}, {"name": "📰 新聞紙", "type": 1},
        {"name": "📦 ダンボール", "type": 1}, {"name": "🥛 牛乳パック(洗)", "type": 1},
        {"name": "📚 雑誌", "type": 1}, {"name": "📃 チラシ", "type": 1},
        {"name": "🍫 お菓子の箱", "type": 1}, {"name": "📓 ノート", "type": 1},
        {"name": "🍵 割れた茶碗", "type": 2}, {"name": "🥛 割れたコップ", "type": 2},
        {"name": "🧤 ゴム手袋", "type": 2}, {"name": "☂️ 壊れた傘", "type": 2},
        {"name": "🧊 保冷剤", "type": 2}, {"name": "📼 ビデオテープ", "type": 2},
        {"name": "💡 電球", "type": 2}, {"name": "💿 CD・DVD", "type": 2},
        {"name": "🪞 割れた鏡", "type": 2}, {"name": "🔋 乾電池", "type": 2},
    ]
    
    categories = {
        0: {"name": "🔥 燃える", "color": "primary"},
        1: {"name": "♻️ 資 源", "color": "primary"},
        2: {"name": "🧱 埋 立", "color": "secondary"}
    }

    # --- 2. ステート管理 ---
    if 'game_state' not in st.session_state: st.session_state.game_state = 'READY'
    if 'penalty_time' not in st.session_state: st.session_state.penalty_time = 0
    if 'feedback_mode' not in st.session_state: st.session_state.feedback_mode = False
    if 'feedback_result' not in st.session_state: st.session_state.feedback_result = None

    # ヘッダー
    st.markdown("""
    <div class="game-header">
        <div style="font-size:22px; font-weight:bold; color:#E65100;">
            ⏱️ 激闘！分別マスター
        </div>
        <div style="font-size:14px; color:#333;">
            10問タイムアタック / <span style="color:red; font-weight:bold;">ミス ＋5秒</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 自己ベスト
    my_best = get_personal_best()
    best_str = f"{my_best} 秒" if my_best else "記録なし"
    st.markdown(f"""<div class="personal-best">👑 キミの歴代最速： <strong>{best_str}</strong></div>""", unsafe_allow_html=True)

    # --- 3. ゲーム進行 ---
    
    # ■ スタート画面
    if st.session_state.game_state == 'READY':
        col1, col2 = st.columns([2, 1])
        with col1:
            st.info("👇 **スタート** を押してゲーム開始！")
        with col2:
            if st.button("🏁 スタート！", use_container_width=True, type="primary"):
                st.session_state.current_questions = random.sample(garbage_data, 10)
                st.session_state.q_index = 0
                st.session_state.start_time = time.time()
                st.session_state.penalty_time = 0
                st.session_state.feedback_mode = False
                st.session_state.game_state = 'PLAYING'
                st.rerun()

        st.write("")
        tab1, tab2 = st.tabs(["📅 今日のランキング", "🏆 歴代ランキング"])
        
        with tab1:
            daily_ranks = get_rankings(mode="daily")
            if not daily_ranks:
                st.info("今日のチャレンジャーはまだいません。")
            else:
                for i, r in enumerate(daily_ranks[:10]):
                    st.markdown(f"**{i+1}位**：`{r['time']}秒` ({r['name']} / {r['school']})")
        
        with tab2:
            all_ranks = get_rankings(mode="all")
            if not all_ranks:
                st.info("記録がありません。")
            else:
                for i, r in enumerate(all_ranks[:10]):
                    st.markdown(f"**{i+1}位**：`{r['time']}秒` ({r['name']} / {r['school']})")

    # ■ プレイ画面
    elif st.session_state.game_state == 'PLAYING':
        # ★BGM音量変更：volume=0.05 (前回の0.1の半分) に設定★
        st.markdown(get_audio_html(FILES["bgm"], loop=True, volume=0.05), unsafe_allow_html=True)

        q_idx = st.session_state.q_index
        total_q = len(st.session_state.current_questions)
        
        if q_idx >= total_q:
            st.session_state.game_state = 'FINISHED'
            st.rerun()

        target_item = st.session_state.current_questions[q_idx]

        st.progress((q_idx / total_q), text=f"第 {q_idx + 1} 問 / 全 {total_q} 問")
        st.markdown(f"""<div class="question-box"><div style="font-size:32px; font-weight:bold; color:#333;">{target_item['name']}</div></div>""", unsafe_allow_html=True)
        st.caption("このゴミはどれ？ 👇")

        c1, c2, c3 = st.columns(3)
        
        def handle_answer(choice):
            correct = st.session_state.current_questions[q_idx]['type']
            if choice == correct:
                st.session_state.feedback_result = 'correct'
            else:
                st.session_state.feedback_result = 'wrong'
                st.session_state.penalty_time += 5
            st.session_state.feedback_mode = True

        disable_btn = st.session_state.feedback_mode
        with c1:
            if st.button(categories[0]['name'], key=f"btn_{q_idx}_0", type=categories[0]['color'], use_container_width=True, disabled=disable_btn):
                handle_answer(0); st.rerun()
        with c2:
            if st.button(categories[1]['name'], key=f"btn_{q_idx}_1", type=categories[1]['color'], use_container_width=True, disabled=disable_btn):
                handle_answer(1); st.rerun()
        with c3:
            if st.button(categories[2]['name'], key=f"btn_{q_idx}_2", type=categories[2]['color'], use_container_width=True, disabled=disable_btn):
                handle_answer(2); st.rerun()

        # 判定表示
        if st.session_state.feedback_mode:
            if st.session_state.feedback_result == 'correct':
                st.markdown("""<div class="feedback-overlay" style="border:5px solid #4CAF50; background-color:#E8F5E9;"><h1 style="color:#2E7D32; font-size:80px; margin:0;">⭕️</h1><h2 style="color:#2E7D32; margin:0;">せいかい！</h2></div>""", unsafe_allow_html=True)
                st.markdown(get_audio_html(FILES["correct"], volume=0.5), unsafe_allow_html=True)
            else:
                st.markdown("""<div class="feedback-overlay" style="border:5px solid #D32F2F; background-color:#FFEBEE;"><h1 style="color:#D32F2F; font-size:80px; margin:0;">❌</h1><h2 style="color:#D32F2F; margin:0;">ちがうよ！</h2><p style="font-weight:bold; color:red; font-size:20px;">+5秒</p></div>""", unsafe_allow_html=True)
                st.markdown(get_audio_html(FILES["wrong"], volume=0.5), unsafe_allow_html=True)

            time.sleep(1)
            st.session_state.start_time += 1.0
            st.session_state.feedback_mode = False
            
            if st.session_state.q_index + 1 >= len(st.session_state.current_questions):
                st.session_state.final_time = round(time.time() - st.session_state.start_time + st.session_state.penalty_time, 2)
                # 自動保存
                name, school = get_user_info()
                save_log(name, school, st.session_state.final_time)
                st.session_state.game_state = 'FINISHED'
            else:
                st.session_state.q_index += 1
            st.rerun()

    # ■ クリア画面（BGMタグがないため、自然にBGMが停止します）
    elif st.session_state.game_state == 'FINISHED':
        st.markdown(get_audio_html(FILES["clear"], volume=0.5), unsafe_allow_html=True)
        st.balloons()
        my_time = st.session_state.final_time
        name, school = get_user_info()

        st.markdown(f"""
        <div style="text-align:center; padding:20px; background-color:white; border-radius:15px; border:2px solid #eee;">
            <h2 style="color:#E91E63; margin:0;">🎉 ゲームクリア！</h2>
            <div style="font-size:50px; font-weight:bold; color:#333; margin:10px 0;">{my_time} <span style="font-size:20px;">秒</span></div>
            <div style="color:red; font-size:14px; margin-bottom:15px;">(ペナルティ +{st.session_state.penalty_time}秒 含む)</div>
            <div style="background-color:#E3F2FD; padding:10px; border-radius:10px; color:#0D47A1; margin-bottom:10px;">
                <strong>{school}</strong> の <strong>{name}</strong> さん<br>記録を保存しました！💾
            </div>
        </div>""", unsafe_allow_html=True)
        st.write("") 
        if st.button("もういちど遊ぶ", type="primary", use_container_width=True):
            st.session_state.game_state = 'READY'
            st.rerun()
            
def login_screen():
    # --- おしゃれなカスタムヘッダー ---
    header_bg_url = "https://images.unsplash.com/photo-1501854140801-50d01698950b?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1920&q=80"

    st.markdown(f"""
    <style>
        .custom-header {{
            background-image: linear-gradient(rgba(0, 0, 0, 0.3), rgba(0, 0, 0, 0.3)), url('{header_bg_url}');
            background-size: cover;
            background-position: center;
            height: 250px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            border-radius: 0 0 25px 25px;
            margin-bottom: 35px;
            color: white;
            box-shadow: 0 10px 20px rgba(0,0,0,0.15);
        }}
        .header-title-main {{
            font-size: 42px;
            font-weight: 900;
            margin: 0;
            padding: 0;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.6);
            letter-spacing: 2px;
        }}
        .header-title-sub {{
            font-size: 18px;
            font-weight: bold;
            margin-top: 15px;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            background-color: rgba(255, 152, 0, 0.9);
            padding: 8px 20px;
            border-radius: 30px;
            display: inline-block;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }}
    </style>
    <div class="custom-header">
        <div class="header-title-main">🍑 おかやまデコ活チャレンジ</div>
        <div class="header-title-sub">目指せ！岡山県で10,000人のエコヒーロー！</div>
    </div>
    """, unsafe_allow_html=True)

    # === ★ デコ活説明コーナー ===
    with st.expander("🔰 最初のミッション：おうちの人と「デコ活」を知ろう！（ここをクリック）", expanded=False):
        
        st.markdown("""
        <div class="kids-action">
            📢 チャレンジを はじめる 前（まえ）に、<br>おうちの 人（ひと）と 一緒（いっしょ）に <br>「デコ活」って なにか 見（み）てみよう！
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="decokatsu-intro">
            <div class="intro-header">STEP 1： 「デコ活」ってなあに？</div>
            <p style="text-align:center;">おうちの人と一緒に、下の絵を見てみよう。</p>
        </div>
        """, unsafe_allow_html=True)

        img1 = "decokatsu_panel_ver03_page-0001.jpg"
        if os.path.exists(img1):
            st.image(img1, caption="出典：環境省「デコ活」資料", use_column_width=True)
        else:
            st.info("※ここに「デコ活とは（蝶のロゴ）」の資料が表示されます")

        st.markdown("""
        <div class="parent-memo">
            <strong>👩‍🏫 おうちの方へ（お子様への伝え方ヒント）</strong><br>
            「この蝶々のマークはね、<strong>みんなの小さな良いこと（エコ）が、地球を救う大きな風になる</strong>っていう意味なんだよ。<br>
            君がスイッチをパチンと消すだけで、地球にとっても良いことがあるんだよ！」
        </div>
        <br>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="decokatsu-intro">
            <div class="intro-header">STEP 2： なにをすればいいの？</div>
            <p style="text-align:center;">いろんな「デコ活」があるよ！下のタブを押して見てみてね。</p>
        </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 全体のまとめ", "🏡 毎日の生活", "🍚 食べ物", "💡 家電・暮らし", "👕 服・ファッション"])
        
        with tab1:
            img_sum = "decokatsu_panel_ver03_page-0002.jpg"
            if os.path.exists(img_sum):
                st.image(img_sum, use_column_width=True, caption="出典：環境省")
        
        with tab2:
            img_daily = "deco_poster_action_ver_03_page-0001.jpg"
            if os.path.exists(img_daily):
                st.image(img_daily, use_column_width=True, caption="出典：環境省")
        
        with tab3:
            img_food = "deco_poster_action_ver_02_page-0001.jpg"
            if os.path.exists(img_food):
                st.image(img_food, use_column_width=True, caption="出典：環境省")
        
        with tab4:
            img_home = "deco_poster_action_ver_05_page-0001.jpg"
            if os.path.exists(img_home):
                st.image(img_home, use_column_width=True, caption="出典：環境省")

        with tab5:
            img_fashion = "deco_poster_action_ver_01_page-0001.jpg"
            if os.path.exists(img_fashion):
                st.image(img_fashion, use_column_width=True, caption="出典：環境省")

        st.markdown("""
        <div class="parent-memo">
            <strong>👩‍🏫 おうちの方へ</strong><br>
            このアプリのチェックリストにある「電気・食事・水・ゴミ」のアクションは、これらのポスターの内容を小学生向けにピックアップしたものです。<br>
            ぜひポスターを見ながら、「うちではこれができそうだね！」と話し合ってみてください。
        </div>
        <br>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="decokatsu-intro">
            <div class="intro-header">STEP 3： 未来はどうなるの？</div>
            <p style="text-align:center;">デコ活を続けると、10年後の未来はこんなに素敵になるよ！</p>
        </div>
        """, unsafe_allow_html=True)

        img3 = "decokatsu_panel_ver03_page-0003.jpg"
        if os.path.exists(img3):
            st.image(img3, caption="出典：環境省「デコ活」資料", use_column_width=True)
        else:
            st.info("※ここに「10年後の暮らし」の資料が表示されます")

        st.markdown("""
        <div class="parent-memo">
            <strong>👩‍🏫 おうちの方へ（未来の姿）</strong><br>
            「エコな生活をすると、地球を守れるだけじゃなくて、<strong>おうちが快適になったり、お金の節約になったり、家族の時間が増えたりする</strong>んだって！<br>
            みんなが笑顔になれる未来を目指そうね。」
        </div>
        """, unsafe_allow_html=True)

    if HAS_PANDAS:
        g_co2, g_heroes, g_participants = fetch_global_stats()
        
        # --- 認定ヒーロー数（豪華版） ---
        st.markdown(f"""
        <div class="special-hero-stats">
            <div class="special-hero-label">👑 現在の 認定エコヒーロー</div>
            <p class="special-hero-num">{g_heroes:,}<span class="special-hero-unit">人</span></p>
        </div>
        """, unsafe_allow_html=True)

        # --- サブ統計（参加者・CO2） ---
        st.markdown(f"""
        <div class="sub-stats-container">
            <div class="sub-stat-box">
                <div class="sub-stat-label">現在の参加者</div>
                <div class="sub-stat-num">{g_participants:,}<span style="font-size:12px;">人</span></div>
            </div>
            <div class="sub-stat-box">
                <div class="sub-stat-label">CO2削減量</div>
                <div class="sub-stat-num">{g_co2:,}<span style="font-size:12px;">g</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # --- ⚽ サッカーボール換算 ---
        soccer_balls = int(g_co2 / 10)  # 10g = 1球（約）
        st.markdown(f"""
        <div class="soccer-visual">
            <div class="soccer-text">もし、みんなが減らしたCO2が<br>⚽サッカーボール⚽ だったら…？</div>
            <div class="soccer-count">{soccer_balls:,} <span style="font-size:16px;">個分！</span></div>
            <div style="font-size:10px; opacity:0.8;">※CO2 1kg(1000g)の体積 ≒ サッカーボール約100個分として計算</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🏫 ヒーロー登録（ログイン）")
    
    # === ★ ログイン注意事項 ===
    st.markdown("""
    <div class="login-guide">
        <strong>📌 わすれないでね！</strong><br>
        ① つづきから するときは、いつも <strong>おなじ「学年・組・番号」</strong> を いれてね。<br>
        ② この ページを <strong>「ブックマーク（お気に入り）」</strong> して、また すぐ これるように してね！
    </div>
    """, unsafe_allow_html=True)

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

        submit = st.form_submit_button("ミッション スタート！", type="primary")

        if submit:
            if not school_core or not nickname_input or not u_class:
                st.warning("すべて入力してね！")
                return

            with st.spinner("データを読み込んでいます..."):
                full_school_name = f"{school_core}小学校"
                
                user_id, saved_name, total, history_dict = fetch_user_data(full_school_name, grade, u_class, number)
                final_name = saved_name if saved_name else nickname_input
                
                st.session_state.user_info = {
                    'id': user_id,
                    'name': final_name,
                    'total_co2': total,
                    'school': full_school_name,
                    'history_dict': history_dict
                }
                st.rerun()
    
    # ★ フェス誘導（ログイン画面下）
    show_event_promo()
    show_footer()

def main_screen():
    user = st.session_state.user_info
    
    is_eco_hero = False
    for actions in user['history_dict'].values():
        if "環境の日アンケート" in actions:
            is_eco_hero = True
            break
    
    st.markdown("### 🍑 おかやまデコ活チャレンジ")
    st.markdown(f"**👋 こんにちは、{user['name']} さん！**")
    
    if is_eco_hero:
        st.markdown(f"""
        <div class="hero-card">
            <div class="hero-title">🏆 おかやまエコヒーロー 認定証</div>
            <div>この証明書は、地球を守る活動に貢献した証です。</div>
            <div class="hero-name">{user['name']} 殿</div>
            <div style="font-weight:bold; color:#D84315;">あなたは 10,000人チャレンジの<br>ひとりとして認定されました！</div>
            <div style="margin-top:10px; font-size:12px;">2026年6月5日 環境の日</div>
        </div>
        """, unsafe_allow_html=True)
        st.balloons()

    GOAL = 500
    MAX_POSSIBLE = 1340
    current = user['total_co2']
    progress_val = min(current / MAX_POSSIBLE, 1.0)
    
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.metric("現在のCO2削減量", f"{current} g")
    with col2:
        if current < GOAL:
            st.metric("まずは目標クリアまで", f"あと {GOAL - current} g")
        else:
             st.metric("目標クリア！", "🎉達成！")
    st.markdown('</div>', unsafe_allow_html=True)
    st.progress(progress_val)
    
    if current >= GOAL:
        if current >= MAX_POSSIBLE:
            st.success("👑 パーフェクト達成！！ 君こそが最強のエコヒーローだ！")
        else:
            st.success(f"🎉 目標の{GOAL}gを達成！次は「パーフェクト（{MAX_POSSIBLE}g）」を目指そう！")
    else:
        st.caption(f"まずは **{GOAL} g** を目指してがんばろう！")
    
    st.markdown("---")

    show_sorting_game()

    st.markdown("### 📝 チャレンジ・チェック表")
    st.info("やったことにチェックを入れて、「ほぞん する」ボタンを押してね！")
    
    if not HAS_PANDAS:
        st.warning("⚠️ 設定(requirements.txt)に 'pandas' を追加してください。")
    else:
        target_dates = ["6/1 (月)", "6/2 (火)", "6/3 (水)", "6/4 (木)"]
        
        # --- チェック項目の短縮名リスト（スマホで見やすくするため） ---
        action_master = {
            "電気": {
                "short": "① 電気",
                "label": "① 💡 だれもいない へやの でんき をけした！",
                "point": 50,
                "help": "例：トイレの電気をパチンと消した、見てないテレビを消した（CO2削減 -50g）"
            },
            "食事": {
                "short": "② 食事",
                "label": "② 🍚 ごはんを のこさず たべた！",
                "point": 100,
                "help": "例：給食をピカピカにした、苦手な野菜もがんばって食べた（CO2削減 -100g）"
            },
            "水": {
                "short": "③ 水",
                "label": "③ 🚰 水（みず）を 大切（たいせつ）に つかった！",
                "point": 30,
                "help": "例：歯みがきの間コップを使って水を止めた、顔を洗うとき出しっぱなしにしなかった（CO2削減 -30g）"
            },
            "分別": {
                "short": "④ 分別",
                "label": "④ ♻️ ゴミを 正（ただ）しく わけた！",
                "point": 80,
                "help": "例：ペットボトルのラベルをはがして捨てた、紙や箱をリサイクルに回した（CO2削減 -80g）"
            },
            "家族": {
                "short": "⑤ 家族",
                "label": "⑤ 👨‍👩‍👧 おうちの 人（ひと）も いっしょに できた！",
                "point": 50,
                "help": "例：おうちの人も、電気・食事・水・ゴミのどれか１つでも気をつけてくれた！（家族ボーナス -50g）"
            }
        }
        
        # マッピング辞書の作成
        short_to_key = {v["short"]: k for k, v in action_master.items()}
        key_to_short = {k: v["short"] for k, v in action_master.items()}
        categories = list(action_master.keys())
        
        # データフレーム用のデータ作成
        df_data = {date: [False]*len(categories) for date in target_dates}
        history = user.get('history_dict', {})
        
        # 履歴データの反映
        for date_col in target_dates:
            if date_col in history:
                done_actions = history[date_col]
                for i, key in enumerate(categories):
                    if key in done_actions:
                         df_data[date_col][i] = True

        # インデックス（行の見出し）を短縮名にする
        display_labels = [action_master[k]["short"] for k in categories]
        df = pd.DataFrame(df_data, index=display_labels)

        edited_df = st.data_editor(
            df,
            column_config={
                "6/1 (月)": st.column_config.CheckboxColumn("6/1(月)", default=False),
                "6/2 (火)": st.column_config.CheckboxColumn("6/2(火)", default=False),
                "6/3 (水)": st.column_config.CheckboxColumn("6/3(水)", default=False),
                "6/4 (木)": st.column_config.CheckboxColumn("6/4(木)", default=False),
            },
            disabled=[], 
            hide_index=False,
            use_container_width=True
        )
        
        with st.expander("❓ アクションの 詳しい例を みる"):
            for k, v in action_master.items():
                st.markdown(f"**{v['label']}**")
                st.caption(f"👉 {v['help']}")
                st.write("")

        if st.button("✅ チェックした 内容（ないよう）を ほぞん する", type="primary"):
            with st.spinner("記録しています..."):
                save_count = 0
                total_new_points_session = 0
                current_history = history.copy()

                for date_col in target_dates:
                    current_checks = edited_df[date_col] # これはSeries (index=short, value=bool)
                    actions_to_save = []
                    day_points = 0
                    
                    # 短縮名からキーに戻して保存リストを作る
                    for short_label, is_checked in current_checks.items():
                        if is_checked:
                            key = short_to_key[short_label]
                            actions_to_save.append(key)
                            day_points += action_master[key]["point"]
                    
                    prev_actions = current_history.get(date_col, [])
                    if set(actions_to_save) != set(prev_actions):
                        prev_points = 0
                        for a in prev_actions:
                             if a in action_master:
                                 prev_points += action_master[a]["point"]
                        
                        diff_points = day_points - prev_points
                        
                        save_daily_challenge(user['id'], user['name'], date_col, actions_to_save, diff_points, "一括更新")
                        total_new_points_session += diff_points
                        save_count += 1
                        current_history[date_col] = actions_to_save
                
                if save_count > 0:
                    st.session_state.user_info['history_dict'] = current_history
                    st.session_state.user_info['total_co2'] += total_new_points_session
                    
                    # 🍑 岡山弁メッセージ
                    praise_msg = random.choice(OKAYAMA_PRAISE_LIST)
                    st.success(f"{praise_msg}\n（ポイント変動: {total_new_points_session}g）")
                    
                    # 💡 日替わりトリビア
                    trivia_msg = random.choice(ECO_TRIVIA_LIST)
                    st.info(f"💡 **きょうの まめちしき**\n\n{trivia_msg}")
                    
                    st.balloons()
                    time.sleep(4) # 読む時間を少し確保
                    st.rerun()
                else:
                    st.info("変更はありませんでした。")

    st.markdown("---")
    
    # ==========================================
    #  🌿 6/5 スペシャルミッション（常時表示・初期クローズ）
    # ==========================================
    
    if is_eco_hero:
        with st.expander("🌿 6/5 環境の日 スペシャルミッション（完了！）", expanded=False):
            st.success("✨ 特別ミッションクリア済み！認定証が発行されています。")
    else:
        with st.expander("🌿 6/5 環境の日 スペシャルミッション（アンケート）", expanded=False):
            st.markdown("※ 6/5(金)になったら、ここに入力してね！（それまでは楽しみに待っててね）")
            
            with st.form("special_mission_form"):
                st.markdown("### 📝 アンケート")
                q1 = st.radio("Q1. 5日間のチャレンジ、どれくらいできましたか？", ["5：パーフェクト達成！", "4：よくできた！", "3：ふつう", "2：もう少し！", "1：チャレンジはした"])
                q2 = st.radio("Q2. デコ活をやってみて、これからも続けたいですか？", ["5：絶対つづける！", "4：つづけたい", "3：気がむいたらやる", "2：むずかしいかも", "1：もうやらない"])
                q3 = st.radio("Q3. おうちの人と「環境」や「エコ」について話しましたか？", ["5：家族みんなでやった！", "4：たくさん話した", "3：少し話した", "2：あまり話していない", "1：全然話していない"])
                st.markdown("---")
                feedback = st.text_area("感想や、これからがんばりたいこと", height=100)
                
                submit_special = st.form_submit_button("💌 アンケートを送って エコヒーロー認定！")
                
                if submit_special:
                    with st.spinner("送信中..."):
                        special_points = 100
                        actions = ["環境の日アンケート"]
                        
                        if save_daily_challenge(
                            user['id'], user['name'], "6/5 (金)", actions, special_points, feedback, q1, q2, q3
                        ):
                            st.session_state.user_info['total_co2'] += special_points
                            if 'history_dict' not in st.session_state.user_info:
                                st.session_state.user_info['history_dict'] = {}
                            st.session_state.user_info['history_dict']["6/5 (金)"] = actions
                            
                            st.balloons()
                            st.success(f"回答ありがとう！ {special_points}g ゲット！\nあなたは「10,000人チャレンジ」のひとりとして認定されました！")
                            time.sleep(3)
                            st.rerun()

    # ==========================================
    #  ✨ 6/6 おまけミッション（デコ活宣言）
    # ==========================================
    is_6_6_done = False
    if "6/6 (土)" in user.get('history_dict', {}):
        is_6_6_done = True

    if is_6_6_done:
        with st.expander("✨ 6/6 (土) 未来へのデコ活宣言（完了！）", expanded=False):
            st.success("素敵な宣言をありがとう！これからもその調子でがんばろう！")
    else:
        with st.expander("✨ 6/6 (土) おまけミッション：未来へのデコ活宣言", expanded=False):
            st.markdown("""
            **5日間のチャレンジ、おつかれさまでした！**<br>
            このチャレンジが終わっても、地球を守る活動はつづきます。<br>
            あなたが**「これからも 続けたいこと」**や**「新しく 始めたいこと」**を書いて教えてね！
            """, unsafe_allow_html=True)
            
            with st.form("declaration_form"):
                declaration_text = st.text_area("私のデコ活宣言", placeholder="例：これからは、毎日ごはんを残さず食べます！\n例：使わない電気は必ず消すのを続けます！", height=100)
                
                submit_declaration = st.form_submit_button("宣言を送って ポイントゲット！")
                
                if submit_declaration:
                    if not declaration_text:
                        st.warning("宣言を書いてね！")
                    else:
                        with st.spinner("送信中..."):
                            bonus_points = 50 # 宣言ボーナス
                            actions = ["デコ活宣言"]
                            
                            if save_daily_challenge(
                                user['id'], user['name'], "6/6 (土)", actions, bonus_points, declaration_text
                            ):
                                st.session_state.user_info['total_co2'] += bonus_points
                                if 'history_dict' not in st.session_state.user_info:
                                    st.session_state.user_info['history_dict'] = {}
                                st.session_state.user_info['history_dict']["6/6 (土)"] = actions
                                
                                st.balloons()
                                st.success(f"宣言ありがとう！ {bonus_points}g ゲット！\nこれからもエコヒーローとして活躍してね！")
                                time.sleep(3)
                                st.rerun()

    st.markdown("---")
    
    # ★ フェス誘導（メイン画面下）
    show_event_promo()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("ログアウト", key="logout"):
        st.session_state.user_info = None
        st.rerun()
        
    show_footer()

if __name__ == "__main__":
    if st.session_state.user_info is None:
        login_screen()
    else:
        main_screen()
