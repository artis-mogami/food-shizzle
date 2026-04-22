import streamlit as st
from PIL import Image, ImageEnhance
import io
import numpy as np
import gc

st.set_page_config(page_title="Pro Food Editor", page_icon="🍳")

# ----------------------------
# 画像ロード
# ----------------------------
@st.cache_data(show_spinner=False)
def load_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

# ----------------------------
# リサイズ
# ----------------------------
def resize_image(img, max_size=5000):
    img.thumbnail((max_size, max_size))
    return img

# ----------------------------
# ホワイトバランス
# ----------------------------
def fix_white_balance(img):
    arr = np.array(img).astype(np.float32)

    avg = np.mean(arr, axis=(0,1))
    gray = np.mean(avg)

    arr[:,:,0] *= gray / (avg[0] + 1e-6)
    arr[:,:,1] *= gray / (avg[1] + 1e-6)
    arr[:,:,2] *= gray / (avg[2] + 1e-6)

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ----------------------------
# 白保護（NEW）
# ----------------------------
def protect_whites(arr, threshold=0.08):
    # 彩度が低い＝白/グレー
    max_c = arr.max(axis=2)
    min_c = arr.min(axis=2)
    sat = max_c - min_c

    mask = sat < threshold
    return mask

# ----------------------------
# 部分カラー強化（緑＋オレンジ）（NEW）
# ----------------------------
def selective_color_boost(img, green_boost=0.25, orange_boost=0.3):
    arr = np.array(img).astype(np.float32) / 255.0

    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    # 緑マスク
    green_mask = (g > r) & (g > b)

    # オレンジマスク（チーズ）
    orange_mask = (r > g) & (g > b) & (r > 0.4)

    # 彩度強化
    avg = np.mean(arr, axis=2, keepdims=True)

    arr[green_mask] += (arr[green_mask] - avg[green_mask]) * green_boost
    arr[orange_mask] += (arr[orange_mask] - avg[orange_mask]) * orange_boost

    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# ガンマ＋濃さUP（改良）
# ----------------------------
def apply_gamma_and_density(img, gamma, density):
    arr = np.array(img).astype(np.float32) / 255.0

    arr = np.power(arr, gamma)

    # 濃さUP（黒を締める）
    arr = arr * density

    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# 白飛び防止
# ----------------------------
def compress_highlight(img, threshold=235, strength=0.5):
    arr = np.array(img).astype(np.float32)

    mask = arr > threshold
    arr[mask] = threshold + (arr[mask] - threshold) * strength

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ----------------------------
# 高品質シャープ（改良）
# ----------------------------
def smart_sharpen(img, strength=1.6):
    arr = np.array(img).astype(np.float32)

    blur = (
        np.roll(arr,1,0) + np.roll(arr,-1,0) +
        np.roll(arr,1,1) + np.roll(arr,-1,1)
    ) / 4

    detail = arr - blur
    arr = arr + detail * strength

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ----------------------------
# UI
# ----------------------------
st.title("🍳 料理フォトエディター（完成版）")

uploaded_file = st.file_uploader("画像アップロード", type=["jpg","jpeg","png"])

DEFAULTS = {
    "gamma": 0.85,
    "density": 1.05,
    "contrast": 1.15,
    "sharpness": 1.8
}

for k,v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.sidebar.header("調整")

gamma = st.sidebar.slider("明るさ", 0.5, 1.5, key="gamma")
density = st.sidebar.slider("色の濃さ", 0.8, 1.3, key="density")
contrast = st.sidebar.slider("コントラスト", 0.8, 2.0, key="contrast")
sharpness = st.sidebar.slider("シャープ", 0.5, 3.0, key="sharpness")

if uploaded_file:
    img = load_image(uploaded_file.read())
    img = resize_image(img)

    # ----------------------------
    # 処理パイプライン（重要）
    # ----------------------------
    img = fix_white_balance(img)
    img = selective_color_boost(img)   # ★色の主役強化
    img = apply_gamma_and_density(img, gamma, density)
    img = compress_highlight(img)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = smart_sharpen(img, sharpness)

    st.image(img, use_container_width=True)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95, subsampling=0)

    st.download_button(
        "ダウンロード",
        buf.getvalue(),
        "food_pro.jpg",
        "image/jpeg"
    )

    del img
    gc.collect()
