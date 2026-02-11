import streamlit as st
import pandas as pd
import datetime
import time
import random
from supabase import create_client, Client

# ==========================================
# 1. アプリ設定 & UIデザイン (大幅リニューアル)
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活チャレンジ2026",
    page_icon="🍑",
    layout="centered", # スマホ・PC両対応で見やすく
    initial_sidebar_state="collapsed"
)

# モダンでリッチなカスタムCSS
st.markdown("""
<style>
    /* --- フォントと基本設定 --- */
    @import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;800&display=swap');
    
    :root {
        --primary-color: #00C853; /* 鮮やかな緑 */
        --primary-dark: #009624;
        --accent-color: #FF6D00; /* ビビッドなオレンジ */
        --bg-color: #F4FBF6; /* 明るいミントグリーン背景 */
        --text-color: #37474F;
        --card-shadow: 0 10px 25px -10px rgba(0,0,0,0.1); /* 柔らかい影 */
        --hover-shadow: 0 15px 35px -10px rgba(0,0,0,0.2); /* ホバー時の影 */
    }

    html, body, [class*="css"] {
        font-family: 'M PLUS Rounded 1c', sans-serif;
        background-color: var(--bg-color);
        color: var(--text-color);
        letter-spacing: 0.03em;
    }
    
    /* --- 共通ヘッダー --- */
    .header-box {
        background: linear-gradient(135deg, #ffffff 0%, #e8f5e9 100%);
        padding: 20px 25px;
        border-radius: 0 0 35px 35px;
        box-shadow: var(--card-shadow);
        margin-bottom: 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 3px solid rgba(0,200,83,0.1);
    }
    .app-logo {
        font-size: 20px; font-weight: 900; color: var(--primary-dark);
        line-height: 1.2; text-shadow: 2px 2px 0px #fff;
    }
    .user-info {
        background: #fff; color: var(--primary-dark);
        padding: 8px 15px; border-radius: 30px;
        font-size: 13px; font-weight: 800;
        border: 2px solid var(--primary-color);
        box-shadow: 0 4px 10px rgba(0,200,83,0.2);
        display: flex; align-items: center; gap: 5px;
    }

    /* --- ④ ログイン画面のカード --- */
    .login-grid { display: flex; flex-wrap: wrap; gap: 20px; justify-content: center; margin-top: 30px; }
    .login-card {
        width: 45%; height: 160px;
        border-radius: 30px;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        color: white; font-weight: 800; font-size: 18px;
        box-shadow: var(--card-shadow), inset 0 -5px 0 rgba(0,0,0,0.1);
        cursor: pointer; transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
        text-align: center; position: relative; overflow: hidden;
    }
    .login-card:hover { transform: translateY(-8px) scale(1.03); box-shadow: var(--hover-shadow); }
    /* グラデーション定義 */
    .bg-student { background: linear-gradient(145deg, #00C853, #009624); }
    .bg-family  { background: linear-gradient(145deg, #2196F3, #1565C0); }
    .bg-jc      { background: linear-gradient(145deg, #FFC107, #FF8F00); color: #fff; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }
    .bg-teacher { background: linear-gradient(145deg, #9C27B0, #7B1FA2); }
    .icon-lg { font-size: 50px; margin-bottom: 10px; filter: drop-shadow(0 4px 4px rgba(0,0,0,0.2)); }

    /* --- ① ホーム画面 --- */
    .tree-wrapper {
        position: relative; text-align: center; margin: 20px 0 60px 0;
        height: 280px; display: flex; align-items: flex-end; justify-content: center;
        background: radial-gradient(circle at center bottom, rgba(0,200,83,0.15) 0%, transparent 70%);
    }
    .total-badge {
        background: #fff;
        border: none;
        /* 緑の多重ボーダー風のリッチな影 */
        box-shadow: 0 0 0 4px #fff, 0 0 0 8px var(--primary-color), 0 15px 30px -10px rgba(0,0,0,0.3);
        border-radius: 50px; padding: 12px 30px;
        font-weight: 900; color: var(--primary-dark); font-size: 16px;
        position: absolute; bottom: -25px; z-index: 5;
    }
    
    /* メインのアクションボタン */
    .stButton>button[kind="primary"] {
        background: linear-gradient(to bottom, #FF9800, #F57C00) !important;
        color: white !important; border: none !important;
        padding: 15px !important; border-radius: 35px !important;
        font-weight: 900 !important; font-size: 22px !important;
        box-shadow: 0 6px 0 #E65100, 0 15px 25px -10px rgba(255, 152, 0, 0.5) !important;
        transition: all 0.1s !important; margin: 20px 0 !important; height: auto !important;
    }
    .stButton>button[kind="primary"]:active {
        transform: translateY(6px) !important;
        box-shadow: 0 0 0 #E65100, 0 5px 10px -5px rgba(255, 152, 0, 0.5) !important;
    }
    
    /* メニューボタンの装飾 */
    .menu-card-style {
        background: #fff; border-radius: 25px; padding: 20px 10px;
        text-align: center; font-weight: 800; font-size: 15px;
        box-shadow: var(--card-shadow); color: var(--text-color);
        height: 100%; display: flex; flex-direction: column;
        justify-content: center; align-items: center; transition: 0.3s;
    }
    .menu-card-style:hover { transform: translateY(-5px); box-shadow: var(--hover-shadow); color: var(--primary-color); }

    /* --- ② アクションリスト & ③ ランキング --- */
    .action-row, .rank-row {
        background: #fff; border-radius: 20px; padding: 18px 25px;
        margin-bottom: 15px; box-shadow: var(--card-shadow);
        display: flex; align-items: center; justify-content: space-between;
        border: none; transition: 0.2s;
    }
    .action-row:hover, .rank-row:hover { transform: translateX(5px); box-shadow: var(--hover-shadow); }
    .medal { font-size: 32px; width: 50px; text-align: center; margin-right: 15px; filter: drop-shadow(0 3px 3px rgba(0,0,0,0.2)); }
    
    /* Streamlit標準要素の調整 */
    .stRadio>div { gap: 10px; background: #fff; padding: 10px; border-radius: 20px; box-shadow: inset 0 2px 5px rgba(0,0,0,0.05); }
    .stButton>button { border-radius: 25px; font-weight: 800; border: none; box-shadow: var(--card-shadow); transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-3px); box-shadow: var(--hover-shadow); }
    div[data-baseweb="input"] { border-radius: 15px; border: 2px solid #E0E0E0; }
    div[data-baseweb="select"]>div { border-radius: 15px; border: 2px solid #E0E0E0; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. データベース接続 & 状態管理 (変更なし)
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

if 'page' not in st.session_state: st.session_state.page = 'LOGIN'
if 'user' not in st.session_state: st.session_state.user = None
if 'game_done' not in st.session_state: st.session_state.game_done = False

# ==========================================
# 3. 画面コンポーネント (View)
# ==========================================

# --- ヘッダー ---
def render_header():
    user = st.session_state.user
    name = user['name'] if user else "ゲスト"
    role_icon = "🍑"
    if user:
        icons = {"student": "👦", "family": "🏠", "jc": "👔", "teacher": "🏫"}
        role_icon = icons.get(user['role'], "🍑")

    st.markdown(f"""
    <div class="header-box">
        <div style="display:flex; align-items:center; gap:15px;">
            <div style="font-size:36px; filter: drop-shadow(0 2px 2px rgba(0,0,0,0.1));">🌏</div>
            <div class="app-logo">おかやまデコ活<br>チャレンジ2026</div>
        </div>
        <div class="user-info">
            <span style="font-size:16px;">{role_icon}</span> {name}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- ④ ログイン画面 (4つの入り口) ---
def screen_login_entry():
    st.markdown("<div style='text-align:center; margin: 50px 0 30px;'><div style='font-size:80px; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.1));'>🍑</div><h1 style='color:#2E7D32; font-weight:900; text-shadow: 2px 2px 0 #fff;'>参加する入り口を選んでね！</h1></div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="login-card bg-student"><div class="icon-lg">👦</div><div>小学生は<br>こちら</div></div>', unsafe_allow_html=True)
        st.button("小学生でスタート", key="btn_s", use_container_width=True)
    with c2:
        st.markdown('<div class="login-card bg-family"><div class="icon-lg">👨‍👩‍👧</div><div>ご家族は<br>こちら</div></div>', unsafe_allow_html=True)
        st.button("ご家族でスタート", key="btn_f", use_container_width=True)
        
    st.write("") # スペース
    
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="login-card bg-jc"><div class="icon-lg">👔</div><div>JCメンバーは<br>こちら</div></div>', unsafe_allow_html=True)
        st.button("JCメンバーでスタート", key="btn_j", use_container_width=True)
    with c4:
        st.markdown('<div class="login-card bg-teacher"><div class="icon-lg">🏫</div><div>先生は<br>こちら</div></div>', unsafe_allow_html=True)
        st.button("先生でスタート", key="btn_t", use_container_width=True)

    # ボタンクリック時の処理 (セッション管理)
    if st.session_state.get('btn_s'): set_login_role("student")
    if st.session_state.get('btn_f'): set_login_role("family")
    if st.session_state.get('btn_j'): set_login_role("jc")
    if st.session_state.get('btn_t'): set_login_role("teacher")

def set_login_role(role):
    st.session_state.temp_role = role
    st.session_state.page = 'LOGIN_FORM'
    st.rerun()

# --- ログイン詳細入力 ---
def screen_login_form():
    role = st.session_state.temp_role
    st.markdown(f"<div style='text-align:center; margin-bottom:30px;'><h2 style='font-weight:900;'>情報を入力してね</h2><span style='background:#eee;padding:5px 15px;border-radius:20px;font-weight:bold;'>{role.upper()}</span></div>", unsafe_allow_html=True)
    
    with st.form("login_details"):
        if role in ["student", "family"]:
            school = st.selectbox("小学校", ["倉敷第一小学校", "岡山中央小学校", "津山東小学校", "伊島小学校"])
            c1, c2, c3 = st.columns(3)
            grade = c1.selectbox("学年", ["1年", "2年", "3年", "4年", "5年", "6年"])
            u_class = c2.text_input("組", "1")
            number = c3.number_input("番号", 1, 50)
            name = st.text_input("ニックネーム", "ももたろう")
            
            if st.form_submit_button("🚀 ミッション開始！", type="primary", use_container_width=True):
                st.session_state.user = {
                    "id": f"{school}_{grade}_{u_class}_{number}",
                    "name": name, "role": role,
                    "group": f"{school} {grade}-{u_class}"
                }
                st.session_state.page = 'HOME'
                st.rerun()
                
        elif role == "jc":
            lom = st.selectbox("所属LOM", ["岡山JC", "倉敷JC", "津山JC", "児島JC", "玉野JC"])
            name = st.text_input("氏名")
            if st.form_submit_button("🔥 LOM対抗戦に参加", type="primary", use_container_width=True):
                st.session_state.user = {
                    "id": f"JC_{name}", "name": name, "role": "jc", "group": lom
                }
                st.session_state.page = 'HOME'
                st.rerun()

# --- ① ホーム画面 (ダッシュボード) ---
def screen_home():
    render_header()
    
    # デコ活の木 (リッチな表現)
    st.markdown("""
    <div class="tree-wrapper">
        <div style="font-size:180px; line-height:1; filter: drop-shadow(0 15px 15px rgba(0,100,0,0.3)); z-index:2;">🌳</div>
        <div class="total-badge">みんなのCO2削減総量: 123,456 kg</div>
        <div style="position:absolute; top:40px; left:10px; font-size:50px; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.2));">🦌</div>
        <div style="position:absolute; top:80px; right:20px; font-size:40px; filter: drop-shadow(0 5px 5px rgba(0,0,0,0.2));">🐿️</div>
    </div>
    """, unsafe_allow_html=True)
    
    # アクション記録ボタン (カスタムCSSで装飾済み)
    if st.button("📝 きょうのアクションを記録する！", type="primary", use_container_width=True):
        st.session_state.page = 'ACTION'
        st.rerun()
        
    st.write("")
    
    # 3つのメニューボタン (デザインをCSSで適用)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="menu-card-style"><div style="font-size:32px; margin-bottom:5px;">👑</div><div>クラス<br>ランク</div></div>', unsafe_allow_html=True)
        st.button("みる", key="go_rank", use_container_width=True)
    with c2:
        st.markdown('<div class="menu-card-style"><div style="font-size:32px; margin-bottom:5px;">🎮</div><div>分別<br>ゲーム</div></div>', unsafe_allow_html=True)
        st.button("あそぶ", key="go_game", use_container_width=True)
    with c3:
        st.markdown('<div class="menu-card-style"><div style="font-size:32px; margin-bottom:5px;">🎓</div><div>環境<br>クイズ</div></div>', unsafe_allow_html=True)
        st.button("とく", key="go_quiz", use_container_width=True)
    
    # ボタンクリック時の遷移
    if st.session_state.get('go_rank'): st.session_state.page = 'RANKING'; st.rerun()
    if st.session_state.get('go_game'): st.session_state.page = 'GAME'; st.rerun()
    if st.session_state.get('go_quiz'): st.toast("準備中だよ！")

# --- ② アクション記録画面 (チェックシート) ---
def screen_action():
    render_header()
    if st.button("🏠 ホームにもどる"): st.session_state.page = 'HOME'; st.rerun()
    
    st.markdown("<h3 style='text-align:center; font-weight:900;'>📅 日付を選んでチェック！</h3>", unsafe_allow_html=True)
    dates = ["6/1(月)", "6/2(火)", "6/3(水)", "6/4(木)", "6/5(金)"]
    selected_day = st.radio(" ", dates, horizontal=True, label_visibility="collapsed")
    
    st.info(f"【{selected_day}】 できたことにチェックを入れよう！")
    
    actions = [
        {"id": "elec", "icon": "💡", "text": "電気をこまめに消した", "pt": 50},
        {"id": "food", "icon": "🍽️", "text": "ご飯を残さず食べた", "pt": 100},
        {"id": "water", "icon": "💧", "text": "水を大切に使った", "pt": 30},
    ]
    
    game_checked = st.session_state.game_done
    
    for act in actions:
        st.markdown(f"""
        <div class="action-row">
            <div style="display:flex; align-items:center;">
                <div style="font-size:36px; margin-right:15px;">{act['icon']}</div>
                <div style="font-weight:bold; font-size:18px;">{act['text']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # ボタンを右端に配置するためのカラム調整
        bc1, bc2 = st.columns([3, 1])
        with bc2:
            if st.button(f"できた！ (+{act['pt']})", key=f"{selected_day}_{act['id']}", use_container_width=True):
                st.toast(f"すごい！ +{act['pt']}ポイント Get!", icon="🎉")
                st.balloons()
        st.write("") # スペース

    # ゲーム項目
    st.markdown("---")
    st.markdown("""
    <div class="action-row" style="background:#FFF3E0;">
        <div style="display:flex; align-items:center;">
            <div style="font-size:36px; margin-right:15px;">🎮</div>
            <div style="font-weight:bold; font-size:18px;">分別ゲームで遊んだ</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    bc3, bc4 = st.columns([3, 1])
    with bc4:
        if game_checked:
            st.button("✅ 達成済！", disabled=True, use_container_width=True)
        else:
            if st.button("▶ ゲームへ", type="primary", use_container_width=True):
                st.session_state.page = 'GAME'
                st.rerun()

    if "6/5" in selected_day:
        st.markdown("---")
        st.success("🎓 全ミッション終了！アンケートに答えて認定証をもらおう！")
        if st.button("認定証をもらう", type="primary", use_container_width=True):
            st.balloons()
            st.image("https://placehold.co/600x400/FFF/D4AF37?text=Certificate", caption="おかやまエコヒーロー認定証")

# --- ③ ランキング画面 ---
def screen_ranking():
    render_header()
    if st.button("←もどる"): st.session_state.page = 'HOME'; st.rerun()
    
    user_group = st.session_state.user['group']
    st.markdown(f"<div style='text-align:center; margin-bottom:20px;'><div style='font-size:40px'>🏆</div><h3 style='font-weight:900; margin:0;'>{user_group}<br>現在の順位</h3></div>", unsafe_allow_html=True)
    
    ranks = [
        {"rank": 1, "name": "倉敷第一小 5年2組", "avg": 850, "medal": "🥇"},
        {"rank": 2, "name": "伊島小 6年1組", "avg": 820, "medal": "🥈"},
        {"rank": 3, "name": "津山東小 4年3組", "avg": 790, "medal": "🥉"},
    ]
    
    for r in ranks:
        bg_style = "background: linear-gradient(145deg, #FFF8E1, #FFECB3);" if r['rank'] == 1 else "background: white;"
        border = "border: 3px solid #FFC107;" if r['rank'] == 1 else ""
        medal_shadow = "filter: drop-shadow(0 4px 4px rgba(212,175,55,0.5));" if r['rank'] == 1 else ""
        
        st.markdown(f"""
        <div class="rank-row" style="{bg_style} {border}">
            <div class="medal" style="{medal_shadow}">{r['medal']}</div>
            <div style="flex-grow:1">
                <div style="font-size:13px; font-weight:800; color:#666; margin-bottom:5px;">{r['rank']}位</div>
                <div style="font-size:18px; font-weight:900;">{r['name']}</div>
            </div>
            <div style="text-align:right; background:rgba(255,255,255,0.5); padding:5px 15px; border-radius:15px;">
                <div style="font-size:11px; font-weight:bold;">平均</div>
                <div style="color:#2E7D32; font-weight:900; font-size:20px;">{r['avg']}<span style="font-size:14px;">g</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("""
    <div style="background:#E8F5E9; padding:20px; border-radius:20px; border:3px solid #4CAF50; text-align:center; margin-top:30px; box-shadow: var(--card-shadow);">
        <div style="font-size:40px; margin-bottom:10px;">🌱</div>
        <div style="font-weight:900; font-size:18px; color:#2E7D32;">あなたのクラスは現在 1位 です！</div>
        <div>すごい！この調子でがんばろう！</div>
    </div>
    """, unsafe_allow_html=True)

# --- 🎮 分別ゲーム画面 (変更なし) ---
def screen_game():
    render_header()
    st.markdown("<h3 style='text-align:center; font-weight:900;'>⏱️ 激闘！分別マスター</h3>", unsafe_allow_html=True)
    
    if 'game_status' not in st.session_state: st.session_state.game_status = 'READY'
    
    if st.session_state.game_status == 'READY':
        st.markdown("""
        <div style="background:white; padding:30px; border-radius:25px; text-align:center; border:4px solid #FF9800; box-shadow:var(--card-shadow);">
            <div style="font-size:50px;">🔥♻️🧱</div>
            <p style="font-weight:bold; font-size:18px;">10問タイムアタック！<br>間違えると <b style="color:#D32F2F;">+5秒</b> ペナルティ！</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("🏁 スタート！", type="primary", use_container_width=True):
            st.session_state.q_list = random.sample([
                {"name":"🍌 バナナの皮", "t":0}, {"name":"🥤 ペットボトル", "t":1},
                {"name":"📦 ダンボール", "t":1}, {"name":"🥢 割り箸", "t":0},
                {"name":"💡 電球", "t":2}, {"name":"🥣 割れた皿", "t":2}
            ] * 2, 10)
            st.session_state.q_idx = 0
            st.session_state.start_t = time.time()
            st.session_state.penalty = 0
            st.session_state.game_status = 'PLAYING'
            st.rerun()
            
    elif st.session_state.game_status == 'PLAYING':
        idx = st.session_state.q_idx
        q = st.session_state.q_list[idx]
        
        st.progress((idx)/10, text=f"第{idx+1}問")
        st.markdown(f"<div style='font-size:40px; font-weight:900; text-align:center; padding:40px; background:white; border-radius:25px; border:4px dashed #607D8B; margin:20px 0; box-shadow:var(--card-shadow);'>{q['name']}</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        def ans(t):
            if t == q['t']: st.toast("⭕ せいかい！")
            else:
                st.toast("❌ +5秒！", icon="🚨")
                st.session_state.penalty += 5
            
            if idx + 1 < 10: st.session_state.q_idx += 1
            else:
                st.session_state.final_time = round(time.time() - st.session_state.start_t + st.session_state.penalty, 2)
                st.session_state.game_status = 'FINISHED'
                st.session_state.game_done = True
            st.rerun()

        st.markdown("<style>div.stButton > button:first-child { height: 80px; font-size: 24px; }</style>", unsafe_allow_html=True)
        if c1.button("🔥 燃える", use_container_width=True): ans(0)
        if c2.button("♻️ 資源", use_container_width=True): ans(1)
        if c3.button("🧱 埋立", use_container_width=True): ans(2)

    elif st.session_state.game_status == 'FINISHED':
        st.balloons()
        st.markdown(f"""
        <div style="background:white; padding:30px; border-radius:25px; text-align:center; border:4px solid #4CAF50; box-shadow:var(--card-shadow);">
            <h2 style="color:#2E7D32; margin:0;">🎉 クリア！</h2>
            <div style="font-size:60px; font-weight:900; color:#333; margin:20px 0;">{st.session_state.final_time} <span style="font-size:30px;">秒</span></div>
            <p style="color:#D32F2F; font-weight:bold;">(ペナルティ +{st.session_state.penalty}秒 含む)</p>
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("📝 記録画面に戻る", type="primary", use_container_width=True):
            st.session_state.page = 'ACTION'
            st.session_state.game_status = 'READY'
            st.rerun()
        st.write("")
        if st.button("🔄 もう一度あそぶ", use_container_width=True):
            st.session_state.game_status = 'READY'
            st.rerun()

# ==========================================
# 4. メイン実行フロー (SPA制御)
# ==========================================
if __name__ == "__main__":
    if st.session_state.page == 'LOGIN':
        screen_login_entry()
    elif st.session_state.page == 'LOGIN_FORM':
        screen_login_form()
    elif st.session_state.page == 'HOME':
        screen_home()
    elif st.session_state.page == 'ACTION':
        screen_action()
    elif st.session_state.page == 'RANKING':
        screen_ranking()
    elif st.session_state.page == 'GAME':
        screen_game()
