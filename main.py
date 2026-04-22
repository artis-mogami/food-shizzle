import streamlit as st
from PIL import Image, ImageEnhance
import io

st.set_page_config(page_title="究極の料理写真補正")
st.title("🍳 料理写真シズル感メーカー")
st.write("画像をアップするだけで、解像度を変えずに鮮やかに補正します。")

uploaded_file = st.file_uploader("料理写真を選択してください...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 画像を開く
    img = Image.open(uploaded_file)
    
    # 元の形式や解像度を保持するための準備
    format = img.format
    
    # --- 補正処理 ---
    # 彩度 1.6倍
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.6)
    
    # コントラスト 1.4倍
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.4)
    
    # シャープネス 2.5倍
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(2.5)
    
    # 明るさ 1.1倍
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.1)
    
    # 表示
    st.image(img, caption="補正後のイメージ（プレビュー）", use_container_width=True)
    
    # ダウンロードボタン
    buf = io.BytesIO()
    img.save(buf, format=format, quality=95)
    byte_im = buf.getvalue()
    
    st.download_button(
        label="✨ 補正済み画像をダウンロード（高画質のまま）",
        data=byte_im,
        file_name=f"shizzle_{uploaded_file.name}",
        mime=f"image/{format.lower()}"
    )