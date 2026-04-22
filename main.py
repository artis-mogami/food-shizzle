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
# ホワイトバランス（弱め）
# ----------------------------
def fix_white_balance_soft(img, strength=0.6):
    arr = np.array(img).astype(np.float32)

    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    avg_r, avg_g, avg_b = np.mean(r), np.mean(g), np.mean(b)
    avg_gray = (avg_r + avg_g + avg_b) / 3

    r = r * (1 + (avg_gray / (avg_r+1e-6) - 1) * strength)
    g = g * (1 + (avg_gray / (avg_g+1e-6) - 1) * strength)
    b = b * (1 + (avg_gray / (avg_b+1e-6) - 1) * strength)

    return Image.fromarray(np.clip(np.stack([r,g,b], axis=2), 0, 255).astype(np.uint8))

# ----------------------------
# オレンジ寄せ（NEW）
# ----------------------------
def warm_tone(img, r_gain=1.05, g_gain=1.02, b_gain=0.97):
    arr = np.array(img).astype(np.float32)

    arr[:,:,0] *= r_gain
    arr[:,:,1] *= g_gain
    arr[:,:,2] *= b_gain

    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))

# ----------------------------
# ハイライト圧縮（自然版）
# ----------------------------
def compress_highlight_soft(img, threshold=210, strength=0.7):
    arr = np.array(img).astype(np.float32)

    for c in range(3):
        ch = arr[:,:,c]
        mask = ch > threshold
        ch[mask] = threshold + (ch[mask] - threshold) * strength
        arr[:,:,c] = ch

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
st.title("🍳 料理フォトエディター（オレンジ寄せ改善版）")

uploaded_file = st.file_uploader("画像をアップロード", type=["jpg", "jpeg", "png"])

DEFAULTS = {
    "gamma": 0.9,
    "vibrance": 0.45,
    "contrast": 1.1,
    "sharpness": 1.6
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
    # 処理パイプライン（重要順）
    # ----------------------------
    img = fix_white_balance_soft(img)   # 弱WB
    img = warm_tone(img)                # ★オレンジ寄せ
    img = apply_gamma_and_vibrance(img, gamma, vibrance)
    img = compress_highlight_soft(img)  # ★白飛び抑制（改善版）
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
