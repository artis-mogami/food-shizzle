import streamlit as st
from PIL import Image, ImageEnhance
import io

st.set_page_config(page_title="Custom Food Editor", page_icon="🍳")

st.title("🍳 料理フォトエディター (高機能版)")
st.write("各項目は「1.0」が元の状態です。スライダーを下げるとマイナス補正になります。")

# --- 1. パラメータの初期値設定 ---
# 理想のAfter.jpgに近い推奨値を初期値にセット
DEFAULTS = {
    'sat': 2.2,
    'con': 1.4,
    'bri': 1.1,
    'sha': 3.0
}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- 2. リセット機能 ---
def reset_params():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value

# サイドバーに操作系をまとめる
st.sidebar.subheader("🛠 補正コントロール")
if st.sidebar.button("設定をリセット"):
    reset_params()

# --- 3. ファイルアップロード ---
uploaded_file = st.file_uploader("写真をアップロード...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 画像の読み込み（ポインタをリセットして読み込みミスを防ぐ）
    uploaded_file.seek(0)
    image_bytes = uploaded_file.read()
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    st.divider()
    
    # --- 4. 調整スライダー（マイナス調整対応） ---
    # 0.0 〜 1.0 がマイナス方向、1.0以上がプラス方向の調整になります
    col1, col2 = st.columns(2)
    with col1:
        sat_val = st.slider("色の鮮やかさ (彩度)", 0.0, 5.0, key="sat")
        con_val = st.slider("立体感 (コントラスト)", 0.0, 5.0, key="con")
    with col2:
        sha_val = st.slider("質感の強さ (シャープネス)", 0.0, 10.0, key="sha")
        bri_val = st.slider("明るさ調整", 0.0, 3.0, key="bri")

    # --- 5. 補正処理の実行 ---
    # 処理順序：彩度 -> コントラスト -> 明るさ -> シャープネス
    enhanced = ImageEnhance.Color(img).enhance(sat_val)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(con_val)
    enhanced = ImageEnhance.Brightness(enhanced).enhance(bri_val)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(sha_val)

    # プレビュー表示
    st.image(enhanced, caption="補正後のプレビュー", use_container_width=True)

    # --- 6. ダウンロード ---
    buf = io.BytesIO()
    # 最高画質を維持して保存
    enhanced.save(buf, format="JPEG", quality=100, subsampling=0)
    
    st.download_button(
        label="🚀 補正済み画像をフルサイズで保存",
        data=buf.getvalue(),
        file_name=f"fixed_{uploaded_file.name}",
        mime="image/jpeg",
        use_container_width=True
    )
    
    st.info("※1.0が元の写真の状態です。それより下げると効果が弱まります。")
