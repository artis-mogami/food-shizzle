import streamlit as st
from PIL import Image, ImageEnhance
import io
import numpy as np
import gc
import cv2

st.set_page_config(page_title="Stable Pro Food Editor", page_icon="🍳")

# ----------------------------
# 画像ロード
# ----------------------------
@st.cache_data(show_spinner=False)
def load_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

# ----------------------------
# リサイズ（保存はそのまま）
# ----------------------------
def resize_preview(img, max_size=1024):
    preview = img.copy()
    preview.thumbnail((max_size, max_size))
    return preview

# ----------------------------
# メイン補正（改善版）
# ----------------------------
def process_image(img, p):
    img_np = np.array(img)

    hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)

    # ----------------------------
    # 白保護（超重要）
    # ----------------------------
    low_sat = s < 35

    # ----------------------------
    # 全体彩度
    # ----------------------------
    s *= p["density"]

    # ----------------------------
    # 🍃 緑（濃く＆暗く）
    # ----------------------------
    green = (h > 35) & (h < 85)
    s[green] += p["green_boost"] * 255
    v[green] *= (1 - 0.2 * p["green_boost"])  # ←ここ強化

    # ----------------------------
    # 🧀 オレンジ（チーズ）
    # ----------------------------
    orange = (h > 10) & (h < 28)
    s[orange] += p["orange_boost"] * 255

    # ----------------------------
    # ⚠ 黄色だけ抑える（ここが精度の肝）
    # ----------------------------
    yellow = (h > 25) & (h < 45)
    s[yellow] *= (1 - p["yellow_reduce"])
    v[yellow] *= (1 - 0.15 * p["yellow_reduce"])  # ←追加（白濁防止）

    # ----------------------------
    # 青寄せ（ほんの少し）
    # ----------------------------
    h -= p["cool_strength"] * 8

    # ----------------------------
    # 明るさ（ガンマ）
    # ----------------------------
    v = np.power(v / 255.0, p["gamma"]) * 255

    # ----------------------------
    # 白飛び防止
    # ----------------------------
    mask = v > p["highlight_th"]
    v[mask] = p["highlight_th"] + (v[mask] - p["highlight_th"]) * p["highlight_str"]

    # ----------------------------
    # 白を守る（これが一番効く）
    # ----------------------------
    s[low_sat] *= 0.5
    v[low_sat] = np.maximum(v[low_sat], 245)

    # clip
    h = np.clip(h, 0, 179)
    s = np.clip(s, 0, 255)
    v = np.clip(v, 0, 255)

    hsv = cv2.merge([h, s, v]).astype(np.uint8)
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    img_out = Image.fromarray(rgb)

    # 質感
    img_out = ImageEnhance.Contrast(img_out).enhance(p["contrast"])
    img_out = ImageEnhance.Sharpness(img_out).enhance(p["sharp"])

    return img_out

# ----------------------------
# デフォルト（After寄せ）
# ----------------------------
DEFAULTS = {
    "gamma": 0.92,
    "density": 1.12,
    "green_boost": 0.5,
    "orange_boost": 0.38,
    "yellow_reduce": 0.32,
    "cool_strength": 0.025,
    "highlight_th": 235,
    "highlight_str": 0.5,
    "contrast": 1.25,
    "sharp": 2.6
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
st.title("🍳 料理フォトエディター（完成版）")

uploaded_file = st.file_uploader("画像アップロード", type=["jpg","jpeg","png"])

st.sidebar.header("🎛 調整")
st.sidebar.button("🔄 リセット", on_click=reset_settings)

for key in DEFAULTS:
    st.sidebar.slider(key, min_value=0.0, max_value=2.0, key=key)

if uploaded_file:
    file_bytes = uploaded_file.read()
    img = load_image(file_bytes)

    params = {k: st.session_state[k] for k in DEFAULTS}

    img_out = process_image(img, params)

    preview = resize_preview(img_out, 1024)
    st.image(preview, caption="プレビュー")

    buf = io.BytesIO()
    img_out.save(buf, format="JPEG", quality=95, subsampling=0)

    st.download_button("高解像度ダウンロード", buf.getvalue(), "edited.jpg", "image/jpeg")

    del img, img_out
    gc.collect()
