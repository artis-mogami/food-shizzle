import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.title("画像補正アプリ（自然な鮮やかさ＋赤抑制＋白飛び防止）")

uploaded_file = st.file_uploader("画像をアップロード", type=["jpg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file)
    img = np.array(image)

    # RGB → BGR
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # float化
    img_float = img.astype(np.float32) / 255.0

    # =========================
    # 赤み軽減
    # =========================
    img_float[:, :, 2] *= 0.93

    # =========================
    # ハイライト圧縮（白飛び防止）
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
    # 彩度強化（Vibrance風）
    # =========================
    hsv = cv2.cvtColor((img_float * 255).astype(np.uint8), cv2.COLOR_BGR2HSV).astype(np.float32)

    h, s, v = cv2.split(hsv)

    # 低彩度だけ強く上げる（自然な発色）
    s = s / 255.0
    s = s + (1 - s) * 0.35  # ←ここが重要（0.3〜0.5推奨）

    s = np.clip(s * 255, 0, 255)

    hsv = cv2.merge([h, s, v])
    img_float = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR).astype(np.float32) / 255.0

    # =========================
    # コントラスト微調整
    # =========================
    img_float = img_float * 1.05 - 0.02
    img_float = np.clip(img_float, 0, 1)

    # 出力
    output = (img_float * 255).astype(np.uint8)

    # BGR → RGB
    output = cv2.cvtColor(output, cv2.COLOR_BGR2RGB)

    st.image(output, caption="補正後", use_column_width=True)
