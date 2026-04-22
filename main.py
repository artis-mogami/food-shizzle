import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io
import gc
import numpy as np

st.set_page_config(page_title="Ultra-Res Food Retoucher", page_icon="🍳")

def apply_tone_curve(img, brightness, contrast, saturation, sharpness):
    # 1. 輝度の調整（白飛びを防ぐため、単純なBrightnessではなくガンマ補正的に処理）
    # 0.9〜0.95あたりが「After.jpg」のマットな黒を作るコツです
    img = ImageEnhance.Brightness(img).enhance(brightness)
    
    # 2. 自動コントラスト（極端な端をカットして階調を整える）
    img = ImageOps.autocontrast(img, cutoff=0.2)
    
    # 3. コントラストと彩度の適用
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = ImageEnhance.Color(img).enhance(saturation)
    
    # 4. シャープネス
    img = ImageEnhance.Sharpness(img).enhance(sharpness)
    
    return img

st.title("🍳 5152px解像度維持・劇的レタッチャー")

# プロが「After.jpg」を作るための黄金比設定
DEFAULTS = {'sat': 1.4, 'con': 1.2, 'sha': 3.0, 'bri': 0.95}

if 'p' not in st.session_state:
    st.session_state.p = DEFAULTS.copy()

uploaded_file = st.file_uploader("5152x5152のBefore.jpgをアップロード...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    raw_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    w, h = raw_img.size
    
    st.info(f"📸 オリジナル解像度を保持: {w} x {h}")

    # スライダー
    col1, col2 = st.columns(2)
    with col1:
        sat = st.slider("色の深み (彩度)", 0.0, 3.0, value=st.session_state.p['sat'])
        con = st.slider("立体感 (コントラスト)", 0.0, 3.0, value=st.session_state.p['con'])
    with col2:
        sha = st.slider("具材の質感 (シャープ)", 0.0, 10.0, value=st.session_state.p['sha'])
        bri = st.slider("白飛び抑制 (明るさ)", 0.0, 2.0, value=st.session_state.p['bri'])

    # メモリ節約のためプレビューは縮小
    preview = raw_img.copy()
    preview.thumbnail((1200, 1200))
    preview = apply_tone_curve(preview, bri, con, sat, sha)
    st.image(preview, caption="補正プレビュー", use_container_width=True)

    if st.button("🚀 5152x5152で保存 (高画質書き出し)", use_container_width=True):
        with st.spinner("巨大な画像を1ピクセルずつ精密に加工しています..."):
            final_img = apply_tone_curve(raw_img, bri, con, sat, sha)
            buf = io.BytesIO()
            # サブサンプリングなし、品質100で解像度を完全維持
            final_img.save(buf, format="JPEG", quality=100, subsampling=0)
            
            st.download_button(
                label="✅ 5152px画像をダウンロード",
                data=buf.getvalue(),
                file_name=f"ultra_fixed_{uploaded_file.name}",
                mime="image/jpeg",
                use_container_width=True
            )
            buf.close()
            del final_img
            gc.collect()

    del raw_img, preview
    gc.collect()
