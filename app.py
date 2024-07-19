
import streamlit as st
from anthropic import Anthropic
import base64
import os




# Ensure your API key is set as an environment variable or directly in the script
API_KEY = st.secrets["api_keys"]["ANTHROPIC_API_KEY"]

# Initialize the Anthropic client with the API key
if API_KEY is None:
    st.error("API key is not set. Please set the ANTHROPIC_API_KEY environment variable.")
else:
    client = Anthropic(api_key=API_KEY)
    MODEL_NAME = "claude-3-5-sonnet-20240620"



# Function to encode image to base64
def encode_image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        binary_data = image_file.read()
    return base64.b64encode(binary_data).decode('utf-8')

# Load custom CSS
def load_css(css_file_path):
    with open(css_file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Load the custom CSS
load_css("styles.css")

# Step 1: Color Analysis
st.markdown("<h1> First, lets analyse your skintone today 🔍 </h1>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload your image for color analysis", type=["jpeg", "jpg", "png"])

if uploaded_file is not None:
    # Save the uploaded file to a temporary location
    with open("temp_image.jpeg", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Encode the uploaded image
    encoded_image = encode_image_to_base64("temp_image.jpeg")

    # Prepare the image content for the request
    image_contents = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": encoded_image}}
    ]

    text_content = {
        "type": "text", 
        "text": "You are the assistant of a fashion stylist that has no time to see the image of the client. Your task is to see the image of the client and tell your boss only one of the color palettes season of the person (Autumn, winter,summer, spring) and the color of the eyes, hair and skin of the image. Write the result in this format going to a new line every time there is a comma: Color palette:, Eye Color:, Hair Color:, Skin Color:"
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

# Step 2: Outfit Recommendation (This will be executed only after the color analysis step is completed)
if 'color_analysis_result' in locals():
    # Folder with outfit pictures
    folder_path = "ZClosetbcn"

    # Get a list of all image files in the folder and sort them to ensure consistent order
    image_files = sorted([f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))])
    # Create the exact format list of image file names
    image_files_formatted = [f"{filename}" for filename in image_files]

    # Encode all images to base64
    encoded_images = [encode_image_to_base64(os.path.join(folder_path, image)) for image in image_files_formatted]

    # Prepare the image contents for the request
    image_contents = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": encoded_image}}
        for encoded_image in encoded_images
    ]

    # Display title
    st.markdown("<h1> MATCH MAKER </h1>", unsafe_allow_html=True)

    # Display images on Streamlit in four columns
    columns = st.columns(4)
    for idx, image in enumerate(image_files):
        with columns[idx % 4]:
            st.image(os.path.join(folder_path, image), width=120)

    # Streamlit text input for location
    st.markdown("<h3>Where are you going today?</h3>", unsafe_allow_html=True)
    location = st.text_input("Location and activity:", "")
    hour = st.text_input("What time?:", "")
    people = st.text_input("With who?:", "")

    # Apply inline styles to ensure font size change
    st.markdown(
        """
        <style>
        .stTextInput > div > div > input {
            font-size: 20px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Prepare the text content with user input
    text_content = {
        "type": "text",
        "text": f"You are a fashion designer. Focus only on the clothes. I will show some images in a given order, the first image is named image1.png, the second one image2.png and so on./"
                f"Your task is to tell me which image has the better outfit for the location {location} and time {hour} and the people {people} I am going with. Moreover, consider my color palette {color_analysis_result}. VERY IMPORTANT, you need to tell me as first thing the image title ONLY OF THE CHOSEN IMAGE. DO NOT SAY OTHER IMAGE NAMES and tell me why you chose the one you chose"
    }

    # Message list for the request
    message_list = [
        {"role": 'user', "content": image_contents + [text_content]}
    ]

    # Create the response when the user enters a location
    if people:
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=2048,
            messages=message_list
        )

        # Display the response and the chosen image
        if response and response.content and isinstance(response.content, list) and len(response.content) > 0:
            chosen_outfit_text = response.content[0].text
            st.write(chosen_outfit_text)
            
            # Find and display the chosen image
            chosen_image = None
            for image in image_files:
                if image in chosen_outfit_text.lower():
                    chosen_image = image
                    break
            
            if chosen_image:
                st.image(os.path.join(folder_path, chosen_image), caption="Chosen for your location", width=150)
            else:
                st.write("Could not determine the chosen outfit from the response.")
        else:
            st.write("Unexpected response format or empty response.")
