import streamlit as st

st.title("鍵の読み込みテスト")

# 秘密鍵があるかチェック
if "gcp_service_account" in st.secrets:
    st.success("✅ 成功！ [gcp_service_account] が見つかりました！")
    # 中身が空でないかチェック
    key_data = st.secrets["gcp_service_account"]
    st.write(f"Project ID: {key_data.get('project_id', '不明')}")
else:
    st.error("❌ 失敗... [gcp_service_account] が見つかりません。")
    
    st.write("---")
    st.write("いま読み込めている secrets の中身（キーのみ表示）:")
    st.write(list(st.secrets.keys()))
