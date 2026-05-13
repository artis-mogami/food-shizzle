import streamlit as st
from PIL import Image, ImageEnhance
from streamlit_image_comparison import image_comparison

import io
import gc
import zipfile

import numpy as np
import cv2

# =========================================================
# ページ設定
# =========================================================

st.set_page_config(
    page_title="Food Shizzle",
    page_icon="🍕",
    layout="wide"
)

# =========================================================
# 初期値
# =========================================================

DEFAULT = {
    "gamma": 0.95,
    "density": 1.05,
    "green_boost": 0.35,
    "yellow_reduce": 0.08,
    "cool": 0.04,
    "highlight_th": 235,
    "contrast": 1.2,
    "sharp": 2.3,
    "darken": 0.92,
    "gray_mix": 0.08
}

PRESET_PIZZA = {
    "gamma": 0.95,
    "density": 1.07,
    "green_boost": 0.23,
    "yellow_reduce": 0.00,
    "cool": 0.06,
    "highlight_th": 224,
    "contrast": 1.33,
    "sharp": 2.30,
    "darken": 0.92,
    "gray_mix": 0.02
}

# =========================================================
# セッション初期化
# =========================================================

if "params" not in st.session_state:
    st.session_state.params = DEFAULT.copy()

# =========================================================
# LUT風フィルター
# =========================================================

LUTS = {
    "None": None,
    "Warm": {
        "r": 1.08,
        "g": 1.02,
        "b": 0.95
    },
    "Cool": {
        "r": 0.95,
        "g": 1.00,
        "b": 1.08
    },
    "Cinema": {
        "r": 1.10,
        "g": 1.00,
        "b": 0.90
    },
    "Fresh": {
        "r": 1.00,
        "g": 1.08,
        "b": 1.00
    }
}

# =========================================================
# 画像ロード
# =========================================================

@st.cache_data(show_spinner=False)
def load_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

# =========================================================
# プレビュー縮小
# =========================================================

def preview_resize(img, max_size=1400):

    img_copy = img.copy()

    img_copy.thumbnail(
        (max_size, max_size),
        Image.Resampling.LANCZOS
    )

    return img_copy

# =========================================================
# LUT適用
# =========================================================

def apply_lut(rgb, lut_name):

    lut = LUTS[lut_name]

    if lut is None:
        return rgb

    rgb = rgb.astype(np.float32)

    rgb[:, :, 0] *= lut["r"]
    rgb[:, :, 1] *= lut["g"]
    rgb[:, :, 2] *= lut["b"]

    rgb = np.clip(rgb, 0, 255)

    return rgb.astype(np.uint8)

# =========================================================
# 補正処理
# =========================================================

def process_image(img, p, lut_name="None"):

    img_np = np.array(img).astype(np.uint8)

    hsv = cv2.cvtColor(
        img_np,
        cv2.COLOR_RGB2HSV
    ).astype(np.float32)

    h, s, v = cv2.split(hsv)

    # -------------------------
    # 彩度低い部分を抑える
    # -------------------------

    low_sat = s < 40
    s[low_sat] *= 0.3

    # -------------------------
    # 色濃度
    # -------------------------

    s *= p["density"]

    # -------------------------
    # チーズ補正
    # -------------------------

    cheese = (h > 15) & (h < 35)

    s[cheese] *= (1 - p["yellow_reduce"])
    v[cheese] *= 1.02

    # -------------------------
    # 葉っぱ補正
    # -------------------------

    green = (h > 35) & (h < 85)

    s[green] += p["green_boost"] * 255
    v[green] *= 0.8

    # -------------------------
    # 青寄せ
    # -------------------------

    h -= p["cool"] * 10

    # -------------------------
    # ガンマ
    # -------------------------

    v = np.power(
        v / 255.0,
        p["gamma"]
    ) * 255

    # -------------------------
    # 暗さ
    # -------------------------

    v *= p["darken"]

    # -------------------------
    # グレー感
    # -------------------------

    s *= (1 - p["gray_mix"])

    # -------------------------
    # 白飛び抑制
    # -------------------------

    highlight = v > p["highlight_th"]

    v[highlight] = (
        p["highlight_th"]
        + (
            (v[highlight] - p["highlight_th"])
            * 0.3
        )
    )

    # -------------------------
    # clamp
    # -------------------------

    h = np.clip(h, 0, 179)
    s = np.clip(s, 0, 255)
    v = np.clip(v, 0, 255)

    hsv = cv2.merge([
        h.astype(np.uint8),
        s.astype(np.uint8),
        v.astype(np.uint8)
    ])

    rgb = cv2.cvtColor(
        hsv,
        cv2.COLOR_HSV2RGB
    )

    # -------------------------
    # LUT
    # -------------------------

    rgb = apply_lut(rgb, lut_name)

    img_out = Image.fromarray(rgb)

    # -------------------------
    # コントラスト
    # -------------------------

    img_out = ImageEnhance.Contrast(
        img_out
    ).enhance(
        p["contrast"]
    )

    # -------------------------
    # シャープ
    # -------------------------

    img_out = ImageEnhance.Sharpness(
        img_out
    ).enhance(
        p["sharp"]
    )

    return img_out

