import cv2
import numpy as np

# =========================
# 画像読み込み
# =========================
img = cv2.imread("input.jpg")

if img is None:
    raise ValueError("画像が読み込めません。パスを確認してください。")

# =========================
# float化（0〜1）
# =========================
img_float = img.astype(np.float32) / 255.0

# =========================
# ① 赤みを抑える
# =========================
# OpenCVはBGRなので Rは index=2
red_strength = 0.92  # 0.90〜0.95くらいで調整
img_float[:, :, 2] *= red_strength

# =========================
# ② ハイライト圧縮（白飛び防止）
# =========================
def compress_highlight(channel, threshold=0.8, strength=0.5):
    return np.where(
        channel > threshold,
        threshold + (channel - threshold) * strength,
        channel
    )

for i in range(3):
    img_float[:, :, i] = compress_highlight(img_float[:, :, i])

# =========================
# ③ 軽いコントラスト補正
# =========================
alpha = 1.05  # コントラスト
beta = -0.02  # 明るさ微調整

img_float = img_float * alpha + beta

# =========================
# ④ クリップ処理
# =========================
img_float = np.clip(img_float, 0, 1)

# =========================
# ⑤ 8bitに戻す
# =========================
output = (img_float * 255).astype(np.uint8)

# =========================
# 保存
# =========================
cv2.imwrite("output.jpg", output)

print("保存完了: output.jpg")
