import streamlit as st
from PIL import Image, ImageEnhance
import io

# ページ設定
st.set_page_config(page_title="Ultimate Food Editor", page_icon="🍳", layout="centered")

st.title("🍳 料理写真・究極シズル感エディター")
st.write("「After.jpg」の質感を再現します。料理の鮮やかさを優先して調整してください。")

# --- セッション状態の初期化（リセットボタン用） ---
if 'sat' not in st.session_state:
    st.session_state.sat = 1.8
if 'con' not in st.session_state:
    st.session_state.con = 1.6
if 'sha' not in st.session_state:
    st.session_state.sha = 3.0
if 'bri' not in st.session_state:
    st.session_state.bri = 1.0

def reset_values():
    st.session_state.sat = 1.8
    st.session_state.con = 1.6
    st.session_state.sha = 3.0
    st.session_state.bri = 1.0

# --- ファイルアップロード ---
uploaded_file = st.file_uploader("写真をアップロードしてください...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    img = Image.open(uploaded_file)
    original_format = img.format

    st.divider()
    
    # --- 調整用スライダー（調整幅を拡大） ---
    st.subheader("🛠 パラメータ微調整")
    
    col1, col2 = st.columns(2)
    with col1:
        sat_val = st.slider("色彩の鮮やかさ (彩度)", 0.0, 5.0, key="sat")
        con_val = st.slider("立体感の強調 (コントラスト)", 0.0, 5.0, key="con")
    with col2:
        sha_val = st.slider("具材の質感 (シャープネス)", 0.0, 10.0, key="sha")
        bri_val = st.slider("明るさ調整", 0.0, 3.0, key="bri")

    # リセットボタン
    st.button("値をリセットする", on_click=reset_values)

    # --- 補正処理の実行 ---
    # 1. 彩度：赤・緑・黄を劇的に強調
    enhanced_img = ImageEnhance.Color(img).enhance(sat_val)
    # 2. コントラスト：シャドウを深くし、パキッとさせる
    enhanced_img = ImageEnhance.Contrast(enhanced_img).enhance(con_val)
    # 3. シャープネス：チーズや葉脈のディテールを強調
    enhanced_img = ImageEnhance.Sharpness(enhanced_img).enhance(sha_val)
    # 4. 明るさ調整
    enhanced_img = ImageEnhance.Brightness(enhanced_img).enhance(bri_val)
    
    # プレビュー表示
    st.image(enhanced_img, caption="補正後のイメージ (解像度は維持されています)", use_container_width=True)
    
    # --- ダウンロードボタン ---
    buf = io.BytesIO()
    save_format = original_format if original_format else "PNG"
    # 高画質・解像度維持設定
    enhanced_img.save(buf, format=save_format, quality=100, subsampling=0)
    byte_im = buf.getvalue()
    
    st.download_button(
        label="🚀 補正済み画像をフルサイズで保存",
        data=byte_im,
        file_name=f"fixed_{uploaded_file.name}",
        mime=f"image/{save_format.lower()}",
        use_container_width=True
    )
    
    st.info("※ダウンロードされる画像は、元の写真のサイズ（解像度）を完全に維持しています。")
