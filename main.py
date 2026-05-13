import streamlit as st
from PIL import Image
import numpy as np
import cv2
import io
import zipfile
import json
import matplotlib.pyplot as plt

from streamlit_image_comparison import image_comparison

# =========================
# PAGE
# =========================

st.set_page_config(
    page_title="Food Shizzle",
    layout="wide"
)

st.title("🍕 Food Shizzle")
st.caption("Food Photo Color Grading Tool")

# =========================
# DEFAULT SETTINGS
# =========================

DEFAULTS = {
    "brightness": 1.00,
    "contrast": 1.08,
    "saturation": 1.10,
    "warmth": -0.03,
    "red_boost": 0.02,
    "green_boost": 0.12,
    "green_dark": 0.88,
    "cheese_white": 0.90,
    "shadow": 1.03,
    "highlight": 0.94,
    "sharpness": 1.05,
}

# =========================
# SESSION STATE
# =========================

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# =========================
# SIDEBAR
# =========================

st.sidebar.header("🎛 Color Controls")

if st.sidebar.button("Reset"):
    for k, v in DEFAULTS.items():
        st.session_state[k] = v

for k in DEFAULTS.keys():
    st.sidebar.slider(
        k,
        min_value=0.0,
        max_value=2.0,
        key=k
    )

# =========================
# PRESET SAVE
# =========================

st.sidebar.header("💾 Preset")

preset_name = st.sidebar.text_input("Preset Name")

if st.sidebar.button("Save Preset"):

    preset = {
        k: st.session_state[k]
        for k in DEFAULTS.keys()
    }

    json_str = json.dumps(preset, indent=2)

    st.sidebar.download_button(
        "Download Preset",
        json_str,
        file_name=f"{preset_name or 'preset'}.json",
        mime="application/json"
    )

preset_file = st.sidebar.file_uploader(
    "Load Preset",
    type=["json"]
)

if preset_file:

    loaded = json.load(preset_file)

    for k in DEFAULTS.keys():
        if k in loaded:
            st.session_state[k] = float(loaded[k])

# =========================
# FUNCTIONS
# =========================

def preview_resize(img, max_width=900):

    h, w = img.shape[:2]

    if w <= max_width:
        return img

    scale = max_width / w

    new_w = int(w * scale)
    new_h = int(h * scale)

    return cv2.resize(
        img,
        (new_w, new_h),
        interpolation=cv2.INTER_AREA
    )


def apply_adjustments(img):

    img = img.astype(np.float32) / 255.0

    # brightness
    img *= st.session_state["brightness"]

    # contrast
    img = ((img - 0.5) * st.session_state["contrast"]) + 0.5

    # saturation
    hsv = cv2.cvtColor(
        (img * 255).astype(np.uint8),
        cv2.COLOR_RGB2HSV
    ).astype(np.float32)

    hsv[:, :, 1] *= st.session_state["saturation"]
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)

    img = cv2.cvtColor(
        hsv.astype(np.uint8),
        cv2.COLOR_HSV2RGB
    ).astype(np.float32) / 255.0

    # warmth
    img[:, :, 0] += st.session_state["warmth"] * 0.5
    img[:, :, 2] -= st.session_state["warmth"] * 0.5

    # red boost
    img[:, :, 0] *= (1.0 + st.session_state["red_boost"])

    # green boost
    img[:, :, 1] *= (1.0 + st.session_state["green_boost"])

    # green dark
    green_mask = (
        (img[:, :, 1] > img[:, :, 0]) &
        (img[:, :, 1] > img[:, :, 2])
    )

    img[:, :, 1][green_mask] *= st.session_state["green_dark"]

    # cheese yellow suppress
    yellow_mask = (
        (img[:, :, 0] > 0.6) &
        (img[:, :, 1] > 0.55) &
        (img[:, :, 2] < 0.5)
    )

    img[yellow_mask] *= st.session_state["cheese_white"]

    # shadows
    shadow_mask = img < 0.4
    img[shadow_mask] *= st.session_state["shadow"]

    # highlights
    highlight_mask = img > 0.7
    img[highlight_mask] *= st.session_state["highlight"]

    # sharpen
    blur = cv2.GaussianBlur(img, (0, 0), 3)

    img = cv2.addWeighted(
        img,
        1.0 + st.session_state["sharpness"],
        blur,
        -st.session_state["sharpness"],
        0
    )

    img = np.clip(img, 0, 1)

    return (img * 255).astype(np.uint8)


def create_histogram(img):

    fig, ax = plt.subplots(figsize=(5, 2))

    colors = ["r", "g", "b"]

    for i, c in enumerate(colors):

        hist = cv2.calcHist(
            [img],
            [i],
            None,
            [256],
            [0, 256]
        )

        ax.plot(hist, color=c)

    ax.set_xlim([0, 256])

    return fig


# =========================
# FILE UPLOAD
# =========================

uploaded_files = st.file_uploader(
    "Upload Images",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

# =========================
# MAIN
# =========================

if uploaded_files:

    zip_buffer = io.BytesIO()

    for uploaded_file in uploaded_files:

        image = Image.open(uploaded_file).convert("RGB")

        img = np.array(image)

        img_out = apply_adjustments(img)

        # =========================
        # PREVIEW
        # =========================

        st.subheader(uploaded_file.name)

        preview_before = preview_resize(img, 900)
        preview_after = preview_resize(img_out, 900)

        image_comparison(
            img1=preview_before,
            img2=preview_after,
            label1="Before",
            label2="After",
            width=900,
        )

        # =========================
        # HISTOGRAM
        # =========================

        with st.expander("📊 Histogram"):

            fig = create_histogram(img_out)

            st.pyplot(fig)

        # =========================
        # DOWNLOAD
        # =========================

        output = Image.fromarray(img_out)

        img_buffer = io.BytesIO()

        output.save(
            img_buffer,
            format="JPEG",
            quality=95
        )

        img_buffer.seek(0)

        out_name = uploaded_file.name.replace(
            ".jpg",
            "_graded.jpg"
        ).replace(
            ".png",
            "_graded.jpg"
        )

        st.download_button(
            f"Download {out_name}",
            img_buffer,
            file_name=out_name,
            mime="image/jpeg"
        )

        # ZIP
        with zipfile.ZipFile(zip_buffer, "a") as zipf:

            zipf.writestr(
                out_name,
                img_buffer.getvalue()
            )

    # =========================
    # ZIP DOWNLOAD
    # =========================

    st.divider()

    st.download_button(
        "📦 Download All Images ZIP",
        zip_buffer.getvalue(),
        file_name="food_shizzle_export.zip",
        mime="application/zip"
    )
