import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io
import gc
import numpy as np

st.set_page_config(page_title="Stable Pro Food Editor", page_icon="🍳")

# --- 画像処理のキャッシュ ---
@st.cache_data
def load_and_convert(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

def apply_gamma_and_vibrance(img, gamma, vibrance_val):
    # 画像をnumpy配列に変換して階調と彩度を分離処理
    img_array = np.array(img).astype(np.float32) / 255.0
    
    # 1. ガンマ補正（白潰れを防ぎ、シャドウだけを締める）
    # image_15.pngのようなマットな黒を出すため、0.8前後が推奨
    img_gamma = np.power(img_array, gamma)
    
    # 2. 自然な彩度（Vibrance）のシミュレーション
    # チーズの黄色を潰さず、バジルの緑を鮮やかにする
    avg = np.mean(img_gamma, axis=2, keepdims=True)
    img_vibrance = img_gamma + (img_gamma - avg) * vibrance_val
    
    # 範囲を0-1にクリップして8bitに戻す
    result_array = np.clip(img_vibrance * 255.0, 0, 255).astype(np.uint8)
    del img_array, img_gamma, img_vibrance, avg # メモリ解放
    return Image.fromarray(result_array)

st.title("🍳 料理フォトエディター ")
st.write("質感をディテールを壊さずに再現します。")

# --- 1. パラメータの管理 ---
# image_15.pngを再現するための新しい黄金比（初期値）
DEFAULTS = {
    'gamma_val': 0.8, # ガンマ：After.jpgのようにマットな黒を出す
    'vib_val': 0.4,   # 自然な彩度：チーズを潰さず、バジルを鮮やかに
    'con_val': 1.1,   # コントラスト：元画像のディテールを完全に守るため、ほぼ変化なし
    'sha_val': 2.0    # シャープネス： After.jpgのようにギラギラさせない
}

# セッション状態に値を登録
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
uploaded_file = st.file_uploader("Before.jpgをアップロード...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # メモリを節約するためキャッシュを使用
    file_bytes = uploaded_file.read()
    raw_img = load_and_convert(file_bytes)
    uploaded_file.seek(0)
    
    st.divider()
    
    # --- 3. 調整スライダー ---
    # 白飛びを防ぐため、「明るさ」ではなく「ガンマ」と「自然な彩度」で調整します
    col1, col2 = st.columns(2)
    with col1:
        gamma_slider = st.slider("影の深さ (ガンマ補正)", 0.2, 2.0, key="gamma_val")
        vib_slider = st.slider("色の鮮やかさ (自然な彩度)", 0.0, 1.0, key="vib_val")
    with col2:
        sha_slider = st.slider("質感の強さ (シャープネス)", 0.0, 10.0, key="sha_val")
        con_slider = st.slider("立体感 (コントラスト)", 0.0, 3.0, key="con_val")

    # --- 4. 補正実行（メモリリークを防ぐためuse_container_widthを使用） ---
    # 1. プロ仕様の階調調整
    img_fixed = apply_gamma_and_vibrance(raw_img, gamma_slider, vib_slider)
    # 2. 微調整のコントラストとシャープネス
    img_fixed = ImageEnhance.Contrast(img_fixed).enhance(con_slider)
    img_fixed = ImageEnhance.Sharpness(img_fixed).enhance(sha_slider)

    # プレビュー表示（解像度は維持）
    st.image(img_fixed, caption="補正後のイメージ (解像度は維持されています)", use_container_width=True)

    # ダウンロード
    buf = io.BytesIO()
    # JPEGで高画質に保存、解数度は完全に維持
    img_fixed.save(buf, format="JPEG", quality=100, subsampling=0)
    
    st.download_button(
        label="🚀 補正済み画像をフルサイズで保存",
        data=buf.getvalue(),
        file_name=f"fixed_{uploaded_file.name}",
        mime="image/jpeg",
        use_container_width=True
    )
    
    # メモリ解放
    del raw_img, img_fixed
    gc.collect()
