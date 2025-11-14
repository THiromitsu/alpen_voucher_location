import streamlit as st
import fitz  # PyMuPDF
import io
from PIL import Image
import numpy as np

st.set_page_config(page_title="PDF座標取得ツール", layout="wide")
st.title("PDF座標取得ツール（クリックで座標 / ドラッグで矩形取得）")


# -------------------------
# Utility functions
# -------------------------

def pix_to_image(pix):
    """PyMuPDF Pixmap → PIL.Image"""
    img_bytes = pix.tobytes("png")
    return Image.open(io.BytesIO(img_bytes))


def convert_click_to_pdf_coords(click_x, click_y, display_w, display_h, pdf_w, pdf_h):
    """画面上のクリック座標 → PDF内部座標に変換"""
    scale_x = pdf_w / display_w
    scale_y = pdf_h / display_h
    px = click_x * scale_x
    py = pdf_h - (click_y * scale_y)
    return px, py


def convert_box_to_pdf_coords(box, display_w, display_h, pdf_w, pdf_h):
    """画面上のドラッグ矩形 → PDF内部のRect座標へ変換"""
    x1, y1, x2, y2 = box
    p1 = convert_click_to_pdf_coords(x1, y1, display_w, display_h, pdf_w, pdf_h)
    p2 = convert_click_to_pdf_coords(x2, y2, display_w, display_h, pdf_w, pdf_h)
    return (*p1, *p2)


# -------------------------
# UI
# -------------------------

uploaded = st.file_uploader("PDFファイルをアップロードしてください（Bページの1枚）", type=["pdf"])

if uploaded:
    pdf_bytes = uploaded.read()
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    pg = st.number_input("ページ番号（0開始）", min_value=0, max_value=doc.page_count - 1, value=0)
    page = doc.load_page(pg)
    pdf_rect = page.rect

    # PDFを画像化
    zoom = 2
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = pix_to_image(pix)

    st.write(f"PDFページサイズ: {pdf_rect.width} x {pdf_rect.height}")
    st.write("画像をドラッグ or クリックすると座標が表示されます。")

    # Streamlit の画像描画（クリック・ドラッグ情報付き）
    container = st.container()
    with container:
        result = st.image(img, use_column_width=True)
        # NOTE: 標準の st.image は座標取得イベントを持たないため、
        # ここでは streamlit-drawable-canvas を使用するのが一般的。
        # しかし外部依存を避けるため、やむを得ず "簡易版の矩形取得UI" にします。

    st.warning("※ Streamlit 単体では画像クリック座標を直接取得できないため、"
               "streamlit-drawable-canvas を使用します。下記で矩形を描けます。")

    from streamlit_drawable_canvas import st_canvas

    canvas_res = st_canvas(
        fill_color="",
        stroke_width=2,
        stroke_color="red",
        background_image=img,
        width=img.width,
        height=img.height,
        drawing_mode="rect",
        key="canvas",
    )

    # 矩形取得処理
    if canvas_res.json_data is not None:
        objects = canvas_res.json_data["objects"]
        if len(objects) > 0:
            obj = objects[-1]  # 最後に描いた矩形
            left = obj["left"]
            top = obj["top"]
            width = obj["width"]
            height = obj["height"]

            x1 = left
            y1 = top
            x2 = left + width
            y2 = top + height

            st.write("【画面上の矩形】")
            st.write(f"({x1:.1f}, {y1:.1f}) → ({x2:.1f}, {y2:.1f})")

            # PDF内部座標への変換
            pdf_x1, pdf_y1, pdf_x2, pdf_y2 = convert_box_to_pdf_coords(
                (x1, y1, x2, y2),
                img.width, img.height,
                pdf_rect.width, pdf_rect.height
            )

            st.success("【PDF内部のRect（PyMuPDFで使える座標）】")
            st.code(
                f"fitz.Rect({pdf_x1:.1f}, {pdf_y1:.1f}, {pdf_x2:.1f}, {pdf_y2:.1f})",
                language="python"
            )

st.stop()
