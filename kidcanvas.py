import streamlit as st
from PIL import Image
from streamlit_drawable_canvas import st_canvas
import base64
from io import BytesIO
import zipfile
import requests
from diffusers import AutoPipelineForImage2Image
import torch


def hex_to_rgba(value: str, opacity: float) -> str:
    value = value.lstrip('#')
    lv = len(value)
    rgb = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
    return f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {opacity})"


def zipfile_downloader(input_prompt: str, doodle: Image, gen_images: list) -> str:
    zip_in_memory = BytesIO()
    with zipfile.ZipFile(zip_in_memory, "a", zipfile.ZIP_DEFLATED, False) as zipped:
        in_memory = BytesIO()
        doodle.save(in_memory, format="PNG")
        zipped.writestr(f"KidCanvas_{input_prompt}/input_image_{input_prompt}.png", in_memory.getvalue())

        for i, img in enumerate(gen_images):
            in_memory = BytesIO()
            img.save(in_memory, format="PNG")
            zipped.writestr(f"KidCanvas_{input_prompt}/output_image_{input_prompt}_{i+1}.png", in_memory.getvalue())
        
    b64 = base64.b64encode(zip_in_memory.getvalue()).decode()
    href = f'<a href="data:application/octet-stream;base64,{b64}" download="KidCanvas_{input_prompt}.zip">Download input</a>'
    return href


def run_model(
        input_prompt: str,
        elaborate_prompt: list,
        sketch,
        negative_prompt: str,
        seed: int,
        num_inference_steps: int,
        strength: float,
        guidance_scale: float,
    ) -> list:
    prompt = []
    for p in elaborate_prompt:
        prompt.append(input_prompt + ", " + p) 
    
    gen_images = st.session_state["model"](
        prompt=prompt,
        image=sketch,
        negative_prompt=[negative_prompt] * len(prompt),
        generator=torch.Generator(device="cuda").manual_seed(seed),
        num_images_per_prompt=1,
        num_inference_steps=num_inference_steps,
        height=400,
        width=600,
        strength=strength,
        guidance_scale=guidance_scale,
    )

    return gen_images[0]


def advanced_setting():
    with st.expander("Advanced setting"):
        with st.form("setting"):
            elaborate_prompt = st.text_area(
                "Extra prompt",
                value="realistic, high quality, detailed, colorful; cartoon, high quality, detailed; 3d animated, high quality, detailed, colorful",
                help="3 extra prompts separated by semicolon (;)"
            )
            elaborate_prompt = elaborate_prompt.split(";")
            negative_prompt = st.text_input("Negative prompt", value="distorted, deformed, disfigured, ugly")
            setting_col_1 = st.columns(1)
            with setting_col_1[0]:
                num_inference_steps = st.number_input(
                    "Number of inference steps", value=50, max_value=100, min_value=1
                )
            

            setting_col_2 = st.columns(2)
            with setting_col_2[0]:
                strength = st.number_input(
                    "Strength", value=0.6, max_value=1.0, step=0.1,
                    help="higher strength generates more different image"
                )
            with setting_col_2[1]:
                guidance_scale = st.number_input(
                    "Guidance scale", value=7.0, min_value=1.0,
                    help="higher scale generate image more align to the prompt"
                )
            
            button_setting = st.form_submit_button("Save setting")
        
        return elaborate_prompt, negative_prompt, num_inference_steps, strength, guidance_scale
        

def load_diffuser():
    # Load the model
    pipeline_img2img = AutoPipelineForImage2Image.from_pretrained(
        "runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16, variant="fp16", use_safetensors=True
    )
    pipeline_img2img.enable_model_cpu_offload()

    return pipeline_img2img


