import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import datetime

# ==========================================
#  1. 設定
# ==========================================
st.set_page_config(page_title="ガラポン受付システム", page_icon="🎰", layout="wide")

# Google Sheets 接続 (app.pyと同じ)
SCOPE = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

@st.cache_resource
def get_connection():
    try:
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPE
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"接続エラー: {e}")
        return None

# データ取得＆集計（ここがポイント！）
def fetch_aggregated_data():
    client = get_connection()
    if not client: return pd.DataFrame()
    
    sheet = client.open("decokatsu_db").sheet1
    data = sheet.get_all_records()
    
    if not data: return pd.DataFrame()
    
    df = pd.DataFrame(data)
    
    # 数値変換
    df['CO2削減量'] = pd.to_numeric(df['CO2削減量'], errors='coerce').fillna(0)
    
    # IDごとに集計（ポイント合計、最新の名前、実施項目のリスト化）
    # ※ ID形式: 学校名_学年_組_番号
    agg_df = df.groupby('ID').agg({
        'ニックネーム': 'last', # 最新のニックネーム
        'CO2削減量': 'sum',     # 合計ポイント
        '実施項目': lambda x: ", ".join([str(v) for v in x if v]) # 履歴を結合
    }).reset_index()
    
    # 「ガラポン済」かどうか判定
    agg_df['抽選状況'] = agg_df['実施項目'].apply(lambda x: '✅ 済み' if 'ガラポン済' in x else '未実施')
    
    return agg_df

# ガラポン実施を記録する関数
def mark_lottery_done(user_id, nickname):
    client = get_connection()
    sheet = client.open("decokatsu_db").sheet1
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 抽選済みログを追記 (ポイント0で記録)
    # [日時, ID, 名前, 対象日付, 項目, ポイント, メモ, q1, q2, q3]
    sheet.append_row([now, user_id, nickname, "会場受付", "ガラポン済", 0, "現地抽選完了", "", "", ""])
    st.cache_data.clear() # キャッシュクリアして再読み込み

# ==========================================
#  2. 画面レイアウト
# ==========================================
st.title("🎰 おかやまデコ活フェス ガラポン受付")

# --- 検索エリア ---
st.markdown("### 🔍 参加者をさがす")
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    search_text = st.text_input("学校名 または お名前 で検索", placeholder="例：倉敷、たろう")

# データ読み込み
df = fetch_aggregated_data()

if not df.empty:
    # --- フィルタリング ---
    if search_text:
        # 学校名(IDに含まれる) または ニックネーム で検索
        filtered_df = df[
            df['ID'].str.contains(search_text, na=False) | 
            df['ニックネーム'].str.contains(search_text, na=False)
        ]
    else:
        filtered_df = df

    # --- 一覧表示 ---
    st.dataframe(
        filtered_df[['ID', 'ニックネーム', 'CO2削減量', '抽選状況']],
        column_config={
            "CO2削減量": st.column_config.NumberColumn("合計CO2 (g)", format="%d g"),
        },
        use_container_width=True,
        hide_index=True
    )

    # --- 個別操作エリア ---
    st.markdown("---")
    st.markdown("### 🎟 抽選処理")
    
    # セレクトボックスで対象者を選択（検索結果があればそれに絞る）
    target_list = filtered_df['ID'].tolist()
    if target_list:
        selected_id = st.selectbox("対象者を選択してください", target_list, format_func=lambda x: f"{x} : {filtered_df[filtered_df['ID']==x]['ニックネーム'].values[0]}")
        
        target_row = filtered_df[filtered_df['ID'] == selected_id].iloc[0]
        
        col_info, col_action = st.columns([1, 1])
        
        with col_info:
            st.info(f"**{target_row['ニックネーム']}** さんのデータ")
            st.metric("現在の合計ポイント", f"{target_row['CO2削減量']} g")
            
            # 抽選回数の計算（例：500gで1回、1000gで2回など）
            lottery_count = int(target_row['CO2削減量'] // 500) 
            st.write(f"👉 抽選可能回数（500g毎）： **{lottery_count} 回**")

        with col_action:
            if "済み" in target_row['抽選状況']:
                st.warning("⚠️ この参加者はすでにガラポンを回しています。")
            elif target_row['CO2削減量'] < 500:
                st.error("ポイントが足りません（目標500g）")
            else:
                if st.button("✅ ガラポン完了として記録する", type="primary"):
                    mark_lottery_done(selected_id, target_row['ニックネーム'])
                    st.success(f"{target_row['ニックネーム']} さんの抽選を記録しました！")
                    time.sleep(2)
                    st.rerun()
    else:
        st.write("検索結果がありません。")

else:
    st.warning("データがまだありません。")
