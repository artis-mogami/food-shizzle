import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io

st.set_page_config(page_title="AI Food Sizzler", page_icon="🍳")

st.title("🍳 AI×シズル感エディター")
st.write("AIアルゴリズムで料理を認識するように最適化し、理想のAfterを再現します。")

# --- セッション状態の初期化 ---
if 'sat' not in st.session_state:
    st.session_state.sat = 1.6
if 'con' not in st.session_state:
    st.session_state.con = 1.4
if 'bri' not in st.session_state:
    st.session_state.bri = 1.0

# --- リセット関数（rerunを追加して確実に反映させる） ---
def reset():
    st.session_state.sat = 1.6
    st.session_state.con = 1.4
    st.session_state.bri = 1.0
    st.rerun() 

uploaded_file = st.file_uploader("写真をアップロード...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    img = Image.open(uploaded_file).convert("RGB")
    original_format = img.format

    # --- AI風：自動最適化処理 ---
    # After.jpgの深い黒を再現するため、ピクセル統計から自動でコントラストを最大化
    img_auto = ImageOps.autocontrast(img, cutoff=0.5)
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        sat_val = st.slider("料理の鮮やかさ", 0.0, 5.0, key="sat")
        con_val = st.slider("立体感（AI自動補正に上乗せ）", 0.0, 5.0, key="con")
    with col2:
        bri_val = st.slider("明るさ調整", 0.0, 3.0, key="bri")
        # リセットボタン（クリック時にreset関数を呼び出し）
        st.button("設定をリセット", on_click=reset, use_container_width=True)

    # --- パラメータ適用 ---
    # 1. 彩度
    enhanced = ImageEnhance.Color(img_auto).enhance(sat_val)
    # 2. コントラスト
    enhanced = ImageEnhance.Contrast(enhanced).enhance(con_val)
    # 3. 明るさ
    enhanced = ImageEnhance.Brightness(enhanced).enhance(bri_val)
    # 4. シャープネス（After.jpgの質感を出すため固定で強めに設定）
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(3.5)

    # 表示
    st.image(enhanced, caption="AI最適化済みプレビュー", use_container_width=True)

    # ダウンロード
    buf = io.BytesIO()
    # 最高画質を維持
    enhanced.save(buf, format="JPEG", quality=100, subsampling=0)
    
    st.download_button(
        label="🚀 補正済み画像をフルサイズで保存",
        data=buf.getvalue(),
        file_name=f"ai_sizzled_{uploaded_file.name}",
        mime="image/jpeg",
        use_container_width=True
    )
    
    st.info("※このツールは元の画像の解像度を100%維持します。")
