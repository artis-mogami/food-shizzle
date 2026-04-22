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
# 色強化（改良版）
# ----------------------------
def selective_color_boost(img, green_boost=0.45, orange_boost=0.55):
    arr = np.array(img).astype(np.float32) / 255.0
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    white_mask = get_white_mask(arr)

    # 緑（強化）
    green_mask = (g > r * 0.8) & (g > b * 0.8)

    # オレンジ（広げた）
    orange_mask = (r > g * 0.85) & (g > b * 0.6) & (r > 0.3)

    avg = np.mean(arr, axis=2, keepdims=True)

    green_mask &= ~white_mask
    orange_mask &= ~white_mask

    arr[green_mask] += (arr[green_mask] - avg[green_mask]) * green_boost
    arr[orange_mask] += (arr[orange_mask] - avg[orange_mask]) * orange_boost

    # チーズをしっかりオレンジ寄せ
    arr[:,:,0] *= 1.03
    arr[:,:,1] *= 1.01

    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# トーン
# ----------------------------
def apply_tone(img, gamma=0.92, density=1.05):
    arr = np.array(img).astype(np.float32) / 255.0
    arr = np.power(arr, gamma)
    arr = arr * density
    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# 白飛び防止
# ----------------------------
def compress_highlight(img, threshold=242, strength=0.6):
    arr = np.array(img).astype(np.float32)
    mask = arr > threshold
    arr[mask] = threshold + (arr[mask] - threshold) * strength
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ----------------------------
# クール寄せ（NEW）
# ----------------------------
def add_cool_tone(img, strength=0.03):
    arr = np.array(img).astype(np.float32) / 255.0
    white_mask = get_white_mask(arr)

    # 赤を少し下げて青を足す
    arr[:,:,0] *= (1 - strength)
    arr[:,:,2] *= (1 + strength)

    arr[white_mask] = arr[white_mask]

    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# シャープ（強化）
# ----------------------------
def smart_sharpen(img, strength=2.4):
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
st.title("🍳 料理フォトエディター（色完成版）")

uploaded_file = st.file_uploader("画像アップロード", type=["jpg","jpeg","png"])

if uploaded_file:
    img = load_image(uploaded_file.read())
    img = resize_image(img)

    # パイプライン
    img = fix_white_balance(img)
    img = selective_color_boost(img)
    img = apply_tone(img)
    img = add_cool_tone(img)  # ←ここが今回のキモ
    img = compress_highlight(img)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = smart_sharpen(img, 2.4)

    st.image(img, use_container_width=True)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95, subsampling=0)

    st.download_button("ダウンロード", buf.getvalue(), "food_pro.jpg", "image/jpeg")

    del img
    gc.collect()
