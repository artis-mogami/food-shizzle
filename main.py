import streamlit as st
from PIL import Image, ImageEnhance
import io
import numpy as np
import gc

st.set_page_config(page_title="Stable Pro Food Editor", page_icon="🍳")

# ----------------------------
# 画像ロード
# ----------------------------
@st.cache_data(show_spinner=False)
def load_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

# ----------------------------
# リサイズ（最大5000px）
# ----------------------------
def resize_image(img, max_size=5000):
    img.thumbnail((max_size, max_size))
    return img

# ----------------------------
# ホワイトバランス補正
# ----------------------------
def fix_white_balance(img):
    arr = np.array(img).astype(np.float32)

    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    avg_r, avg_g, avg_b = np.mean(r), np.mean(g), np.mean(b)
    avg_gray = (avg_r + avg_g + avg_b) / 3

    r *= avg_gray / (avg_r + 1e-6)
    g *= avg_gray / (avg_g + 1e-6)
    b *= avg_gray / (avg_b + 1e-6)

    balanced = np.stack([r, g, b], axis=2)
    return Image.fromarray(np.clip(balanced, 0, 255).astype(np.uint8))

# ----------------------------
# 赤み抑制（NEW）
# ----------------------------
def reduce_red(img, strength=0.94):
    arr = np.array(img).astype(np.float32)
    arr[:,:,0] *= strength  # Rチャンネル
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ----------------------------
# ハイライト圧縮（白飛び防止）（NEW）
# ----------------------------
def compress_highlight(img, threshold=200, strength=0.6):
    arr = np.array(img).astype(np.float32)

    mask = arr > threshold
    arr[mask] = threshold + (arr[mask] - threshold) * strength

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ----------------------------
# ガンマ＋自然彩度
# ----------------------------
def apply_gamma_and_vibrance(img, gamma, vibrance):
    arr = np.array(img).astype(np.float32) / 255.0

    arr = np.power(arr, gamma)

    avg = np.mean(arr, axis=2, keepdims=True)
    arr = arr + (arr - avg) * vibrance

    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# UI
# ----------------------------
st.title("🍳 料理フォトエディター（改善版）")
st.write("赤み補正＋白飛び防止を追加")

uploaded_file = st.file_uploader("画像をアップロード", type=["jpg", "jpeg", "png"])

DEFAULTS = {
    "gamma": 0.85,
    "vibrance": 0.4,
    "contrast": 1.1,
    "sharpness": 1.8
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.sidebar.header("調整")

gamma = st.sidebar.slider("影の深さ", 0.3, 1.5, key="gamma")
vibrance = st.sidebar.slider("鮮やかさ", 0.0, 1.0, key="vibrance")
contrast = st.sidebar.slider("コントラスト", 0.5, 2.0, key="contrast")
sharpness = st.sidebar.slider("シャープネス", 0.0, 5.0, key="sharpness")

if uploaded_file:
    file_bytes = uploaded_file.read()

    img = load_image(file_bytes)
    img = resize_image(img, 5000)

    # ----------------------------
    # 処理パイプライン
    # ----------------------------
    img = fix_white_balance(img)
    img = reduce_red(img)  # ★追加
    img = apply_gamma_and_vibrance(img, gamma, vibrance)
    img = compress_highlight(img)  # ★追加
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)

    st.image(img, caption="補正後", use_container_width=True)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95, subsampling=0)

    st.download_button(
        "ダウンロード",
        buf.getvalue(),
        file_name="edited.jpg",
        mime="image/jpeg"
    )

    del img
    gc.collect()
