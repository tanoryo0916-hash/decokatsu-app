import streamlit as st
import pandas as pd
from supabase import create_client, Client
import time

# ==========================================
#  1. 設定＆デザイン
# ==========================================
st.set_page_config(page_title="JCメンバー デコ活", page_icon="👔", layout="centered")

# スマホで見やすくするCSS
st.markdown("""
<style>
    .stButton>button { width: 100%; height: 60px; font-weight: bold; border-radius: 10px; background-color: #0277BD; color: white; }
    .metric-box { border: 2px solid #0277BD; padding: 15px; border-radius: 10px; text-align: center; background-color: #E1F5FE; margin-bottom: 20px; }
    .lom-ranking { padding: 10px; background-color: #FAFAFA; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 5px; }
    .rank-1 { background-color: #FFF8E1; border: 2px solid #FFD54F; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
#  2. データ定義 (ユニバーサルデコ活)
# ==========================================
ACTION_MASTER = {
    "てまえどり": {"point": 40, "label": "🏪 てまえどり (40g)", "desc": "商品棚の手前（期限が近いもの）から取る"},
    "リフューズ": {"point": 30, "label": "🥡 カトラリー辞退 (30g)", "desc": "「お箸・スプーン・袋はいいです」と断る"},
    "待機電力": {"point": 20, "label": "🔌 待機電力カット (20g)", "desc": "使わない家電のスイッチ・コンセントOFF"},
    "節水": {"point": 60, "label": "🚿 シャワー短縮 (60g)", "desc": "1分短縮、または出しっぱなしにしない"},
    "完食": {"point": 50, "label": "🍽️ 完食・ロスゼロ (50g)", "desc": "外食・弁当含め、食品ロスを出さない"},
    "発信": {"point": 100, "label": "📱 エコの発信 (100g)", "desc": "SNS投稿、職場・LOMでの会話"},
    "スマートムーブ": {"point": 80, "label": "🚶 スマートムーブ (80g)", "desc": "徒歩・自転車・階段利用、ふんわりアクセル"}
}

# 岡山ブロック内15LOMリスト
LOM_LIST = [
    "岡山", "倉敷", "津山", "玉野", "児島", "笠岡", "美作", 
    "新見", "備前", "高梁", "総社", "井原", "真庭", "勝央", "瀬戸内"
]

TARGET_DATES = ["6/1(月)", "6/2(火)", "6/3(水)", "6/4(木)", "6/5(金)"]

# ==========================================
#  3. Supabase接続
# ==========================================
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except:
        st.error("Supabase接続エラー: secretsを設定してください")
        return None

supabase = init_connection()

# ==========================================
#  4. データ操作関数
# ==========================================

def fetch_member_logs(user_name, lom_name):
    """ログインユーザーの過去の記録を取得"""
    if not supabase: return pd.DataFrame()
    try:
        response = supabase.table("logs_member")\
            .select("*")\
            .eq("user_name", user_name)\
            .eq("lom_name", lom_name)\
            .execute()
        return pd.DataFrame(response.data)
    except:
        return pd.DataFrame()

def fetch_lom_ranking():
    """LOMごとの合計ポイントを集計"""
    if not supabase: return pd.DataFrame()
    try:
        # 全データ取得（本来はRPC推奨ですが簡易的に）
        response = supabase.table("logs_member").select("lom_name, points").execute()
        df = pd.DataFrame(response.data)
        if df.empty: return pd.DataFrame()
        
        # LOMごとに集計
        ranking = df.groupby("lom_name")["points"].sum().reset_index()
        ranking = ranking.sort_values("points", ascending=False).reset_index(drop=True)
        return ranking
    except:
        return pd.DataFrame()

def save_logs(user_name, lom_name, edited_df):
    """チェック表の内容を保存"""
    if not supabase: return
    
    insert_list = []
    
    # マスタの逆引き辞書（表示ラベル -> キー）
    label_to_key = {v["label"]: k for k, v in ACTION_MASTER.items()}
    
    for idx, row in edited_df.iterrows():
        display_label = row["アクション項目"]
        action_key = label_to_key[display_label]
        point = ACTION_MASTER[action_key]["point"]
        
        for date_col in TARGET_DATES:
            is_checked = row[date_col]
            if is_checked:
                insert_list.append({
                    "user_name": user_name,
                    "lom_name": lom_name,
                    "target_date": date_col,
                    "action_label": action_key,
                    "is_done": True,
                    "points": point
                })
    
    # 既存データを削除して入れ直す（簡易的な更新処理）
    # ※本番ではUpsertやDelete Insertを厳密に行うのがベター
    try:
        # まずこのユーザーの期間中のデータを消す（重複防止）
        supabase.table("logs_member")\
            .delete()\
            .eq("user_name", user_name)\
            .eq("lom_name", lom_name)\
            .in_("target_date", TARGET_DATES)\
            .execute()
            
        # 新しいデータをInsert
        if insert_list:
            supabase.table("logs_member").insert(insert_list).execute()
            
        return True
    except Exception as e:
        st.error(f"保存エラー: {e}")
        return False

# ==========================================
#  5. メイン画面
# ==========================================

def main():
    st.title("👔 JCメンバー デコ活")
    
    # --- ログインセクション ---
    if "jc_user" not in st.session_state:
        st.info("LOM名と氏名を入力してログインしてください")
        with st.form("login"):
            lom = st.selectbox("所属LOM", LOM_LIST)
            name = st.text_input("氏名", placeholder="例：岡山 太郎")
            if st.form_submit_button("ログイン"):
                if name:
                    st.session_state.jc_user = {"lom": lom, "name": name}
                    st.rerun()
                else:
                    st.warning("氏名を入力してください")
        return

    # --- ダッシュボード ---
    user = st.session_state.jc_user
    st.markdown(f"**👤 {user['lom']}JC {user['name']} 君**")
    
    # 既存データの読み込み
    logs_df = fetch_member_logs(user['name'], user['lom'])
    
    # ポイント計算
    total_points = logs_df['points'].sum() if not logs_df.empty else 0
    
    st.markdown(f"""
    <div class="metric-box">
        <div style="font-size:14px;">現在の獲得ポイント</div>
        <div style="font-size:32px; font-weight:bold; color:#0277BD;">{total_points:,} <span style="font-size:16px;">g-CO2</span></div>
    </div>
    """, unsafe_allow_html=True)

    # --- 入力フォーム (Pattern A: Excel風) ---
    st.subheader("📝 実践チェック")
    
    # データフレームの準備
    display_items = [v["label"] for v in ACTION_MASTER.values()]
    df_data = {"アクション項目": display_items}
    
    # 過去のチェック状態を復元
    for date in TARGET_DATES:
        checks = []
        for item in display_items:
            # ログの中に、この日付・このアクションがあるか探す
            # ※本来はもっと効率的なPandas操作推奨ですが、わかりやすさ優先
            label_to_key = {v["label"]: k for k, v in ACTION_MASTER.items()}
            key = label_to_key[item]
            
            is_done = False
            if not logs_df.empty:
                match = logs_df[
                    (logs_df['target_date'] == date) & 
                    (logs_df['action_label'] == key)
                ]
                if not match.empty:
                    is_done = True
            checks.append(is_done)
        df_data[date] = checks

    df = pd.DataFrame(df_data)

    # データエディター表示
    edited_df = st.data_editor(
        df,
        column_config={
            "アクション項目": st.column_config.TextColumn("メニュー", disabled=True),
            "6/1(月)": st.column_config.CheckboxColumn("1(月)", default=False),
            "6/2(火)": st.column_config.CheckboxColumn("2(火)", default=False),
            "6/3(水)": st.column_config.CheckboxColumn("3(水)", default=False),
            "6/4(木)": st.column_config.CheckboxColumn("4(木)", default=False),
            "6/5(金)": st.column_config.CheckboxColumn("5(金)", default=False),
        },
        hide_index=True,
        use_container_width=True
    )
    
    # 保存ボタン
    if st.button("記録を保存する", type="primary"):
        with st.spinner("保存中..."):
            if save_logs(user['name'], user['lom'], edited_df):
                st.success("保存しました！")
                st.balloons()
                time.sleep(1)
                st.rerun()

    st.markdown("---")

    # --- LOM対抗ランキング ---
    st.subheader("🏆 LOM対抗ランキング")
    ranking_df = fetch_lom_ranking()
    
    if not ranking_df.empty:
        # 自分のLOMの順位を探す
        my_rank = ranking_df[ranking_df['lom_name'] == user['lom']].index
        if not my_rank.empty:
            rank_num = my_rank[0] + 1
            st.info(f"現在、{user['lom']}JCは **第{rank_num}位** です！")

        # トップ5表示
        for i, row in ranking_df.head(5).iterrows():
            rank = i + 1
            icon = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"{rank}位"
            style_class = "rank-1" if rank == 1 else ""
            
            st.markdown(f"""
            <div class="lom-ranking {style_class}">
                <span style="font-size:20px;">{icon}</span> 
                <strong>{row['lom_name']}JC</strong> 
                <span style="float:right; font-weight:bold; color:#0277BD;">{row['points']:,} pt</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("まだデータがありません")

    if st.button("ログアウト", key="logout_btn"):
        st.session_state.jc_user = None
        st.rerun()

if __name__ == "__main__":
    main()
