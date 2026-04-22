import streamlit as st
from PIL import Image, ImageEnhance
import io
import numpy as np
import gc

st.set_page_config(page_title="Food Photo Pro", page_icon="🍳")

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
# ホワイトバランス補正（青被り除去）
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
# 料理特化カラー強調（ここが今回の改善）
# ----------------------------
def boost_food_colors(img):
    arr = np.array(img).astype(np.float32)

    r = arr[:,:,0]
    g = arr[:,:,1]
    b = arr[:,:,2]

    # 食材を美味しく見せる調整
    r *= 1.08   # 赤アップ
    g *= 1.03   # 緑少しアップ
    b *= 0.92   # 青抑制（皿の青対策）

    boosted = np.stack([r, g, b], axis=2)
    return Image.fromarray(np.clip(boosted, 0, 255).astype(np.uint8))

# ----------------------------
# ガンマ＋自然彩度
# ----------------------------
def apply_gamma_and_vibrance(img, gamma, vibrance):
    arr = np.array(img).astype(np.float32) / 255.0

    # ガンマ補正
    arr = np.power(arr, gamma)

    # 自然な彩度（Vibrance）
    avg = np.mean(arr, axis=2, keepdims=True)
    arr = arr + (arr - avg) * vibrance

    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))

# ----------------------------
# UI
# ----------------------------
st.title("🍳 料理フォト補正ツール")
st.write("アップするだけで自然に美味しく見せる")

uploaded_file = st.file_uploader("画像をアップロード", type=["jpg", "jpeg", "png"])

# 初期値（この写真に最適化）
DEFAULTS = {
    "gamma": 0.8,
    "vibrance": 0.5,
    "contrast": 1.2,
    "sharpness": 1.5
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# サイドバー
st.sidebar.header("調整")

gamma = st.sidebar.slider("影の深さ（ガンマ）", 0.3, 1.5, key="gamma")
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
    img = fix_white_balance(img)
    img = boost_food_colors(img)
    img = apply_gamma_and_vibrance(img, gamma, vibrance)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Sharpness(img).enhance(sharpness)

    st.image(img, caption="補正後", use_container_width=True)

    # 保存
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
