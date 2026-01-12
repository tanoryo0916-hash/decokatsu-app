import streamlit as st
import time
import random
import json
import os
import base64
import datetime

# --- ⚙️ ページ設定 ---
st.set_page_config(
    page_title="デコ活キッズ",
    page_icon="🌱",
    layout="centered"
)

# --- 📁 データ管理: ユーザー情報 ---
USER_DB_FILE = "users_db.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user(user_key, user_data):
    users = load_users()
    users[user_key] = user_data
    with open(USER_DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

# --- 📁 データ管理: ランキング情報 ---
RANKING_FILE = "ranking_log.json"

def load_logs():
    if os.path.exists(RANKING_FILE):
        try:
            with open(RANKING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_log(name, school, score_time):
    logs = load_logs()
    today_str = datetime.date.today().isoformat()
    new_record = {
        "name": name,
        "school": school,
        "time": score_time,
        "date": today_str
    }
    logs.append(new_record)
    with open(RANKING_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)

# --- 🎮 ゲーム関数: 激闘！分別マスター ---
def show_sorting_game():
    
    # 音声ファイル定義
    FILES = {
        "bgm": "bgm.mp3",
        "correct": "correct.mp3",
        "wrong": "wrong.mp3",
        "clear": "clear.mp3"
    }

    # 音声再生用HTML生成関数（音量強制固定版）
    def get_audio_html(filename, loop=False, volume=0.5, element_id=None):
        file_path = os.path.abspath(filename)
        if not os.path.exists(file_path): return ""

        try:
            with open(file_path, "rb") as f:
                data = f.read()
            b64 = base64.b64encode(data).decode()
        except: return ""

        if element_id is None:
            element_id = f"audio_{random.randint(0, 1000000)}"
            
        loop_attr = "loop" if loop else ""
        
        # onplay属性で再生開始時に強制的に音量を適用
        return f"""
            <div style="width:0; height:0; overflow:hidden;">
                <audio id="{element_id}" {loop_attr} autoplay onplay="this.volume={volume}">
                    <source src="data:audio/mpeg;base64,{b64}" type="audio/mp3">
                </audio>
                <script>
                    var audio = document.getElementById("{element_id}");
                    if(audio) {{
                        audio.volume = {volume};
                        audio.play().catch(e => console.log("Blocked"));
                    }}
                </script>
            </div>
        """

    # BGM停止用スクリプト
    def stop_bgm_script():
        return """
        <script>
            var bgm = document.getElementById("game_bgm");
            if (bgm) {
                bgm.pause();
                bgm.currentTime = 0;
            }
        </script>
        """

    # ランキング集計（自己ベストのみ抽出）
    def get_rankings(mode="all"):
        logs = load_logs()
        if not logs: return []
        today_str = datetime.date.today().isoformat()
        best_records = {} 
        for record in logs:
            if mode == "daily" and record["date"] != today_str: continue
            key = f"{record['school']}_{record['name']}"
            if key not in best_records:
                best_records[key] = record
            else:
                if record["time"] < best_records[key]["time"]:
                    best_records[key] = record
        ranking_list = list(best_records.values())
        ranking_list.sort(key=lambda x: x["time"])
        return ranking_list

    # ユーザー情報取得
    def get_user_info():
        info = st.session_state.get('user_info', {})
        return info.get('name', 'ゲスト'), info.get('school', '体験入学校')

    # 自己ベスト取得
    def get_personal_best():
        name, school = get_user_info()
        for r in get_rankings(mode="all"):
            if r['name'] == name and r['school'] == school: return r['time']
        return None

    # --- ゲーム画面デザインCSS ---
    st.markdown("""
    <style>
        .game-header { background-color:#FFF3E0; padding:15px; border-radius:15px; border:3px solid #FF9800; text-align:center; margin-bottom:10px; }
        .question-box { text-align:center; padding:20px; background-color:#FFFFFF; border-radius:15px; margin:20px 0; border:4px solid #607D8B; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-height: 120px; display: flex; align-items: center; justify-content: center; }
        .feedback-overlay { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 9999; padding: 30px; border-radius: 20px; text-align: center; width: 80%; max-width: 350px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); background-color: white; animation: popIn 0.2s ease-out; }
        @keyframes popIn { 0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0; } 100% { transform: translate(-50%, -50%) scale(1); opacity: 1; } }
        .personal-best { text-align: right; font-size: 14px; color: #555; background-color: #f0f2f6; padding: 5px 10px; border-radius: 5px; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

    # ゴミデータ定義
    garbage_data = [
        {"name": "🍌 バナナの皮", "type": 0}, {"name": "🤧 使ったティッシュ", "type": 0},
        {"name": "🥢 汚れた割り箸", "type": 0}, {"name": "🧸 古いぬいぐるみ", "type": 0},
        {"name": "🍂 落ち葉", "type": 0}, {"name": "👕 汚れたTシャツ", "type": 0},
        {"name": "🧾 レシート", "type": 0}, {"name": "🐟 魚の骨", "type": 0},
        {"name": "😷 使い捨てマスク", "type": 0}, {"name": "🥚 卵の殻", "type": 0},
        {"name": "🥤 ペットボトル", "type": 1}, {"name": "🥫 空き缶", "type": 1},
        {"name": "🍾 空き瓶", "type": 1}, {"name": "📰 新聞紙", "type": 1},
        {"name": "📦 ダンボール", "type": 1}, {"name": "🥛 牛乳パック(洗)", "type": 1},
        {"name": "📚 雑誌", "type": 1}, {"name": "📃 チラシ", "type": 1},
        {"name": "🍫 お菓子の箱", "type": 1}, {"name": "📓 ノート", "type": 1},
        {"name": "🍵 割れた茶碗", "type": 2}, {"name": "🥛 割れたコップ", "type": 2},
        {"name": "🧤 ゴム手袋", "type": 2}, {"name": "☂️ 壊れた傘", "type": 2},
        {"name": "🧊 保冷剤", "type": 2}, {"name": "📼 ビデオテープ", "type": 2},
        {"name": "💡 電球", "type": 2}, {"name": "💿 CD・DVD", "type": 2},
        {"name": "🪞 割れた鏡", "type": 2}, {"name": "🔋 乾電池", "type": 2},
    ]
    categories = {0: {"name": "🔥 燃える", "color": "primary"}, 1: {"name": "♻️ 資 源", "color": "primary"}, 2: {"name": "🧱 埋 立", "color": "secondary"}}

    # ステート管理
    if 'game_state' not in st.session_state: st.session_state.game_state = 'READY'
    if 'penalty_time' not in st.session_state: st.session_state.penalty_time = 0
    if 'feedback_mode' not in st.session_state: st.session_state.feedback_mode = False
    if 'feedback_result' not in st.session_state: st.session_state.feedback_result = None

    # --- ヘッダー表示 ---
    st.markdown("""<div class="game-header"><div style="font-size:22px; font-weight:bold; color:#E65100;">⏱️ 激闘！分別マスター</div><div style="font-size:14px; color:#333;">10問タイムアタック / <span style="color:red; font-weight:bold;">ミス ＋5秒</span></div></div>""", unsafe_allow_html=True)
    
    my_best = get_personal_best()
    best_str = f"{my_best} 秒" if my_best else "記録なし"
    st.markdown(f"""<div class="personal-best">👑 キミの歴代最速： <strong>{best_str}</strong></div>""", unsafe_allow_html=True)

    # --- ゲーム進行ロジック ---
    
    # ■ スタート画面
    if st.session_state.game_state == 'READY':
        col1, col2 = st.columns([2, 1])
        with col1: st.info("👇 **スタート** を押してゲーム開始！")
        with col2:
            if st.button("🏁 スタート！", use_container_width=True, type="primary"):
                st.session_state.current_questions = random.sample(garbage_data, 10)
                st.session_state.q_index = 0
                st.session_state.start_time = time.time()
                st.session_state.penalty_time = 0
                st.session_state.feedback_mode = False
                st.session_state.game_state = 'PLAYING'
                st.rerun()

        st.write("")
        tab1, tab2 = st.tabs(["📅 今日のランキング", "🏆 歴代ランキング"])
        with tab1:
            daily_ranks = get_rankings(mode="daily")
            if not daily_ranks: st.info("今日のチャレンジャーはまだいません。")
            else:
                for i, r in enumerate(daily_ranks[:10]): st.markdown(f"**{i+1}位**：`{r['time']}秒` ({r['name']} / {r['school']})")
        with tab2:
            all_ranks = get_rankings(mode="all")
            if not all_ranks: st.info("記録がありません。")
            else:
                for i, r in enumerate(all_ranks[:10]): st.markdown(f"**{i+1}位**：`{r['time']}秒` ({r['name']} / {r['school']})")

    # ■ プレイ画面
    elif st.session_state.game_state == 'PLAYING':
        # ★BGM再生：音量 0.02 (2%)★
        st.markdown(get_audio_html(FILES["bgm"], loop=True, volume=0.02, element_id="game_bgm"), unsafe_allow_html=True)

        q_idx = st.session_state.q_index
        total_q = len(st.session_state.current_questions)
        if q_idx >= total_q: st.session_state.game_state = 'FINISHED'; st.rerun()

        target_item = st.session_state.current_questions[q_idx]
        st.progress((q_idx / total_q), text=f"第 {q_idx + 1} 問 / 全 {total_q} 問")
        st.markdown(f"""<div class="question-box"><div style="font-size:32px; font-weight:bold; color:#333;">{target_item['name']}</div></div>""", unsafe_allow_html=True)
        st.caption("このゴミはどれ？ 👇")

        c1, c2, c3 = st.columns(3)
        def handle_answer(choice):
            correct = st.session_state.current_questions[q_idx]['type']
            if choice == correct: st.session_state.feedback_result = 'correct'
            else: st.session_state.feedback_result = 'wrong'; st.session_state.penalty_time += 5
            st.session_state.feedback_mode = True

        disable_btn = st.session_state.feedback_mode
        with c1:
            if st.button(categories[0]['name'], key=f"btn_{q_idx}_0", type=categories[0]['color'], use_container_width=True, disabled=disable_btn): handle_answer(0); st.rerun()
        with c2:
            if st.button(categories[1]['name'], key=f"btn_{q_idx}_1", type=categories[1]['color'], use_container_width=True, disabled=disable_btn): handle_answer(1); st.rerun()
        with c3:
            if st.button(categories[2]['name'], key=f"btn_{q_idx}_2", type=categories[2]['color'], use_container_width=True, disabled=disable_btn): handle_answer(2); st.rerun()

        # 判定表示
        if st.session_state.feedback_mode:
            # ★SE再生：音量 1.0 (最大)★
            if st.session_state.feedback_result == 'correct':
                st.markdown("""<div class="feedback-overlay" style="border:5px solid #4CAF50; background-color:#E8F5E9;"><h1 style="color:#2E7D32; font-size:80px; margin:0;">⭕️</h1><h2 style="color:#2E7D32; margin:0;">せいかい！</h2></div>""", unsafe_allow_html=True)
                st.markdown(get_audio_html(FILES["correct"], volume=1.0), unsafe_allow_html=True)
            else:
                st.markdown("""<div class="feedback-overlay" style="border:5px solid #D32F2F; background-color:#FFEBEE;"><h1 style="color:#D32F2F; font-size:80px; margin:0;">❌</h1><h2 style="color:#D32F2F; margin:0;">ちがうよ！</h2><p style="font-weight:bold; color:red; font-size:20px;">+5秒</p></div>""", unsafe_allow_html=True)
                st.markdown(get_audio_html(FILES["wrong"], volume=1.0), unsafe_allow_html=True)
            
            time.sleep(1)
            st.session_state.start_time += 1.0
            st.session_state.feedback_mode = False
            
            # 最終問題チェック & 自動保存
            if st.session_state.q_index + 1 >= len(st.session_state.current_questions):
                st.session_state.final_time = round(time.time() - st.session_state.start_time + st.session_state.penalty_time, 2)
                name, school = get_user_info()
                save_log(name, school, st.session_state.final_time)
                st.session_state.game_state = 'FINISHED'
            else: st.session_state.q_index += 1
            st.rerun()

    # ■ クリア画面
    elif st.session_state.game_state == 'FINISHED':
        # ★BGM停止 & クリア音再生★
        st.markdown(stop_bgm_script(), unsafe_allow_html=True)
        st.markdown(get_audio_html(FILES["clear"], volume=1.0), unsafe_allow_html=True)
        
        st.balloons()
        my_time = st.session_state.final_time
        name, school = get_user_info()
        st.markdown(f"""<div style="text-align:center; padding:20px; background-color:white; border-radius:15px; border:2px solid #eee;"><h2 style="color:#E91E63; margin:0;">🎉 ゲームクリア！</h2><div style="font-size:50px; font-weight:bold; color:#333; margin:10px 0;">{my_time} <span style="font-size:20px;">秒</span></div><div style="color:red; font-size:14px; margin-bottom:15px;">(ペナルティ +{st.session_state.penalty_time}秒 含む)</div><div style="background-color:#E3F2FD; padding:10px; border-radius:10px; color:#0D47A1; margin-bottom:10px;"><strong>{school}</strong> の <strong>{name}</strong> さん<br>記録を保存しました！💾</div></div>""", unsafe_allow_html=True)
        st.write("") 
        if st.button("もういちど遊ぶ", type="primary", use_container_width=True):
            st.session_state.game_state = 'READY'; st.rerun()

# --- 🚪 ログイン画面 ---
def login_screen():
    st.markdown("""
    <style>
        .login-container { background-color: #E3F2FD; padding: 30px; border-radius: 20px; border: 3px solid #90CAF9; text-align: center; }
        .title { color: #1565C0; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)
    st.markdown('<div class="login-container"><div class="title">🏫 デコ活アプリをはじめよう！</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        school_list = ["", "岡山中央小学校", "伊島小学校", "津島小学校", "鹿田小学校", "石井小学校", "その他"]
        school = st.selectbox("小学校はどこ？", school_list)
        if school == "その他": school = st.text_input("小学校の名前を入力してね")
    with col2:
        grade = st.selectbox("何年生？", ["1年生", "2年生", "3年生", "4年生", "5年生", "6年生"])

    name = st.text_input("ニックネーム（お名前）", placeholder="例：ももたろう")
    st.markdown("---")
    
    if st.button("🚀 スタート！", type="primary", use_container_width=True):
        if not school or not name:
            st.error("小学校名とニックネームを入れてね！")
        else:
            user_key = f"{school}_{grade}_{name}"
            users = load_users()
            
            if user_key in users:
                st.session_state.user_info = users[user_key]
                st.toast(f"おかえりなさい！ {name} さん", icon="👋")
            else:
                new_user_data = {"school": school, "grade": grade, "name": name, "registered_at": datetime.date.today().isoformat()}
                save_user(user_key, new_user_data)
                st.session_state.user_info = new_user_data
                st.toast(f"はじめまして！ {name} さん", icon="✨")
            
            st.session_state.logged_in = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- 🏠 メイン画面（ダッシュボード） ---
def main_screen():
    user = st.session_state.user_info
    
    # 挨拶エリア
    st.markdown(f"""
    <div style="padding:15px; background-color:#E8F5E9; border-radius:15px; border-left: 5px solid #4CAF50; margin-bottom:20px;">
        <h3 style="margin:0; color:#2E7D32;">こんにちは！ {user['name']} さん 🌱</h3>
        <p style="margin:0; color:#555;">今日も地球にいいこと、デコ活しよう！</p>
    </div>
    """, unsafe_allow_html=True)

    # ゲーム表示エリア
    show_sorting_game()
    
    st.markdown("---")

    # チャレンジチェック表（簡易版）
    st.subheader("📝 今日のチャレンジ・チェック")
    with st.expander("ここを押してチェックしてね", expanded=False):
        check1 = st.checkbox("給食（ごはん）を残さず食べた")
        check2 = st.checkbox("使っていない電気を消した")
        check3 = st.checkbox("ゴミを分別して捨てた")
        if st.button("ほぞんする"):
            st.success("よくがんばったね！ 記録したよ！")
            st.balloons()
            
    st.markdown("---")
    if st.button("ログアウト（おわるときにおしてね）"):
        st.session_state.logged_in = False
        st.rerun()

# --- 🚀 アプリ実行エントリーポイント ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_screen()
else:
    main_screen()
