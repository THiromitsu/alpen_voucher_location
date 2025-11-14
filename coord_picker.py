import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import io
import numpy as np
from streamlit_image_coordinates import streamlit_image_coordinates


st.set_page_config(page_title="PDF座標取得ツール", layout="wide")
st.title("PDF座標取得ツール（クリックで座標 / ドラッグで矩形）")


def pix_to_image(pix):
    img_bytes = pix.tobytes("png")
    return Image.open(io.BytesIO(img_bytes))


def convert_click_to_pdf_coords(click_x, click_y, display_w, display_h, pdf_w, pdf_h):
    scale_x = pdf_w / display_w
    scale_y = pdf_h / display_h
    px = click_x * scale_x
    py = pdf_h - (click_y * scale_y)
    return px, py


uploaded = st.file_uploader("PDFファイルをアップロード（Bページ1枚）", type=["pdf"])

if uploaded:
    pdf_bytes = uploaded.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    pg = st.number_input("ページ番号（0開始）", min_value=0, max_value=doc.page_count - 1, value=0)
    page = doc.load_page(pg)
    pdf_rect = page.rect

    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = pix_to_image(pix)

    # Streamlit Image Coordinates を使う
    st.write("画像をクリックすると PDF 内部座標に変換します。")
    coord = streamlit_image_coordinates(img)

    if coord is not None:
        x = coord["x"]
        y = coord["y"]

        st.write(f"クリック位置 (画像座標): ({x}, {y})")

        pdf_x, pdf_y = convert_click_to_pdf_coords(
            x, y, img.width, img.height, pdf_rect.width, pdf_rect.height
        )

        st.success("【PDF内部座標（PyMuPDF用）】")
        st.code(f"({pdf_x:.1f}, {pdf_y:.1f})", language="python")

