import streamlit as st
import datetime
import gspread
from google.oauth2.service_account import Credentials
import time

# ==========================================
#  1. 設定＆デザイン（GIGA端末向け）
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活ポケット",
    page_icon="🌱",
    layout="centered",  # 小さい画面でも中央に寄せて見やすく
    initial_sidebar_state="collapsed"
)

# 低解像度・タッチパネル向けのCSS調整
st.markdown("""
<style>
    /* 全体のフォントを少し大きく */
    html, body, [class*="css"] {
        font-family: 'Hiragino Kaku Gothic ProN', 'Meiryo', sans-serif;
    }
    /* ボタンを指で押しやすく大きくする */
    .stButton>button {
        width: 100%;
        height: 80px;  /* 高さ確保 */
        font-size: 20px !important;
        border-radius: 15px;
        font-weight: bold;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    /* 選択ボックス（セレクトボックス）の文字を見やすく */
    .stSelectbox label {
        font-size: 18px !important;
    }
    /* 成功メッセージを派手に */
    .stToast {
        font-size: 18px;
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
    # StreamlitのSecretsから認証情報を取得
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=SCOPE
    )
    client = gspread.authorize(credentials)
    return client

# ユーザーデータを取得（ログイン）
def fetch_user_data(school, grade, u_class, number):
    client = get_connection()
    sheet = client.open("decokatsu_db").sheet1
    
    # 全データを取得して検索（人数が多い場合は本来もっと工夫が必要）
    records = sheet.get_all_records()
    
    # ユニークIDを作成（例：倉敷小_5_2_15）
    user_id = f"{school}_{grade}_{u_class}_{number}"
    
    # 該当ユーザーの過去の合計削減量を探す
    total_co2 = 0
    nickname = ""
    
    for row in records:
        # 行に 'ID' キーがあるか確認し、一致するかチェック
        if str(row.get('ID')) == user_id:
            total_co2 += int(row.get('CO2削減量', 0))
            if not nickname:
                nickname = row.get('ニックネーム', '名無し')
    
    return user_id, nickname, total_co2

# データを保存
def save_action(user_id, nickname, action, co2_val):
    try:
        client = get_connection()
        sheet = client.open("decokatsu_db").sheet1
        
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # [日時, ID, ニックネーム, アクション, CO2]
        sheet.append_row([now, user_id, nickname, action, co2_val])
        return True
    except Exception as e:
        st.error(f"通信エラー: 学校のネット環境を確認してね。 ({e})")
        return False

# ==========================================
#  3. セッション管理
# ==========================================
if 'user_info' not in st.session_state:
    st.session_state.user_info = None # ログインしていない状態

# ==========================================
#  4. アプリ画面構成
# ==========================================

def login_screen():
    st.image("https://placehold.jp/3d4070/ffffff/800x300.png?text=DecoKatsu", use_column_width=True)
    st.markdown("### 🏫 学校のタブレットでログイン")
    st.info("自分の「年・組・番号」を入れてね！")

    with st.form("login_form"):
        col1, col2 = st.columns(2)
        with col1:
            school = st.selectbox("小学校", ["倉敷市立〇〇小学校", "倉敷市立△△小学校", "その他"])
            grade = st.selectbox("学年", ["1年", "2年", "3年", "4年", "5年", "6年"])
        with col2:
            u_class = st.number_input("組（クラス）", min_value=1, max_value=10, step=1)
            number = st.number_input("出席番号", min_value=1, max_value=50, step=1)
        
        # 初回のみニックネームを聞く（本来はDBにあるかチェックするが簡易化）
        nickname = st.text_input("ニックネーム（ひらがな）", placeholder="例：たろう")

        submit = st.form_submit_button("スタート！", type="primary")

        if submit:
            if not nickname:
                st.warning("ニックネームを入れてね！")
                return

            with st.spinner("データを読み込んでいます..."):
                user_id, saved_name, total = fetch_user_data(school, grade, u_class, number)
                
                # 既存データがあれば名前を上書きしない、なければ新規の名前を使う
                final_name = saved_name if saved_name else nickname
                
                st.session_state.user_info = {
                    'id': user_id,
                    'name': final_name,
                    'total_co2': total,
                    'school': school
                }
                st.rerun()

def main_screen():
    user = st.session_state.user_info
    
    # ヘッダーエリア
    st.markdown(f"##### 👋 こんにちは、{user['name']} さん")
    
    # メーター（大きく見やすく）
    st.metric(label="現在のCO2削減量", value=f"{user['total_co2']} g")
    # 目標3000gに対する進捗
    progress_val = min(user['total_co2'] / 3000, 1.0)
    st.progress(progress_val)
    
    if progress_val >= 1.0:
        st.success("🎉 目標達成！すごい！")

    st.markdown("---")
    st.markdown("### 👇 今日のチャレンジを選んでタップ！")

    # アクションボタン（2列レイアウトで指で押しやすく）
    col1, col2 = st.columns(2)

    def register_action(label, point, icon):
        # ボタンのラベルにアイコンとポイントを表示
        btn_label = f"{icon} {label}\n(+{point}g)"
        if st.button(btn_label):
            # 処理中はスピナーを表示
            with st.spinner('送信中...'):
                if save_action(user['id'], user['name'], label, point):
                    user['total_co2'] += point
                    st.toast(f"ナイス！ {label} 成功！", icon="✨")
                    time.sleep(1)
                    st.rerun()

    with col1:
        register_action("電気を消す", 50, "💡")
        register_action("水を止める", 30, "🚰")
        register_action("徒歩・自転車", 100, "🚲")

    with col2:
        register_action("残さず食べる", 100, "🍚")
        register_action("ゴミ分別", 80, "♻️")
        register_action("家族と話す", 50, "👨‍👩‍👧")

    st.markdown("---")
    
    # イベント情報・QRコードへの切り替え（簡易タブ）
    tab1, tab2 = st.tabs(["📅 イベント情報", "🎟 ガラポン参加証"])
    
    with tab1:
        st.info("6月6日(土)・7日(日) イオンモール倉敷で開催！")
        st.write("このアプリを使って、会場でガラポンができるよ！")
    
    with tab2:
        if user['total_co2'] > 0:
            st.success("この画面を受付で見せてね！")
            # QRコード生成（ユーザーIDを埋め込む）
            qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={user['id']}"
            st.image(qr_url, caption=f"ID: {user['id']}")
        else:
            st.warning("まずはアクションをしてポイントを貯めよう！")
    
    # ログアウトボタン（共有端末の場合に必要）
    if st.button("ログアウト（終わるときはここ）"):
        st.session_state.user_info = None
        st.rerun()

# ==========================================
#  メイン実行
# ==========================================
if st.session_state.user_info is None:
    login_screen()
else:
    main_screen()
