# --------------- NORMAL WORKING TEST --------------------------
# REQUIREMENTS
import streamlit as st
from anthropic import Anthropic
import base64
import os
# API set directly as environment variable
API_KEY = st.secrets["api_keys"]["ANTHROPIC_API_KEY"]


# Initialize the Anthropic client with the API key
if API_KEY is None:
    st.error("API key is not set. Please set the ANTHROPIC_API_KEY environment variable.")
else:
    client = Anthropic(api_key=API_KEY)
    MODEL_NAME = "claude-3-5-sonnet-20240620"


# ---------------------------------------------------------------------------------------
# FUNCTIONS (move to another file)

# Function to encode image to base64
def encode_image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        binary_data = image_file.read()
    return base64.b64encode(binary_data).decode('utf-8')

# Load custom CSS
def load_css(css_file_path):
    with open(css_file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
# ---------------------------------------------------------------------------------------

# Set style for streamlit: Load the custom CSS
load_css("styles.css")

# Step 1: Color Analysis
st.markdown("<h1> Upload an image of your face and get the HEX color of your eyes, skin and hair 🔍 </h1>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload your image for color analysis", type=["jpeg", "jpg", "png"])

if uploaded_file is not None:
    # Save the uploaded file to a temporary location
    with open("temp_image.jpeg", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Encode the uploaded image
    encoded_image = encode_image_to_base64("temp_image.jpeg")
    # print(encoded_image)

    # Prepare the image content for the request
    image_contents = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": encoded_image}}
    ]

    text_content = {
        "type": "text", 
        "text": "You are the assistant of a fashion stylist that has no time to see the image of the client. Your task is to see the image of the client and tell your boss the color of the eyes, hair and skin of the image - APROXIMATE AN AVERAGE HEX COLOR. Write the result in this format going to a new line every time there is a comma: Eye Color:, Hair Color:, Skin Color:"
    }

    message_list = [
        {"role": 'user', "content": image_contents + [text_content]}
    ]

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=2048,
        messages=message_list
    )

    # Display the response from color analysis
    if response and response.content and isinstance(response.content, list) and len(response.content) > 0:
        color_analysis_result = response.content[0].text
        st.write(color_analysis_result)
    else:
        st.write("Unexpected response format or empty response.")
else:
    st.write("Please upload an image to continue.")


