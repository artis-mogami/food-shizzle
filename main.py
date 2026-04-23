import streamlit as st
from PIL import Image, ImageEnhance
import io
import numpy as np
import cv2
import gc

st.set_page_config(page_title="Pizza Color Editor", page_icon="🍕")

# ----------------------------
# 画像ロード
# ----------------------------
@st.cache_data(show_spinner=False)
def load_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

# ----------------------------
# プレビュー用
# ----------------------------
def preview_resize(img, max_size=1024):
    img_copy = img.copy()
    img_copy.thumbnail((max_size, max_size))
    return img_copy

# ----------------------------
# 補正ロジック（ピザ特化）
# ----------------------------
def process_image(img, p):
    img_np = np.array(img).astype(np.uint8)

    hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)

    # ----------------------------
    # 白保護（チーズ対策）
    # ----------------------------
    low_sat = s < 40
    s[low_sat] *= 0.25

    # ----------------------------
    # 彩度ベース
    # ----------------------------
    s *= p["density"]

    # ----------------------------
    # チーズ（黄ばみ除去 + コク）
    # ----------------------------
    cheese = (h > 15) & (h < 35)
    s[cheese] *= (1 - p["yellow_reduce"])
    v[cheese] *= 1.08

    # ----------------------------
    # 葉っぱ（濃く・暗く）
    # ----------------------------
    green = (h > 35) & (h < 85)
    s[green] += p["green_boost"] * 255
    v[green] *= 0.85

    # ----------------------------
    # 青寄せ（全体のくすみ除去）
    # ----------------------------
    h -= p["cool"] * 10

    # ----------------------------
    # 明るさ（自然補正）
    # ----------------------------
    v = np.power(v / 255.0, p["gamma"]) * 255

    # ----------------------------
    # 白飛び防止
    # ----------------------------
    mask = v > 235
    v[mask] = 235 + (v[mask] - 235) * 0.5

    # ----------------------------
    # clip（超重要）
    # ----------------------------
    h = np.clip(h, 0, 179)
    s = np.clip(s, 0, 255)
    v = np.clip(v, 0, 255)

    hsv = cv2.merge([
        h.astype(np.uint8),
        s.astype(np.uint8),
        v.astype(np.uint8)
    ])

    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    img_out = Image.fromarray(rgb)

    img_out = ImageEnhance.Contrast(img_out).enhance(p["contrast"])
    img_out = ImageEnhance.Sharpness(img_out).enhance(p["sharp"])

    return img_out

# ----------------------------
# UI
# ----------------------------
st.title("🍕 ピザ補正エディター（完成版）")

uploaded = st.file_uploader("画像アップロード", type=["jpg","png","jpeg"])

st.sidebar.header("調整")

gamma = st.sidebar.slider("明るさ", 0.7, 1.2, 0.92, 0.01)
density = st.sidebar.slider("色の濃さ", 0.9, 1.3, 1.1, 0.01)
green_boost = st.sidebar.slider("葉っぱ強化", 0.0, 0.8, 0.5, 0.01)
yellow_reduce = st.sidebar.slider("チーズ黄ばみ除去", 0.0, 0.5, 0.3, 0.01)
cool = st.sidebar.slider("青寄せ", 0.0, 0.08, 0.04, 0.001)
contrast = st.sidebar.slider("コントラスト", 1.0, 1.5, 1.25, 0.01)
sharp = st.sidebar.slider("シャープ", 1.0, 3.5, 2.3, 0.1)

params = {
    "gamma": gamma,
    "density": density,
    "green_boost": green_boost,
    "yellow_reduce": yellow_reduce,
    "cool": cool,
    "contrast": contrast,
    "sharp": sharp
}

# ----------------------------
# 実行
# ----------------------------
if uploaded:
    img = load_image(uploaded.read())

    img_out = process_image(img, params)

    preview = preview_resize(img_out, 1024)

    st.image(preview, caption="After（プレビュー）")

    buf = io.BytesIO()
    img_out.save(buf, format="JPEG", quality=95, subsampling=0)

    st.download_button("高画質ダウンロード", buf.getvalue(), "pizza.jpg")

    del img, img_out
    gc.collect()
