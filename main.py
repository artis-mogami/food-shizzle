import streamlit as st
from PIL import Image, ImageEnhance
import io
import numpy as np
import cv2
import gc

st.set_page_config(page_title="Pizza Color Editor", page_icon="🍕")

# ----------------------------
# 初期値
# ----------------------------
DEFAULT = {
    "gamma": 0.95,
    "density": 1.05,
    "green_boost": 0.35,
    "yellow_reduce": 0.08,
    "cool": 0.04,
    "highlight_th": 235,
    "contrast": 1.2,
    "sharp": 2.3,
    "darken": 0.92,      # ★追加（全体暗く）
    "gray_mix": 0.08     # ★追加（グレー感）
}

# ----------------------------
# セッション初期化
# ----------------------------
if "params" not in st.session_state:
    st.session_state.params = DEFAULT.copy()

# ----------------------------
# 画像ロード
# ----------------------------
@st.cache_data(show_spinner=False)
def load_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

# ----------------------------
# プレビュー
# ----------------------------
def preview_resize(img, max_size=1024):
    img_copy = img.copy()
    img_copy.thumbnail((max_size, max_size))
    return img_copy

# ----------------------------
# 補正ロジック（改善版）
# ----------------------------
def process_image(img, p):
    img_np = np.array(img).astype(np.uint8)

    hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV).astype(np.float32)
    h, s, v = cv2.split(hsv)

    # ----------------------------
    # 白保護
    # ----------------------------
    low_sat = s < 40
    s[low_sat] *= 0.3

    # ----------------------------
    # 彩度
    # ----------------------------
    s *= p["density"]

    # ----------------------------
    # チーズ（黄色抑え）
    # ----------------------------
    cheese = (h > 15) & (h < 35)
    s[cheese] *= (1 - p["yellow_reduce"])
    v[cheese] *= 1.02  # ←上げすぎない

    # ----------------------------
    # 葉っぱ（濃く＆暗く）
    # ----------------------------
    green = (h > 35) & (h < 85)
    s[green] += p["green_boost"] * 255
    v[green] *= 0.8

    # ----------------------------
    # 青寄せ
    # ----------------------------
    h -= p["cool"] * 10

    # ----------------------------
    # ガンマ（弱め）
    # ----------------------------
    v = np.power(v / 255.0, p["gamma"]) * 255

    # ----------------------------
    # ★ 全体を少し暗く
    # ----------------------------
    v *= p["darken"]

    # ----------------------------
    # ★ グレー感（彩度を軽く落とす）
    # ----------------------------
    s *= (1 - p["gray_mix"])

    # ----------------------------
    # 白飛び抑制
    # ----------------------------
    highlight = v > p["highlight_th"]
    v[highlight] = p["highlight_th"] + (
        (v[highlight] - p["highlight_th"]) * 0.3
    )

    # ----------------------------
    # clip
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

    # ----------------------------
    # 質感
    # ----------------------------
    img_out = ImageEnhance.Contrast(img_out).enhance(p["contrast"])
    img_out = ImageEnhance.Sharpness(img_out).enhance(p["sharp"])

    return img_out

# ----------------------------
# UI
# ----------------------------
st.title("🍕 ピザ補正エディター（最終調整版）")

uploaded = st.file_uploader("画像アップロード", type=["jpg","png","jpeg"])

st.sidebar.header("調整")

def slider(key, label, min_v, max_v, step):
    st.session_state.params[key] = st.sidebar.slider(
        label,
        min_v,
        max_v,
        st.session_state.params[key],
        step
    )

slider("gamma", "明るさ", 0.7, 1.2, 0.01)
slider("density", "色の濃さ", 0.9, 1.3, 0.01)
slider("green_boost", "葉っぱ強化", 0.0, 0.8, 0.01)
slider("yellow_reduce", "チーズ黄ばみ除去", 0.0, 0.5, 0.01)
slider("cool", "青寄せ", 0.0, 0.08, 0.001)
slider("darken", "全体暗さ", 0.8, 1.0, 0.01)
slider("gray_mix", "グレー感", 0.0, 0.2, 0.01)

slider("highlight_th", "白飛び閾値", 220, 250, 1)
slider("contrast", "コントラスト", 1.0, 1.5, 0.01)
slider("sharp", "シャープ", 1.0, 3.5, 0.1)

# ----------------------------
# リセットボタン
# ----------------------------
if st.sidebar.button("リセット"):
    st.session_state.params = DEFAULT.copy()

params = st.session_state.params

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

    st.download_button(
        "高画質ダウンロード",
        buf.getvalue(),
        "pizza.jpg"
    )

    del img, img_out
    gc.collect()
