import streamlit as st
from PIL import Image, ImageEnhance
import io
import numpy as np
import cv2
import gc

st.set_page_config(page_title="Food Editor PRO", page_icon="🍳")

# ----------------------------
# 画像ロード
# ----------------------------
@st.cache_data(show_spinner=False)
def load_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

# ----------------------------
# プレビュー用リサイズ（軽量）
# ----------------------------
def preview_resize(img, max_size=1024):
    img_copy = img.copy()
    img_copy.thumbnail((max_size, max_size))
    return img_copy

# ----------------------------
# メイン補正
# ----------------------------
def process_image(img, params):
    img_np = np.array(img).astype(np.uint8)

    hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)

    # ----------------------------
    # 白保護（かなり強め）
    # ----------------------------
    low_sat_mask = s < 35

    # ----------------------------
    # 彩度
    # ----------------------------
    s = s * params["density"]

    # ----------------------------
    # 葉っぱ（濃く・暗く）
    # ----------------------------
    green_mask = (h > 35) & (h < 85)
    s[green_mask] += params["green_boost"] * 255
    v[green_mask] *= 0.9

    # ----------------------------
    # チーズ（コク強化）
    # ----------------------------
    orange_mask = (h > 10) & (h < 30)
    s[orange_mask] += params["orange_boost"] * 255
    v[orange_mask] *= 1.05

    # ----------------------------
    # 黄色抑制（強め）
    # ----------------------------
    yellow_mask = (h > 25) & (h < 45)
    s[yellow_mask] *= (1 - params["yellow_reduce"])

    # ----------------------------
    # 青寄せ（ほんの少し）
    # ----------------------------
    h = h - params["cool_strength"] * 10

    # ----------------------------
    # ガンマ補正
    # ----------------------------
    v = np.power(v / 255.0, params["gamma"]) * 255

    # ----------------------------
    # 白飛び防止
    # ----------------------------
    mask = v > params["highlight_th"]
    v[mask] = params["highlight_th"] + (v[mask] - params["highlight_th"]) * params["highlight_str"]

    # ----------------------------
    # 白は絶対守る
    # ----------------------------
    s[low_sat_mask] = s[low_sat_mask] * 0.3

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

    # 最終仕上げ
    img_out = ImageEnhance.Contrast(img_out).enhance(params["contrast"])
    img_out = ImageEnhance.Sharpness(img_out).enhance(params["sharp"])

    return img_out

# ----------------------------
# デフォルト
# ----------------------------
DEFAULTS = {
    "gamma": 0.92,
    "density": 1.12,
    "green_boost": 0.45,
    "orange_boost": 0.5,
    "yellow_reduce": 0.28,
    "cool_strength": 0.04,
    "highlight_th": 235,
    "highlight_str": 0.5,
    "contrast": 1.25,
    "sharp": 2.3
}

def reset_settings():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------------
# UI
# ----------------------------
st.title("🍳 Food Editor PRO（色補正完成版）")

uploaded_file = st.file_uploader("画像アップロード", type=["jpg","jpeg","png"])

st.sidebar.header("調整")
st.sidebar.button("リセット", on_click=reset_settings)

for k in DEFAULTS:
    st.sidebar.slider(k, 0.0, 2.0, key=k)

# ----------------------------
# 処理
# ----------------------------
if uploaded_file:
    file_bytes = uploaded_file.read()

    img = load_image(file_bytes)

    params = {k: st.session_state[k] for k in DEFAULTS.keys()}

    # 高解像度で処理
    img_out = process_image(img, params)

    # プレビューだけ軽量化
    preview = preview_resize(img_out, 1024)

    st.image(preview, caption="After（プレビュー）", use_container_width=True)

    # ダウンロード（高解像度維持）
    buf = io.BytesIO()
    img_out.save(buf, format="JPEG", quality=95, subsampling=0)

    st.download_button(
        "ダウンロード（高画質）",
        buf.getvalue(),
        "edited.jpg",
        "image/jpeg"
    )

    del img, img_out
    gc.collect()
