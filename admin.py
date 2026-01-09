import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime
import time

# ==========================================
#  1. 設定とセキュリティ
# ==========================================
st.set_page_config(
    page_title="ガラポン受付システム",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSSでデザイン調整
st.markdown("""
<style>
    .big-font { font-size: 24px !important; font-weight: bold; }
    .success-status { color: green; font-weight: bold; font-size: 18px; }
    .warning-status { color: red; font-weight: bold; font-size: 18px; }
    .hero-badge {
        background: linear-gradient(135deg, #FFD700, #FFB300);
        color: #5D4037;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        display: inline-block;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    div[data-testid="stMetricValue"] { font-size: 36px; color: #E65100; }
</style>
""", unsafe_allow_html=True)

# Google Sheets 接続設定
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
        st.error(f"❌ データベース接続エラー: {e}")
        return None

# ==========================================
#  2. データ処理関数
# ==========================================

# データの取得と集計
def fetch_data():
    client = get_connection()
    if not client: return pd.DataFrame()
    
    try:
        sheet = client.open("decokatsu_db").sheet1
        data = sheet.get_all_records()
        
        if not data: return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        # 数値変換
        df['CO2削減量'] = pd.to_numeric(df['CO2削減量'], errors='coerce').fillna(0)
        
        # IDごとに集計
        agg_df = df.groupby('ID').agg({
            'ニックネーム': 'last', # 最新の名前
            'CO2削減量': 'sum',     # ポイント合計
            '実施項目': lambda x: ", ".join([str(v) for v in x if v]) # 履歴を結合
        }).reset_index()
        
        # ★ ステータス判定
        # 1. 抽選済みかどうか
        agg_df['抽選状況'] = agg_df['実施項目'].apply(lambda x: '✅ 済み' if 'ガラポン済' in x else '未実施')
        # 2. エコヒーロー認定されているか（アンケート回答済みか）
        agg_df['is_eco_hero'] = agg_df['実施項目'].apply(lambda x: '環境の日アンケート' in x)
        
        return agg_df
        
    except Exception as e:
        st.error(f"データ取得エラー: {e}")
        return pd.DataFrame()

# ガラポン実施の記録
def mark_lottery_done(user_id, nickname):
    client = get_connection()
    if not client: return False
    
    try:
        sheet = client.open("decokatsu_db").sheet1
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        sheet.append_row([now, user_id, nickname, "会場受付", "ガラポン済", 0, "現地抽選完了", "", "", ""])
        return True
    except Exception as e:
        st.error(f"書き込みエラー: {e}")
        return False

# ==========================================
#  3. アプリ画面構成
# ==========================================

st.title("🎰 おかやまデコ活フェス ガラポン受付")
st.markdown("参加者の「学校名」または「お名前」を聞いて検索してください。")

# データ読み込み（リロードボタン付き）
col_r1, col_r2 = st.columns([8, 2])
with col_r2:
    if st.button("🔄 データを最新にする"):
        st.cache_data.clear()
        st.rerun()

df = fetch_data()

if not df.empty:
    # --- 🔍 検索エリア ---
    with st.container():
        st.markdown("### 1. 参加者をさがす")
        search_query = st.text_input("検索キーワード（学校名、名前、IDなど）", placeholder="例：倉敷、たろう")

    # --- 📋 検索結果リスト ---
    target_row = None
    
    if search_query:
        # キーワードで絞り込み
        filtered_df = df[
            df['ID'].str.contains(search_query, na=False) | 
            df['ニックネーム'].str.contains(search_query, na=False)
        ]
        
        if len(filtered_df) == 0:
            st.warning("見つかりませんでした。")
        else:
            # 選択肢の作成
            options = filtered_df['ID'].tolist()
            labels = {row['ID']: f"{row['ID']} : {row['ニックネーム']} 様" for index, row in filtered_df.iterrows()}
            
            selected_id = st.selectbox(
                "該当する参加者を選んでください", 
                options, 
                format_func=lambda x: labels[x]
            )
            
            target_row = df[df['ID'] == selected_id].iloc[0]

    # --- 🎟 操作エリア（対象者が選ばれたら表示） ---
    if target_row is not None:
        st.markdown("---")
        st.markdown("### 2. 抽選チェック")
        
        col_info, col_action = st.columns([1, 1])
        
        # 左側：ステータス表示
        with col_info:
            st.markdown(f"<div class='big-font'>{target_row['ニックネーム']} 様</div>", unsafe_allow_html=True)
            st.caption(f"ID: {target_row['ID']}")
            
            # 認定情報の表示
            is_hero = target_row['is_eco_hero']
            if is_hero:
                st.markdown("<span class='hero-badge'>🏆 エコヒーロー認定済み</span>", unsafe_allow_html=True)
            else:
                st.markdown("🛑 未認定（アンケート未回答）")
            
            total_points = int(target_row['CO2削減量'])
            st.metric("現在の合計ポイント", f"{total_points:,} g")

        # 右側：アクションボタン
        with col_action:
            status = target_row['抽選状況']
            is_hero = target_row['is_eco_hero']
            
            if "済み" in status:
                st.markdown("<div class='warning-status'>⚠️ すでに抽選済みです</div>", unsafe_allow_html=True)
                st.info("※重複参加に注意してください")
            
            elif not is_hero:
                st.markdown("<div class='warning-status'>❌ 抽選できません</div>", unsafe_allow_html=True)
                st.error("エコヒーロー認定（6/5のアンケート回答）が必要です。")
                
            else:
                st.markdown("<div class='success-status'>✅ 抽選可能です</div>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                # 誤操作防止のため、確認してから実行
                with st.popover("🎟 抽選済みにする（押下）"):
                    st.write("本当に「抽選完了」として記録しますか？")
                    if st.button("はい、記録します", type="primary"):
                        with st.spinner("記録中..."):
                            if mark_lottery_done(target_row['ID'], target_row['ニックネーム']):
                                st.success("記録しました！")
                                time.sleep(1)
                                st.cache_data.clear() # データ更新
                                st.rerun()            # 画面リロード
                            else:
                                st.error("エラーが発生しました。もう一度試してください。")

else:
    st.info("データがまだありません。")
