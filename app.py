import base64
import json
import os
import re
import time
import uuid
from io import BytesIO
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
# from svgpathtools import parse_path


def hex_to_rgba(value, opacity):
    value = value.lstrip('#')
    lv = len(value)
    rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"


def page_sketch():
    st.markdown(
        """
        Instruction:
        1. Draw on the canvas
        2. Use the drawing tools at the sidebar
        3. Click transform
        """
    )

    # Drawing tools
    drawing_mode = st.sidebar.selectbox(
        "Drawing Mode:", ("freedraw", "point", "line", "rect", "polygon", "circle", "transform"),
    )
    
    col_1 = st.sidebar.columns(2)
    with col_1[0]:
        stroke_width = st.slider("Brush size", 1, 25, 2)
    with col_1[1]:
        point_display_radius = st.slider("Point radius", 1, 25, 10)
    
    col_2 = st.sidebar.columns(2)
    with col_2[0]:
        stroke_color = st.color_picker("Brush color")
    with col_2[1]:
        stroke_opacity = st.number_input(
            "Brush opacity", value=1.0, min_value=0.0, max_value=1.0, step=0.1
        )

    col_3 = st.sidebar.columns(2)
    with col_3[0]:
        fill_color = st.color_picker("Fill color", "#7D7DFF")
    with col_3[1]:
        fill_opacity = st.number_input("Fill opacity", value=1.0, min_value=0.0, max_value=1.0, step=0.1)
    

    st.sidebar.markdown(
        """
        ---
        Changing below will refesh the canvas
        """
    )
    bg_color = st.sidebar.color_picker("Canvas Background color", "#eee")
    image_uploader = st.sidebar.file_uploader("Upload image", type=["png", "jpg"])
    image_external = st.sidebar.text_input("Set online image")

    if image_uploader:
        background_image = Image.open(image_uploader) if image_uploader else None
        background_image = background_image.resize((600, 400))
        # Crop
    
    
    # Display the canvas
    canvas = st_canvas(
        fill_color=hex_to_rgba(fill_color, fill_opacity),
        stroke_width=stroke_width,
        stroke_color=hex_to_rgba(stroke_color, stroke_opacity),
        background_color=bg_color,
        background_image=background_image if image_uploader else None,
        update_streamlit=True,
        drawing_mode=drawing_mode,
        point_display_radius=point_display_radius if drawing_mode == "point" else 0,
        display_toolbar=True,
        key="canvas",
    )

    transform = st.button("Transform")

    if transform:
        with st.spinner("Transforming . . ."):
            # Display result
            doodle = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA')
            if image_uploader:
                canvas_result = Image.alpha_composite(background_image.convert('RGBA'), doodle)
            else:
                canvas_result = doodle
            st.image(canvas_result)
            


def advanced_setting():
    pass

def png_export():
    st.markdown(
        """
    Realtime update is disabled for this demo. 
    Press the 'Download' button at the bottom of canvas to update exported image.
    """
    )
    try:
        Path("tmp/").mkdir()
    except FileExistsError:
        pass

    # Regular deletion of tmp files
    # Hopefully callback makes this better
    now = time.time()
    N_HOURS_BEFORE_DELETION = 1
    for f in Path("tmp/").glob("*.png"):
        st.write(f, os.stat(f).st_mtime, now)
        if os.stat(f).st_mtime < now - N_HOURS_BEFORE_DELETION * 3600:
            Path.unlink(f)

    if st.session_state["button_id"] == "":
        st.session_state["button_id"] = re.sub(
            "\d+", "", str(uuid.uuid4()).replace("-", "")
        )

    button_id = st.session_state["button_id"]
    file_path = f"tmp/{button_id}.png"

    custom_css = f""" 
        <style>
            #{button_id} {{
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background-color: rgb(255, 255, 255);
                color: rgb(38, 39, 48);
                padding: .25rem .75rem;
                position: relative;
                text-decoration: none;
                border-radius: 4px;
                border-width: 1px;
                border-style: solid;
                border-color: rgb(230, 234, 241);
                border-image: initial;
            }} 
            #{button_id}:hover {{
                border-color: rgb(246, 51, 102);
                color: rgb(246, 51, 102);
            }}
            #{button_id}:active {{
                box-shadow: none;
                background-color: rgb(246, 51, 102);
                color: white;
                }}
        </style> """

    data = st_canvas(update_streamlit=False, key="png_export")
    if data is not None and data.image_data is not None:
        img_data = data.image_data
        im = Image.fromarray(img_data.astype("uint8"), mode="RGBA")
        im.save(file_path, "PNG")

        buffered = BytesIO()
        im.save(buffered, format="PNG")
        img_data = buffered.getvalue()
        try:
            # some strings <-> bytes conversions necessary here
            b64 = base64.b64encode(img_data.encode()).decode()
        except AttributeError:
            b64 = base64.b64encode(img_data).decode()

        dl_link = (
            custom_css
            + f'<a download="{file_path}" id="{button_id}" href="data:file/txt;base64,{b64}">Export PNG</a><br></br>'
        )
        st.markdown(dl_link, unsafe_allow_html=True)


def main():
    if "button_id" not in st.session_state:
        st.session_state["button_id"] = ""
    if "color_to_label" not in st.session_state:
        st.session_state["color_to_label"] = {}
    
    page_sketch()


if __name__ == "__main__":
    st.set_page_config(
        page_title="KidCanvas: AI for Kid Sketch", page_icon=":frame_with_picture:"
    )
    st.title("KidCanvas: AI for Kid Sketch 🖼️")
    st.sidebar.subheader("Drawing Tools")
    main()
