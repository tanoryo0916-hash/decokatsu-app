import streamlit as st
import pandas as pd
import datetime
import time
import random
from supabase import create_client, Client

# ==========================================
# 1. デザイン設定 & CSS (GIGA端末・スマホ対応)
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活チャレンジ2026",
    page_icon="🍑",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# カスタムCSS: 議案の「遊びの遊び化」をデザインで表現
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Noto Sans JP', sans-serif;
        background-color: #F0F9EE; /* 環境に優しい薄緑 */
    }
    
    /* ヘッダー */
    .main-header {
        background: linear-gradient(135deg, #FF9800 0%, #FF5722 100%);
        padding: 1.5rem;
        border-radius: 0 0 25px 25px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* カードデザイン */
    .stCard {
        background: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 15px;
        border-bottom: 4px solid #4CAF50;
    }

    /* ボタンカスタマイズ (タップしやすい大きさ) */
    .stButton>button {
        border-radius: 30px;
        height: 50px;
        font-weight: bold !important;
        font-size: 18px !important;
        box-shadow: 0 4px 0 rgba(0,0,0,0.1);
        transition: all 0.1s;
    }
    .stButton>button:active {
        transform: translateY(4px);
        box-shadow: none;
    }

    /* ゲーム用スタイル */
    .game-question {
        font-size: 32px;
        font-weight: 900;
        text-align: center;
        padding: 30px;
        background: #FFF;
        border: 4px dashed #607D8B;
        border-radius: 20px;
        color: #333;
        margin: 10px 0;
    }
    
    /* ランキングアイテム */
    .rank-row {
        display: flex;
        justify-content: space-between;
        padding: 10px;
        border-bottom: 1px solid #eee;
        font-weight: bold;
    }
    .rank-badge {
        background-color: #FFD700;
        color: #5D4037;
        padding: 2px 8px;
        border-radius: 5px;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. データベース接続 & ロジック
# ==========================================
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except:
        return None

supabase = init_connection()

# --- データ保存関数 ---
def save_daily_log(user_data, date_str, actions, points):
    """5日間チェックシートの保存（遡り入力対応）"""
    if not supabase: return
    try:
        data = {
            "user_id": user_data['id'],
            "role": user_data['role'],
            "group_name": user_data['group'], # 学校名+クラス or LOM名
            "target_date": date_str,
            "actions": ",".join(actions),
            "points": points,
            "updated_at": "now()"
        }
        # 実際は upsert (既存なら更新) が望ましい
        supabase.table("logs_2026").upsert(data).execute()
        return True
    except:
        return False

def save_game_score(user_data, score_time):
    """ゲームスコア保存"""
    if not supabase: return
    try:
        data = {
            "user_id": user_data['id'],
            "name": user_data['name'],
            "group_name": user_data['group'],
            "time": score_time,
            "created_at": "now()"
        }
        supabase.table("game_scores").insert(data).execute()
    except:
        pass

# --- ランキング取得（議案：平均値算出） ---
def fetch_rankings(category):
    """
    category: 'class' or 'lom'
    本来はSupabase側で集計するが、デモ用にダミーデータを返す構造
    """
    if category == 'class':
        return [
            {"rank": 1, "name": "倉敷第一小 5-1", "avg": 485},
            {"rank": 2, "name": "岡山中央小 4-3", "avg": 420},
            {"rank": 3, "name": "伊島小 6-2", "avg": 395},
        ]
    else: # LOM
        return [
            {"rank": 1, "name": "岡山JC", "avg": 610},
            {"rank": 2, "name": "倉敷JC", "avg": 580},
            {"rank": 3, "name": "津山JC", "avg": 450},
        ]

# ==========================================
# 3. 分別ゲームロジック
# ==========================================
GARBAGE_ITEMS = [
    {"name": "🍌 バナナの皮", "type": 0}, {"name": "🥤 ペットボトル", "type": 1},
    {"name": "🤧 ティッシュ", "type": 0}, {"name": "📦 ダンボール", "type": 1},
    {"name": "🥫 空き缶", "type": 1}, {"name": "💡 電球", "type": 2},
    {"name": "🍂 落ち葉", "type": 0}, {"name": "🥣 割れた皿", "type": 2},
]
# 0:燃える, 1:資源, 2:埋立

# ==========================================
# 4. 画面コンポーネント
# ==========================================

def login_screen():
    st.markdown("""
        <div class="main-header">
            <h1>🍑 おかやまデコ活2026</h1>
            <p>10,000人のヒーロー求む！</p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["👦 じどう・かぞく", "👔 JCメンバー", "🏫 先生"])

    with tab1:
        st.markdown("### 🏫 学校をえらんでね")
        with st.form("student_login"):
            school = st.selectbox("小学校名", ["倉敷第一小学校", "岡山中央小学校", "津山東小学校", "その他"])
            col_g, col_c, col_n = st.columns(3)
            grade = col_g.selectbox("学年", ["1年", "2年", "3年", "4年", "5年", "6年"])
            u_class = col_c.text_input("組", placeholder="1")
            number = col_n.number_input("番号", 1, 50)
            
            # 議案：家族アカウント
            role_sel = st.radio("つかう人は？", ["ぼく・わたし (児童)", "おうちの人 (家族)"], horizontal=True)
            nickname = st.text_input("ニックネーム (ひらがな)", placeholder="ももたろう")
            
            if st.form_submit_button("🚀 スタート！", type="primary", use_container_width=True):
                if u_class and nickname:
                    st.session_state.user = {
                        "id": f"{school}_{grade}_{u_class}_{number}",
                        "name": nickname,
                        "group": f"{school} {grade}-{u_class}",
                        "role": "student" if "児童" in role_sel else "family"
                    }
                    st.rerun()
                else:
                    st.error("組とニックネームを入れてね")

    with tab2:
        st.markdown("### 👔 LOM対抗戦エントリー")
        with st.form("jc_login"):
            lom = st.selectbox("所属LOM", ["岡山JC", "倉敷JC", "津山JC", "児島JC", "玉野JC", "笠岡JC", "井原JC", "総社JC", "高梁JC", "新見JC", "備前JC", "瀬戸内JC", "赤磐JC", "真庭JC", "美作JC"])
            jc_name = st.text_input("氏名")
            if st.form_submit_button("エントリー", type="primary", use_container_width=True):
                if jc_name:
                    st.session_state.user = {
                        "id": f"JC_{lom}_{jc_name}",
                        "name": jc_name,
                        "group": lom,
                        "role": "jc"
                    }
                    st.rerun()

    with tab3:
        st.info("先生用ダッシュボードは、配布された管理者パスワードでログインしてください。")

def main_dashboard():
    user = st.session_state.user
    
    # ユーザーヘッダー
    role_icon = "👔" if user['role'] == "jc" else "👦"
    st.markdown(f"""
        <div class="main-header" style="padding:1rem; border-radius:0 0 20px 20px;">
            <div style="font-size:14px; opacity:0.9;">{user['group']}</div>
            <div style="font-size:24px; font-weight:bold;">{role_icon} {user['name']} 隊員</div>
        </div>
    """, unsafe_allow_html=True)

    # 議案：遊びの遊び化（Wランキング）
    tab_action, tab_game, tab_rank = st.tabs(["📝 デコ活記録", "⏱️ 分別ゲーム", "🏆 ランキング"])

    # --- 1. アクション記録 (5日間シート) ---
    with tab_action:
        st.markdown('<div class="stCard">', unsafe_allow_html=True)
        st.markdown("### 📅 日付をえらんで記録")
        # 議案：遡り入力可能
        target_date = st.select_slider("", options=["6/1", "6/2", "6/3", "6/4", "6/5"], value="6/1")
        
        st.write(f"**{target_date}** にできたことは？")
        
        actions = [
            ("💡 電気", 50), ("🍚 食事", 100), ("🚰 水", 30), ("♻️ 分別", 80), ("👨‍👩‍👧 家族", 50)
        ]
        
        # フォーム
        with st.form(f"act_{target_date}"):
            cols = st.columns(2)
            done_acts = []
            total_pts = 0
            for i, (label, pts) in enumerate(actions):
                if cols[i%2].checkbox(f"{label} ({pts}g)", key=f"{target_date}_{i}"):
                    done_acts.append(label)
                    total_pts += pts
            
            if st.form_submit_button("✅ 記録して保存", type="primary", use_container_width=True):
                # save_daily_log(user, target_date, done_acts, total_pts)
                st.balloons()
                st.success(f"{total_pts}g のCO2削減完了！ナイスデコ活！")
        
        # 環境の日スペシャル (6/5のみ)
        if target_date == "6/5":
            st.markdown("---")
            st.markdown("#### 🎓 エコヒーロー認定試験")
            if st.button("アンケートに答えて認定証をもらう"):
                st.image("https://placehold.co/600x400/FFF8E1/D4AF37?text=CERTIFICATE", caption="おかやまエコヒーロー認定証")
                st.info("おめでとう！画像を保存してね！")
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 2. 激闘！分別マスター (ゲーム) ---
    with tab_game:
        st.markdown('<div class="stCard">', unsafe_allow_html=True)
        st.markdown("### ⏱️ 激闘！分別マスター")
        st.caption("10問タイムアタック！間違えると+5秒！")

        if 'game_state' not in st.session_state: st.session_state.game_state = 'READY'
        
        if st.session_state.game_state == 'READY':
            if st.button("🏁 スタート！", type="primary", use_container_width=True):
                st.session_state.q_list = random.sample(GARBAGE_ITEMS * 2, 10) # 10問
                st.session_state.q_idx = 0
                st.session_state.start_time = time.time()
                st.session_state.penalty = 0
                st.session_state.game_state = 'PLAYING'
                st.rerun()

        elif st.session_state.game_state == 'PLAYING':
            idx = st.session_state.q_idx
            q_item = st.session_state.q_list[idx]
            
            st.progress((idx)/10, text=f"第 {idx+1} 問")
            st.markdown(f'<div class="game-question">{q_item["name"]}</div>', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            # コールバック関数
            def answer(ans_type):
                if ans_type == q_item['type']:
                    st.toast("⭕ せいかい！", icon="✨")
                else:
                    st.toast("❌ +5秒ペナルティ", icon="🚨")
                    st.session_state.penalty += 5
                
                if st.session_state.q_idx + 1 < 10:
                    st.session_state.q_idx += 1
                else:
                    final = round(time.time() - st.session_state.start_time + st.session_state.penalty, 2)
                    st.session_state.final_score = final
                    st.session_state.game_state = 'FINISHED'
                    # save_game_score(user, final)

            if c1.button("🔥 燃える", use_container_width=True): answer(0); st.rerun()
            if c2.button("♻️ 資源", use_container_width=True): answer(1); st.rerun()
            if c3.button("🧱 埋立", use_container_width=True): answer(2); st.rerun()

        elif st.session_state.game_state == 'FINISHED':
            st.balloons()
            st.markdown(f"## 記録: {st.session_state.final_score} 秒")
            st.info(f"ペナルティ: +{st.session_state.penalty}秒 込み")
            if st.button("もう一度ちょうせん！", type="primary", use_container_width=True):
                st.session_state.game_state = 'READY'
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. ランキング (議案：平均値による公平性) ---
    with tab_rank:
        st.markdown('<div class="stCard">', unsafe_allow_html=True)
        st.markdown("### 🏆 リアルタイム順位")
        st.caption("※ 1人あたりの平均削減量で競います")
        
        r_col1, r_col2 = st.columns(2)
        
        with r_col1:
            st.markdown("**🏫 クラス対抗**")
            ranks = fetch_rankings('class')
            for r in ranks:
                st.markdown(f'<div class="rank-row"><span class="rank-badge">{r["rank"]}</span>{r["name"]} <br><span style="color:#2E7D32">{r["avg"]}g</span></div>', unsafe_allow_html=True)
        
        with r_col2:
            st.markdown("**👔 LOM対抗**")
            ranks = fetch_rankings('lom')
            for r in ranks:
                st.markdown(f'<div class="rank-row"><span class="rank-badge">{r["rank"]}</span>{r["name"]} <br><span style="color:#2E7D32">{r["avg"]}g</span></div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # ログアウト
    if st.button("ログアウト", key="logout"):
        st.session_state.user = None
        st.rerun()

# ==========================================
# 5. メイン実行
# ==========================================
if __name__ == "__main__":
    if 'user' not in st.session_state or st.session_state.user is None:
        login_screen()
    else:
        main_dashboard()
