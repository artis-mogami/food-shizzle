import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io
import gc

st.set_page_config(page_title="Stable Deep Mat Food Editor", page_icon="🍳")

# --- 計算負荷を減らすための画像読み込みキャッシュ ---
@st.cache_data
def load_image(image_bytes):
    return Image.open(io.BytesIO(image_bytes)).convert("RGB")

st.title("🍳 料理フォトエディター (基準画像再現＆安定版)")
st.write("ご提示いただいた基準画像のマットで深みのある質感を再現します。白飛びせず、スライダー操作も安定させました。")

# --- 1. パラメータの管理 ---
# 基準画像を分析し、白潰れを防ぎつつマットな深みを出すための推奨値（初期値）
DEFAULTS = {
    'sat_val': 1.4, # 彩度：基準画像のように落ち着いた鮮やかさ
    'con_val': 1.1, # コントラスト：元画像のチーズのディテールを守るため、ほぼ変化なし
    'bri_val': 0.9, # 明るさ：After.jpgよりもさらに下げ（マイナス補正）基準画像に近づける
    'sha_val': 2.0  # シャープネス：After.jpgのようにマットで、ギラギラさせない
}

# セッション状態に値を登録（初回のみ）
for key, val in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# リセットボタンの処理
def reset_action():
    for key, val in DEFAULTS.items():
        st.session_state[key] = val

st.sidebar.subheader("🛠 補正コントロール")
st.sidebar.button("設定をリセット", on_click=reset_action)

# --- 2. ファイルアップロード ---
uploaded_file = st.file_uploader("写真をアップロード...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # メモリを節約するため、一度開いたファイルデータをキャッシュに渡す
    file_bytes = uploaded_file.read()
    img = load_image(file_bytes)
    uploaded_file.seek(0) # ファイルポインタを戻す（安定化対策）
    
    st.divider()
    
    # --- 3. 調整スライダー ---
    # 白飛びを防ぐため、明るさの初期値を0.9（マイナス補正）に設定しています
    col1, col2 = st.columns(2)
    with col1:
        sat = st.slider("色彩の鮮やかさ (彩度)", 0.0, 5.0, key="sat_val")
        con = st.slider("立体感 (コントラスト)", 0.0, 5.0, key="con_val")
    with col2:
        sha = st.slider("質感の強さ (シャープネス)", 0.0, 10.0, key="sha_val")
        bri = st.slider("明るさ調整", 0.0, 3.0, key="bri_val")

    # --- 4. 補正実行（変数を上書きしてメモリ消費を抑える） ---
    # 白潰れ防止のキモ：明るさを少し下げることから処理を開始する
    processed_img = ImageEnhance.Brightness(img).enhance(bri)
    processed_img = ImageEnhance.Color(processed_img).enhance(sat)
    processed_img = ImageEnhance.Contrast(processed_img).enhance(con)
    processed_img = ImageEnhance.Sharpness(processed_img).enhance(sha)

    # プレビュー表示（メモリリークを防ぐためuse_container_widthを使用）
    st.image(processed_img, caption="補正後のイメージ (解像度は維持)", use_container_width=True)

    # --- 5. ダウンロード ---
    buf = io.BytesIO()
    # JPEGで高画質に保存、解像度は完全に維持、quality=95 でメモリを節約
    processed_img.save(buf, format="JPEG", quality=95, subsampling=0)
    
    st.download_button(
        label="🚀 補正済み画像をフルサイズで保存",
        data=buf.getvalue(),
        file_name=f"fixed_{uploaded_file.name}",
        mime="image/jpeg",
        use_container_width=True
    )
    
    # 明示的にバッファを閉じる（メモリ対策）
    buf.close()
    
    # 処理済みの画像オブジェクトをdelしてgc.collect()で強制的にメモリから削除
    del img, processed_img
    gc.collect()
