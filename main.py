import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io

st.set_page_config(page_title="High-Speed Food Sizzler", page_icon="🍳")

# --- 計算負荷を減らすためのキャッシュ設定 ---
@st.cache_data
def apply_auto_fix(image_bytes):
    # 重い自動補正処理は一度だけ実行して結果を保存する
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return ImageOps.autocontrast(img, cutoff=0.5)

st.title("🍳 AI×シズル感エディター (高速版)")

if 'sat' not in st.session_state:
    st.session_state.sat = 1.6
if 'con' not in st.session_state:
    st.session_state.con = 1.4
if 'bri' not in st.session_state:
    st.session_state.bri = 1.0

def reset():
    st.session_state.sat = 1.6
    st.session_state.con = 1.4
    st.session_state.bri = 1.0
    st.rerun()

uploaded_file = st.file_uploader("写真をアップロード...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 画像データを一度読み込んでキャッシュに渡す
    file_bytes = uploaded_file.read()
    img_auto = apply_auto_fix(file_bytes)
    
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        # スライダーを離したときだけ更新したい場合は、反映まで少しラグがあるが計算回数が減る
        sat_val = st.slider("料理の鮮やかさ", 0.0, 5.0, key="sat")
        con_val = st.slider("立体感", 0.0, 5.0, key="con")
    with col2:
        bri_val = st.slider("明るさ調整", 0.0, 3.0, key="bri")
        st.button("設定をリセット", on_click=reset, use_container_width=True)

    # --- パラメータ適用（ここも最適化） ---
    # 連続して計算を重ねる
    enhanced = ImageEnhance.Color(img_auto).enhance(sat_val)
    enhanced = ImageEnhance.Contrast(enhanced).enhance(con_val)
    enhanced = ImageEnhance.Brightness(enhanced).enhance(bri_val)
    enhanced = ImageEnhance.Sharpness(enhanced).enhance(3.5)

    # プレビュー表示
    st.image(enhanced, caption="AI最適化済みプレビュー", use_container_width=True)

    # ダウンロードボタン
    buf = io.BytesIO()
    enhanced.save(buf, format="JPEG", quality=100, subsampling=0)
    st.download_button(
        label="🚀 補正済み画像をフルサイズで保存",
        data=buf.getvalue(),
        file_name=f"fast_sizzled_{uploaded_file.name}",
        mime="image/jpeg",
        use_container_width=True
    )
