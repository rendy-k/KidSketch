import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import base64
from io import BytesIO
import requests


def hex_to_rgba(value, opacity):
    value = value.lstrip('#')
    lv = len(value)
    rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"


def page_sketch():
    st.markdown(
        """
        Instruction:
        (1) Draw on the canvas, (2) Use the drawing tools at the sidebar, (3) Click transform
        """
    )

    # Drawing tools
    drawing_mode = st.sidebar.selectbox(
        "Drawing Mode:", ("freedraw", "point", "line", "rect", "polygon", "circle", "transform"),
    )
    # !!Rename drawing mode
    
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
    # !!Selectbox for cached images in session state

    # url="https://static.vecteezy.com/system/resources/previews/009/780/776/original/cute-little-monkey-cartoon-on-tree-branch-free-vector.jpg"
    

    st.sidebar.markdown(
        """
        ---
        Made by: Rendy-K (https://github.com/rendy-k/KidCanvas)
        """
    )
    
    background_image = None
    if image_uploader:
        background_image = Image.open(image_uploader) if image_uploader else None
    elif image_external:
        background_image = Image.open(BytesIO(requests.get(image_external, stream=True).content))
    if background_image:
        width_expected = int((600/400*background_image.size[1]))
        width_factor = int((background_image.size[0] - width_expected)/2)
        background_image = background_image.crop(
            (width_factor, 0, background_image.size[0]-width_factor, background_image.size[1])
        )
        background_image = background_image.resize((600, 400))
        
    

    # Display the canvas
    canvas = st_canvas(
        fill_color=hex_to_rgba(fill_color, fill_opacity),
        stroke_width=stroke_width,
        stroke_color=hex_to_rgba(stroke_color, stroke_opacity),
        background_color=bg_color,
        background_image=background_image if background_image else None,
        update_streamlit=True,
        drawing_mode=drawing_mode,
        point_display_radius=point_display_radius if drawing_mode == "point" else 0,
        display_toolbar=True,
        key="canvas",
    )

    transform = st.button("Transform ✏️")

    if transform:
        with st.spinner("Transforming . . ."):
            # Process the input
            doodle = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA')
            if background_image:
                canvas_result = Image.alpha_composite(background_image.convert('RGBA'), doodle)
            else:
                canvas_result = doodle
            img_bg = Image.new('RGBA', (600, 400), bg_color)
            canvas_result = Image.alpha_composite(img_bg, canvas_result)
            

            # Run the model
            
            # Display result
            st.image(canvas_result) # Change to the result

            # Download
            
            in_memory = BytesIO()
            canvas_result.save(in_memory, format="PNG")
            b64 = base64.b64encode(in_memory.getvalue()).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="KidCanvas_input.png">Download input</a>'
            # href2 = f'<a href="data:application/octet-stream;base64,{b64.decode()}" download=KidCanvas_result>Download result</a>'
            st.markdown(href, unsafe_allow_html=True)
            # st.markdown(href2, unsafe_allow_html=True)


def load_model():
    pass


def advanced_setting():
    pass # Expander


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
