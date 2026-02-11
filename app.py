import streamlit as st
import pandas as pd
import datetime
import time
import random
from supabase import create_client, Client

# ==========================================
# 1. アプリ設定 & UIデザイン (CSS)
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活チャレンジ2026",
    page_icon="🍑",
    layout="centered",  # ← "centered" に変更してください
    initial_sidebar_state="collapsed"
)

# 添付画像のUIを再現するカスタムCSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'M PLUS Rounded 1c', sans-serif;
        background-color: #F0F9EE; /* 全体の背景色：優しい緑 */
        color: #424242;
    }
    
    /* --- 共通ヘッダー --- */
    .header-box {
        background: white;
        padding: 15px 20px;
        border-radius: 0 0 25px 25px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .app-logo { font-size: 18px; font-weight: 800; color: #2E7D32; line-height: 1.2; }
    .user-info {
        background: #FFEBEE; color: #D32F2F;
        padding: 5px 12px; border-radius: 20px;
        font-size: 12px; font-weight: bold; border: 2px solid #FFCDD2;
    }

    /* --- ④ ログイン画面のグリッドボタン --- */
    .login-grid { display: flex; flex-wrap: wrap; gap: 15px; justify-content: center; }
    .login-card {
        width: 45%; height: 140px;
        border-radius: 20px;
        display: flex; flex-direction: column;
        align-items: center; justify-content: center;
        color: white; font-weight: bold; font-size: 16px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        cursor: pointer; transition: transform 0.1s;
        text-align: center;
    }
    .login-card:hover { transform: scale(1.02); }
    .bg-student { background-color: #4CAF50; } /* 緑 */
    .bg-family  { background-color: #2196F3; } /* 青 */
    .bg-jc      { background-color: #FFC107; color: #5D4037; } /* 黄 */
    .bg-teacher { background-color: #9C27B0; } /* 紫 */
    .icon-lg { font-size: 40px; margin-bottom: 5px; }

    /* --- ① ホーム画面：デコ活の木 --- */
    .tree-wrapper {
        position: relative; text-align: center; margin: 10px 0 30px 0;
        height: 250px; display: flex; align-items: flex-end; justify-content: center;
    }
    .total-badge {
        background: rgba(255,255,255,0.95);
        border: 3px solid #4CAF50; border-radius: 50px;
        padding: 8px 20px; font-weight: 800; color: #1B5E20;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        position: absolute; bottom: -15px; z-index: 5;
    }
    .big-orange-btn {
        background: linear-gradient(180deg, #FF9800 0%, #F57C00 100%);
        color: white; padding: 15px; border-radius: 30px;
        text-align: center; font-weight: 900; font-size: 20px;
        box-shadow: 0 4px 0 #E65100; cursor: pointer; margin: 10px 0;
        border: none; width: 100%;
    }
    .menu-btn {
        background: white; border-radius: 15px; padding: 10px;
        text-align: center; font-weight: bold; font-size: 14px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); border: 2px solid #EEE;
        height: 100%; display: flex; flex-direction: column; justify-content: center; align-items: center;
    }

    /* --- ② アクションリスト --- */
    .action-row {
        background: white; border-radius: 15px; padding: 15px;
        margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex; align-items: center; justify-content: space-between;
        border: 1px solid #E0E0E0;
    }
    .check-btn-done {
        background: #4CAF50; color: white; padding: 8px 15px;
        border-radius: 20px; font-weight: bold; font-size: 12px;
    }

    /* --- ③ ランキング --- */
    .rank-row {
        background: white; padding: 12px; border-radius: 12px;
        margin-bottom: 10px; display: flex; align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .medal { font-size: 24px; width: 40px; text-align: center; margin-right: 10px; }
    
    /* ボタン調整 */
    .stButton>button { border-radius: 20px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. データベース接続 & 状態管理
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

# セッション状態の初期化 (SPAのような画面遷移のため)
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
        <div style="display:flex; align-items:center; gap:10px;">
            <div style="font-size:30px;">🌏</div>
            <div class="app-logo">おかやまデコ活<br>チャレンジ2026</div>
        </div>
        <div class="user-info">
            <div>{role_icon} {name}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- ④ ログイン画面 (4つの入り口) ---
def screen_login_entry():
    st.markdown("<div style='text-align:center; margin: 40px 0;'><div style='font-size:60px'>🍑</div><h2 style='color:#2E7D32'>参加する入り口を選んでね！</h2></div>", unsafe_allow_html=True)
    
    # グリッドレイアウトを列で表現
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="login-card bg-student"><div class="icon-lg">👦</div><div>小学生は<br>こちら</div></div>', unsafe_allow_html=True)
        if st.button("小学生でスタート", key="btn_s"): set_login_role("student")
    with c2:
        st.markdown('<div class="login-card bg-family"><div class="icon-lg">👨‍👩‍👧</div><div>ご家族は<br>こちら</div></div>', unsafe_allow_html=True)
        if st.button("ご家族でスタート", key="btn_f"): set_login_role("family")
        
    st.write("") # スペース
    
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="login-card bg-jc"><div class="icon-lg">👔</div><div>JCメンバーは<br>こちら</div></div>', unsafe_allow_html=True)
        if st.button("JCメンバーでスタート", key="btn_j"): set_login_role("jc")
    with c4:
        st.markdown('<div class="login-card bg-teacher"><div class="icon-lg">🏫</div><div>先生は<br>こちら</div></div>', unsafe_allow_html=True)
        if st.button("先生でスタート", key="btn_t"): set_login_role("teacher")

def set_login_role(role):
    st.session_state.temp_role = role
    st.session_state.page = 'LOGIN_FORM'
    st.rerun()

# --- ログイン詳細入力 ---
def screen_login_form():
    role = st.session_state.temp_role
    st.markdown(f"<h3 style='text-align:center'>情報を入力してね ({role.upper()})</h3>", unsafe_allow_html=True)
    
    with st.form("login_details"):
        if role in ["student", "family"]:
            school = st.selectbox("小学校", ["倉敷第一小学校", "岡山中央小学校", "津山東小学校", "伊島小学校"])
            c1, c2, c3 = st.columns(3)
            grade = c1.selectbox("学年", ["1年", "2年", "3年", "4年", "5年", "6年"])
            u_class = c2.text_input("組", "1")
            number = c3.number_input("番号", 1, 50)
            name = st.text_input("ニックネーム", "ももたろう")
            
            if st.form_submit_button("ミッション開始！", type="primary"):
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
            if st.form_submit_button("LOM対抗戦に参加", type="primary"):
                st.session_state.user = {
                    "id": f"JC_{name}", "name": name, "role": "jc", "group": lom
                }
                st.session_state.page = 'HOME'
                st.rerun()

# --- ① ホーム画面 (ダッシュボード) ---
def screen_home():
    render_header()
    
    # デコ活の木 (視覚的インパクト)
    st.markdown("""
    <div class="tree-wrapper">
        <div style="font-size:150px; line-height:1; filter: drop-shadow(0 10px 10px rgba(0,0,0,0.1));">🌳</div>
        <div class="total-badge">みんなのCO2削減総量: 123,456 kg</div>
        <div style="position:absolute; top:50px; left:20px; font-size:40px;">🦌</div>
        <div style="position:absolute; top:80px; right:30px; font-size:30px;">🐿️</div>
    </div>
    """, unsafe_allow_html=True)
    
    # アクション記録ボタン (一番目立つ)
    if st.button("📝 きょうのアクションを記録する！", type="primary", use_container_width=True):
        st.session_state.page = 'ACTION'
        st.rerun()
        
    st.write("")
    
    # 3つのメニューボタン (画像配置準拠)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="menu-btn"><div style="font-size:24px">👑</div><div>クラス<br>ランク</div></div>', unsafe_allow_html=True)
        if st.button("みる", key="go_rank"): 
            st.session_state.page = 'RANKING'
            st.rerun()
    with c2:
        st.markdown('<div class="menu-btn"><div style="font-size:24px">🎮</div><div>分別<br>ゲーム</div></div>', unsafe_allow_html=True)
        if st.button("あそぶ", key="go_game"): 
            st.session_state.page = 'GAME'
            st.rerun()
    with c3:
        st.markdown('<div class="menu-btn"><div style="font-size:24px">🎓</div><div>環境<br>クイズ</div></div>', unsafe_allow_html=True)
        if st.button("とく", key="go_quiz"): st.toast("準備中だよ！")

# --- ② アクション記録画面 (チェックシート) ---
def screen_action():
    render_header()
    if st.button("🏠 ホームにもどる"): st.session_state.page = 'HOME'; st.rerun()
    
    st.markdown("### 📅 日付を選んでチェック！")
    # 画像のようなタブ切り替え
    dates = ["6/1(月)", "6/2(火)", "6/3(水)", "6/4(木)", "6/5(金)"]
    selected_day = st.radio(" ", dates, horizontal=True, label_visibility="collapsed")
    
    st.info(f"【{selected_day}】 できたことにチェックを入れよう！")
    
    # アクションリスト
    actions = [
        {"id": "elec", "icon": "💡", "text": "電気をこまめに消した", "pt": 50},
        {"id": "food", "icon": "🍽️", "text": "ご飯を残さず食べた", "pt": 100},
        {"id": "water", "icon": "💧", "text": "水を大切に使った", "pt": 30},
    ]
    
    # ゲーム連携: ゲームをプレイ済みならチェックが入る
    game_checked = st.session_state.game_done
    game_status_icon = "✅" if game_checked else "⬜"
    game_bg = "#E8F5E9" if game_checked else "white"
    
    # リスト描画
    for act in actions:
        c_icon, c_text, c_btn = st.columns([1, 4, 2])
        with c_icon: st.markdown(f"<div style='font-size:30px; text-align:center'>{act['icon']}</div>", unsafe_allow_html=True)
        with c_text: st.markdown(f"**{act['text']}**")
        with c_btn:
            if st.button("できた！", key=f"{selected_day}_{act['id']}"):
                st.toast(f"すごい！ +{act['pt']}ポイント Get!", icon="🎉")
                st.balloons()
                # ここでDB保存処理 (save_log)

    # ゲーム項目 (特別扱い)
    st.markdown("---")
    cg_icon, cg_text, cg_btn = st.columns([1, 4, 2])
    with cg_icon: st.markdown("<div style='font-size:30px; text-align:center'>🎮</div>", unsafe_allow_html=True)
    with cg_text: st.markdown(f"**分別ゲームで遊んだ**")
    with cg_btn:
        if game_checked:
            st.markdown("<div class='check-btn-done'>達成済！</div>", unsafe_allow_html=True)
        else:
            if st.button("ゲームへ"):
                st.session_state.page = 'GAME'
                st.rerun()

    # 6/5 スペシャル認定証
    if "6/5" in selected_day:
        st.markdown("---")
        st.success("🎓 全ミッション終了！アンケートに答えて認定証をもらおう！")
        if st.button("認定証をもらう"):
            st.balloons()
            st.image("https://placehold.co/600x400/FFF/D4AF37?text=Certificate", caption="おかやまエコヒーロー認定証")

# --- ③ ランキング画面 ---
def screen_ranking():
    render_header()
    if st.button("🏠 ホームにもどる"): st.session_state.page = 'HOME'; st.rerun()
    
    user_group = st.session_state.user['group']
    
    st.markdown(f"<h3 style='text-align:center'>🏆 {user_group}<br>現在の順位</h3>", unsafe_allow_html=True)
    
    # ダミーデータ
    ranks = [
        {"rank": 1, "name": "倉敷第一小 5年2組", "avg": 850, "medal": "🥇"},
        {"rank": 2, "name": "伊島小 6年1組", "avg": 820, "medal": "🥈"},
        {"rank": 3, "name": "津山東小 4年3組", "avg": 790, "medal": "🥉"},
    ]
    
    for r in ranks:
        bg_color = "#FFF8E1" if r['rank'] == 1 else "white"
        border = "2px solid #FFC107" if r['rank'] == 1 else "none"
        st.markdown(f"""
        <div class="rank-row" style="background:{bg_color}; border:{border}">
            <div class="medal">{r['medal']}</div>
            <div style="flex-grow:1">
                <div style="font-size:12px; font-weight:bold; color:#666">{r['rank']}位</div>
                <div style="font-size:16px; font-weight:900">{r['name']}</div>
            </div>
            <div style="text-align:right">
                <div style="font-size:10px">平均</div>
                <div style="color:#2E7D32; font-weight:bold">{r['avg']}g</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.info("あなたのクラスは現在 **1位** です！\nこの調子でがんばろう！")

# --- 🎮 分別ゲーム画面 ---
def screen_game():
    render_header()
    
    st.markdown("### ⏱️ 激闘！分別マスター")
    
    if 'game_status' not in st.session_state: st.session_state.game_status = 'READY'
    
    if st.session_state.game_status == 'READY':
        st.markdown("""
        <div style="background:white; padding:20px; border-radius:15px; text-align:center; border:2px solid #FF9800;">
            <p>10問タイムアタック！<br>間違えると <b>+5秒</b> ペナルティ！</p>
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
        st.markdown(f"<div style='font-size:40px; text-align:center; padding:30px; background:white; border-radius:20px; border:4px dashed #607D8B; margin:10px 0;'>{q['name']}</div>", unsafe_allow_html=True)
        
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
                st.session_state.game_done = True # アクション記録に反映
            st.rerun()

        if c1.button("🔥 燃える", use_container_width=True): ans(0)
        if c2.button("♻️ 資源", use_container_width=True): ans(1)
        if c3.button("🧱 埋立", use_container_width=True): ans(2)

    elif st.session_state.game_status == 'FINISHED':
        st.balloons()
        st.success(f"クリア！ タイム: {st.session_state.final_time}秒")
        if st.button("記録画面に戻る", type="primary"):
            st.session_state.page = 'ACTION'
            st.session_state.game_status = 'READY'
            st.rerun()
        if st.button("もう一度あそぶ"):
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