# =========================================================
# タイトル
# =========================================================

st.title("🍕 Food Shizzle")

# =========================================================
# アップロード
# =========================================================

uploaded_files = st.file_uploader(
    "画像アップロード",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

# =========================================================
# サイドバー
# =========================================================

st.sidebar.header("調整")

# -------------------------
# プリセット
# -------------------------

if st.sidebar.button("🍕おすすめフィルター"):
    st.session_state.params = PRESET_PIZZA.copy()

# -------------------------
# LUT
# -------------------------

selected_lut = st.sidebar.selectbox(
    "LUT風フィルター",
    list(LUTS.keys())
)

# -------------------------
# スライダー
# -------------------------

def slider(key, label, min_v, max_v, step):

    current_value = st.session_state.params[key]

    current_value = max(min_v, min(max_v, current_value))

    st.session_state.params[key] = st.sidebar.slider(
        label,
        min_value=min_v,
        max_value=max_v,
        value=current_value,
        step=step,
        key=key
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

# -------------------------
# リセット
# -------------------------

if st.sidebar.button("リセット"):
    st.session_state.params = DEFAULT.copy()

params = st.session_state.params

# =========================================================
# メイン処理
# =========================================================

if uploaded_files:

    zip_buffer = io.BytesIO()

    for uploaded in uploaded_files:

        # -------------------------
        # load
        # -------------------------

        img = load_image(uploaded.read())

        # -------------------------
        # process
        # -------------------------

        img_out = process_image(
            img,
            params,
            selected_lut
        )

        # -------------------------
        # preview
        # -------------------------

        before_preview = preview_resize(img, 1200)
        after_preview = preview_resize(img_out, 1200)

        # -------------------------
        # Before / After
        # -------------------------

        st.subheader(uploaded.name)

        image_comparison(
            img1=before_preview,
            img2=after_preview,
            label1="Before",
            label2="After",
            width=900,
            starting_position=50,
            show_labels=True,
            make_responsive=True
        )

        # -------------------------
        # download image
        # -------------------------

        img_buffer = io.BytesIO()

        img_out.save(
            img_buffer,
            format="JPEG",
            quality=95,
            subsampling=0
        )

        st.download_button(
            f"{uploaded.name} をDL",
            data=img_buffer.getvalue(),
            file_name=f"edited_{uploaded.name}.jpg",
            mime="image/jpeg"
        )

        # -------------------------
        # zip
        # -------------------------

        with zipfile.ZipFile(
            zip_buffer,
            "a",
            zipfile.ZIP_DEFLATED
        ) as zipf:

            zipf.writestr(
                f"edited_{uploaded.name}.jpg",
                img_buffer.getvalue()
            )

        # -------------------------
        # cleanup
        # -------------------------

        del img
        del img_out

        gc.collect()

    # =====================================================
    # ZIP DL
    # =====================================================

    st.divider()

    st.download_button(
        "📦 一括ZIPダウンロード",
        data=zip_buffer.getvalue(),
        file_name="food_shizzle_export.zip",
        mime="application/zip"
    )
