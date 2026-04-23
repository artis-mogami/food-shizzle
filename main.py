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
# リサイズ
# ----------------------------
def resize_image(img, max_size=5000):
    img.thumbnail((max_size, max_size))
    return img

# ----------------------------
# メイン補正（安定版）
# ----------------------------
def process_image(img, params):
    img_np = np.array(img)

    # RGB → HSV
    hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)

    # =========================
    # ① 白濁防止（低彩度は触らない）
    # =========================
    low_sat_mask = s < 40

    # =========================
    # ② 彩度（自然な濃さ）
    # =========================
    s = s * params["density"]
    s[low_sat_mask] = s[low_sat_mask]  # 白保護

    # =========================
    # ③ 葉っぱ（緑）
    # =========================
    green_mask = (h > 35) & (h < 85)
    s[green_mask] += params["green_boost"] * 255

    # =========================
    # ④ チーズ（オレンジ）
    # =========================
    orange_mask = (h > 10) & (h < 30)
    s[orange_mask] += params["orange_boost"] * 255

    # =========================
    # ⑤ 黄色抑制
    # =========================
    yellow_mask = (h > 25) & (h < 40)
    s[yellow_mask] *= (1 - params["yellow_reduce"])

    # =========================
    # ⑥ 青寄せ（ほんの少し）
    # =========================
    h = h - params["cool_strength"] * 10

    # =========================
    # ⑦ 明るさ（ガンマ）
    # =========================
    v = np.power(v / 255.0, params["gamma"]) * 255

    # =========================
    # ⑧ 白飛び防止
    # =========================
    mask = v > params["highlight_th"]
    v[mask] = params["highlight_th"] + (v[mask] - params["highlight_th"]) * params["highlight_str"]

    # clip
    s = np.clip(s, 0, 255)
    v = np.clip(v, 0, 255)
    h = np.clip(h, 0, 179)

    hsv = cv2.merge([h, s, v]).astype(np.uint8)
    rgb = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    img_out = Image.fromarray(rgb)

    # 最後の質感調整
    img_out = ImageEnhance.Contrast(img_out).enhance(params["contrast"])
    img_out = ImageEnhance.Sharpness(img_out).enhance(params["sharp"])

    return img_out

# ----------------------------
# デフォルト
# ----------------------------
DEFAULTS = {
    "gamma": 0.9,
    "density": 1.15,
    "green_boost": 0.35,
    "orange_boost": 0.4,
    "yellow_reduce": 0.2,
    "cool_strength": 0.03,
    "highlight_th": 235,
    "highlight_str": 0.5,
    "contrast": 1.2,
    "sharp": 2.2
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
st.title("🍳 料理フォトエディター（安定版・色崩れ修正）")

uploaded_file = st.file_uploader("画像アップロード", type=["jpg","jpeg","png"])

st.sidebar.header("🎛 調整")
st.sidebar.button("🔄 リセット", on_click=reset_settings)

gamma = st.sidebar.slider("明るさ", 0.7, 1.2, key="gamma")
density = st.sidebar.slider("色の濃さ", 0.9, 1.3, key="density")
green_boost = st.sidebar.slider("葉っぱ", 0.0, 0.8, key="green_boost")
orange_boost = st.sidebar.slider("チーズ", 0.0, 0.8, key="orange_boost")
yellow_reduce = st.sidebar.slider("黄色抑制", 0.0, 0.4, key="yellow_reduce")
cool_strength = st.sidebar.slider("青寄せ", 0.0, 0.08, key="cool_strength")
highlight_th = st.sidebar.slider("白飛び閾値", 220, 255, key="highlight_th")
highlight_str = st.sidebar.slider("白飛び抑制", 0.3, 0.8, key="highlight_str")
contrast = st.sidebar.slider("コントラスト", 1.0, 1.5, key="contrast")
sharp = st.sidebar.slider("シャープ", 1.0, 3.5, key="sharp")

if uploaded_file:
    file_bytes = uploaded_file.read()
    img = load_image(file_bytes)
    img = resize_image(img, 5000)

    params = {k: st.session_state[k] for k in DEFAULTS.keys()}

    img_out = process_image(img, params)

    st.image(img_out, caption="補正後", use_container_width=True)

    buf = io.BytesIO()
    img_out.save(buf, format="JPEG", quality=95, subsampling=0)

    st.download_button("ダウンロード", buf.getvalue(), "edited.jpg", "image/jpeg")

    del img, img_out
    gc.collect()
