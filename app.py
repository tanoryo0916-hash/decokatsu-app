import streamlit as st
import time
import random
import json
import os
import base64
import datetime

# ==========================================
# 1. 初期設定 & 定数定義
# ==========================================
st.set_page_config(
    page_title="デコ活キッズ",
    page_icon="🌱",
    layout="centered"
)

# ファイルパス設定
USER_DB_FILE = "users_db.json"
RANKING_FILE = "ranking_log.json"

# 音声ファイル定義（BGMは削除）
FILES = {
    "correct": "correct.mp3",
    "wrong": "wrong.mp3",
    "clear": "clear.mp3"
}

# ==========================================
# 2. データ管理関数（保存・読込）
# ==========================================
def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return [] if "ranking" in filepath else {}
    return [] if "ranking" in filepath else {}

def save_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ユーザー関連
def save_user(user_key, user_data):
    users = load_json(USER_DB_FILE)
    users[user_key] = user_data
    save_json(USER_DB_FILE, users)

def get_user_data(user_key):
    users = load_json(USER_DB_FILE)
    return users.get(user_key, {})

# ランキング関連
def save_log(name, school, score_time):
    logs = load_json(RANKING_FILE)
    today_str = datetime.date.today().isoformat()
    new_record = {
        "name": name,
        "school": school,
        "time": score_time,
        "date": today_str
    }
    logs.append(new_record)
    save_json(RANKING_FILE, logs)

def get_rankings(mode="all"):
    logs = load_json(RANKING_FILE)
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

# ==========================================
# 3. 音声・UI ヘルパー関数
# ==========================================
def get_audio_html(filename, loop=False, volume=0.5, element_id=None):
    file_path = os.path.abspath(filename)
    if not os.path.exists(file_path): return ""
    try:
        with open(file_path, "rb") as f: data = f.read()
        b64 = base64.b64encode(data).decode()
    except: return ""

    if element_id is None: element_id = f"audio_{random.randint(0, 1000000)}"
    loop_attr = "loop" if loop else ""
    
    # SE(効果音)用：音量は引数で指定
    return f"""
        <div style="width:0; height:0; overflow:hidden;">
            <audio id="{element_id}" {loop_attr} autoplay onplay="this.volume={volume}">
                <source src="data:audio/mpeg;base64,{b64}" type="audio/mp3">
            </audio>
        </div>
    """

