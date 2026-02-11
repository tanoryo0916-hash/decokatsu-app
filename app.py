import streamlit as st
import pandas as pd
import datetime
import time
import random
from supabase import create_client, Client

# ==========================================
# 1. アプリ設定 & リッチデザインCSS
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活チャレンジ2026",
    page_icon="🍑",
    layout="centered", # スマホ・PC両対応で見やすく中央寄せ
    initial_sidebar_state="collapsed"
)

# 🎨 オシャレで使いやすいUIのためのCSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;800;900&display=swap');
    
    /* 全体のフォントと色 */
    html, body, [class*="css"] {
        font-family: 'M PLUS Rounded 1c', sans-serif;
        background-color: #F4FBF6; /* 明るいミントグリーン背景 */
        color: #37474F;
    }

    /* --- ヘッダー --- */
    .header-container {
        background: white;
        padding: 15px 20px;
        border-radius: 0 0 30px 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 30px; border-bottom: 4px solid #C8E6C9;
    }
    .app-name { font-size: 20px; font-weight: 900; color: #2E7D32; line-height: 1.2; }
    .user-badge {
        background: #E8F5E9; color: #2E7D32; padding: 6px 15px;
        border-radius: 20px; font-size: 13px; font-weight: 800;
        display: flex; align-items: center; gap: 5px; border: 2px solid #C8E6C9;
    }

    /* --- ボタンのスタイル（重要：ここを変えてオシャレに） --- */
    
    /* 1. メインのアクションボタン（記録する） */
    .big-action-btn button {
        background: linear-gradient(135deg, #FF6F00 0%, #FF8F00 100%) !important;
        color: white !important;
        height: 90px !important;
        border-radius: 30px !important;
        font-size: 24px !important;
        font-weight: 900 !important;
        box-shadow: 0 10px 0 #E65100, 0 20px 20px rgba(255, 111, 0, 0.3) !important;
        border: none !important;
        transition: transform 0.1s, box-shadow 0.1s !important;
        margin-bottom: 10px !important;
    }
    .big-action-btn button:active { 
        transform: translateY(10px) !important; 
        box-shadow: 0 0 0 #E65100, 0 0 0 rgba(0,0,0,0) !important;
    }

    /* 2. メニューボタン（ランク・ゲームなど） */
    .menu-btn button {
        background: white !important;
        color: #455A64 !important;
        height: 120px !important; /* 正方形っぽく */
        border-radius: 25px !important;
        border: 2px solid #ECEFF1 !important;
        box-shadow: 0 6px 0 #CFD8DC, 0 10px 10px rgba(0,0,0,0.05) !important; /* 下に厚みを持たせる */
        font-weight: 800 !important;
        font-size: 16px !important;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        transition: transform 0.1s !important;
    }
    .menu-btn button:hover {
        border-color: #81C784 !important;
        color: #2E7D32 !important;
        transform: translateY(-2px) !important;
    }
    .menu-btn button:active {
        transform: translateY(6px) !important; /* 押した時に凹む */
        box-shadow: 0 0 0 #CFD8DC !important;
    }
    .menu-icon { font-size: 40px; margin-bottom: 5px; }

    /* --- ログイン入口カード --- */
    .login-btn button {
        height: 150px !important;
        border-radius: 30px !important;
        color: white !important;
        font-size: 18px !important;
        font-weight: 900 !important;
        border: none !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15) !important;
        transition: transform 0.2s !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    .login-btn button:hover { transform: translateY(-5px) scale(1.02) !important; }
    
    /* 色分けクラス */
    .btn-green button { background: linear-gradient(135deg, #43A047, #66BB6A) !important; }
    .btn-blue button { background: linear-gradient(135deg, #1E88E5, #42A5F5) !important; }
    .btn-yellow button { background: linear-gradient(135deg, #FFB300, #FFCA28) !important; color: #5D4037 !important; text-shadow:none !important; }
    .btn-purple button { background: linear-gradient(135deg, #8E24AA, #AB47BC) !important; }

    /* --- ランキングリスト --- */
    .rank-card {
        background: white; border-radius: 20px; padding: 15px 20px; margin-bottom: 15px;
        display: flex; align-items: center; box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        border: 2px solid transparent;
        transition: transform 0.2s;
    }
    .rank-card:hover { transform: scale(1.02); }
    .rank-1 { border-color: #FFD700; background: linear-gradient(to right, #FFFDE7, #FFF); }
    .medal { font-size: 32px; width: 50px; text-align: center; margin-right: 15px; filter: drop-shadow(0 2px 2px rgba(0,0,0,0.2)); }

    /* Streamlit標準要素の調整 */
    .stRadio>div { background: white; padding: 15px; border-radius: 20px; box-shadow: inset 0 2px 5px rgba(0,0,0,0.05); gap: 10px; }
    div[data-baseweb="input"] { border-radius: 15px; border: 2px solid #E0E0E0; }
    div[data-baseweb="select"]>div { border-radius: 15px; border: 2px solid #E0E0E0; }

</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. データベース接続 & ステート管理
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

# 画面遷移の状態管理
if 'page' not in st.session_state: st.session_state.page = 'LOGIN'
if 'user' not in st.session_state: st.session_state.user = None
if 'game_done' not in st.session_state: st.session_state.game_done = False

def go_to(page_name):
    """画面遷移用関数"""
    st.session_state.page = page_name
    st.rerun()

# ==========================================
# 3. 各画面コンポーネント (View)
# ==========================================

# --- ヘッダー表示 ---
def render_header():
    user = st.session_state.user
    name = user['name'] if user else "ゲスト"
    role_map = {"student": "👦 児童", "family": "🏠 家族", "jc": "👔 JC", "teacher": "🏫 先生"}
    role_label = role_map.get(user['role'], "ゲスト") if user else ""

    st.markdown(f"""
    <div class="header-container">
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="font-size:32px; filter: drop-shadow(0 2px 2px rgba(0,0,0,0.1));">🌏</div>
            <div class="app-name">おかやまデコ活<br>チャレンジ2026</div>
        </div>
        <div class="user-badge">
            {role_label} | {name}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- ① ログイン入口画面 ---
def view_login_entry():
    st.markdown("<div style='text-align:center; margin: 40px 0 30px;'><div style='font-size:80px; filter: drop-shadow(0 10px 10px rgba(0,0,0,0.1));'>🍑</div><h2 style='color:#2E7D32; font-weight:900; letter-spacing:2px;'>参加する入り口を選んでね</h2></div>", unsafe_allow_html=True)
    
    # 4色の大きなボタン（グリッドレイアウト）
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="login-btn btn-green">', unsafe_allow_html=True)
        if st.button("👦\n小学生", key="l_stu", use_container_width=True):
            st.session_state.temp_role = "student"
            go_to('LOGIN_FORM')
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="login-btn btn-blue">', unsafe_allow_html=True)
        if st.button("🏠\nご家族", key="l_fam", use_container_width=True):
            st.session_state.temp_role = "family"
            go_to('LOGIN_FORM')
        st.markdown('</div>', unsafe_allow_html=True)
    
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="login-btn btn-yellow">', unsafe_allow_html=True)
        if st.button("👔\nJCメンバー", key="l_jc", use_container_width=True):
            st.session_state.temp_role = "jc"
            go_to('LOGIN_FORM')
        st.markdown('</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="login-btn btn-purple">', unsafe_allow_html=True)
        if st.button("🏫\n先生", key="l_tea", use_container_width=True):
            st.session_state.temp_role = "teacher"
            go_to('LOGIN_FORM')
        st.markdown('</div>', unsafe_allow_html=True)

# --- ログインフォーム詳細 ---
def view_login_form():
    role = st.session_state.temp_role
    st.markdown(f"<div style='text-align:center; margin-bottom:20px;'><h3 style='font-weight:900; margin-bottom:5px;'>情報を入力してね</h3><span style='background:#ECEFF1; padding:5px 15px; border-radius:15px; font-size:12px; font-weight:bold; color:#546E7A;'>{role.upper()}</span></div>", unsafe_allow_html=True)

    with st.form("login"):
        if role in ["student", "family"]:
            school = st.selectbox("小学校", ["倉敷第一小学校", "岡山中央小学校", "津山東小学校", "伊島小学校"])
            c1, c2, c3 = st.columns(3)
            grade = c1.selectbox("学年", ["1年", "2年", "3年", "4年", "5年", "6年"])
            u_class = c2.text_input("組", "1")
            num = c3.number_input("番号", 1, 50)
            name = st.text_input("ニックネーム", "ももたろう")
            
            if st.form_submit_button("🚀 スタート！", type="primary"):
                # ここでユーザー情報を保存
                st.session_state.user = {
                    "id": f"{school}_{grade}_{u_class}_{num}",
                    "name": name, "role": role, "group": f"{school} {grade}-{u_class}"
                }
                go_to('HOME')
                
        else: # JC or Teacher
            org_label = "所属LOM" if role == "jc" else "担当クラス"
            org_opts = ["岡山JC", "倉敷JC", "津山JC"] if role == "jc" else ["5年2組", "6年1組"]
            org = st.selectbox(org_label, org_opts)
            name = st.text_input("氏名")
            
            if st.form_submit_button("🔥 ログイン", type="primary"):
                st.session_state.user = {
                    "id": f"{role}_{name}", "name": name, "role": role, "group": org
                }
                go_to('HOME')

# --- ② ホーム画面 (ダッシュボード) ---
def view_home():
    render_header()
    
    # 🌳 デコ活の木 (視覚的フィードバック)
    st.markdown("""
    <div style="text-align:center; position:relative; margin-bottom:30px; margin-top:10px;">
        <div style="font-size:160px; line-height:1; filter: drop-shadow(0 15px 15px rgba(0,100,0,0.2)); z-index:2; position:relative;">🌳</div>
        <div style="position:absolute; top:40px; left:10px; font-size:50px; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.2)); animation: bounce 2s infinite;">🦌</div>
        <div style="position:absolute; top:80px; right:20px; font-size:40px; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.2));">🐿️</div>
        
        <div style="background:white; border:4px solid #4CAF50; border-radius:50px; padding:12px 25px; display:inline-block; font-weight:900; color:#1B5E20; box-shadow:0 8px 15px rgba(0,0,0,0.1); position:relative; top:-20px; z-index:5;">
            みんなの削減量: 123,456 kg
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 🔥 メインアクションボタン (CTA)
    st.markdown('<div class="big-action-btn">', unsafe_allow_html=True)
    if st.button("📝 きょうの記録をつける！", use_container_width=True):
        go_to('ACTION')
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.write("") # スペース
    
    # 📱 メニューボタン (アイコン+テキスト一体型)
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
        if st.button("👑\nランク", key="m_rank", use_container_width=True):
            go_to('RANKING')
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c2:
        st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
        if st.button("🎮\nゲーム", key="m_game", use_container_width=True):
            go_to('GAME')
        st.markdown('</div>', unsafe_allow_html=True)
        
    with c3:
        st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
        if st.button("🎓\nクイズ", key="m_quiz", use_container_width=True):
            st.toast("6月5日にオープンするよ！", icon="🔒")
        st.markdown('</div>', unsafe_allow_html=True)

# --- ③ アクション記録画面 (チェックシート) ---
def view_action():
    render_header()
    if st.button("🏠 ホームに戻る", type="secondary"): go_to('HOME')
    
    st.markdown("<h3 style='text-align:center; font-weight:900; margin:20px 0;'>📅 日付を選んでね</h3>", unsafe_allow_html=True)
    
    # 日付タブ
    days = ["6/1(月)", "6/2(火)", "6/3(水)", "6/4(木)", "6/5(金)"]
    selected = st.radio(" ", days, horizontal=True, label_visibility="collapsed")
    
    st.info(f"【{selected}】 できたこと全部にチェック！")
    
    # アクションリスト定義
    acts = [
        ("💡", "電気をこまめに消した", 50),
        ("🍚", "ご飯を残さず食べた", 100),
        ("💧", "水を大切に使った", 30)
    ]
    
    # チェックリストUI
    for icon, label, pt in acts:
        # カード風レイアウト
        with st.container():
            c_icon, c_lbl, c_btn = st.columns([1, 4, 2])
            with c_icon: st.markdown(f"<div style='font-size:36px; text-align:center'>{icon}</div>", unsafe_allow_html=True)
            with c_lbl: st.markdown(f"<div style='font-weight:bold; font-size:18px; margin-top:5px;'>{label}</div>", unsafe_allow_html=True)
            with c_btn:
                # 押した感のあるボタン
                if st.button(f"できた! (+{pt})", key=f"{selected}_{label}", use_container_width=True):
                    st.toast(f"ナイス！ {pt}ポイントゲット！", icon="🎉")
                    st.balloons()
            st.markdown("---") 

    # ゲーム連携項目
    st.markdown(f"**🎮 分別ゲーム**")
    if st.session_state.game_done:
        st.success("✅ クリア済み！ (+50pt)")
    else:
        if st.button("▶ ゲームに挑戦する", type="primary", use_container_width=True):
            go_to('GAME')

    # 6/5限定: 認定証
    if "6/5" in selected:
        st.markdown("---")
        st.success("🎓 全ミッション終了！")
        if st.button("🏆 認定証をもらう", use_container_width=True):
            st.balloons()
            st.image("https://placehold.co/600x400/FFF/D4AF37?text=CERTIFICATE", caption="おかやまエコヒーロー認定証")

# --- ④ ランキング画面 (Wランキング) ---
def view_ranking():
    render_header()
    if st.button("🏠 ホームに戻る"): go_to('HOME')
    
    user_group = st.session_state.user['group']
    role = st.session_state.user['role']
    
    # 自分の属性に合わせてランキングタイトルを変更
    rank_title = "LOM対抗" if role == "jc" else "クラス対抗"
    
    st.markdown(f"<div style='text-align:center; margin-bottom:20px'><div style='font-size:50px'>🏆</div><h3 style='font-weight:900'>{rank_title}<br>現在の順位</h3><p>※1人あたりの平均削減量</p></div>", unsafe_allow_html=True)
    
    # ダミーデータ (本来はfetch_rankings関数から取得)
    if role == "jc":
        ranks = [(1, "岡山JC", 620), (2, "倉敷JC", 580), (3, "津山JC", 450)]
    else:
        ranks = [(1, "倉敷第一小 5-2", 850), (2, "伊島小 6-1", 820), (3, "津山東小 4-3", 790)]
    
    for r, name, score in ranks:
        is_top = (r == 1)
        # 1位だけ特別に金色に装飾
        st.markdown(f"""
        <div class="rank-card {'rank-1' if is_top else ''}">
            <div class="medal">{'🥇' if r==1 else '🥈' if r==2 else '🥉'}</div>
            <div style="flex-grow:1">
                <div style="font-size:12px; font-weight:800; color:#555">{r}位</div>
                <div style="font-size:18px; font-weight:900">{name}</div>
            </div>
            <div style="text-align:right">
                <div style="font-size:10px; font-weight:bold; color:#777;">平均</div>
                <div style="color:#2E7D32; font-weight:900; font-size:22px">{score}<span style="font-size:14px">g</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if role != "jc":
        st.info(f"あなたのクラス：**{user_group}** は現在 1位 です！")

# --- ⑤ 分別ゲーム画面 (激闘！分別マスター) ---
def view_game():
    render_header()
    
    st.markdown("<h3 style='text-align:center; font-weight:900;'>⏱️ 分別マスター</h3>", unsafe_allow_html=True)
    
    if 'game_state' not in st.session_state: st.session_state.game_state = 'READY'
    
    if st.session_state.game_state == 'READY':
        st.markdown("""
        <div style="background:white; padding:30px; border-radius:25px; text-align:center; border:4px solid #FF9800; box-shadow:0 5px 15px rgba(0,0,0,0.1); margin-bottom:20px;">
            <div style="font-size:60px;">🔥♻️</div>
            <p style="font-weight:900; font-size:18px; margin-top:10px;">10問タイムアタック！<br>ミスすると <b style="color:#D32F2F;">+5秒</b> ペナルティ！</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🏁 スタート！", type="primary", use_container_width=True):
            # ゲームデータ初期化
            st.session_state.q_list = random.sample([
                ("🍌 バナナの皮", 0), ("🥤 ペットボトル", 1), ("📦 ダンボール", 1), 
                ("🥢 割り箸", 0), ("💡 電球", 2), ("🥣 割れた皿", 2)
            ]*4, 10)
            st.session_state.q_idx = 0
            st.session_state.start_t = time.time()
            st.session_state.penalty = 0
            st.session_state.game_state = 'PLAYING'
            st.rerun()
            
    elif st.session_state.game_state == 'PLAYING':
        idx = st.session_state.q_idx
        q_name, q_type = st.session_state.q_list[idx]
        
        st.progress((idx)/10, text=f"第 {idx+1} 問")
        st.markdown(f"<div style='font-size:40px; text-align:center; font-weight:900; padding:40px; background:white; border-radius:20px; border:4px dashed #90A4AE; margin:20px 0; box-shadow:0 5px 10px rgba(0,0,0,0.05);'>{q_name}</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        
        def ans(t):
            if t == q_type: 
                st.toast("⭕ せいかい！")
            else:
                st.toast("❌ +5秒", icon="🚨")
                st.session_state.penalty += 5
            
            if idx + 1 < 10: 
                st.session_state.q_idx += 1
            else:
                st.session_state.final_time = round(time.time() - st.session_state.start_t + st.session_state.penalty, 2)
                st.session_state.game_done = True
                st.session_state.game_state = 'FINISHED'
            st.rerun()

        # ゲーム用ボタンのスタイル調整
        st.markdown("<style>div.stButton button {height: 80px !important; font-size: 20px !important;}</style>", unsafe_allow_html=True)
        
        if c1.button("🔥 燃える", use_container_width=True): ans(0)
        if c2.button("♻️ 資源", use_container_width=True): ans(1)
        if c3.button("🧱 埋立", use_container_width=True): ans(2)

    elif st.session_state.game_state == 'FINISHED':
        st.balloons()
        st.markdown(f"""
        <div style="background:white; padding:30px; border-radius:25px; text-align:center; border:4px solid #4CAF50; box-shadow:0 10px 20px rgba(0,0,0,0.1);">
            <h2 style="color:#2E7D32; margin:0;">🎉 クリア！</h2>
            <div style="font-size:60px; font-weight:900; color:#333; margin:20px 0;">{st.session_state.final_time} <span style="font-size:30px;">秒</span></div>
            <p style="color:#D32F2F; font-weight:bold;">(ペナルティ +{st.session_state.penalty}秒 含む)</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.write("")
        if st.button("📝 記録画面に戻る", type="primary", use_container_width=True):
            go_to('ACTION')
            st.session_state.game_state = 'READY' 

# ==========================================
# 4. メインルーティング (画面切り替え)
# ==========================================
if __name__ == "__main__":
    p = st.session_state.page
    if p == 'LOGIN': view_login_entry()
    elif p == 'LOGIN_FORM': view_login_form()
    elif p == 'HOME': view_home()
    elif p == 'ACTION': view_action()
    elif p == 'RANKING': view_ranking()
    elif p == 'GAME': view_game()
