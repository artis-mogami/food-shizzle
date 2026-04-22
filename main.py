import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io
import gc

st.set_page_config(page_title="Ultimate Food Master", page_icon="🍕")

st.title("🍕 究極の料理レタッチャー (基準画像・色温度一致版)")
st.write("Before.jpgを、ご提示いただいたAfter.jpgの『温かみ』と『深い質感』に限りなく近づけます。")

# --- 1. パラメータの管理 (基準画像への最適化) ---
DEFAULTS = {
    'sat_val': 1.45,  # 彩度：バジルとトマトの鮮やかさを両立
    'con_val': 1.15,  # コントラスト：白飛びさせずに立体感を出す
    'bri_val': 0.93,  # 明るさ：全体をわずかに下げて黒を沈める
    'warmth': 1.08,   # 温かみ：赤・黄を強めて基準画像の色温度に寄せる
    'sha_val': 2.5    # 質感：具材のディテールを際立たせる
}

if 'p' not in st.session_state:
    st.session_state.p = DEFAULTS.copy()

def reset_action():
    st.session_state.p = DEFAULTS.copy()

st.sidebar.button("基準設定にリセット", on_click=reset_action)

# --- 2. ファイルアップロード ---
uploaded_file = st.file_uploader("Before.jpgをアップロード...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 画像の読み込み
    img = Image.open(uploaded_file).convert("RGB")
    
    # --- 3. 調整スライダー ---
    col1, col2 = st.columns(2)
    with col1:
        sat = st.slider("色の鮮やかさ", 0.0, 3.0, key="sat_s", value=st.session_state.p['sat_val'])
        con = st.slider("立体感 (コントラスト)", 0.0, 3.0, key="con_s", value=st.session_state.p['con_val'])
        warm = st.slider("温かみ (色温度)", 0.5, 1.5, key="warm_s", value=st.session_state.p['warmth'])
    with col2:
        sha = st.slider("質感 (シャープネス)", 0.0, 10.0, key="sha_s", value=st.session_state.p['sha_val'])
        bri = st.slider("明るさ調整", 0.0, 2.0, key="bri_s", value=st.session_state.p['bri_val'])

    # --- 4. 高度な補正ロジック ---
    # 1. 色温度の調整 (暖色系に寄せる)
    r, g, b = img.split()
    r = ImageEnhance.Brightness(r).enhance(warm)      # 赤を強調
    g = ImageEnhance.Brightness(g).enhance(1.0 + (warm-1.0)*0.5) # 黄色のために緑も少し強調
    img_colored = Image.merge("RGB", (r, g, b))

    # 2. 基本補正
    processed = ImageEnhance.Brightness(img_colored).enhance(bri)
    processed = ImageEnhance.Contrast(processed).enhance(con)
    processed = ImageEnhance.Color(processed).enhance(sat)
    
    # 3. 白飛び防止 (ハイライトのクリッピング)
    processed = ImageOps.autocontrast(processed, cutoff=(0, 2)) # 上位2%の明るさを抑える
    
    # 4. シャープネス
    processed = ImageEnhance.Sharpness(processed).enhance(sha)

    # プレビュー
    st.image(processed, caption="基準画像に近づけました", use_container_width=True)

    # --- 5. ダウンロード (サイズ・解像度維持) ---
    buf = io.BytesIO()
    processed.save(buf, format="JPEG", quality=100, subsampling=0)
    
    st.download_button(
        label="🚀 5152x5152のまま保存",
        data=buf.getvalue(),
        file_name=f"fixed_{uploaded_file.name}",
        mime="image/jpeg",
        use_container_width=True
    )
    
    del img, processed, img_colored
    gc.collect()
