import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import time

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
    /* チェックボックス（トグル） */
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
    /* スペシャルミッション用 */
    .special-mission {
        background-color: #e0f7fa;
        padding: 20px;
        border-radius: 15px;
        border: 2px dashed #00bcd4;
        text-align: center;
        margin-bottom: 20px;
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
        st.error("システムエラー: 設定(Secrets)を確認してください")
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
            # 組は自由入力に変更
            u_class = st.text_input("組（クラス）", placeholder="例：1、A、松")
        with col2:
            number = st.number_input("出席番号", min_value=1, max_value=50, step=1)
            
        # ニックネーム例を変更
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
    
    # ==========================================
    #  📊 チャレンジ一覧表 (6/1-6/4)
    # ==========================================
    st.markdown("### 📊 きみのチャレンジ記録")
    
    if not HAS_PANDAS:
        st.warning("⚠️ 表を表示するには設定(requirements.txt)に 'pandas' を追加してください。")
    else:
        # 正しい曜日 (2026年6月)
        target_dates_table = ["6/1 (月)", "6/2 (火)", "6/3 (水)", "6/4 (木)"]
        categories = ["電気", "食事", "水", "分別", "マイデコ"]
        category_labels = {
            "電気": "①電気", "食事": "②食事", "水": "③水　", "分別": "④分別", "マイデコ": "⑤デコ"
        }

        # データフレーム作成
        df = pd.DataFrame(index=[category_labels[c] for c in categories], columns=target_dates_table)
        df = df.fillna("ー")

        if user.get('history'):
            for record in user['history']:
                r_date = record['date']
                r_actions = record['actions']
                if r_date in target_dates_table:
                    for cat in categories:
                        if cat in r_actions:
                            df.at[category_labels[cat], r_date] = "🟢"
        
        st.table(df)

    st.markdown("---")
    
    # ==========================================
    #  📝 チャレンジ入力 / 6/5特別ミッション
    # ==========================================
    
    # 日付リスト（2026年の曜日）
    all_dates = ["6/1 (月)", "6/2 (火)", "6/3 (水)", "6/4 (木)", "6/5 (金)", "6/6 (土)", "6/7 (日)"]
    
    # 今日の日付を自動選択
    today_md = datetime.date.today().strftime("%-m/%-d")
    default_idx = 0
    for i, d in enumerate(all_dates):
        if today_md in d:
            default_idx = i
            
    target_date = st.selectbox("📅 日付を選んでね", all_dates, index=default_idx)

    # --- 🌟 6/5 環境の日 スペシャルミッション ---
    if "6/5" in target_date:
        st.markdown("""
        <div class="special-mission">
            <h2>🌿 環境の日 スペシャルミッション 🌿</h2>
            <p>今日は環境の日！<br>6/1〜6/4までのチャレンジを振り返って、<br>アンケートに答えよう！</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("special_mission_form"):
            st.markdown("**Q. 4日間のデコ活チャレンジはどうでしたか？**")
            feedback = st.text_area("感想や、これからがんばりたいことを書いてね！", height=150, placeholder="例：電気を消すのが習慣になった！家族とエコの話ができて楽しかった！")
            
            submit_special = st.form_submit_button("💌 感想を送ってポイントGET！")
            
            if submit_special:
                if not feedback:
                    st.warning("感想を書いてね！")
                else:
                    with st.spinner("送信中..."):
                        # スペシャルボーナス 100g
                        special_points = 100
                        actions = ["環境の日アンケート"]
                        
                        if save_daily_challenge(user['id'], user['name'], target_date, actions, special_points, feedback):
                            st.session_state.user_info['total_co2'] += special_points
                            st.balloons()
                            st.success(f"ありがとう！スペシャルボーナス {special_points}g ゲット！")
                            time.sleep(2)
                            st.rerun()

    # --- 通常のチャレンジ入力 ---
    else:
        st.info(f"【{target_date}】 できたことにスイッチを入れよう！")

        with st.form("challenge_form"):
            check_1 = st.toggle("① 💡 電気を消した (+50g)")
            check_2 = st.toggle("② 🍚 残さず食べた (+100g)")
            check_3 = st.toggle("③ 🚰 水を止めた (+30g)")
            check_4 = st.toggle("④ ♻️ 正しく分けた (+80g)")
            check_5 = st.toggle("⑤ 🍴 マイ・デコ活 (+50g)")
            
            st.markdown("---")
            memo_input = st.text_area("🏡 家族で作戦会議（メモ）", height=80, placeholder="例：家族みんなで早寝早起き！")
            
            submit_challenge = st.form_submit_button("✅ まとめて送信！")
            
            if submit_challenge:
                points = 0
                actions = []
                if check_1: points += 50; actions.append("電気")
                if check_2: points += 100; actions.append("食事")
                if check_3: points += 30; actions.append("水")
                if check_4: points += 80; actions.append("分別")
                if check_5: points += 50; actions.append("マイデコ")
                
                if points == 0 and not memo_input:
                    st.warning("チェックを入れてね！")
                else:
                    with st.spinner("記録しています..."):
                        if save_daily_challenge(user['id'], user['name'], target_date, actions, points, memo_input):
                            full_school_name = user['school']
                            # データ再取得（表の更新のため）
                            _, _, new_total, new_history = fetch_user_data(full_school_name, "", "", "")
                            
                            st.session_state.user_info['total_co2'] += points
                            # 履歴への簡易追加（リロード対策）
                            st.session_state.user_info['history'].append({
                                'date': target_date,
                                'actions': ",".join(actions)
                            })
                            
                            st.balloons()
                            st.success(f"{points}g ゲット！表が更新されたよ！")
                            time.sleep(2)
                            st.rerun()

    st.markdown("---")
    
    with st.expander("🎟 ガラポン参加証"):
        if user['total_co2'] > 0:
            st.success("会場の受付で見せてね！")
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={user['id']}"
            st.image(qr_url, width=200)
            st.write(f"ID: {user['id']}")
        else:
            st.write("まずはチャレンジしよう！")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("ログアウト", key="logout"):
        st.session_state.user_info = None
        st.rerun()

if __name__ == "__main__":
    if st.session_state.user_info is None:
        login_screen()
    else:
        main_screen()
