import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.title("画像補正アプリ（赤み軽減＋白飛び防止）")

uploaded_file = st.file_uploader("画像をアップロード", type=["jpg", "png"])

if uploaded_file:
    # PILで読み込み
    image = Image.open(uploaded_file)
    img = np.array(image)

    # RGB → BGR変換（OpenCV用）
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # float化
    img_float = img.astype(np.float32) / 255.0

    # =========================
    # 赤み軽減
    # =========================
    img_float[:, :, 2] *= 0.92

    # =========================
    # ハイライト圧縮
    # =========================
    def compress_highlight(channel):
        return np.where(
            channel > 0.8,
            0.8 + (channel - 0.8) * 0.5,
            channel
        )

    for i in range(3):
        img_float[:, :, i] = compress_highlight(img_float[:, :, i])

    # =========================
    # 軽いコントラスト
    # =========================
    img_float = img_float * 1.05 - 0.02
    img_float = np.clip(img_float, 0, 1)

    # 戻す
    output = (img_float * 255).astype(np.uint8)

    # BGR → RGB
    output = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)

    # 表示
    st.image(output, caption="補正後", use_column_width=True)