def page_sketch():
    expander_col = st.columns(2)
    with expander_col[0]:
        with st.expander("Instruction"):
            st.markdown(
                """
                Instruction:\n
                (1) Draw on the canvas\n
                (2) Use the drawing tools at the sidebar\n
                (3) Click the 'Send to streamlit' button located at the bottom left of the canvas (icon: arrow pointing down)\n
                (4) Click transform
                """
            )
    with expander_col[1]:
        (
            elaborate_prompt, negative_prompt, num_inference_steps, strength, guidance_scale
        ) = advanced_setting()

    # Drawing tools
    drawing_mode = st.sidebar.selectbox(
        "Drawing Mode:", ("freedraw", "rectangle", "polygon", "circle", "line", "point", "move"),
    )
    drawing_mode_mapper = {"rectangle": "rect", "move": "transform"}
    if drawing_mode in drawing_mode_mapper.keys():
        drawing_mode = drawing_mode_mapper[drawing_mode]
    
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
    
    st.sidebar.markdown(
        """
        ---
        Made by: Rendy-K (https://github.com/rendy-k/KidCanvas)
        """
    )
    
    canvas_height, canvas_width = 400, 600
    background_image = None
    if image_uploader:
        background_image = Image.open(image_uploader) if image_uploader else None
    elif image_external:
        background_image = Image.open(BytesIO(requests.get(image_external, stream=True).content))
    if background_image:
        width_expected = int((canvas_width/canvas_height*background_image.size[1]))
        width_factor = int((background_image.size[0] - width_expected)/2)
        background_image = background_image.crop(
            (width_factor, 0, background_image.size[0]-width_factor, background_image.size[1])
        )
        background_image = background_image.resize((canvas_width, canvas_height))
    

    # Display the canvas
    canvas = st_canvas(
        fill_color=hex_to_rgba(fill_color, fill_opacity),
        stroke_width=stroke_width,
        stroke_color=hex_to_rgba(stroke_color, stroke_opacity),
        background_color=bg_color,
        background_image=background_image if background_image else None,
        update_streamlit=False,
        drawing_mode=drawing_mode,
        point_display_radius=point_display_radius if drawing_mode == "point" else 0,
        display_toolbar=True,
        height=canvas_height,
        width=canvas_width,
        key="canvas",
    )

    # Prompt
    with st.form("input_prompt"):
        input_col = st.columns([3, 1, 1])
        with input_col[0]:
            input_prompt = st.text_input("Describe the picture", value="")
        with input_col[1]:
            include_bg = st.checkbox(
                "Include background",
                value=True, help="If unchecked, the background will not be processed"
            )
        with input_col[2]:
            manual_seed = st.number_input("Seed", value=12)
        transform = st.form_submit_button("Transform ✏️")

    if transform:
        if input_prompt != "":
            with st.spinner("Transforming . . ."):
                # Process the input
                doodle = Image.fromarray(canvas.image_data.astype('uint8'), 'RGBA')
                # Imported background
                if background_image==True and include_bg==True:
                    canvas_result = Image.alpha_composite(background_image.convert('RGBA'), doodle)
                else:
                    canvas_result = doodle
                
                # Run the model
                gen_images = run_model(
                    input_prompt, elaborate_prompt,
                    canvas_result,
                    negative_prompt,
                    manual_seed,
                    num_inference_steps,
                    strength,
                    guidance_scale,
                )
                
                # Save images to session state
                st.session_state["generated_images"].append(doodle)
                st.session_state["generated_images"].extend(gen_images)
                
                
                # Display result
                for i in gen_images:
                    st.image(i)

                # Download
                href = zipfile_downloader(input_prompt, doodle, gen_images)
                st.markdown(href, unsafe_allow_html=True)
        else:
            st.markdown("Please describe the picture")


def main():
    st.set_page_config(
        page_title="KidCanvas: AI for Kid Sketch", page_icon=":frame_with_picture:"
    )
    st.title("KidCanvas: AI for Kid Sketch 🖼️")
    st.sidebar.subheader("Drawing Tools")
    
    # Save image
    if "generated_images" not in st.session_state:
        st.session_state["generated_images"] = []

    # Load diffuser model
    if "model" not in st.session_state:
        st.session_state["model"] = None
        st.session_state["model"] = load_diffuser()
    
    page_sketch()


if __name__ == "__main__":
    main()