# ==========================================
# 4. ゲーム機能本体 (Game)
# ==========================================
def show_sorting_game():
    st.markdown("""<style>.game-header { background-color:#FFF3E0; padding:15px; border-radius:15px; border:3px solid #FF9800; text-align:center; margin-bottom:10px; } .question-box { text-align:center; padding:20px; background-color:#FFFFFF; border-radius:15px; margin:20px 0; border:4px solid #607D8B; box-shadow: 0 4px 6px rgba(0,0,0,0.1); min-height: 120px; display: flex; align-items: center; justify-content: center; } .feedback-overlay { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); z-index: 9999; padding: 30px; border-radius: 20px; text-align: center; width: 80%; max-width: 350px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); background-color: white; animation: popIn 0.2s ease-out; } @keyframes popIn { 0% { transform: translate(-50%, -50%) scale(0.5); opacity: 0; } 100% { transform: translate(-50%, -50%) scale(1); opacity: 1; } } .personal-best { text-align: right; font-size: 14px; color: #555; background-color: #f0f2f6; padding: 5px 10px; border-radius: 5px; margin-top: 5px; }</style>""", unsafe_allow_html=True)

    if 'game_state' not in st.session_state: st.session_state.game_state = 'READY'
    if 'penalty_time' not in st.session_state: st.session_state.penalty_time = 0
    if 'feedback_mode' not in st.session_state: st.session_state.feedback_mode = False
    
    garbage_data = [
        {"name": "🍌 バナナの皮", "type": 0}, {"name": "🤧 使ったティッシュ", "type": 0}, {"name": "🥢 汚れた割り箸", "type": 0},
        {"name": "🧸 古いぬいぐるみ", "type": 0}, {"name": "🍂 落ち葉", "type": 0}, {"name": "👕 汚れたTシャツ", "type": 0},
        {"name": "🧾 レシート", "type": 0}, {"name": "🐟 魚の骨", "type": 0}, {"name": "😷 使い捨てマスク", "type": 0}, {"name": "🥚 卵の殻", "type": 0},
        {"name": "🥤 ペットボトル", "type": 1}, {"name": "🥫 空き缶", "type": 1}, {"name": "🍾 空き瓶", "type": 1},
        {"name": "📰 新聞紙", "type": 1}, {"name": "📦 ダンボール", "type": 1}, {"name": "🥛 牛乳パック(洗)", "type": 1},
        {"name": "📚 雑誌", "type": 1}, {"name": "📃 チラシ", "type": 1}, {"name": "🍫 お菓子の箱", "type": 1}, {"name": "📓 ノート", "type": 1},
        {"name": "🍵 割れた茶碗", "type": 2}, {"name": "🥛 割れたコップ", "type": 2}, {"name": "🧤 ゴム手袋", "type": 2},
        {"name": "☂️ 壊れた傘", "type": 2}, {"name": "🧊 保冷剤", "type": 2}, {"name": "📼 ビデオテープ", "type": 2},
        {"name": "💡 電球", "type": 2}, {"name": "💿 CD・DVD", "type": 2}, {"name": "🪞 割れた鏡", "type": 2}, {"name": "🔋 乾電池", "type": 2},
    ]
    categories = {0: {"name": "🔥 燃える", "color": "primary"}, 1: {"name": "♻️ 資 源", "color": "primary"}, 2: {"name": "🧱 埋 立", "color": "secondary"}}

    def get_user_info():
        info = st.session_state.get('user_info', {})
        return info.get('name', 'ゲスト'), info.get('school', '体験入学校')
    
    def get_personal_best():
        name, school = get_user_info()
        for r in get_rankings(mode="all"):
            if r['name'] == name and r['school'] == school: return r['time']
        return None

    st.markdown("""<div class="game-header"><div style="font-size:22px; font-weight:bold; color:#E65100;">⏱️ 激闘！分別マスター</div><div style="font-size:14px; color:#333;">10問タイムアタック / <span style="color:red; font-weight:bold;">ミス ＋5秒</span></div></div>""", unsafe_allow_html=True)
    
    if st.session_state.game_state != 'FINISHED':
        best_str = f"{get_personal_best()} 秒" if get_personal_best() else "記録なし"
        st.markdown(f"""<div class="personal-best">👑 キミの歴代最速： <strong>{best_str}</strong></div>""", unsafe_allow_html=True)

    if st.session_state.game_state == 'READY':
        col1, col2 = st.columns([2, 1])
        with col1: st.info("👇 **スタート** を押してゲーム開始！")
        with col2:
            if st.button("🏁 スタート！", use_container_width=True, type="primary"):
                st.session_state.current_questions = random.sample(garbage_data, 10)
                st.session_state.q_index = 0
                st.session_state.penalty_time = 0
                st.session_state.feedback_mode = False
                st.session_state.start_time = time.time()
                st.session_state.game_state = 'PLAYING'
                st.rerun()
        st.write("")
        tab1, tab2 = st.tabs(["📅 今日のランキング", "🏆 歴代ランキング"])
        with tab1:
            dr = get_rankings(mode="daily")
            if not dr: st.info("今日のチャレンジャーはまだいません。")
            else:
                for i, r in enumerate(dr[:10]): st.markdown(f"**{i+1}位**：`{r['time']}秒` ({r['name']} / {r['school']})")
        with tab2:
            ar = get_rankings(mode="all")
            if not ar: st.info("記録がありません。")
            else:
                for i, r in enumerate(ar[:10]): st.markdown(f"**{i+1}位**：`{r['time']}秒` ({r['name']} / {r['school']})")

    elif st.session_state.game_state == 'PLAYING':
        # BGM再生コード削除済み
        if st.session_state.q_index >= len(st.session_state.current_questions): st.session_state.game_state = 'FINISHED'; st.rerun()

        q_idx = st.session_state.q_index
        item = st.session_state.current_questions[q_idx]
        st.progress((q_idx / 10), text=f"第 {q_idx + 1} 問 / 全 10 問")
        st.markdown(f"""<div class="question-box"><div style="font-size:32px; font-weight:bold; color:#333;">{item['name']}</div></div>""", unsafe_allow_html=True)
        st.caption("このゴミはどれ？ 👇")

        c1, c2, c3 = st.columns(3)
        def handle_answer(choice):
            correct = st.session_state.current_questions[q_idx]['type']
            st.session_state.feedback_result = 'correct' if choice == correct else 'wrong'
            if choice != correct: st.session_state.penalty_time += 5
            st.session_state.feedback_mode = True

        disabled = st.session_state.feedback_mode
        with c1: 
            if st.button(categories[0]['name'], key=f"b0_{q_idx}", type=categories[0]['color'], use_container_width=True, disabled=disabled): handle_answer(0); st.rerun()
        with c2: 
            if st.button(categories[1]['name'], key=f"b1_{q_idx}", type=categories[1]['color'], use_container_width=True, disabled=disabled): handle_answer(1); st.rerun()
        with c3: 
            if st.button(categories[2]['name'], key=f"b2_{q_idx}", type=categories[2]['color'], use_container_width=True, disabled=disabled): handle_answer(2); st.rerun()

        if st.session_state.feedback_mode:
            res = st.session_state.feedback_result
            if res == 'correct':
                st.markdown("""<div class="feedback-overlay" style="border:5px solid #4CAF50; background-color:#E8F5E9;"><h1 style="color:#2E7D32; font-size:80px; margin:0;">⭕️</h1><h2 style="color:#2E7D32; margin:0;">せいかい！</h2></div>""", unsafe_allow_html=True)
                st.markdown(get_audio_html(FILES["correct"], volume=1.0), unsafe_allow_html=True)
            else:
                st.markdown("""<div class="feedback-overlay" style="border:5px solid #D32F2F; background-color:#FFEBEE;"><h1 style="color:#D32F2F; font-size:80px; margin:0;">❌</h1><h2 style="color:#D32F2F; margin:0;">ちがうよ！</h2><p style="font-weight:bold; color:red; font-size:20px;">+5秒</p></div>""", unsafe_allow_html=True)
                st.markdown(get_audio_html(FILES["wrong"], volume=1.0), unsafe_allow_html=True)
            time.sleep(1)
            st.session_state.start_time += 1.0
            st.session_state.feedback_mode = False
            if st.session_state.q_index + 1 >= 10:
                st.session_state.final_time = round(time.time() - st.session_state.start_time + st.session_state.penalty_time, 2)
                name, school = get_user_info()
                save_log(name, school, st.session_state.final_time)
                st.session_state.game_state = 'FINISHED'
            else:
                st.session_state.q_index += 1
            st.rerun()

    elif st.session_state.game_state == 'FINISHED':
        st.markdown(get_audio_html(FILES["clear"], volume=1.0), unsafe_allow_html=True)
        st.balloons()
        my_time = st.session_state.final_time
        name, school = get_user_info()
        st.markdown(f"""<div style="text-align:center; padding:20px; background-color:white; border-radius:15px; border:2px solid #eee;"><h2 style="color:#E91E63; margin:0;">🎉 ゲームクリア！</h2><div style="font-size:50px; font-weight:bold; color:#333; margin:10px 0;">{my_time} <span style="font-size:20px;">秒</span></div><div style="color:red; font-size:14px; margin-bottom:15px;">(ペナルティ +{st.session_state.penalty_time}秒 含む)</div><div style="background-color:#E3F2FD; padding:10px; border-radius:10px; color:#0D47A1; margin-bottom:10px;"><strong>{school}</strong> の <strong>{name}</strong> さん<br>記録を保存しました！💾</div></div>""", unsafe_allow_html=True)
        st.write("") 
        if st.button("もういちど遊ぶ", type="primary", use_container_width=True):
            st.session_state.game_state = 'READY'; st.rerun()

