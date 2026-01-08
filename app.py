import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import time

# ==========================================
#  1. 設定＆デザイン（GIGA端末向け最適化）
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活チャレンジ",
    page_icon="🌏",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CSS設定（見やすく、押しやすく） ---
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
    }
    /* チェックボックス（トグル）周りのデザイン */
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
    /* 送信ボタンを大きく目立たせる */
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
    /* 「小学校」という固定文字のスタイル調整 */
    .school-suffix {
        font-size: 20px;
        font-weight: bold;
        padding-top: 35px; /* 入力欄の高さに合わせる */
        color: #333;
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

def fetch_user_data(school_full_name, grade, u_class, number):
    client = get_connection()
    if not client: return None, None, 0

    try:
        sheet = client.open("decokatsu_db").sheet1
        records = sheet.get_all_records()
        
        # ID作成：学校名 + 学年 + 組 + 番号
        user_id = f"{school_full_name}_{grade}_{u_class}_{number}"
        
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
        # === 変更点1：小学校名を「〇〇」+「小学校(固定)」に分割 ===
        st.markdown("**小学校の名前**")
        col_sch1, col_sch2 = st.columns([3, 1])
        with col_sch1:
            school_core = st.text_input("小学校名（ラベルなし）", placeholder="例：倉敷", label_visibility="collapsed")
        with col_sch2:
            st.markdown('<div class="school-suffix">小学校</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            grade = st.selectbox("学年", ["1年", "2年", "3年", "4年", "5年", "6年"])
            
            # === 変更点2：組を自由入力（テキスト）に変更 ===
            u_class = st.text_input("組（クラス）", placeholder="例：1、A、松")
            
        with col2:
            number = st.number_input("出席番号", min_value=1, max_value=50, step=1)
            
        # === 変更点3：ニックネーム例を変更 ===
        nickname_input = st.text_input("ニックネーム（ひらがな）", placeholder="例：でこかつたろう")

        submit = st.form_submit_button("スタート！", type="primary")

        if submit:
            if not school_core or not nickname_input or not u_class:
                st.warning("学校名、クラス、ニックネームを入れてね！")
                return

            with st.spinner("データを読み込んでいます..."):
                # 入力された名前に「小学校」をくっつけて正式名称にする
                full_school_name = f"{school_core}小学校"
                
                user_id, saved_name, total = fetch_user_data(full_school_name, grade, u_class, number)
                final_name = saved_name if saved_name else nickname_input
                
                st.session_state.user_info = {
                    'id': user_id,
                    'name': final_name,
                    'total_co2': total,
                    'school': full_school_name
                }
                st.rerun()

def main_screen():
    user = st.session_state.user_info
    
    st.markdown(f"**👋 こんにちは、{user['name']} さん！**")
    
    # --- メーター表示 ---
    GOAL = 3000
    current = user['total_co2']
    st.progress(min(current / GOAL, 1.0))
    st.caption(f"現在のCO2削減パワー: **{current} g** / 目標 {GOAL} g")
    
    st.markdown("---")
    
    # === デジタル・チャレンジシート ===
    st.header("📝 今日のチャレンジ")
    
    # 日付選択
    date_options = ["6/1 (土)", "6/2 (日)", "6/3 (月)", "6/4 (火)", "6/5 (水)", "6/6 (木)", "6/7 (日)"]
    today_md = datetime.date.today().strftime("%-m/%-d")
    default_idx = 0
    for i, d in enumerate(date_options):
        if today_md in d:
            default_idx = i
            
    target_date = st.selectbox("📅 日付を選んでね", date_options, index=default_idx)
    
    st.info(f"【{target_date}】 できたことにスイッチを入れよう！")

    with st.form("challenge_form"):
        # チェック項目（トグルスイッチ）
        check_1 = st.toggle("① 💡 電気を消した (+50g)", help="使っていない部屋の電気をこまめに消そう")
        check_2 = st.toggle("② 🍚 残さず食べた (+100g)", help="給食や晩ごはん、残さず食べたかな？")
        check_3 = st.toggle("③ 🚰 水を止めた (+30g)", help="歯磨きのとき、水を流しっぱなしにしてない？")
        check_4 = st.toggle("④ ♻️ 正しく分けた (+80g)", help="ゴミを分別したり、リサイクルしたかな？")
        check_5 = st.toggle("⑤ 🍴 マイ・デコ活 (+50g)", help="自分だけの特別なエコ活動をしたかな？")
        
        st.markdown("---")
        
        st.markdown("**🏡 家族で作戦会議！**")
        memo_input = st.text_area("地球のために、これから我が家でできること（任意）", height=80, placeholder="例：買い物のときはエコバッグを持つ！")
        
        submit_challenge = st.form_submit_button("✅ まとめて送信！")
        
        if submit_challenge:
            points = 0
            actions = []
            if check_1: 
                points += 50
                actions.append("電気")
            if check_2: 
                points += 100
                actions.append("食事")
            if check_3: 
                points += 30
                actions.append("水")
            if check_4: 
                points += 80
                actions.append("分別")
            if check_5: 
                points += 50
                actions.append("マイデコ")
            
            if points == 0 and not memo_input:
                st.warning("何かひとつでもチェックを入れてね！")
            else:
                with st.spinner("記録しています..."):
                    if save_daily_challenge(user['id'], user['name'], target_date, actions, points, memo_input):
                        st.session_state.user_info['total_co2'] += points
                        st.balloons()
                        st.success(f"{points}g のパワーを送ったよ！明日もがんばろう！")
                        time.sleep(2)
                        st.rerun()

    st.markdown("---")
    
    with st.expander("🎟 ガラポン参加証を表示する"):
        if user['total_co2'] > 0:
            st.success("会場の受付でこれを見せてね！")
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={user['id']}"
            st.image(qr_url, width=200)
            st.write(f"ID: {user['id']}")
        else:
            st.warning("まずはチャレンジを送信してポイントを貯めよう！")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("ログアウト", key="logout"):
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
