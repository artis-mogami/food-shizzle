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
# 白完全保護（強化版）
# ----------------------------
def get_white_mask(arr, threshold=0.06):
    max_c = arr.max(axis=2)
    min_c = arr.min(axis=2)
    sat = max_c - min_c
    return sat < threshold

# ----------------------------
# 色ブースト（改良版）
# ----------------------------
def selective_color_boost(img, green_boost=0.35, orange_boost=0.45):
    arr = np.array(img).astype(np.float32) / 255.0

    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    white_mask = get_white_mask(arr)

    # 緑判定（広げた）
    green_mask = (g > r * 0.85) & (g > b * 0.85)

    # オレンジ判定（広げた）
    orange_mask = (r > g * 0.9) & (g > b * 0.7) & (r > 0.35)

    avg = np.mean(arr, axis=2, keepdims=True)

    # 白以外のみ適用
    green_mask &= ~white_mask
    orange_mask &= ~white_mask

    arr[green_mask] += (arr[green_mask] - avg[green_mask]) * green_boost
    arr[orange_mask] += (arr[orange_mask] - avg[orange_mask]) * orange_boost

    # オレンジを少し赤寄りに
    arr[:,:,0] *= 1.05  # R微増

    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# トーン（濃さ＋ガンマ）
# ----------------------------
def apply_tone(img, gamma=0.9, density=1.08):
    arr = np.array(img).astype(np.float32) / 255.0

    arr = np.power(arr, gamma)
    arr = arr * density

    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# ハイライト圧縮
# ----------------------------
def compress_highlight(img, threshold=240, strength=0.5):
    arr = np.array(img).astype(np.float32)

    mask = arr > threshold
    arr[mask] = threshold + (arr[mask] - threshold) * strength

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ----------------------------
# ウォームトーン（NEW）
# ----------------------------
def add_warmth(img, strength=0.04):
    arr = np.array(img).astype(np.float32) / 255.0

    white_mask = get_white_mask(arr)

    # 白以外だけ暖色化
    arr[:,:,0] += strength
    arr[:,:,2] -= strength * 0.5

    arr[white_mask] = arr[white_mask]  # 白保護

    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# シャープ
# ----------------------------
def smart_sharpen(img, strength=2.0):
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
st.title("🍳 料理フォトエディター（完成版＋）")

uploaded_file = st.file_uploader("画像アップロード", type=["jpg","jpeg","png"])

if uploaded_file:
    img = load_image(uploaded_file.read())
    img = resize_image(img)

    # ----------------------------
    # パイプライン（最重要）
    # ----------------------------
    img = fix_white_balance(img)
    img = selective_color_boost(img)
    img = apply_tone(img)
    img = add_warmth(img)
    img = compress_highlight(img)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img = smart_sharpen(img, 2.0)

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