# ==========================================
# 5. デコ活チャレンジ機能 (Challenges)
# ==========================================
def show_challenge_sheet():
    st.markdown("""<div style="background-color:#E1F5FE; padding:15px; border-radius:10px; border-left:5px solid #03A9F4; margin-top:20px;"><h3 style="color:#0277BD; margin:0;">📝 デコ活チャレンジ！</h3><p style="margin:0; font-size:14px;">きょう、できたことにチェックをいれよう！</p></div>""", unsafe_allow_html=True)

    challenges = {
        "🥦 食べる (食品ロス)": ["給食やご飯を残さず食べた", "野菜をたくさん食べた", "賞味期限が近いものから食べた"],
        "💡 住む (省エネ・節水)": ["見ていないテレビを消した", "部屋を出るとき電気を消した", "水を出しっぱなしにしなかった"],
        "🎁 買う・捨てる (3R)": ["マイバッグを持って買い物に行った", "ゴミを正しく分別して捨てた", "壊れたものを直して使った"],
        "🚗 移動など (その他)": ["近くなら歩いて行った", "外で元気に遊んだ", "家族とエコの話をした"]
    }

    user_info = st.session_state.user_info
    user_key = f"{user_info['school']}_{user_info['grade']}_{user_info['name']}"
    today_str = datetime.date.today().isoformat()
    saved_data = get_user_data(user_key)
    history = saved_data.get("challenge_history", {})
    today_checks = history.get(today_str, [])

    with st.form("challenge_form"):
        new_checks = []
        for category, items in challenges.items():
            st.markdown(f"**{category}**")
            for item in items:
                is_checked = item in today_checks
                if st.checkbox(item, value=is_checked): new_checks.append(item)
            st.write("")
        
        submitted = st.form_submit_button("✅ チェックを保存する", type="primary", use_container_width=True)
        if submitted:
            history[today_str] = new_checks
            saved_data["challenge_history"] = history
            save_user(user_key, saved_data)
            count = len(new_checks)
            if count == 0: st.warning("チェックが入っていないよ？")
            elif count < 5: st.success(f"保存しました！ {count}個達成！明日もがんばろう！")
            else: st.success(f"すごい！！ {count}個も達成！デコ活マスターだね！🎉"); st.balloons()

