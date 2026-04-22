import streamlit as st
from PIL import Image, ImageEnhance
import io
import numpy as np
import gc

st.set_page_config(page_title="Stable Pro Food Editor", page_icon="🍳")

@st.cache_data(show_spinner=False)
def load_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

def resize_image(img, max_size=5000):
    img.thumbnail((max_size, max_size))
    return img

# ----------------------------
# ソフトWB
# ----------------------------
def fix_white_balance_soft(img, strength=0.6):
    arr = np.array(img).astype(np.float32)
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    avg_r, avg_g, avg_b = np.mean(r), np.mean(g), np.mean(b)
    avg_gray = (avg_r + avg_g + avg_b) / 3

    r *= 1 + (avg_gray/(avg_r+1e-6)-1)*strength
    g *= 1 + (avg_gray/(avg_g+1e-6)-1)*strength
    b *= 1 + (avg_gray/(avg_b+1e-6)-1)*strength

    return Image.fromarray(np.clip(np.stack([r,g,b],axis=2),0,255).astype(np.uint8))

# ----------------------------
# オレンジ寄せ
# ----------------------------
def warm_tone(img):
    arr = np.array(img).astype(np.float32)
    arr[:,:,0] *= 1.05
    arr[:,:,1] *= 1.02
    arr[:,:,2] *= 0.97
    return Image.fromarray(np.clip(arr,0,255).astype(np.uint8))

# ----------------------------
# ハイライト圧縮
# ----------------------------
def compress_highlight_soft(img):
    arr = np.array(img).astype(np.float32)
    for c in range(3):
        ch = arr[:,:,c]
        mask = ch > 210
        ch[mask] = 210 + (ch[mask]-210)*0.7
        arr[:,:,c] = ch
    return Image.fromarray(np.clip(arr,0,255).astype(np.uint8))

# ----------------------------
# Vibrance
# ----------------------------
def apply_gamma_and_vibrance(img, gamma, vibrance):
    arr = np.array(img).astype(np.float32)/255.0
    arr = np.power(arr, gamma)
    avg = np.mean(arr, axis=2, keepdims=True)
    arr = arr + (arr-avg)*vibrance
    return Image.fromarray(np.clip(arr*255,0,255).astype(np.uint8))

# ----------------------------
# ★ 色域強調（緑＆オレンジ）
# ----------------------------
def boost_food_colors(img):
    arr = np.array(img).astype(np.float32)/255.0

    # RGB → HSV（簡易）
    maxc = arr.max(axis=2)
    minc = arr.min(axis=2)
    diff = maxc - minc

    h = np.zeros_like(maxc)

    mask = diff != 0
    r, g, b = arr[:,:,0], arr[:,:,1], arr[:,:,2]

    h[mask & (maxc == r)] = (60 * ((g-b)/diff) + 360)[mask & (maxc == r)]
    h[mask & (maxc == g)] = (60 * ((b-r)/diff) + 120)[mask & (maxc == g)]
    h[mask & (maxc == b)] = (60 * ((r-g)/diff) + 240)[mask & (maxc == b)]

    h = h % 360

    s = diff / (maxc + 1e-6)

    # ------------------------
    # マスク生成
    # ------------------------
    green_mask = (h > 60) & (h < 160)
    orange_mask = (h > 10) & (h < 50)

    # 彩度UP
    s[green_mask] *= 1.4
    s[orange_mask] *= 1.3

    s = np.clip(s, 0, 1)

    # 再構成（簡易）
    arr = arr * (1 + (s[...,None] - np.mean(arr,axis=2,keepdims=True))*0.5)

    return Image.fromarray(np.clip(arr*255,0,255).astype(np.uint8))

# ----------------------------
# ★ エッジシャープ（重要）
# ----------------------------
def enhance_edges(img):
    arr = np.array(img).astype(np.float32)

    kernel = np.array([
        [0, -1, 0],
        [-1, 5,-1],
        [0, -1, 0]
    ])

    from scipy.signal import convolve2d

    result = np.zeros_like(arr)

    for c in range(3):
        result[:,:,c] = convolve2d(arr[:,:,c], kernel, mode='same', boundary='symm')

    return Image.fromarray(np.clip(result,0,255).astype(np.uint8))

# ----------------------------
# UI
# ----------------------------
st.title("🍳 料理フォトエディター（プロ版）")

uploaded_file = st.file_uploader("画像アップロード", type=["jpg","jpeg","png"])

if uploaded_file:
    img = load_image(uploaded_file.read())
    img = resize_image(img, 5000)

    img = fix_white_balance_soft(img)
    img = warm_tone(img)
    img = apply_gamma_and_vibrance(img, 0.9, 0.45)

    img = boost_food_colors(img)     # ★色強調
    img = compress_highlight_soft(img)
    img = enhance_edges(img)         # ★シャープ

    img = ImageEnhance.Contrast(img).enhance(1.1)

    st.image(img, use_container_width=True)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)

    st.download_button("ダウンロード", buf.getvalue(), "food.jpg")
