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
    layout="centered",  # 画面中央に寄せて視認性を高める
    initial_sidebar_state="collapsed" # サイドバーは隠す
)

# --- CSS設定 ---
# 子供が指で押しやすいようにボタンを大きく、文字を見やすく調整
st.markdown("""
<style>
    /* 全体のフォントを視認性の高いものに */
    html, body, [class*="css"] {
        font-family: 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
    }
    /* ボタンのスタイル：高さを出して押しやすく */
    .stButton>button {
        width: 100%;
        height: 80px;
        font-size: 20px !important;
        border-radius: 15px;
        font-weight: bold;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        border: 2px solid #f0f2f6;
    }
    /* ボタンを押した時の動き */
    .stButton>button:active {
        box-shadow: none;
        transform: translateY(2px);
    }
    /* セレクトボックス等のラベルサイズ */
    .stSelectbox label, .stNumberInput label, .stTextInput label {
        font-size: 16px !important;
        font-weight: bold;
    }
    /* 成功メッセージの強調 */
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
    """Google Sheetsへの接続を確立（キャッシュして高速化）"""
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=SCOPE
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error("システムエラー: 設定を確認してください (Secrets/API)")
        return None

def fetch_user_data(school, grade, u_class, number):
    """ユーザーの過去データを取得して計算する"""
    client = get_connection()
    if not client: return None, None, 0

    try:
        # シート名は作成したものに合わせてください
        sheet = client.open("decokatsu_db").sheet1
        
        # 全データを取得（※大規模運用時はquery機能等の検討が必要）
        records = sheet.get_all_records()
        
        # ユーザーIDを生成（例：倉敷小_5_2_15）
        user_id = f"{school}_{grade}_{u_class}_{number}"
        
        total_co2 = 0
        nickname = ""
        
        # 該当IDのログを集計
        for row in records:
            if str(row.get('ID')) == user_id:
                # 数値型に変換して加算
                try:
                    val = int(row.get('CO2削減量', 0))
                    total_co2 += val
                except:
                    pass
                
                # 最新のニックネームを取得（あれば）
                if row.get('ニックネーム'):
                    nickname = row.get('ニックネーム')
        
        return user_id, nickname, total_co2

    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return None, None, 0

def save_action(user_id, nickname, action, co2_val):
    """アクションをスプレッドシートに保存"""
    client = get_connection()
    if not client: return False

    try:
        sheet = client.open("decokatsu_db").sheet1
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # スプレッドシートの列順序に合わせてデータを追加
        # [日時, ID, ニックネーム, アクション, CO2削減量]
        sheet.append_row([now, user_id, nickname, action, co2_val])
        return True
    except Exception as e:
        st.error(f"保存に失敗しました。ネット環境を確認してください。 ({e})")
        return False

# ==========================================
#  3. セッション状態の管理
# ==========================================
if 'user_info' not in st.session_state:
    st.session_state.user_info = None

# ==========================================
#  4. 画面コンポーネント
# ==========================================

def login_screen():
    """ログイン画面（年・組・番号入力）"""
    st.image("https://placehold.jp/3d4070/ffffff/800x300.png?text=DecoKatsu", use_column_width=True)
    st.markdown("### 🏫 デコ活ポケット ログイン")
    st.info("学校の「年・組・出席番号」を入れてスタート！")

    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            school = st.selectbox("小学校", ["倉敷市立〇〇小学校", "倉敷市立△△小学校", "その他"])
            grade = st.selectbox("学年", ["1年", "2年", "3年", "4年", "5年", "6年"])
        with col2:
            u_class = st.number_input("組（クラス）", min_value=1, max_value=10, step=1)
            number = st.number_input("出席番号", min_value=1, max_value=50, step=1)
        
        nickname_input = st.text_input("ニックネーム（ひらがな）", placeholder="例：たろう")

        submit = st.form_submit_button("スタート！", type="primary")

        if submit:
            if not nickname_input:
                st.warning("ニックネームを入れてね！")
                return

            with st.spinner("データを読み込んでいます..."):
                user_id, saved_name, total = fetch_user_data(school, grade, u_class, number)
                
                # 過去に名前があればそれを使用、なければ入力値を使用
                final_name = saved_name if saved_name else nickname_input
                
                st.session_state.user_info = {
                    'id': user_id,
                    'name': final_name,
                    'total_co2': total,
                    'school': school
                }
                st.rerun()

def main_screen():
    """メイン操作画面"""
    user = st.session_state.user_info
    
    # --- ヘッダーエリア ---
    st.markdown(f"**👋 {user['name']} さんのチャレンジ**")
    
    # --- メーター表示（ゲーミフィケーション） ---
    # 目標値設定（例：3000g）
    GOAL = 3000
    current = user['total_co2']
    
    col_m1, col_m2 = st.columns([2, 1])
    with col_m1:
        st.metric(label="現在のCO2削減量", value=f"{current} g")
    with col_m2:
        st.write(f"目標まで\nあと {max(0, GOAL - current)} g")

    # プログレスバー
    progress_val = min(current / GOAL, 1.0)
    st.progress(progress_val)
    
    if progress_val >= 1.0:
        st.balloons()
        st.success("🎉 おめでとう！目標達成！地球を守ったね！")

    st.markdown("---")
    st.markdown("### 👇 やったことをタップ！")

    # --- アクションボタン配置 ---
    # 2列構成で押しやすく配置
    col1, col2 = st.columns(2)

    # ボタン生成関数
    def create_action_btn(col, label, point, icon, color_msg):
        with col:
            # ラベル内に改行を入れて情報を整理
            btn_label = f"{icon} {label}\n(+{point}g)"
            if st.button(btn_label):
                with st.spinner('記録中...'):
                    if save_action(user['id'], user['name'], label, point):
                        # 成功したらセッション情報を更新してリロード
                        st.session_state.user_info['total_co2'] += point
                        st.toast(f"{color_msg}！ +{point}g ゲット！", icon="✨")
                        time.sleep(1) # 少し待ってからリロード
                        st.rerun()

    # 左カラム
    create_action_btn(col1, "電気を消す", 50, "💡", "ナイス")
    create_action_btn(col1, "水を止める", 30, "🚰", "いいね")
    create_action_btn(col1, "徒歩・自転車", 100, "🚲", "すごい")

    # 右カラム
    create_action_btn(col2, "残さず食べる", 100, "🍚", "えらい")
    create_action_btn(col2, "ゴミ分別", 80, "♻️", "さすが")
    create_action_btn(col2, "家族と話す", 50, "👨‍👩‍👧", "すてき")

    st.markdown("---")
    
    # --- イベント情報 / QRコード タブ ---
    tab1, tab2 = st.tabs(["📅 イベント情報", "🎟 ガラポン参加証"])
    
    with tab1:
        st.subheader("🎉 おかやまデコ活フェス2026")
        st.info("**日時:** 6月6日(土)・7日(日) 10:00〜16:00\n\n**場所:** イオンモール倉敷 1F")
        st.markdown("""
        * ✨ **EV車がやってくる！**
        * ✨ **豪華景品のガラポン！**
        * ✨ **スタンプラリーもあるよ！**
        """)
    
    with tab2:
        st.subheader("会場でガラポン！")
        if user['total_co2'] > 0:
            st.success("この画面を会場の受付で見せてね！")
            # QRコード（ユーザーIDを含む）を表示
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={user['id']}"
            st.image(qr_url, width=200)
            st.caption(f"ID: {user['id']}")
        else:
            st.warning("まずはアクションボタンを押して、ポイントを貯めよう！")
    
    # --- ログアウト ---
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("ログアウト（おわるときはここ）"):
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
