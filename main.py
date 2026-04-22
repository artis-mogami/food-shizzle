import streamlit as st
from PIL import Image, ImageEnhance
import numpy as np
import io
import gc

st.set_page_config(page_title="Food Editor Pro", page_icon="🍳")

# ----------------------------
# Load
# ----------------------------
@st.cache_data
def load_image(b):
    return Image.open(io.BytesIO(b)).convert("RGB")

def resize_image(img, max_size=5000):
    img.thumbnail((max_size, max_size))
    return img

# ----------------------------
# HSV変換（NumPy）
# ----------------------------
def rgb_to_hsv(arr):
    arr = arr / 255.0
    r,g,b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    maxc = np.max(arr, axis=2)
    minc = np.min(arr, axis=2)
    diff = maxc - minc

    h = np.zeros_like(maxc)
    s = np.zeros_like(maxc)
    v = maxc

    mask = diff != 0

    h[mask & (maxc == r)] = (60 * ((g-b)/diff) + 360)[mask & (maxc == r)]
    h[mask & (maxc == g)] = (60 * ((b-r)/diff) + 120)[mask & (maxc == g)]
    h[mask & (maxc == b)] = (60 * ((r-g)/diff) + 240)[mask & (maxc == b)]

    h = h % 360
    s[maxc != 0] = diff[maxc != 0] / maxc[maxc != 0]

    return h, s, v

# ----------------------------
# 白保護＋色強調
# ----------------------------
def selective_color_boost(img):
    arr = np.array(img).astype(np.float32)
    original = arr.copy()

    h, s, v = rgb_to_hsv(arr)

    # ------------------------
    # マスク
    # ------------------------
    white_mask = (s < 0.12) & (v > 0.75)
    green_mask = (h > 60) & (h < 160)
    orange_mask = (h > 10) & (h < 50)

    # ------------------------
    # 色強調（非白のみ）
    # ------------------------
    boost = np.ones_like(arr)

    boost[:,:,0] += orange_mask * 0.08   # R
    boost[:,:,1] += green_mask * 0.10    # G
    boost[:,:,2] -= orange_mask * 0.05   # B少し下げる

    arr = arr * boost

    # ------------------------
    # 白を戻す（重要）
    # ------------------------
    arr[white_mask] = original[white_mask]

    return Image.fromarray(np.clip(arr,0,255).astype(np.uint8))

# ----------------------------
# ハイライト圧縮（弱め）
# ----------------------------
def compress_highlight(img):
    arr = np.array(img).astype(np.float32)
    mask = arr > 220
    arr[mask] = 220 + (arr[mask]-220)*0.6
    return Image.fromarray(np.clip(arr,0,255).astype(np.uint8))

# ----------------------------
# シャープ（安全版）
# ----------------------------
def sharpen(img):
    return ImageEnhance.Sharpness(img).enhance(1.6)

# ----------------------------
# ガンマ
# ----------------------------
def gamma(img, g=0.9):
    arr = np.array(img).astype(np.float32)/255.0
    arr = np.power(arr, g)
    return Image.fromarray(np.clip(arr*255,0,255).astype(np.uint8))

# ----------------------------
# UI
# ----------------------------
st.title("🍳 料理フォトエディター（白保護版）")

uploaded = st.file_uploader("画像アップロード", type=["jpg","png","jpeg"])

if uploaded:
    img = load_image(uploaded.read())
    img = resize_image(img, 5000)

    # パイプライン
    img = gamma(img, 0.9)
    img = selective_color_boost(img)   # ★重要
    img = compress_highlight(img)
    img = sharpen(img)

    st.image(img, use_container_width=True)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)

    st.download_button("ダウンロード", buf.getvalue(), "edited.jpg")

    del img
    gc.collect()
