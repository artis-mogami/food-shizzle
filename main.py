import streamlit as st
from PIL import Image, ImageEnhance
import io
import gc

st.set_page_config(page_title="Deep Mat Food Editor", page_icon="🍳")

st.title("🍳 料理フォトエディター (マット・深み優先版)")
st.write("ご提示いただいた基準画像のマットで深みのある質感を再現します。チーズのディテールを守ります。")

# --- 1. パラメータの管理 ---
# 基準画像を分析し、白飛びを防ぎつつマットな深みを出すための推奨値
DEFAULTS = {
    'sat_val': 1.4, # 彩度：基準画像のように落ち着いた鮮やかさ
    'con_val': 1.1, # コントラスト：元画像のディテールを完全に守るため、ほぼ変化なし
    'bri_val': 1.0, # 明るさ：元画像を維持し、白飛びを徹底的に防ぐ
    'sha_val': 1.5  # シャープネス：基準画像のようにマットで、ギラギラさせない
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
    uploaded_file.seek(0)
    raw_img = Image.open(uploaded_file).convert("RGB")
    
    st.divider()
    
    # --- 3. 調整スライダー ---
    col1, col2 = st.columns(2)
    with col1:
        sat = st.slider("色彩の鮮やかさ (彩度)", 0.0, 5.0, key="sat_val")
        con = st.slider("立体感 (コントラスト)", 0.0, 5.0, key="con_val")
    with col2:
        sha = st.slider("質感の強さ (シャープネス)", 0.0, 10.0, key="sha_val")
        bri = st.slider("明るさ調整", 0.0, 3.0, key="bri_val")

    # --- 4. 補正実行（変数を上書きしてメモリ消費を抑える） ---
    # 処理順序：彩度 -> コントラスト -> 明るさ -> シャープネス
    processed_img = ImageEnhance.Color(raw_img).enhance(sat)
    processed_img = ImageEnhance.Contrast(processed_img).enhance(con)
    processed_img = ImageEnhance.Brightness(processed_img).enhance(bri)
    processed_img = ImageEnhance.Sharpness(processed_img).enhance(sha)

    # プレビュー表示
    st.image(processed_img, caption="補正後のプレビュー", use_container_width=True)

    # --- 5. ダウンロード ---
    buf = io.BytesIO()
    # JPEGで高画質に保存、解像度は完全に維持
    processed_img.save(buf, format="JPEG", quality=100, subsampling=0)
    
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
