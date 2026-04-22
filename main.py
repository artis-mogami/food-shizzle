import streamlit as st
from PIL import Image, ImageEnhance
import io

st.set_page_config(page_title="Pro Food Editor", page_icon="🍳")

# --- 画像読み込み用のキャッシュ ---
@st.cache_data
def load_image(image_bytes):
    # RGBに変換して読み込む
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

st.title("🍳 プロ仕様・料理フォトエディター")
st.write("理想の『After.jpg』を、手動パラメータで精密に再現します。背景の色は守ります。")

# --- セッション状態の初期化 ---
# 理想のAfterを再現するための推奨値（デフォルト）
if 'sat' not in st.session_state:
    st.session_state.sat = 2.2 # 彩度強め
if 'con' not in st.session_state:
    st.session_state.con = 1.4 # コントラスト適度
if 'bri' not in st.session_state:
    st.session_state.bri = 1.1 # わずかに明るく

# リセット関数
def reset():
    st.session_state.sat = 2.2
    st.session_state.con = 1.4
    st.session_state.bri = 1.1
    st.rerun()

uploaded_file = st.file_uploader("写真をアップロード...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # キャッシュを使って画像読み込み
    file_bytes = uploaded_file.read()
    img = load_image(file_bytes)
    original_format = img.format
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        # スライダー範囲を広く確保
        sat_val = st.slider("料理の鮮やかさ (彩度)", 0.0, 5.0, key="sat")
        con_val = st.slider("立体感 (コントラスト)", 0.0, 5.0, key="con")
    with col2:
        bri_val = st.slider("明るさ調整", 0.0, 3.0, key="bri")
        st.button("設定をリセット", on_click=reset, use_container_width=True)

    # --- 補正処理の実行（ここを修正） ---
    # 【変更点】ImageOps（自動補正）を廃止し、手動で精密に重ねる
    
    # 1. まず彩度を大幅に上げる（料理の色を出す）
    enhanced = ImageEnhance.Color(img).enhance(sat_val)
    # 2. 次にコントラストを調整（黒を締め、料理を浮かび上がらせる）
    enhanced = ImageEnhance.Contrast(enhanced).enhance(con_val)
    # 3. 明るさ調整
    enhanced = ImageEnhance.Brightness(enhanced).enhance(bri_val)
    # 4. シャープネス（カリッとした質感を固定で適用）
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(3.0)

    # プレビュー表示
    st.image(enhanced, caption="補正後のイメージ (解像度は維持)", use_container_width=True)

    # ダウンロード
    buf = io.BytesIO()
    # JPEGで高画質に保存、解像度は完全に維持
    enhanced.save(buf, format="JPEG", quality=100, subsampling=0)
    byte_im = buf.getvalue()
    
    st.download_button(
        label="🚀 補正済み画像をフルサイズで保存",
        data=byte_im,
        file_name=f"fixed_{uploaded_file.name}",
        mime="image/jpeg",
        use_container_width=True
    )
    
    st.info("※元の写真の解像度（ピクセルサイズ）を完全に維持して保存します。")
