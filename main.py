import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io

st.set_page_config(layout="wide")

# =========================
# 初期値
# =========================
DEFAULTS = {
    "gamma": 0.9,
    "density": 1.1,
    "green_boost": 0.4,
    "orange_boost": 0.5,
    "yellow_reduce": 0.2,
    "cool_strength": 0.03,
    "highlight_th": 235,
    "highlight_str": 0.5,
    "contrast": 1.2,
    "sharp": 2.0
}

def reset_settings():
    for k, v in DEFAULTS.items():
        st.session_state[k] = v

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# 処理関数
# =========================
def process(img):

    img = np.array(img).astype(np.float32) / 255.0

    # ---- ガンマ（明るさ）----
    img = np.power(img, st.session_state.gamma)

    # ---- HSV変換 ----
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    # ---- 全体の色の濃さ ----
    hsv[:, :, 1] *= st.session_state.density

    # ---- 葉っぱ強化（緑）----
    green = (hsv[:, :, 0] > 35) & (hsv[:, :, 0] < 85)
    hsv[:, :, 1][green] *= (1 + st.session_state.green_boost)

    # ---- チーズ強化（オレンジ）----
    orange = (hsv[:, :, 0] > 10) & (hsv[:, :, 0] < 35)
    hsv[:, :, 1][orange] *= (1 + st.session_state.orange_boost)

    # ---- 黄色抑制 ----
    yellow = (hsv[:, :, 0] > 20) & (hsv[:, :, 0] < 40)
    hsv[:, :, 0][yellow] -= st.session_state.yellow_reduce * 10

    # ---- 青寄せ ----
    hsv[:, :, 0] += st.session_state.cool_strength * 10

    # ---- 白飛び防止 ----
    v = hsv[:, :, 2]
    mask = v * 255 > st.session_state.highlight_th
    hsv[:, :, 2][mask] = (
        st.session_state.highlight_th / 255 +
        (v[mask] - st.session_state.highlight_th / 255) * st.session_state.highlight_str
    )
    hsv[:, :, 1][mask] *= 0.5  # 白濁防止

    hsv = np.clip(hsv, 0, 1)

    img = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    # ---- コントラスト ----
    img = (img - 0.5) * st.session_state.contrast + 0.5

    # ---- シャープ ----
    kernel = np.array([
        [0, -1, 0],
        [-1, 5 + st.session_state.sharp, -1],
        [0, -1, 0]
    ])
    img = cv2.filter2D(img, -1, kernel)

    return np.clip(img, 0, 1)


# =========================
# UI
# =========================
st.title("🍳 料理フォトエディター（ピザ用）")

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
    img = Image.open(uploaded_file).convert("RGB")
    result = process(img)

    col1, col2 = st.columns(2)
    col1.image(img, caption="Before", use_container_width=True)
    col2.image(result, caption="After", use_container_width=True)

    buf = io.BytesIO()
    Image.fromarray((result*255).astype(np.uint8)).save(buf, format="JPEG", quality=95)

    st.download_button(
        "ダウンロード",
        buf.getvalue(),
        file_name="edited.jpg",
        mime="image/jpeg"
    )
