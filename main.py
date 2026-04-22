import streamlit as st
from PIL import Image, ImageEnhance
import io
import gc  # ガベージコレクション（不要メモリの解放用）

st.set_page_config(page_title="Lightweight Food Editor", page_icon="🍳")

st.title("🍳 料理フォトエディター (メモリ節約版)")

# --- 1. パラメータの管理 ---
DEFAULTS = {'sat': 2.2, 'con': 1.4, 'bri': 1.1, 'sha': 3.0}

for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value

def reset_params():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value

st.sidebar.subheader("🛠 補正コントロール")
if st.sidebar.button("設定をリセット"):
    reset_params()

# --- 2. ファイルアップロード ---
uploaded_file = st.file_uploader("写真をアップロード...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 画像読み込み（メモリ節約のため、その都度開いて閉じる）
    uploaded_file.seek(0)
    with Image.open(uploaded_file) as img:
        img = img.convert("RGB")
        
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            sat_val = st.slider("色の鮮やかさ", 0.0, 5.0, key="sat")
            con_val = st.slider("立体感", 0.0, 5.0, key="con")
        with col2:
            sha_val = st.slider("質感の強さ", 0.0, 10.0, key="sha")
            bri_val = st.slider("明るさ調整", 0.0, 3.0, key="bri")

        # --- 3. 補正処理 ---
        # 処理ごとに新しい変数を作らず、上書きすることでメモリを節約
        img = ImageEnhance.Color(img).enhance(sat_val)
        img = ImageEnhance.Contrast(img).enhance(con_val)
        img = ImageEnhance.Brightness(img).enhance(bri_val)
        img = ImageEnhance.Sharpness(img).enhance(sha_val)

        # プレビュー表示
        st.image(img, caption="補正後のプレビュー", use_container_width=True)

        # --- 4. ダウンロード ---
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=95, subsampling=0) # 100より95の方が圧倒的に軽い
        byte_im = buf.getvalue()
        
        st.download_button(
            label="🚀 補正済み画像を保存",
            data=byte_im,
            file_name=f"fixed_{uploaded_file.name}",
            mime="image/jpeg",
            use_container_width=True
        )
        
        # 明示的にバッファをクリア
        buf.close()

    # 不要なオブジェクトを削除してメモリを強制解放
    del img
    gc.collect()

# --- 5. メモリが限界に近い時のためのヒント ---
st.sidebar.info("エラーが出る場合は、右上の『⋮』メニューから『Reboot App』を押してメモリを掃除してください。")
