import streamlit as st
import pandas as pd
import datetime
import time
import os
import base64
import random
from supabase import create_client, Client
import extra_streamlit_components as stx

# ==========================================
#  0. 全体設定
# ==========================================
st.set_page_config(
    page_title="おかやまデコ活チャレンジ2026",
    page_icon="🍑",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Supabase接続 (共通) ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Supabase接続エラー: secretsを確認してください。 {e}")
        return None

supabase = init_connection()

# --- Cookieマネージャー (自動ログイン用) ---
# 修正: @st.cache_resource を削除しました
def get_manager():
    return stx.CookieManager()

cookie_manager = get_manager()

# ==========================================
#  1. 共通関数 & 統計ダッシュボード
# ==========================================

# 音声再生用
def get_audio_html(filename, loop=False, volume=1.0, element_id=None):
    if not os.path.exists(filename): return ""
    try:
        with open(filename, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        mime_type = "audio/mpeg"
        if element_id is None: element_id = f"audio_{random.randint(0, 1000000)}"
        loop_attr = "loop" if loop else ""
        return f"""<div style="width:0; height:0; overflow:hidden;"><audio id="{element_id}" {loop_attr} autoplay><source src="data:{mime_type};base64,{b64}" type="audio/mp3"></audio></div>"""
    except:
        return ""

# 🌍 全体の成長ステージロジック（3万人目標版）
def get_global_stage(total_g):
    if total_g < 100000: return "🌱", "希望の芽生え", "まずは 100kg を目指そう！", "#E0F7FA", 100000
    elif total_g < 500000: return "🌳", "地域のシンボルツリー", "つぎは 500kg！大きな木に！", "#C8E6C9", 500000
    elif total_g < 2000000: return "🌲", "深まる緑の森", "目指せ 2トン！森を広げよう", "#81C784", 2000000
    elif total_g < 5000000: return "⛰️", "雄大なグリーンマウンテン", "つぎは 5トン！山を作ろう", "#4DB6AC", 5000000
    elif total_g < 10000000: return "🌏", "美しい地球", "奇跡の 10トンを目指して！", "#4FC3F7", 10000000
    else: return "🪐", "銀河一のエコ地域", "伝説達成！15トンまであと少し！", "#B39DDB", 15000000

def show_global_stage_visual(total_g):
    icon, title, msg, bg, next_val = get_global_stage(total_g)
    progress = 1.0 if next_val == 15000000 else min(total_g / next_val, 1.0)
    
    # 単位調整
    if total_g < 1000: disp_val = f"{total_g:,} g"
    elif total_g < 1000000: disp_val = f"{total_g/1000:.1f} kg"
    else: disp_val = f"{total_g/1000000:.2f} t"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {bg}, #ffffff); border: 4px solid {bg}; border-radius: 20px; padding: 20px; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <div style="font-size: 14px; font-weight:bold; color:#546E7A; margin-bottom:5px;">現在の オール岡山ステージ</div>
        <div style="font-size: 80px; animation: pulse 2s infinite; margin: 10px 0;">{icon}</div>
        <div style="font-size: 24px; font-weight: 900; color: #37474F;">{title}</div>
        <div style="font-size: 32px; font-weight: 900; color: #00897B; margin: 5px 0;">{disp_val} <span style="font-size:16px; color:#555;">削減中！</span></div>
        <div style="background:rgba(255,255,255,0.6); padding:5px 15px; border-radius:20px; display:inline-block; font-weight:bold; color:#455A64;">🚀 {msg}</div>
    </div>
    <style>@keyframes pulse {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.1); }} 100% {{ transform: scale(1); }} }}</style>
    """, unsafe_allow_html=True)
    st.progress(progress)

# ダッシュボード用データ取得 (10分キャッシュ)
@st.cache_data(ttl=600)
def fetch_dashboard_stats():
    if not supabase: return 0, 0, 0, pd.DataFrame()

    # 1. エコヒーロー数
    res_hero = supabase.table("logs_student").select("user_id, actions_str").execute()
    df_hero = pd.DataFrame(res_hero.data)
    hero_count = 0
    student_count = 0
    if not df_hero.empty:
        hero_count = df_hero[df_hero['actions_str'].astype(str).str.contains("環境の日アンケート", na=False)]['user_id'].nunique()
        student_count = df_hero['user_id'].nunique()

    # 2. 参加者総数 (学生+JC)
    res_mem = supabase.table("logs_member").select("user_name").execute()
    df_mem = pd.DataFrame(res_mem.data)
    member_count = df_mem['user_name'].nunique() if not df_mem.empty else 0
    total_participants = student_count + member_count

    # 3. CO2削減総量
    res_stu_pt = supabase.table("logs_student").select("action_points").execute()
    df_stu_pt = pd.DataFrame(res_stu_pt.data)
    stu_total = df_stu_pt['action_points'].sum() if not df_stu_pt.empty else 0
    
    res_mem_pt = supabase.table("logs_member").select("points").execute()
    df_mem_pt = pd.DataFrame(res_mem_pt.data)
    mem_total = df_mem_pt['points'].sum() if not df_mem_pt.empty else 0
    
    total_co2 = stu_total + mem_total

    # 4. ゲームランキング (Top 10)
    res_game = supabase.table("game_scores").select("*").order("time", desc=False).limit(10).execute()
    df_ranking = pd.DataFrame(res_game.data)

    return hero_count, total_participants, total_co2, df_ranking

# ダッシュボード表示
def show_global_dashboard():
    hero_cnt, part_cnt, co2_total, df_rank = fetch_dashboard_stats()

    # ビジュアル表示
    show_global_stage_visual(co2_total)

    st.markdown("### 📊 詳細データ")
    c1, c2, c3 = st.columns(3)
    c1.metric("👑 エコヒーロー", f"{hero_cnt:,} 人")
    c2.metric("🤝 全参加者数", f"{part_cnt:,} 人")
    c3.metric("📉 CO2削減総量", f"{co2_total:,} g")

    with st.expander("⏱️ 分別ゲーム 最速ランキング (Top 10)"):
        if not df_rank.empty:
            for i, row in df_rank.iterrows():
                icon = "🥇" if i==0 else "🥈" if i==1 else "🥉" if i==2 else f"{i+1}."
                st.markdown(f"**{icon} {row['time']}秒** : {row['name']} ({row['school']})")
        else:
            st.info("データがありません")

# ==========================================
#  2. 小学生用アプリ ロジック
# ==========================================

def student_app_main():
    # CSS
    st.markdown("""
    <style>
        .stButton>button { width: 100%; height: 70px; font-size: 20px !important; border-radius: 35px; font-weight: 900; background: linear-gradient(135deg, #FF9800 0%, #FF5722 100%); color: white; border: none; box-shadow: 0 4px 10px rgba(255,87,34,0.4); }
        .hero-card { background: linear-gradient(135deg, #FFD54F, #FFECB3); border: 4px solid #FFA000; border-radius: 20px; padding: 25px; text-align: center; margin-bottom: 25px; color: #5D4037; }
        .hero-name { font-size: 28px; font-weight: 900; border-bottom: 3px dashed #5D4037; display: inline-block; margin: 10px 0; }
        .login-guide { background-color: #FFEBEE; border: 2px solid #FFCDD2; border-radius: 15px; padding: 15px; margin-bottom: 20px; color: #B71C1C; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

    # 🌳 木の成長ロジック (1000g完結版)
    def get_tree_stage(total_points):
        if total_points == 0: return "🟤", "まだ 土の中...", 50, "#EFEBE9"
        elif total_points < 100: return "🌱", "芽がでた！", 100, "#E8F5E9"
        elif total_points < 300: return "🌿", "すこし 育ったよ", 300, "#C8E6C9"
        elif total_points < 600: return "🪴", "若木", 600, "#A5D6A7"
        elif total_points < 900: return "🌳", "立派な 木", 900, "#81C784"
        elif total_points < 1000: return "🍎", "実が なった！", 1000, "#FFF9C4"
        else: return "🌈", "伝説の 巨木！", 99999, "#B3E5FC"

    def show_my_tree(total_points):
        icon, status_text, next_goal, bg_color = get_tree_stage(total_points)
        progress = 1.0 if next_goal == 99999 else min(total_points / next_goal, 1.0)
        rest_msg = "コンプリート！！" if next_goal == 99999 else f"あと {next_goal - total_points} g で進化！"

        st.markdown(f"""
        <div style="background-color: {bg_color}; border: 4px solid #fff; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border-radius: 20px; padding: 20px; text-align: center; margin-bottom: 20px;">
            <div style="font-size: 100px; line-height: 1.2; animation: float 3s ease-in-out infinite;">{icon}</div>
            <div style="font-size: 24px; font-weight: 900; color: #2E7D32; margin-top: 10px;">{status_text}</div>
            <div style="font-size: 14px; color: #666;">(合計: {total_points} g)</div>
            <div style="margin-top: 10px; font-weight:bold; color:#555;">{rest_msg}</div>
        </div>
        <style>@keyframes float {{ 0% {{ transform: translateY(0px); }} 50% {{ transform: translateY(-10px); }} 100% {{ transform: translateY(0px); }} }}</style>
        """, unsafe_allow_html=True)
        st.progress(progress)

    # DB関数
    def fetch_student_data(user_id):
        if not supabase: return user_id, "", 0, {}
        try:
            res = supabase.table("logs_student").select("*").eq("user_id", user_id).execute()
            if not res.data: return user_id, "", 0, {}
            df = pd.DataFrame(res.data)
            total = df['action_points'].sum()
            nickname = df['nickname'].iloc[-1] if 'nickname' in df.columns else ""
            history = {}
            for _, row in df.iterrows():
                if row['target_date']: history[row['target_date']] = str(row['actions_str']).split(", ")
            return user_id, nickname, int(total), history
        except: return user_id, "", 0, {}

    def save_student_log(user_id, nickname, target_date, actions, points, memo, q1="", q2="", q3=""):
        if not supabase: return False
        try:
            school_name = user_id.split("_")[0]
            data = {
                "user_id": user_id, "nickname": nickname, "school_name": school_name,
                "target_date": target_date, "actions_str": ", ".join(actions),
                "action_points": points, "memo": memo, "q1": q1, "q2": q2, "q3": q3
            }
            supabase.table("logs_student").insert(data).execute()
            return True
        except Exception as e:
            return False

    # ゲームロジック
    def show_game():
        st.markdown("### ⏱️ 激闘！分別マスター")
        if 'game_state' not in st.session_state: st.session_state.game_state = 'READY'
        
        garbage_data = [
            {"name": "🍌 バナナの皮", "type": 0}, {"name": "🥤 ペットボトル", "type": 1}, 
            {"name": "📰 新聞紙", "type": 1}, {"name": "🍵 割れた茶碗", "type": 2},
            {"name": "🤧 ティッシュ", "type": 0}, {"name": "🥫 空き缶", "type": 1}
        ]
        cats = {0: "🔥 燃える", 1: "♻️ 資 源", 2: "🧱 埋 立"}

        if st.session_state.game_state == 'READY':
            if st.button("🏁 ゲームスタート！"):
                st.session_state.game_qs = random.sample(garbage_data, 5)
                st.session_state.g_idx = 0
                st.session_state.g_start = time.time()
                st.session_state.game_state = 'PLAYING'
                st.rerun()
        elif st.session_state.game_state == 'PLAYING':
            q_idx = st.session_state.g_idx
            if q_idx >= len(st.session_state.game_qs):
                final_time = round(time.time() - st.session_state.g_start, 2)
                u = st.session_state.student_user
                try:
                    supabase.table("game_scores").insert({
                        "name": u['name'], "school": u['school'], 
                        "time": final_time, "date": datetime.date.today().isoformat()
                    }).execute()
                except: pass
                st.session_state.last_time = final_time
                st.session_state.game_state = 'FINISHED'
                st.rerun()

            item = st.session_state.game_qs[q_idx]
            st.info(f"第{q_idx+1}問: {item['name']}")
            c1, c2, c3 = st.columns(3)
            def ans(c):
                # 簡易化のためペナルティなしで進行
                st.session_state.g_idx += 1
            with c1: 
                if st.button(cats[0], key=f"g{q_idx}0"): ans(0); st.rerun()
            with c2: 
                if st.button(cats[1], key=f"g{q_idx}1"): ans(1); st.rerun()
            with c3: 
                if st.button(cats[2], key=f"g{q_idx}2"): ans(2); st.rerun()

        elif st.session_state.game_state == 'FINISHED':
            st.balloons()
            st.success(f"クリア！ タイム: {st.session_state.last_time}秒")
            if st.button("もう一回"):
                st.session_state.game_state = 'READY'
                st.rerun()

    # --- 画面遷移管理 ---
    if 'student_user' not in st.session_state:
        # ログイン画面
        st.markdown("### 🏫 小学生 エコヒーロー登録")
        st.markdown("""<div class="login-guide">📌 <strong>学年・組・番号</strong> はいつも同じものを入れてね！</div>""", unsafe_allow_html=True)
        with st.form("student_login"):
            school = st.text_input("小学校名", placeholder="例：倉敷")
            c1, c2, c3 = st.columns(3)
            grade = c1.selectbox("学年", ["1年", "2年", "3年", "4年", "5年", "6年"])
            u_class = c2.text_input("組", placeholder="1, A")
            num = c3.number_input("出席番号", 1, 50)
            name = st.text_input("ニックネーム (ひらがな)")
            if st.form_submit_button("スタート！"):
                if school and u_class and name:
                    uid = f"{school}小学校_{grade}_{u_class}_{num}"
                    _, saved_name, total, hist = fetch_student_data(uid)
                    
                    # Cookie保存 (30日)
                    cookie_manager.set("decokatsu_user_id", uid, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                    
                    st.session_state.student_user = {
                        "id": uid, "name": saved_name if saved_name else name,
                        "school": f"{school}小学校", "total": total, "history": hist
                    }
                    st.rerun()
        if st.button("⬅️ TOPに戻る"):
            st.session_state.app_mode = 'select'
            st.rerun()
            
    else:
        # メイン画面
        user = st.session_state.student_user
        st.markdown(f"### 👋 こんにちは、{user['name']} さん！")
        
        # 認定証
        is_hero = any("環境の日アンケート" in acts for acts in user['history'].values())
        if is_hero:
            st.markdown(f"""<div class="hero-card"><div class="hero-name">🏆 認定エコヒーロー</div><br>{user['name']} 殿<br><small>2026.6.5 認定</small></div>""", unsafe_allow_html=True)

        # 木の成長表示
        show_my_tree(user['total'])

        st.divider()
        show_game()
        st.divider()

        # チェックシート
        st.markdown("### 📝 今日のチャレンジ")
        dates = ["6/1(月)", "6/2(火)", "6/3(水)", "6/4(木)"]
        actions = {
            "電気": {"label": "① 💡 電気をこまめに消した", "pt": 50},
            "食事": {"label": "② 🍚 ご飯を残さず食べた", "pt": 100},
            "水": {"label": "③ 🚰 水を大切に使った", "pt": 30},
            "分別": {"label": "④ ♻️ ゴミを分別した", "pt": 80},
            "家族": {"label": "⑤ 👨‍👩‍👧 家族も一緒にできた", "pt": 50}
        }
        
        df_data = {d: [False]*len(actions) for d in dates}
        for d in dates:
            if d in user['history']:
                for i, k in enumerate(actions.keys()):
                    if k in user['history'][d]: df_data[d][i] = True
        
        df = pd.DataFrame(df_data, index=[v['label'] for v in actions.values()])
        edited = st.data_editor(df, column_config={d: st.column_config.CheckboxColumn(d) for d in dates}, use_container_width=True)

        # ★ 保存ボタン (修正版)
        if st.button("✅ 記録を保存する", type="primary"):
            saved_cnt = 0
            new_pt = 0
            curr_hist = user['history'].copy()
            error_slot = st.empty()

            for d in dates:
                acts_to_save = []
                pt_day = 0
                for idx, (label, val) in enumerate(edited[d].items()):
                    if val:
                        key = list(actions.keys())[idx]
                        acts_to_save.append(key)
                        pt_day += actions[key]['pt']
                
                prev_acts = curr_hist.get(d, [])
                if set(acts_to_save) != set(prev_acts):
                    prev_pt = sum([actions[k]['pt'] for k in prev_acts if k in actions])
                    diff = pt_day - prev_pt
                    
                    if save_student_log(user['id'], user['name'], d, acts_to_save, diff, "一括"):
                        new_pt += diff
                        curr_hist[d] = acts_to_save
                        saved_cnt += 1
                    else:
                        error_slot.error(f"保存エラー: {d} (DB接続を確認してください)")
            
            if saved_cnt > 0:
                st.session_state.student_user['total'] += new_pt
                st.session_state.student_user['history'] = curr_hist
                st.balloons()
                st.success(f"保存しました！ ポイント変動: {new_pt}g")
                time.sleep(2)
                st.rerun()
            else:
                st.info("変更がありませんでした。")

        # 6/5, 6/6 特別ミッション
        with st.expander("🌿 6/5 環境の日・6/6 未来宣言"):
            st.info("6/5(金)になったらここに入力してね！")
            q1 = st.radio("チャレンジどうだった？", ["最高！", "普通", "まだまだ"], key="q1")
            memo = st.text_input("感想を一言", key="memo")
            if st.button("送信して認定証ゲット"):
                if save_student_log(user['id'], user['name'], "6/5(金)", ["環境の日アンケート"], 100, memo, q1=q1):
                    st.success("送信しました！")
                    st.session_state.student_user['history']["6/5(金)"] = ["環境の日アンケート"]
                    st.rerun()

        if st.button("ログアウト"):
            cookie_manager.delete("decokatsu_user_id")
            del st.session_state.student_user
            st.rerun()


# ==========================================
#  3. JCメンバー用アプリ ロジック
# ==========================================

def member_app_main():
    # CSS (ダークモード対策: 文字色指定)
    st.markdown("""
    <style>
        .stButton>button { width: 100%; height: 60px; font-weight: bold; border-radius: 10px; background-color: #0277BD; color: white; }
        .metric-box { border: 2px solid #0277BD; padding: 15px; border-radius: 10px; text-align: center; background-color: #E1F5FE; color: #333333; margin-bottom: 20px; }
        .lom-ranking { padding: 10px; background-color: #FAFAFA; color: #333333; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 5px; }
        .rank-1 { background-color: #FFF8E1; border: 2px solid #FFD54F; font-weight: bold; color: #E65100; }
    </style>
    """, unsafe_allow_html=True)

    ACTION_MASTER = {
        "てまえどり": {"point": 40, "label": "🏪 てまえどり (40g)"},
        "リフューズ": {"point": 30, "label": "🥡 カトラリー辞退 (30g)"},
        "待機電力": {"point": 20, "label": "🔌 待機電力カット (20g)"},
        "節水": {"point": 60, "label": "🚿 シャワー短縮 (60g)"},
        "完食": {"point": 50, "label": "🍽️ 完食・ロスゼロ (50g)"},
        "発信": {"point": 100, "label": "📱 エコの発信 (100g)"},
        "スマートムーブ": {"point": 80, "label": "🚶 スマートムーブ (80g)"}
    }
    LOM_LIST = ["岡山", "倉敷", "津山", "玉野", "児島", "笠岡", "美作", "新見", "備前", "高梁", "総社", "井原", "真庭", "勝央", "瀬戸内"]
    TARGET_DATES = ["6/1(月)", "6/2(火)", "6/3(水)", "6/4(木)", "6/5(金)"]

    def fetch_member_logs(user_name, lom_name):
        if not supabase: return pd.DataFrame()
        try:
            res = supabase.table("logs_member").select("*").eq("user_name", user_name).eq("lom_name", lom_name).execute()
            return pd.DataFrame(res.data)
        except: return pd.DataFrame()

    def fetch_lom_ranking():
        if not supabase: return pd.DataFrame()
        try:
            res = supabase.table("logs_member").select("lom_name, points").execute()
            df = pd.DataFrame(res.data)
            if df.empty: return pd.DataFrame()
            return df.groupby("lom_name")["points"].sum().sort_values(ascending=False).reset_index()
        except: return pd.DataFrame()

    def save_member_logs(user_name, lom_name, edited_df):
        if not supabase: return False
        insert_list = []
        label_to_key = {v["label"]: k for k, v in ACTION_MASTER.items()}
        
        for idx, row in edited_df.iterrows():
            key = label_to_key[row["アクション項目"]]
            pt = ACTION_MASTER[key]["point"]
            for date in TARGET_DATES:
                if row[date]:
                    insert_list.append({
                        "user_name": user_name, "lom_name": lom_name,
                        "target_date": date, "action_label": key,
                        "is_done": True, "points": pt
                    })
        try:
            supabase.table("logs_member").delete().eq("user_name", user_name).eq("lom_name", lom_name).in_("target_date", TARGET_DATES).execute()
            if insert_list: supabase.table("logs_member").insert(insert_list).execute()
            return True
        except: return False

    if "jc_user" not in st.session_state:
        st.title("👔 JCメンバー デコ活")
        st.info("所属LOMと氏名を入力してください")
        with st.form("jc_login"):
            lom = st.selectbox("所属LOM", LOM_LIST)
            name = st.text_input("氏名", placeholder="例：岡山 太郎")
            if st.form_submit_button("ログイン"):
                if name:
                    # Cookie保存 (30日) - JCは "LOM_Name" をキーにする
                    ckey = f"{lom}_{name}"
                    cookie_manager.set("decokatsu_user_id", ckey, expires_at=datetime.datetime.now() + datetime.timedelta(days=30))
                    
                    st.session_state.jc_user = {"lom": lom, "name": name}
                    st.rerun()
                else: st.warning("氏名を入力してください")
        if st.button("⬅️ TOPに戻る"):
            st.session_state.app_mode = 'select'
            st.rerun()
    else:
        user = st.session_state.jc_user
        st.markdown(f"**👤 {user['lom']}JC {user['name']} 君**")
        
        logs = fetch_member_logs(user['name'], user['lom'])
        total = logs['points'].sum() if not logs.empty else 0
        st.markdown(f"""<div class="metric-box"><div style="font-size:14px;">現在の獲得ポイント</div><div style="font-size:32px; font-weight:bold; color:#0277BD;">{total:,} <span style="font-size:16px;">g-CO2</span></div></div>""", unsafe_allow_html=True)

        st.subheader("📝 実践チェック")
        disp_items = [v["label"] for v in ACTION_MASTER.values()]
        df_data = {"アクション項目": disp_items}
        
        for d in TARGET_DATES:
            checks = []
            for item in disp_items:
                label_to_key = {v["label"]: k for k, v in ACTION_MASTER.items()}
                k = label_to_key[item]
                is_done = False
                if not logs.empty:
                    match = logs[(logs['target_date'] == d) & (logs['action_label'] == k)]
                    if not match.empty: is_done = True
                checks.append(is_done)
            df_data[d] = checks
        
        edited = st.data_editor(pd.DataFrame(df_data), column_config={d: st.column_config.CheckboxColumn(d, default=False) for d in TARGET_DATES}, use_container_width=True, hide_index=True)

        if st.button("記録を保存する", type="primary"):
            if save_member_logs(user['name'], user['lom'], edited):
                st.success("保存しました！")
                st.balloons()
                time.sleep(1)
                st.rerun()

        st.markdown("---")
        st.subheader("🏆 LOM対抗ランキング")
        ranks = fetch_lom_ranking()
        if not ranks.empty:
            my_rank_df = ranks[ranks['lom_name'] == user['lom']]
            if not my_rank_df.empty:
                st.info(f"{user['lom']}JCは 現在 **{my_rank_df.index[0]+1}位** です！")
            
            for i, r in ranks.head(5).iterrows():
                rk = i + 1
                cls = "rank-1" if rk==1 else ""
                st.markdown(f"""<div class="lom-ranking {cls}"><strong>{rk}位 {r['lom_name']}JC</strong> <span style="float:right; font-weight:bold; color:#0277BD;">{r['points']:,} pt</span></div>""", unsafe_allow_html=True)

        if st.button("ログアウト"):
            cookie_manager.delete("decokatsu_user_id")
            del st.session_state.jc_user
            st.rerun()

# ==========================================
#  4. メイン実行ブロック（入り口）
# ==========================================

def main_selector():
    # 1. Cookieによる自動ログインチェック
    cookie_user_id = cookie_manager.get(cookie="decokatsu_user_id")
    
    if 'student_user' not in st.session_state and 'jc_user' not in st.session_state:
        if cookie_user_id:
            if "小学校" in str(cookie_user_id):
                # 小学生自動ログイン
                try:
                    with st.spinner("おかえりなさい！自動ログイン中..."):
                        _, saved_name, total, hist = fetch_student_data(cookie_user_id)
                        sch = cookie_user_id.split("_")[0]
                        st.session_state.student_user = {"id": cookie_user_id, "name": saved_name, "school": sch, "total": total, "history": hist}
                        st.session_state.app_mode = 'student'
                        st.rerun()
                except: pass
            else:
                # JC自動ログイン
                try:
                    lom, name = str(cookie_user_id).split("_", 1)
                    st.session_state.jc_user = {"lom": lom, "name": name}
                    st.session_state.app_mode = 'member'
                    st.rerun()
                except: pass

    # 2. 通常のアプリ画面
    if 'app_mode' not in st.session_state:
        st.session_state.app_mode = 'select'

    if st.session_state.app_mode == 'select':
        st.markdown("""
        <div style="background:linear-gradient(rgba(0,0,0,0.3),rgba(0,0,0,0.3)), url('https://images.unsplash.com/photo-1501854140801-50d01698950b'); background-size:cover; padding:60px 20px; border-radius:20px; text-align:center; color:white; margin-bottom:30px;">
            <h1 style="text-shadow: 2px 2px 4px rgba(0,0,0,0.8);">🍑 おかやまデコ活チャレンジ</h1>
            <p style="font-weight:bold; background:rgba(255,152,0,0.9); display:inline-block; padding:5px 15px; border-radius:20px;">みんなの行動で未来を変えよう！</p>
        </div>
        """, unsafe_allow_html=True)

        # 全体ダッシュボード
        show_global_dashboard()
        
        st.markdown("---")
        st.markdown("### 👇 参加する方を選んでね")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎒 小学生のみんな\n(エコヒーロー)", type="primary"):
                st.session_state.app_mode = 'student'
                st.rerun()
        
        with col2:
            if st.button("👔 JCメンバー\n(LOM対抗戦)"):
                st.session_state.app_mode = 'member'
                st.rerun()

    elif st.session_state.app_mode == 'student':
        student_app_main()

    elif st.session_state.app_mode == 'member':
        member_app_main()

if __name__ == "__main__":
    main_selector()
