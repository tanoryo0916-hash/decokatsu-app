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
    .special-mission {
        background-color: #e0f7fa;
        padding: 20px;
        border-radius: 15px;
        border: 2px dashed #00bcd4;
        text-align: center;
        margin-bottom: 20px;
    }
    .stRadio label {
        font-size: 16px !important;
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
    if not client: return None, None, 0, {}

    try:
        sheet = client.open("decokatsu_db").sheet1
        records = sheet.get_all_records()
        
        user_id = f"{school_full_name}_{grade}_{u_class}_{number}"
        
        total_co2 = 0
        nickname = ""
        # 履歴を辞書形式で管理 { "6/1 (月)": ["電気", "食事"], ... }
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
                
                # 履歴データを上書き更新
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

def main_screen():
    user = st.session_state.user_info
    
    st.markdown(f"**👋 こんにちは、{user['name']} さん！**")
    
    # --- メーター ---
    GOAL = 3000
    current = user['total_co2']
    st.progress(min(current / GOAL, 1.0))
    st.caption(f"現在のCO2削減パワー: **{current} g** / 目標 {GOAL} g")
    
    st.markdown("---")

    # ==========================================
    #  📊 チャレンジ入力表
    # ==========================================
    st.markdown("### 📝 チャレンジ・チェック表")
    st.info("やったことにチェックを入れて、「保存する」ボタンを押してね！")
    
    if not HAS_PANDAS:
        st.warning("⚠️ 設定(requirements.txt)に 'pandas' を追加してください。")
    else:
        target_dates = ["6/1 (月)", "6/2 (火)", "6/3 (水)", "6/4 (木)"]
        categories = ["電気", "食事", "水", "分別", "マイデコ"]
        
        cat_map = {
            "① 💡 電気を消した": "電気",
            "② 🍚 残さず食べた": "食事",
            "③ 🚰 水を止めた": "水",
            "④ ♻️ 正しく分けた": "分別",
            "⑤ 🍴 マイ・デコ活": "マイデコ"
        }
        point_map = {"電気": 50, "食事": 100, "水": 30, "分別": 80, "マイデコ": 50}
        
        # データの準備
        df_data = {date: [False]*len(categories) for date in target_dates}
        history = user.get('history_dict', {})
        
        for date_col in target_dates:
            if date_col in history:
                done_actions = history[date_col]
                for i, cat in enumerate(categories):
                    if cat_map.get(list(cat_map.keys())[i]) in done_actions:
                         df_data[date_col][i] = True

        df = pd.DataFrame(df_data, index=cat_map.keys())

        edited_df = st.data_editor(
            df,
            column_config={
                "6/1 (月)": st.column_config.CheckboxColumn("6/1 (月)", default=False),
                "6/2 (火)": st.column_config.CheckboxColumn("6/2 (火)", default=False),
                "6/3 (水)": st.column_config.CheckboxColumn("6/3 (水)", default=False),
                "6/4 (木)": st.column_config.CheckboxColumn("6/4 (木)", default=False),
            },
            disabled=[], 
            hide_index=False,
            use_container_width=True
        )

        # === 修正箇所：保存時の処理 ===
        if st.button("✅ チェックした内容を保存する", type="primary"):
            with st.spinner("記録しています..."):
                save_count = 0
                total_new_points_session = 0
                
                # ★修正ポイント: API再取得をせず、手元のデータを更新するための変数を用意
                # （APIの反映遅延対策）
                current_history = history.copy()

                for date_col in target_dates:
                    current_checks = edited_df[date_col]
                    
                    actions_to_save = []
                    day_points = 0
                    
                    for idx, is_checked in current_checks.items():
                        if is_checked:
                            short_name = cat_map[idx]
                            actions_to_save.append(short_name)
                            day_points += point_map[short_name]
                    
                    prev_actions = current_history.get(date_col, [])
                    
                    if set(actions_to_save) != set(prev_actions):
                        prev_points = sum([point_map[a] for a in prev_actions if a in point_map])
                        diff_points = day_points - prev_points
                        
                        # スプレッドシートへ保存
                        save_daily_challenge(
                            user['id'], user['name'], date_col, actions_to_save, diff_points, "一括更新"
                        )
                        total_new_points_session += diff_points
                        save_count += 1
                        
                        # ★手元のデータも更新して最新状態にする
                        current_history[date_col] = actions_to_save
                
                if save_count > 0:
                    # ★修正ポイント: APIから再取得(fetch_user_data)せずに、
                    # 手元で更新したデータをセッションに反映する（即時反映）
                    st.session_state.user_info['history_dict'] = current_history
                    st.session_state.user_info['total_co2'] += total_new_points_session
                    
                    st.balloons()
                    st.success(f"保存しました！ ポイント変動: {total_new_points_session}g")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.info("変更はありませんでした。")

    st.markdown("---")
    
    # ==========================================
    #  6/5 スペシャルミッション
    # ==========================================
    with st.expander("🌿 6/5 環境の日 スペシャルミッション（アンケート）", expanded=True):
        st.write("6/5(金)になったら、ここに入力してね！")
        
        with st.form("special_mission_form"):
            st.markdown("### 📝 アンケート")
            
            q1 = st.radio(
                "Q1. 5日間のチャレンジ、どれくらいできましたか？",
                ["5：パーフェクト達成！", "4：よくできた！", "3：ふつう", "2：もう少し！", "1：チャレンジはした"]
            )
            q2 = st.radio(
                "Q2. デコ活をやってみて、これからも続けたいですか？（必須）",
                ["5：絶対つづける！", "4：つづけたい", "3：気がむいたらやる", "2：むずかしいかも", "1：もうやらない"]
            )
            q3 = st.radio(
                "Q3. おうちの人と「環境」や「エコ」について話しましたか？",
                ["5：家族みんなでやった！", "4：たくさん話した", "3：少し話した", "2：あまり話していない", "1：全然話していない"]
            )
            st.markdown("---")
            feedback = st.text_area("感想や、これからがんばりたいこと", height=100)
            
            submit_special = st.form_submit_button("💌 アンケートを送ってポイントGET！")
            
            if submit_special:
                with st.spinner("送信中..."):
                    special_points = 100
                    actions = ["環境の日アンケート"]
                    
                    if save_daily_challenge(
                        user['id'], user['name'], "6/5 (金)", actions, special_points, feedback, q1, q2, q3
                    ):
                        st.session_state.user_info['total_co2'] += special_points
                        st.balloons()
                        st.success(f"回答ありがとう！スペシャルボーナス {special_points}g ゲット！")
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
