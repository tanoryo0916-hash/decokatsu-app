import streamlit as st
import pandas as pd
import datetime
import time
import random
import os
import base64
from supabase import create_client, Client

# ==========================================
# 1. 定数・設定
# ==========================================
# 参加率計算用の「全校児童数」定義 (デモ用)
SCHOOL_POPULATION = {
    "倉敷第一": 500,
    "岡山中央": 450,
    "津山東": 300,
    "伊島": 600
}

# ガイドブック画像設定
GUIDE_IMAGES = {
    "basic": ["basic_1.png", "basic_2.png"],
    "home": ["action_1.png", "action_2.png"],
    "living": ["action_3.png", "action_4.png", "action_5.png"],
    "move": ["action_6.png", "action_7.png"],
    "future": ["future_1.png", "future_2.png"]
}

# ==========================================
# 2. アプリ設定 & デザインCSS
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活チャレンジ2026",
    page_icon="🍑",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=M+PLUS+Rounded+1c:wght@400;800;900&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'M PLUS Rounded 1c', sans-serif;
        background-color: #F4FBF6;
        color: #37474F;
    }

    /* ヘッダー */
    .header-container {
        background: white; padding: 15px 20px; border-radius: 0 0 30px 30px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05); display: flex; justify-content: space-between; align-items: center;
        margin-bottom: 20px; border-bottom: 4px solid #C8E6C9;
    }
    .app-name { font-size: 20px; font-weight: 900; color: #2E7D32; line-height: 1.2; }
    .user-badge {
        background: #E8F5E9; color: #2E7D32; padding: 6px 15px;
        border-radius: 20px; font-size: 13px; font-weight: 800;
        display: flex; align-items: center; gap: 5px; border: 2px solid #C8E6C9;
    }

    /* ランキングカード */
    .rank-card {
        background: white; border-radius: 20px; padding: 15px 20px; margin-bottom: 15px;
        display: flex; align-items: center; box-shadow: 0 5px 15px rgba(0,0,0,0.05);
        border: 2px solid transparent; transition: transform 0.2s; position: relative;
    }
    .rank-1 { border-color: #FFD700; background: linear-gradient(to right, #FFFDE7, #FFF); }
    .rank-2 { border-color: #C0C0C0; }
    .rank-3 { border-color: #CD7F32; }
    
    .medal { 
        font-size: 32px; width: 50px; text-align: center; margin-right: 15px; 
        filter: drop-shadow(0 2px 2px rgba(0,0,0,0.2)); 
    }
    .rank-num {
        font-size: 20px; font-weight: 900; color: #555; width: 40px; text-align: center; margin-right: 10px;
    }
    .rank-score { text-align: right; margin-left: auto; }
    .score-val { color: #2E7D32; font-weight: 900; font-size: 20px; }
    .score-label { font-size: 10px; font-weight: bold; color: #777; display: block;}

    /* タブ */
    .stTabs [data-baseweb="tab-list"] { gap: 4px; overflow-x: auto; flex-wrap: nowrap; }
    .stTabs [data-baseweb="tab"] {
        height: 45px; white-space: nowrap; padding: 0 15px;
        background-color: #F1F8E9; border-radius: 15px 15px 0 0;
        font-weight: bold; font-size: 12px; border: none;
    }
    .stTabs [aria-selected="true"] { background-color: #fff; color: #2E7D32; border-top: 3px solid #2E7D32; }

    /* UI要素 */
    .big-action-btn button {
        background: linear-gradient(135deg, #FF6F00 0%, #FF8F00 100%) !important;
        color: white !important; height: 90px !important; border-radius: 30px !important;
        font-size: 24px !important; font-weight: 900 !important;
        box-shadow: 0 10px 0 #E65100, 0 20px 20px rgba(255, 111, 0, 0.3) !important;
        border: none !important; margin-bottom: 10px !important;
        transition: transform 0.1s, box-shadow 0.1s !important;
    }
    .big-action-btn button:active { transform: translateY(10px) !important; box-shadow: none !important; }

    .menu-btn button {
        background: white !important; color: #455A64 !important; height: 120px !important;
        border-radius: 25px !important; border: 2px solid #ECEFF1 !important;
        box-shadow: 0 6px 0 #CFD8DC, 0 10px 10px rgba(0,0,0,0.05) !important;
        font-weight: 800 !important; font-size: 16px !important;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        transition: transform 0.1s !important;
    }
    .menu-btn button:active { transform: translateY(6px) !important; box-shadow: none !important; }

    .login-btn button {
        height: 150px !important; border-radius: 30px !important; color: white !important;
        font-size: 18px !important; font-weight: 900 !important; border: none !important;
        box-shadow: 0 10px 20px rgba(0,0,0,0.15) !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2); transition: transform 0.2s !important;
    }
    .login-btn button:hover { transform: translateY(-5px) scale(1.02) !important; }
    
    .btn-green button { background: linear-gradient(135deg, #43A047, #66BB6A) !important; }
    .btn-blue button { background: linear-gradient(135deg, #1E88E5, #42A5F5) !important; }
    .btn-yellow button { background: linear-gradient(135deg, #FFB300, #FFCA28) !important; color: #5D4037 !important; text-shadow:none !important; }
    .btn-purple button { background: linear-gradient(135deg, #8E24AA, #AB47BC) !important; }

    .stRadio>div { background: white; padding: 15px; border-radius: 20px; box-shadow: inset 0 2px 5px rgba(0,0,0,0.05); gap: 10px; }
    div[data-baseweb="input"] { border-radius: 15px; border: 2px solid #E0E0E0; }
    div[data-baseweb="select"]>div { border-radius: 15px; border: 2px solid #E0E0E0; }
    
    /* 学校名の「小学校」ラベル */
    .school-suffix { 
        font-size: 18px; font-weight: bold; color: #555; 
        display: flex; align-items: center; height: 100%; padding-top: 25px; 
    }
    .act-desc { font-size: 12px; color: #607D8B; margin-top: 2px; line-height: 1.4; }
    
    /* 横スクロール */
    .scroll-container {
        display: flex; overflow-x: auto; gap: 15px; padding: 10px 5px 20px 5px;
        scrollbar-width: thin; scrollbar-color: #C8E6C9 transparent;
    }
    .scroll-item {
        height: 250px; width: auto; border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1); flex-shrink: 0; border: 2px solid #fff;
    }
    .guidebook-box { background: white; border-radius: 20px; padding: 20px; margin-bottom: 30px; border: 2px solid #E0F2F1; }
    .guide-title { font-size: 18px; font-weight: 900; color: #00695C; margin-bottom: 10px; display: flex; align-items: center; gap: 10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. データベース接続 & ロジック
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

# --- 画像処理 ---
def get_base64_image(image_path):
    if image_path.startswith("http"): return image_path
    if not os.path.exists(image_path): return None
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

def render_horizontal_gallery(image_list):
    html_content = '<div class="scroll-container">'
    for img_path in image_list:
        img_data = get_base64_image(img_path)
        if img_data:
            src = img_data if img_path.startswith("http") else f"data:image/png;base64,{img_data}"
            html_content += f'<img src="{src}" class="scroll-item" />'
        else:
            dummy = f"https://placehold.co/600x400/E0F2F1/00695C?text={os.path.basename(img_path)}"
            html_content += f'<img src="{dummy}" class="scroll-item" />'
    html_content += '</div>'
    st.markdown(html_content, unsafe_allow_html=True)

# --- DB操作 ---
def load_user_data(user_id):
    if not supabase: return {}
    try:
        response = supabase.table("decokatsu_logs").select("*").eq("user_id", user_id).execute()
        loaded_log = {}
        for row in response.data:
            loaded_log[row['date']] = row['actions']
        return loaded_log
    except: return {}

def sync_action_to_db(user_id, date, actions_list, total_points):
    if not supabase: return
    try:
        data = {
            "user_id": user_id, "date": date, "actions": actions_list, "points": total_points,
            "updated_at": datetime.datetime.now().isoformat()
        }
        supabase.table("decokatsu_logs").upsert(data).execute()
    except: pass

def save_game_score(user_data, score):
    if not supabase: return
    try:
        school_val = user_data.get('group', '').split(' ')[0] if 'group' in user_data else "ゲスト"
        data = {
            "user_id": user_data['id'],
            "nickname": user_data['name'],
            "school": school_val,
            "time": score
        }
        supabase.table("game_scores").insert(data).execute()
    except: pass

# --- ランキング集計 ---
@st.cache_data(ttl=60)
def fetch_all_rankings():
    if not supabase: return {}, {}, {}, []
    try:
        users_res = supabase.table("users").select("user_id, school, grade, class_name").execute()
        users_df = pd.DataFrame(users_res.data)
        logs_res = supabase.table("decokatsu_logs").select("user_id, points").execute()
        logs_df = pd.DataFrame(logs_res.data)
        
        if users_df.empty or logs_df.empty: return {}, {}, {}, []

        merged = pd.merge(logs_df, users_df, on="user_id", how="left")
        
        # 1. 学校別平均
        school_sum = merged.groupby("school")["points"].sum()
        school_count = merged.groupby("school")["user_id"].nunique()
        school_avg = (school_sum / school_count).sort_values(ascending=False).head(10)
        
        # 2. クラス別総量
        merged["class_full"] = merged["grade"] + " " + merged["class_name"] + "組"
        class_ranking = {}
        for school in users_df["school"].unique():
            if not school: continue
            school_data = merged[merged["school"] == school]
            class_sum = school_data.groupby("class_full")["points"].sum().sort_values(ascending=False).head(3)
            class_ranking[school] = class_sum

        # 3. 参加率
        participation_rate = {}
        for school, count in school_count.items():
            total = SCHOOL_POPULATION.get(school, 1000)
            participation_rate[school] = (count / total) * 100
        part_ranking = pd.Series(participation_rate).sort_values(ascending=False).head(10)

        # 4. ゲーム
        game_res = supabase.table("game_scores").select("*").order("time", desc=False).limit(10).execute()
        return school_avg, class_ranking, part_ranking, game_res.data

    except: return {}, {}, {}, []

# ==========================================
# 4. 認証・ステート管理
# ==========================================
def auth_user(user_id, input_nickname, role, school, grade, u_class):
    if not supabase: return True, "デモモード", {"id": user_id, "name": input_nickname, "role": role, "group": f"{school} {grade}-{u_class}"}
    try:
        res = supabase.table("users").select("*").eq("user_id", user_id).execute()
        if res.data:
            stored = res.data[0]['nickname']
            if stored.strip() == input_nickname.strip():
                return True, "ログイン成功！", {"id": user_id, "name": stored, "role": role, "group": f"{school} {grade}-{u_class}"}
            else:
                return False, f"ニックネームが違います (登録名: {stored})", None
        else:
            data = {"user_id": user_id, "nickname": input_nickname, "school": school, "grade": grade, "class_name": u_class}
            supabase.table("users").insert(data).execute()
            return True, "登録完了！", {"id": user_id, "name": input_nickname, "role": role, "group": f"{school} {grade}-{u_class}"}
    except: return False, "エラー", None

if 'page' not in st.session_state: st.session_state.page = 'LOGIN'
if 'user' not in st.session_state: st.session_state.user = None
if 'action_log' not in st.session_state: st.session_state.action_log = {} 
if 'game_done' not in st.session_state: st.session_state.game_done = False

def go_to(page_name):
    st.session_state.page = page_name
    st.rerun()

# ==========================================
# 5. 画面コンポーネント
# ==========================================
def render_header():
    user = st.session_state.user
    name = user['name'] if user else "ゲスト"
    role_label = {"student": "👦 児童", "family": "🏠 家族", "jc": "👔 JC", "teacher": "🏫 先生"}.get(user['role'], "") if user else ""
    st.markdown(f"""<div class="header-container"><div style="display:flex;align-items:center;gap:10px;"><div style="font-size:32px;">🌏</div><div class="app-name">おかやまデコ活<br>チャレンジ2026</div></div><div class="user-badge">{role_label} | {name}</div></div>""", unsafe_allow_html=True)

def view_login_entry():
    st.markdown("<div style='text-align:center; margin: 40px 0 30px;'><div style='font-size:80px;'>🍑</div><h2 style='color:#2E7D32; font-weight:900;'>参加する入り口を選んでね</h2></div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="login-btn btn-green">', unsafe_allow_html=True)
        if st.button("👦\n小学生", key="l_stu", use_container_width=True): st.session_state.temp_role = "student"; go_to('LOGIN_FORM')
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="login-btn btn-blue">', unsafe_allow_html=True)
        if st.button("🏠\nご家族", key="l_fam", use_container_width=True): st.session_state.temp_role = "family"; go_to('LOGIN_FORM')
        st.markdown('</div>', unsafe_allow_html=True)
    c3, c4 = st.columns(2)
    with c3:
        st.markdown('<div class="login-btn btn-yellow">', unsafe_allow_html=True)
        if st.button("👔\nJCメンバー", key="l_jc", use_container_width=True): st.session_state.temp_role = "jc"; go_to('LOGIN_FORM')
        st.markdown('</div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="login-btn btn-purple">', unsafe_allow_html=True)
        if st.button("🏫\n先生", key="l_tea", use_container_width=True): st.session_state.temp_role = "teacher"; go_to('LOGIN_FORM')
        st.markdown('</div>', unsafe_allow_html=True)

# --- ★修正: ログインフォーム（小学校固定表示＆記憶） ---
def view_login_form():
    role = st.session_state.temp_role
    st.markdown(f"<div style='text-align:center; margin-bottom:20px;'><h3 style='font-weight:900;'>情報を入力してね</h3><span style='background:#ECEFF1; padding:5px 15px; border-radius:15px; font-weight:bold;'>{role.upper()}</span></div>", unsafe_allow_html=True)
    with st.form("login"):
        if role in ["student", "family"]:
            st.info("※ 同じ「学校・組・番号」を使えるのは1人だけだよ！")
            
            # 前回の値を復元
            qp = st.query_params
            
            # --- ★学校名入力欄の工夫 ---
            col_s1, col_s2 = st.columns([3, 1])
            school = col_s1.text_input("小学校名", value=qp.get("sch", ""), placeholder="例：倉敷")
            col_s2.markdown('<div class="school-suffix">小学校</div>', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            grade = c1.text_input("学年", value=qp.get("grd", ""), placeholder="5")
            u_class = c2.text_input("組", value=qp.get("cls", ""), placeholder="1")
            num = c3.text_input("番号", value=qp.get("num", ""), placeholder="15")
            
            st.markdown("---")
            st.caption("📌 2回目からは同じニックネームを入れてね")
            name = st.text_input("ニックネーム", placeholder="ももたろう")
            
            if st.form_submit_button("🚀 スタート！", type="primary"):
                if not school or not grade or not u_class or not num or not name:
                    st.error("⚠️ 全部入力してね！")
                else:
                    user_id = f"{school}_{grade}_{u_class}_{num}"
                    is_ok, msg, u_data = auth_user(user_id, name, role, school, grade, u_class)
                    if is_ok:
                        st.session_state.user = u_data
                        st.session_state.action_log = load_user_data(user_id)
                        # ★記憶機能: パラメータ保存
                        st.query_params["sch"] = school
                        st.query_params["grd"] = grade
                        st.query_params["cls"] = u_class
                        st.query_params["num"] = num
                        st.toast(msg); time.sleep(1); go_to('HOME')
                    else: st.error(msg)
        else:
            org = st.selectbox("所属", ["岡山JC", "倉敷JC", "津山JC"])
            name = st.text_input("氏名")
            if st.form_submit_button("🔥 ログイン", type="primary"):
                user_id = f"{role}_{name}"
                st.session_state.user = {"id": user_id, "name": name, "role": role, "group": org}
                st.session_state.action_log = load_user_data(user_id)
                go_to('HOME')

def view_home():
    render_header()
    st.markdown('<div class="guidebook-box"><div class="guide-title"><span style="font-size:24px;">📚</span> デコ活ガイドブック</div><div style="font-size:12px; color:#555; margin-bottom:15px;">画像を見て勉強しよう！横にスクロールできるよ ➡️</div>', unsafe_allow_html=True)
    t1, t2, t3, t4, t5 = st.tabs(["🌱 基本", "🏠 おうち", "🍽️ くらし", "🚗 移動", "🌈 未来"])
    with t1: render_horizontal_gallery(GUIDE_IMAGES["basic"])
    with t2: render_horizontal_gallery(GUIDE_IMAGES["home"])
    with t3: render_horizontal_gallery(GUIDE_IMAGES["living"])
    with t4: render_horizontal_gallery(GUIDE_IMAGES["move"])
    with t5: render_horizontal_gallery(GUIDE_IMAGES["future"])
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; position:relative; margin-bottom:30px;"><div style="font-size:160px;">🌳</div><div style="background:white; border:4px solid #4CAF50; border-radius:50px; padding:12px 25px; display:inline-block; font-weight:900; color:#1B5E20; position:relative; top:-20px;">みんなの削減量: 123,456 kg</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="big-action-btn">', unsafe_allow_html=True)
    if st.button("📝 きょうの記録をつける！", use_container_width=True): go_to('ACTION')
    st.markdown('</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
        if st.button("👑\nランク", key="m_rank", use_container_width=True): go_to('RANKING')
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
        if st.button("🎮\nゲーム", key="m_game", use_container_width=True): go_to('GAME')
        st.markdown('</div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="menu-btn">', unsafe_allow_html=True)
        if st.button("🎓\nクイズ", key="m_quiz", use_container_width=True): st.toast("勉強してね！")
        st.markdown('</div>', unsafe_allow_html=True)

def view_action():
    render_header()
    if st.button("🏠 ホームに戻る"): go_to('HOME')
    st.markdown("<h3 style='text-align:center; font-weight:900; margin:20px 0;'>📅 日付を選んでね</h3>", unsafe_allow_html=True)
    days = ["6/1(月)", "6/2(火)", "6/3(水)", "6/4(木)", "6/5(金)"]
    selected = st.radio(" ", days, horizontal=True, label_visibility="collapsed")
    st.info(f"【{selected}】 できたこと全部にチェック！")
    acts = [
        {"id": "elec", "icon": "💡", "pt": 50, "title": "だれもいない へやの でんき をけした！", "desc": "例：トイレの電気をパチンと消した、見てないテレビを消した（CO2削減 -50g）"},
        {"id": "food", "icon": "🍚", "pt": 100, "title": "ごはんを のこさず たべた！", "desc": "例：給食をピカピカにした、苦手な野菜もがんばって食べた（CO2削減 -100g）"},
        {"id": "water", "icon": "🚰", "pt": 30, "title": "水（みず）を 大切（たいせつ）に つかった！", "desc": "例：歯みがきの間コップを使って水を止めた、顔を洗うとき出しっぱなしにしなかった（CO2削減 -30g）"},
        {"id": "sort", "icon": "♻️", "pt": 80, "title": "ゴミを 正（ただ）しく わけた！", "desc": "例：ペットボトルのラベルをはがして捨てた、紙や箱をリサイクルに回した（CO2削減 -80g）"},
        {"id": "family", "icon": "👨‍👩‍👧", "pt": 50, "title": "おうちの 人（ひと）も いっしょに できた！", "desc": "例：おうちの人も、電気・食事・水・ゴミのどれか１つでも気をつけてくれた！（家族ボーナス -50g）"}
    ]
    completed = st.session_state.action_log.get(selected, [])
    for act in acts:
        with st.container():
            c1, c2, c3 = st.columns([1, 4, 2])
            with c1: st.markdown(f"<div style='font-size:36px; text-align:center'>{act['icon']}</div>", unsafe_allow_html=True)
            with c2: 
                st.markdown(f"<div style='font-weight:bold;'>{act['title']}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='act-desc'>{act['desc']}</div>", unsafe_allow_html=True)
            with c3:
                st.write("")
                if act['id'] in completed: st.button("✅ 達成済", key=f"d_{selected}_{act['id']}", disabled=True, use_container_width=True)
                else:
                    if st.button(f"できた! (+{act['pt']})", key=f"b_{selected}_{act['id']}", use_container_width=True):
                        if selected not in st.session_state.action_log: st.session_state.action_log[selected] = []
                        st.session_state.action_log[selected].append(act['id'])
                        new_acts = st.session_state.action_log[selected]
                        sync_action_to_db(st.session_state.user['id'], selected, new_acts, len(new_acts)*50)
                        st.toast("ナイス！", icon="🎉"); st.rerun()
            st.markdown("---")
    st.markdown(f"**🎮 分別ゲーム**")
    if st.session_state.game_done: st.button("✅ 達成済み (+50pt)", disabled=True, use_container_width=True)
    else:
        if st.button("▶ ゲームに挑戦する", type="primary", use_container_width=True): go_to('GAME')
    if "6/5" in selected:
        st.markdown("---"); st.success("🎓 全ミッション終了！")
        if st.button("🏆 認定証", use_container_width=True): st.balloons(); st.image("https://placehold.co/600x400/FFF/D4AF37?text=CERTIFICATE")

# --- ★修正: ランキング画面（学校名に「小学校」を付与） ---
def view_ranking():
    render_header()
    if st.button("🏠 ホームに戻る"): go_to('HOME')
    st.markdown("<h3 style='text-align:center; font-weight:900;'>🏆 ランキング</h3>", unsafe_allow_html=True)
    school_avg, class_rank, part_rank, game_rank = fetch_all_rankings()
    t1, t2, t3, t4 = st.tabs(["🏫 学校(平均)", "🏢 クラス", "📈 参加率", "🎮 ゲーム"])
    
    # 学校名フォーマット関数
    def fmt_school(name):
        return f"{name}小学校" if "小学校" not in name else name

    with t1:
        st.caption("一人あたりのCO2削減量 (g)")
        if not school_avg.empty:
            for i, (school, score) in enumerate(school_avg.items()):
                rank = i + 1
                color = f"rank-{rank}" if rank <= 3 else ""
                st.markdown(f'<div class="rank-card {color}"><div class="rank-num">{rank}</div><div style="flex-grow:1;font-weight:bold;">{fmt_school(school)}</div><div class="rank-score"><span class="score-val">{int(score)}</span>g</div></div>', unsafe_allow_html=True)
        else: st.info("集計中...")
        
    with t2:
        my_school = st.session_state.user['group'].split(' ')[0]
        st.caption(f"{fmt_school(my_school)} のクラス対抗")
        if my_school in class_rank:
            for i, (cls, score) in enumerate(class_rank[my_school].items()):
                rank = i + 1
                color = f"rank-{rank}" if rank <= 3 else ""
                st.markdown(f'<div class="rank-card {color}"><div class="rank-num">{rank}</div><div style="flex-grow:1;font-weight:bold;">{cls}</div><div class="rank-score"><span class="score-val">{int(score)}</span>g</div></div>', unsafe_allow_html=True)
        else: st.info("データなし")

    with t3:
        st.caption("参加率ランキング")
        if not part_rank.empty:
            for i, (school, rate) in enumerate(part_rank.items()):
                rank = i + 1
                color = f"rank-{rank}" if rank <= 3 else ""
                st.markdown(f'<div class="rank-card {color}"><div class="rank-num">{rank}</div><div style="flex-grow:1;font-weight:bold;">{fmt_school(school)}</div><div class="rank-score"><span class="score-val">{rate:.1f}%</span></div></div>', unsafe_allow_html=True)

    with t4:
        st.caption("ゲームタイムランキング")
        if game_rank:
            for i, r in enumerate(game_rank):
                rank = i + 1
                color = f"rank-{rank}" if rank <= 3 else ""
                p_name = r.get('nickname', r.get('name', '名無し'))
                p_sch = r.get('school', '')
                st.markdown(f'<div class="rank-card {color}"><div class="rank-num">{rank}</div><div style="flex-grow:1;"><div style="font-weight:bold;">{p_name}</div><div style="font-size:10px;">{fmt_school(p_sch)}</div></div><div class="rank-score"><span class="score-val">{r.get("time",0)}</span>秒</div></div>', unsafe_allow_html=True)

def view_game():
    render_header()
    st.markdown("<h3 style='text-align:center; font-weight:900;'>⏱️ 分別マスター</h3>", unsafe_allow_html=True)
    if 'game_state' not in st.session_state: st.session_state.game_state = 'READY'
    
    if st.session_state.game_state == 'READY':
        st.markdown("<div style='background:white; padding:30px; border-radius:25px; text-align:center; border:4px solid #FF9800; margin-bottom:20px;'><div style='font-size:60px;'>🔥♻️</div><p style='font-weight:900;'>10問タイムアタック！<br>ミスすると <b style='color:#D32F2F;'>+5秒</b></p></div>", unsafe_allow_html=True)
        if st.button("🏁 スタート！", type="primary", use_container_width=True):
            st.session_state.q_list = random.sample([("🍌 皮", 0), ("🥤 ペット", 1), ("📦 箱", 1), ("🥢 箸", 0), ("💡 電球", 2), ("🥣 皿", 2)]*4, 10)
            st.session_state.q_idx = 0
            st.session_state.start_t = time.time()
            st.session_state.penalty = 0
            st.session_state.game_state = 'PLAYING'
            st.rerun()
            
    elif st.session_state.game_state == 'PLAYING':
        idx = st.session_state.q_idx
        q_name, q_type = st.session_state.q_list[idx]
        st.progress((idx)/10, text=f"第 {idx+1} 問")
        st.markdown(f"<div style='font-size:40px; text-align:center; font-weight:900; padding:40px; background:white; border-radius:20px; border:4px dashed #90A4AE; margin:20px 0;'>{q_name}</div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        def ans(t):
            if t == q_type: st.toast("⭕ せいかい！")
            else: st.toast("❌ +5秒", icon="🚨"); st.session_state.penalty += 5
            if idx + 1 < 10: st.session_state.q_idx += 1
            else:
                st.session_state.final_time = round(time.time() - st.session_state.start_t + st.session_state.penalty, 2)
                st.session_state.game_done = True
                st.session_state.game_state = 'FINISHED'
                save_game_score(st.session_state.user, st.session_state.final_time)
            st.rerun()
        st.markdown("<style>div.stButton button {height: 80px !important;}</style>", unsafe_allow_html=True)
        if c1.button("🔥 燃える", use_container_width=True): ans(0)
        if c2.button("♻️ 資源", use_container_width=True): ans(1)
        if c3.button("🧱 埋立", use_container_width=True): ans(2)

    elif st.session_state.game_state == 'FINISHED':
        st.balloons()
        st.markdown(f"<div style='background:white; padding:30px; border-radius:25px; text-align:center; border:4px solid #4CAF50;'><h2 style='color:#2E7D32;'>🎉 クリア！</h2><div style='font-size:60px; font-weight:900;'>{st.session_state.final_time}秒</div><p style='color:#D32F2F;'>(ペナルティ +{st.session_state.penalty}秒 込)</p></div>", unsafe_allow_html=True)
        st.write("")
        if st.button("📝 記録画面に戻る", type="primary", use_container_width=True): go_to('ACTION'); st.session_state.game_state = 'READY'

# ==========================================
# 7. ルーティング
# ==========================================
if __name__ == "__main__":
    p = st.session_state.page
    if p == 'LOGIN': view_login_entry()
    elif p == 'LOGIN_FORM': view_login_form()
    elif p == 'HOME': view_home()
    elif p == 'ACTION': view_action()
    elif p == 'RANKING': view_ranking()
    elif p == 'GAME': view_game()
