import streamlit as st
from PIL import Image, ImageEnhance
import io
import numpy as np
import gc

st.set_page_config(page_title="Pro Food Editor", page_icon="🍳")

@st.cache_data(show_spinner=False)
def load_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

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
# 白保護
# ----------------------------
def get_white_mask(arr, threshold=0.05):
    max_c = arr.max(axis=2)
    min_c = arr.min(axis=2)
    return (max_c - min_c) < threshold

# ----------------------------
# 色強化（パラメータ化）
# ----------------------------
def selective_color_boost(img, green_boost, orange_boost):
    arr = np.array(img).astype(np.float32) / 255.0
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    white_mask = get_white_mask(arr)

    green_mask = (g > r * 0.8) & (g > b * 0.8)
    orange_mask = (r > g * 0.85) & (g > b * 0.6) & (r > 0.3)

    avg = np.mean(arr, axis=2, keepdims=True)

    green_mask &= ~white_mask
    orange_mask &= ~white_mask

    arr[green_mask] += (arr[green_mask] - avg[green_mask]) * green_boost
    arr[orange_mask] += (arr[orange_mask] - avg[orange_mask]) * orange_boost

    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# トーン
# ----------------------------
def apply_tone(img, gamma, density):
    arr = np.array(img).astype(np.float32) / 255.0
    arr = np.power(arr, gamma)
    arr = arr * density
    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# 白飛び防止
# ----------------------------
def compress_highlight(img, threshold, strength):
    arr = np.array(img).astype(np.float32)
    mask = arr > threshold
    arr[mask] = threshold + (arr[mask] - threshold) * strength
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ----------------------------
# クール寄せ
# ----------------------------
def add_cool_tone(img, strength):
    arr = np.array(img).astype(np.float32) / 255.0
    white_mask = get_white_mask(arr)

    arr[:,:,0] *= (1 - strength)
    arr[:,:,2] *= (1 + strength)

    arr[white_mask] = arr[white_mask]

    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# シャープ
# ----------------------------
def smart_sharpen(img, strength):
    arr = np.array(img).astype(np.float32)

    blur = (
        np.roll(arr,1,0) + np.roll(arr,-1,0) +
        np.roll(arr,1,1) + np.roll(arr,-1,1)
    ) / 4

    detail = arr - blur
    arr = arr + detail * strength

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ----------------------------
# UI（復活）
# ----------------------------
st.title("🍳 料理フォトエディター（完成版）")

uploaded_file = st.file_uploader("画像アップロード", type=["jpg","jpeg","png"])

st.sidebar.header("🎛 調整")

gamma = st.sidebar.slider("明るさ（ガンマ）", 0.7, 1.2, 0.92)
density = st.sidebar.slider("色の濃さ", 0.9, 1.3, 1.05)

green_boost = st.sidebar.slider("葉っぱ強調", 0.0, 0.8, 0.45)
orange_boost = st.sidebar.slider("チーズ強調", 0.0, 0.8, 0.55)

cool_strength = st.sidebar.slider("青寄せ", 0.0, 0.08, 0.03)

highlight_th = st.sidebar.slider("白飛び閾値", 220, 255, 242)
highlight_str = st.sidebar.slider("白飛び抑制", 0.3, 0.8, 0.6)

contrast = st.sidebar.slider("コントラスト", 1.0, 1.5, 1.2)
sharp = st.sidebar.slider("シャープ", 1.0, 3.5, 2.4)

if uploaded_file:
    img = load_image(uploaded_file.read())
    img = resize_image(img)

    # パイプライン
    img = fix_white_balance(img)
    img = selective_color_boost(img, green_boost, orange_boost)
    img = apply_tone(img, gamma, density)
    img = add_cool_tone(img, cool_strength)
    img = compress_highlight(img, highlight_th, highlight_str)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = smart_sharpen(img, sharp)

    st.image(img, use_container_width=True)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95, subsampling=0)

    st.download_button("ダウンロード", buf.getvalue(), "food_pro.jpg", "image/jpeg")

    del img
    gc.collect()
