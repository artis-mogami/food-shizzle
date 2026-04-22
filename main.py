import streamlit as st
from PIL import Image, ImageEnhance
import io
import gc

st.set_page_config(page_title="Stable Food Editor", page_icon="🍳")

st.title("🍳 料理フォトエディター (安定反映版)")
st.write("各項目 **1.0が元の状態** です。1.0より下げると効果が弱まり（マイナス）、上げると強まります。")

# --- 1. パラメータの初期値管理 ---
# After.jpgに近い推奨値を初期値として設定
DEFAULTS = {
    'sat_val': 2.2,
    'con_val': 1.4,
    'bri_val': 1.1,
    'sha_val': 3.0
}

# セッション状態に値を登録（初回のみ）
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# リセットボタンの処理
def reset_action():
    for key, val in DEFAULTS.items():
        st.session_state[key] = val

st.sidebar.subheader("🛠 補正コントロール")
st.sidebar.button("設定をリセット", on_click=reset_action)

# --- 2. ファイルアップロード ---
uploaded_file = st.file_uploader("写真をアップロード...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 画像の読み込み（一度だけ読み込み、メモリを節約）
    # seek(0)でポインタのズレによる読み込み失敗（画像が消える現象）を防ぐ
    uploaded_file.seek(0)
    raw_img = Image.open(uploaded_file).convert("RGB")
    
    st.divider()
    
    # --- 3. 調整スライダー ---
    # 0.0 〜 1.0 に設定すれば、元画像より効果を弱める（マイナス調整）が可能です
    col1, col2 = st.columns(2)
    with col1:
        # st.session_state[key] と連結することで、スライダーの動きを確実に反映
        sat = st.slider("色彩の鮮やかさ (彩度)", 0.0, 5.0, key="sat_val")
        con = st.slider("立体感 (コントラスト)", 0.0, 5.0, key="con_val")
    with col2:
        sha = st.slider("質感の強さ (シャープネス)", 0.0, 10.0, key="sha_val")
        bri = st.slider("明るさ調整", 0.0, 3.0, key="bri_val")

    # --- 4. 補正実行（変数を上書きしてメモリ消費を抑える） ---
    processed_img = ImageEnhance.Color(raw_img).enhance(sat)
    processed_img = ImageEnhance.Contrast(processed_img).enhance(con)
    processed_img = ImageEnhance.Brightness(processed_img).enhance(bri)
    processed_img = ImageEnhance.Sharpness(processed_img).enhance(sha)

    # プレビュー表示
    st.image(processed_img, caption="補正後のプレビュー", use_container_width=True)

    # --- 5. ダウンロード ---
    buf = io.BytesIO()
    # メモリ節約のため quality=95 を推奨。解像度は維持されます。
    processed_img.save(buf, format="JPEG", quality=95, subsampling=0)
    
    st.download_button(
        label="🚀 補正済み画像をフルサイズで保存",
        data=buf.getvalue(),
        file_name=f"fixed_{uploaded_file.name}",
        mime="image/jpeg",
        use_container_width=True
    )
    
    # メモリ解放
    del raw_img, processed_img
    gc.collect()