# ==========================================
# 6. ログイン & メイン画面制御 (自動ログイン対応)
# ==========================================
def login_screen():
    st.markdown("""<style>.login-container { background-color: #E3F2FD; padding: 30px; border-radius: 20px; border: 3px solid #90CAF9; text-align: center; } .title { color: #1565C0; font-size: 24px; font-weight: bold; margin-bottom: 20px; }</style>""", unsafe_allow_html=True)
    st.markdown('<div class="login-container"><div class="title">🏫 デコ活アプリをはじめよう！</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        # 小学校名は自由入力に変更
        school = st.text_input("小学校のなまえ", placeholder="例：〇〇小学校")
    with col2:
        grade = st.selectbox("何年生？", ["1年生", "2年生", "3年生", "4年生", "5年生", "6年生"])

    name = st.text_input("ニックネーム（お名前）", placeholder="例：ももたろう")
    st.markdown("---")
    
    if st.button("🚀 スタート！", type="primary", use_container_width=True):
        if not school or not name:
            st.error("小学校名とニックネームを入れてね！")
        else:
            user_key = f"{school}_{grade}_{name}"
            users = load_json(USER_DB_FILE)
            
            # データ保存・更新
            if user_key in users:
                user_data = users[user_key]
                st.toast(f"おかえりなさい！ {name} さん", icon="👋")
            else:
                user_data = {"school": school, "grade": grade, "name": name, "registered_at": datetime.date.today().isoformat(), "challenge_history": {}}
                save_user(user_key, user_data)
                st.toast(f"はじめまして！ {name} さん", icon="✨")
            
            # セッションとURLパラメータに保存
            st.session_state.user_info = user_data
            st.session_state.logged_in = True
            
            # URLパラメータを設定（自動ログイン用）
            st.query_params["uid"] = user_key
            st.rerun()
            
    st.markdown('</div>', unsafe_allow_html=True)

def main_screen():
    user = st.session_state.user_info
    
    st.markdown(f"""
    <div style="padding:15px; background-color:#E8F5E9; border-radius:15px; border-left: 5px solid #4CAF50; margin-bottom:20px;">
        <h3 style="margin:0; color:#2E7D32;">こんにちは！ {user['name']} さん 🌱</h3>
        <p style="margin:0; color:#555;">今日も地球にいいこと、デコ活しよう！</p>
    </div>
    """, unsafe_allow_html=True)

    # 次回の自動ログイン案内
    with st.expander("ℹ️ 次から自動でログインするには？"):
        st.info("このページを **「ブックマーク（お気に入り）」** に登録してね！\n次にそのブックマークから開くと、名前を入れなくてもログインできるよ！")

    show_sorting_game()
    st.markdown("---")
    show_challenge_sheet()
    st.markdown("---")
    if st.button("ログアウト（おわるときにおしてね）"):
        st.session_state.logged_in = False
        st.session_state.game_state = 'READY'
        st.query_params.clear() # URLパラメータも消去
        st.rerun()

# ==========================================
# 7. アプリ実行エントリーポイント
# ==========================================
# 自動ログインチェック
if not st.session_state.get('logged_in', False):
    # URLパラメータに 'uid' があるか確認
    params = st.query_params
    if "uid" in params:
        user_key = params["uid"]
        saved_users = load_json(USER_DB_FILE)
        
        # 登録済みユーザーなら自動ログイン
        if user_key in saved_users:
            st.session_state.user_info = saved_users[user_key]
            st.session_state.logged_in = True
            st.toast(f"自動ログインしました！ こんにちは {saved_users[user_key]['name']} さん！", icon="🚀")
            # 念のためrerunして画面更新
            # (ただし無限ループ防止のため、session stateにフラグが立っていればスキップしたいが、Streamlitの仕様上rerunが無難)
            # ここでは描画フローに任せる

if not st.session_state.get('logged_in', False):
    login_screen()
else:
    main_screen()
