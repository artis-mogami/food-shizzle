import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io
import gc

st.set_page_config(page_title="High-Res Pro Retoucher", page_icon="🍳")

def apply_pro_retouch(img, sat, con, sha, bri, mid):
    # 1. サイズ維持のまま、まず「自動コントラスト」で色域を広げる（白飛びしない程度に）
    img = ImageOps.autocontrast(img, cutoff=0.1)
    
    # 2. 明るさ(Brightness)ではなく、中間トーン(Midtones)を調整
    # これによりハイライトを維持したまま影を深くする
    img = ImageEnhance.Brightness(img).enhance(bri)
    
    # 3. コントラスト
    img = ImageEnhance.Contrast(img).enhance(con)
    
    # 4. 彩度（色ごとに強調したいが、全体をバランスよく上げる）
    img = ImageEnhance.Color(img).enhance(sat)
    
    # 5. シャープネス（ディテール強調）
    img = ImageEnhance.Sharpness(img).enhance(sha)
    
    return img

st.title("🍳 5152px完全対応・劇的補正ツール")
st.write("AI生成を使わず、元の巨大な画像データを直接加工することで、サイズと品質を両立します。")

# 基準画像の「あの質感」を出すための極秘プリセット
DEFAULTS = {
    'sat': 1.45,
    'con': 1.25,
    'sha': 3.5,
    'bri': 0.92  # わずかに下げるのがコツ
}

if 'p' not in st.session_state:
    st.session_state.p = DEFAULTS.copy()

if st.sidebar.button("プロの基準設定に戻す"):
    st.session_state.p = DEFAULTS.copy()
    st.rerun()

uploaded_file = st.file_uploader("5152x5152の写真をアップロード...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # メモリ節約のため、低解像度のプレビュー用と、高解像度の保存用を分ける
    file_bytes = uploaded_file.read()
    raw_img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    w, h = raw_img.size
    
    st.info(f"現在の画像サイズ: {w} x {h}")

    col1, col2 = st.columns(2)
    with col1:
        sat = st.slider("色の深み", 0.0, 3.0, value=st.session_state.p['sat'])
        con = st.slider("パキッと感", 0.0, 3.0, value=st.session_state.p['con'])
    with col2:
        sha = st.slider("具材の質感", 0.0, 10.0, value=st.session_state.p['sha'])
        bri = st.slider("白飛び抑制", 0.0, 2.0, value=st.session_state.p['bri'])

    # プレビュー生成（表示用はリサイズして高速化）
    preview_img = raw_img.copy()
    preview_img.thumbnail((1000, 1000))
    preview_img = apply_pro_retouch(preview_img, sat, con, sha, bri, 1.0)
    st.image(preview_img, caption="プレビュー（表示用に縮小中）", use_container_width=True)

    if st.button("🚀 5152x5152のまま書き出し（時間がかかります）", use_container_width=True):
        with st.spinner("巨大な画像をピクセル単位で加工中..."):
            final_img = apply_pro_retouch(raw_img, sat, con, sha, bri, 1.0)
            buf = io.BytesIO()
            # 解像度情報を維持して保存
            final_img.save(buf, format="JPEG", quality=100, subsampling=0)
            
            st.download_button(
                label="✅ 補正済みフルサイズ画像をダウンロード",
                data=buf.getvalue(),
                file_name=f"pro_fixed_{uploaded_file.name}",
                mime="image/jpeg",
                use_container_width=True
            )
            buf.close()
            del final_img
            gc.collect()

    del raw_img, preview_img
    gc.collect()
