import streamlit as st
from PIL import Image, ImageEnhance
import io

st.set_page_config(page_title="Food Sizzle Maker Pro", page_icon="🍳")

st.title("🍳 料理特化型・シズル感メーカー")
st.write("料理の鮮やかさを優先して補正します。スライダーで微調整してダウンロードしてください。")

uploaded_file = st.file_uploader("写真を選択してください...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 画像読み込み
    img = Image.open(uploaded_file)
    original_format = img.format
    
    # サイドバーまたはメイン画面に調整スライダーを設置
    st.divider()
    st.subheader("🛠 補正の微調整")
    col1, col2 = st.columns(2)
    
    with col1:
        # After画像を参考に設定したデフォルト値
        sat_val = st.slider("彩度 (色の鮮やかさ)", 0.0, 3.0, 1.8) 
        con_val = st.slider("コントラスト (明暗の差)", 0.0, 3.0, 1.5)
    with col2:
        sha_val = st.slider("シャープネス (質感の強調)", 0.0, 5.0, 3.0)
        bri_val = st.slider("明るさ", 0.0, 2.0, 1.1)

    # --- 補正実行 ---
    # 料理の「色」を優先して引き上げる
    enhanced_img = ImageEnhance.Color(img).enhance(sat_val)
    # 黒を引き締め、料理を浮かび上がらせる
    enhanced_img = ImageEnhance.Contrast(enhanced_img).enhance(con_val)
    # 具材の輪郭をパキッとさせる
    enhanced_img = ImageEnhance.Sharpness(enhanced_img).enhance(sha_val)
    # 最終的な明るさ調整
    enhanced_img = ImageEnhance.Brightness(enhanced_img).enhance(bri_val)
    
    # プレビュー表示
    st.image(enhanced_img, caption="補正後のプレビュー", use_container_width=True)
    
    # --- ダウンロード ---
    buf = io.BytesIO()
    save_format = original_format if original_format else "PNG"
    # 画質を落とさないようquality=95〜100、解像度は維持
    enhanced_img.save(buf, format=save_format, quality=100, subsampling=0)
    byte_im = buf.getvalue()
    
    st.download_button(
        label="✨ この設定でフルサイズ画像を保存",
        data=byte_im,
        file_name=f"sizzled_{uploaded_file.name}",
        mime=f"image/{save_format.lower()}",
        use_container_width=True
    )
