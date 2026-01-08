import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import time
import pandas as pd # 一覧表を作るために追加

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
        history = [] # 履歴データを格納するリスト
        
        for row in records:
            if str(row.get('ID')) == user_id:
                # 合計計算
                try:
                    val = int(row.get('CO2削減量', 0))
                    total_co2 += val
                except:
                    pass
                
                # ニックネーム確保
                if row.get('ニックネーム'):
                    nickname = row.get('ニックネーム')
                
                # 履歴確保 (日付と実施項目)
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
                
                # 履歴データ(history)も取得するように変更
                user_id, saved_name, total, history = fetch_user_data(full_school_name, grade, u_class, number)
                final_name = saved_name if saved_name else nickname_input
                
                st.session_state.user_info = {
                    'id': user_id,
                    'name': final_name,
                    'total_co2': total,
                    'school': full_school_name,
                    'history': history # セッションに履歴を保存
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
    #  📊 チャレンジ一覧表 (NEW!)
    # ==========================================
    st.markdown("### 📊 きみのチャレンジ記録")
    
    # 履歴データから表を作成するための準備
    # 列: 日付(6/1〜6/4), 行: 項目(電気, 食事...)
    target_dates = ["6/1 (土)", "6/2 (日)", "6/3 (月)", "6/4 (火)"]
    categories = ["電気", "食事", "水", "分別", "マイデコ"]
    category_labels = {
        "電気": "①電気", 
        "食事": "②食事", 
        "水": "③水　", 
        "分別": "④分別", 
        "マイデコ": "⑤デコ"
    }

    # 空のデータフレームを作成（初期値は空文字）
    df = pd.DataFrame(index=[category_labels[c] for c in categories], columns=target_dates)
    df = df.fillna("ー") # 未実施は棒線

    # ユーザーの履歴データを反映
    if user.get('history'):
        for record in user['history']:
            r_date = record['date']
            r_actions = record['actions'] # "電気, 食事" のような文字列
            
            if r_date in target_dates:
                for cat in categories:
                    if cat in r_actions:
                        # 実施していればマルをつける
                        df.at[category_labels[cat], r_date] = "🟢"

    # 表を表示
    st.table(df)

    st.markdown("---")
    
    # === 入力フォーム ===
    st.header("📝 チャレンジ入力")
    
    # 全日程を選択肢に追加
    all_dates = ["6/1 (土)", "6/2 (日)", "6/3 (月)", "6/4 (火)", "6/5 (水)", "6/6 (木)", "6/7 (日)"]
    today_md = datetime.date.today().strftime("%-m/%-d")
    default_idx = 0
    for i, d in enumerate(all_dates):
        if today_md in d:
            default_idx = i
            
    target_date = st.selectbox("📅 日付を選んでね", all_dates, index=default_idx)
    
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
                st.warning("チェックを入れてね！")
            else:
                with st.spinner("記録しています..."):
                    if save_daily_challenge(user['id'], user['name'], target_date, actions, points, memo_input):
                        
                        # セッション情報を更新（再読み込みして表を更新するため）
                        full_school_name = user['school']
                        uid = user['id']
                        # 最新データを再取得
                        _, _, new_total, new_history = fetch_user_data(full_school_name, "", "", "") # 学校名以外はID生成用なので適当でOKだが...
                        
                        # 簡易的にセッションだけ更新（本来は再取得関数を呼ぶべき）
                        st.session_state.user_info['total_co2'] += points
                        # 履歴に今追加した分を仮追加（リロードまでのつなぎ）
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
