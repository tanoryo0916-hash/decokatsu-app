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
    page_icon="🍑",
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
    /* ヒーローカード */
    .hero-card {
        background: linear-gradient(135deg, #FFD700, #FFEB3B);
        border: 4px solid #FFA000;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        color: #5D4037;
    }
    .hero-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 10px;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
    }
    .hero-name {
        font-size: 30px;
        font-weight: 900;
        border-bottom: 2px solid #5D4037;
        display: inline-block;
        margin: 10px 0;
    }
    /* ログイン画面の集計表示 */
    .global-stats {
        background-color: #263238;
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stat-box {
        flex: 1;
        padding: 0 5px;
    }
    .stat-num {
        color: #FFD700;
        font-size: 28px;
        font-weight: bold;
        margin: 0;
    }
    .stat-label {
        font-size: 12px;
        margin: 0;
        opacity: 0.8;
    }
    /* ログイン画面のミッション説明ボックス */
    .mission-box {
        background-color: #FFF3E0;
        border: 2px solid #FFB74D;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        color: #333;
    }
    .mission-header {
        font-size: 20px;
        font-weight: bold;
        color: #E65100;
        margin-bottom: 10px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .metric-container {
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border: 1px solid #ddd;
        text-align: center;
    }
    /* タイトル強調 */
    .main-title {
        text-align: center;
        font-size: 32px;
        font-weight: 900;
        color: #2E7D32;
        margin-bottom: 5px;
        text-shadow: 1px 1px 0 #fff, -1px -1px 0 #fff, 2px 2px 0 rgba(0,0,0,0.1);
    }
    .sub-title {
        text-align: center;
        font-size: 16px;
        font-weight: bold;
        color: #555;
        margin-bottom: 20px;
    }
    /* フッター */
    .footer-container {
        margin-top: 50px;
        padding-top: 20px;
        border-top: 1px solid #ddd;
        text-align: center;
        font-size: 12px;
        color: #666;
    }
    .footer-section {
        margin-bottom: 15px;
    }
    .footer-label {
        font-weight: bold;
        margin-bottom: 5px;
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
        st.error("システムエラー: 設定(Secrets)を確認してください")
        return None

# ★ 全体集計（参加者数・ヒーロー数・CO2）
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

# ★ フッター表示関数
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
#  3. セッション管理
# ==========================================
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# ==========================================
#  4. 画面コンポーネント
# ==========================================

def login_screen():
    st.image("https://placehold.jp/3d4070/ffffff/800x200.png?text=Okayama%20Decokatsu%20Challenge", use_column_width=True)
    
    st.markdown('<div class="main-title">🍑 おかやまデコ活チャレンジ</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">目指せ！岡山県で10,000人のエコヒーロー！</div>', unsafe_allow_html=True)

    if HAS_PANDAS:
        g_co2, g_heroes, g_participants = fetch_global_stats()
        st.markdown(f"""
        <div class="global-stats">
            <p>みんなで地球を救おう！現在の達成状況</p>
            <div style="display:flex; justify-content:space-between; margin-top:10px;">
                <div class="stat-box">
                    <p class="stat-label">現在の参加者</p>
                    <p class="stat-num">{g_participants:,}<span style="font-size:12px;">人</span></p>
                </div>
                <div class="stat-box" style="border-left:1px solid #555; border-right:1px solid #555;">
                    <p class="stat-label">認定ヒーロー</p>
                    <p class="stat-num">{g_heroes:,}<span style="font-size:12px;">人</span></p>
                </div>
                <div class="stat-box">
                    <p class="stat-label">CO2削減量</p>
                    <p class="stat-num">{g_co2:,}<span style="font-size:12px;">g</span></p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="mission-box">
        <div class="mission-header">🌏 緊急ミッション！地球を救うヒーロー求む！</div>
        <p style="font-weight:bold;">君の「スイッチOFF」が、地球を守るパワーになる！</p>
        <p style="font-size:15px;">いま、地球は「CO2」というガスのせいで、どんどん暑くなっているんだ（地球温暖化）。<br>
        でも大丈夫！君が電気をこまめに消したり、ごはんを残さず食べるだけで、地球を冷やすことができるよ。</p>
        <p style="font-weight:bold; color:#E65100;">👉 目標は「10,000人のエコヒーロー」を集めること！<br>
        さあ、君もチームに参加して、未来の地球を守ろう！</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🏫 ヒーロー登録（ログイン）")
    st.info("学校名と、自分の「年・組・番号」を入れてスタート！")

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

        submit = st.form_submit_button("ミッションスタート！", type="primary")

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
    
    # ログイン画面フッター
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

    st.markdown("### 📝 チャレンジ・チェック表")
    st.info("やったことにチェックを入れて、「保存する」ボタンを押してね！")
    
    if not HAS_PANDAS:
        st.warning("⚠️ 設定(requirements.txt)に 'pandas' を追加してください。")
    else:
        target_dates = ["6/1 (月)", "6/2 (火)", "6/3 (水)", "6/4 (木)"]
        
        action_master = {
            "電気": {
                "label": "① 💡 だれもいない部屋の電気を消した！",
                "point": 50,
                "help": "例：トイレの電気をパチンと消した、見てないテレビを消した（CO2削減 -50g）"
            },
            "食事": {
                "label": "② 🍚 ごはんをのこさず食べた！",
                "point": 100,
                "help": "例：給食をピカピカにした、苦手な野菜もがんばって食べた（CO2削減 -100g）"
            },
            "水": {
                "label": "③ 🚰 水を大切に使った！",
                "point": 30,
                "help": "例：歯みがきの間コップを使って水を止めた、顔を洗うとき出しっぱなしにしなかった（CO2削減 -30g）"
            },
            "分別": {
                "label": "④ ♻️ ゴミを正しく分けた！",
                "point": 80,
                "help": "例：ペットボトルのラベルをはがして捨てた、紙や箱をリサイクルに回した（CO2削減 -80g）"
            },
            "家族": {
                "label": "⑤ 👨‍👩‍👧 おうちの人も１つ以上できた！",
                "point": 50,
                "help": "例：おうちの人も、電気・食事・水・ゴミのどれか１つでも気をつけてくれた！（家族ボーナス -50g）"
            }
        }
        
        label_to_key = {v["label"]: k for k, v in action_master.items()}
        categories = list(action_master.keys())
        
        df_data = {date: [False]*len(categories) for date in target_dates}
        history = user.get('history_dict', {})
        
        for date_col in target_dates:
            if date_col in history:
                done_actions = history[date_col]
                for i, key in enumerate(categories):
                    if key in done_actions:
                         df_data[date_col][i] = True

        display_labels = [action_master[k]["label"] for k in categories]
        df = pd.DataFrame(df_data, index=display_labels)

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
        
        with st.expander("❓ アクションの詳しい例を見る"):
            for k, v in action_master.items():
                st.markdown(f"**{v['label']}**")
                st.caption(f"👉 {v['help']}")
                st.write("")

        if st.button("✅ チェックした内容を保存する", type="primary"):
            with st.spinner("記録しています..."):
                save_count = 0
                total_new_points_session = 0
                current_history = history.copy()

                for date_col in target_dates:
                    current_checks = edited_df[date_col]
                    actions_to_save = []
                    day_points = 0
                    
                    for label, is_checked in current_checks.items():
                        if is_checked:
                            key = label_to_key[label]
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
                    st.success(f"保存しました！ ポイント変動: {total_new_points_session}g")
                    time.sleep(1)
                    st.rerun()

    st.markdown("---")
    
    # ==========================================
    #  🌿 6/5 スペシャルミッション
    # ==========================================
    if is_eco_hero:
        with st.expander("🌿 6/5 環境の日 スペシャルミッション（完了！）", expanded=False):
            st.success("✨ 特別ミッションクリア済み！認定証が発行されています。")
    else:
        with st.expander("🌿 6/5 環境の日 スペシャルミッション（アンケート）", expanded=True):
            st.write("6/5(金)になったら、ここに入力してね！")
            
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
        
    # メイン画面フッター
    show_footer()

if __name__ == "__main__":
    if st.session_state.user_info is None:
        login_screen()
    else:
        main_screen()
