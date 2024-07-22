
# -------------------------------- MATCH MAKER --------------------------------

# STEPS OVERVIEW: 
    # 1) API SET UP (either user uploads their API or we approve ours to test)
    # 2) FUNCTION CREATION (to encode images and load style)
    # 3) INITIALIZE STREAMLIT (create simple website with Python) and ask user to upload a picture of their face AND the place where they are going, their age and other relevant attributes 
    # 4) CLAUDE(A) - IDENTIFY SEASONAL PALETTE --> With Claude cision (see Test_LLM_Reading_colors.py) and a guide we provide on PCA (See guide_to_color.txt), recognize the user season palette
    # 5) CLAUDE(B) - IDENTIFY THE CORRECT FOLDER --> Ask Claude to identify which folder is best for the situation (folders are divided by occasion such as party or office)
    # 6) CLAUDE(C) - COMBINE OUTPUTS OF C(A) AND C(B) TO FIND IDEAL OUTFIT --> Prompt to choose from the chosen folder the best image according to the PCA 
    # 7) USER HAS RECCOMENDATION


# -- REQUIREMENTS ----------------------------------------------------------------
import streamlit as st
from anthropic import Anthropic
import base64
import os

# -- API KEY SET UP ----------------------------------------------------------------

# - OPTION 1: API set directly as environment variable
# API_KEY = st.secrets["api_keys"]["ANTHROPIC_API_KEY"]
# # Initialize the Anthropic client with the API key
# if API_KEY is None:
#     st.error("API key is not set. Please set the ANTHROPIC_API_KEY environment variable.")
# else:
#     client = Anthropic(api_key=API_KEY)
#     MODEL_NAME = "claude-3-5-sonnet-20240620"
# API set directly as environment variable
API_KEY = st.secrets["api_keys"]["ANTHROPIC_API_KEY"]

# - OPTION 2: prompt user to add API key 
# Check if the user has provided an API key, otherwise default to the secret
user_claude_api_key = st.sidebar.text_input("Enter your Anthropic API Key:", placeholder="sk-...", type="password")

if "claude_model" not in st.session_state:
    st.session_state["claude_model"] = "claude-3-5-sonnet-20240620"  # Default model

if user_claude_api_key:
    # If the user has provided an API key, use it
    client = Anthropic(api_key=user_claude_api_key)
    print(f'user privided API key')
    MODEL_NAME = st.session_state["claude_model"]
else:
    if API_KEY is None:
        st.error("API key is not set. Please set the ANTHROPIC_API_KEY environment variable.")
    else:
        client = Anthropic(api_key=API_KEY)
        MODEL_NAME = st.session_state["claude_model"]

# -- FUNCTIONS --------------------------------------------------------------
# ---- Function to encode image to base64
def encode_image_to_base64(file_path):
    with open(file_path, "rb") as image_file:
        binary_data = image_file.read()
    return base64.b64encode(binary_data).decode('utf-8')

# --- Load custom CSS
def load_css(css_file_path):
    with open(css_file_path) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)


# -- START STREAMLIT ------------------------------------------------------------------------------------

# Set style for streamlit: Load the custom CSS
load_css("styles.css")

# Step 1: Personal Color Analysis (PCA)
st.markdown("<h1> First, lets analyse your skin tone today 🔍 </h1>", unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload your image for color analysis", type=["jpeg", "jpg", "png"])

if uploaded_file is not None:
    # Save the uploaded file to a temporary location
    with open("temp_image.jpeg", "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Encode the uploaded image
    encoded_image = encode_image_to_base64("temp_image.jpeg")

    # Prepare the image content for the request
    image_contents = [{"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": encoded_image}}]

    # Read Article on PCA to teach Claude about it
    with open('guide_to_color.txt', 'r') as file:
        guide_content = file.read()

    # Ask Claude to use the guide to find the season palette of the person
    text_content = {"type": "text", "text": f"You are the assistant of a fashion stylist that has no time to see the image of the client. Your task is to see the image of the client and tell your boss only one of the color palettes season of the person (Autumn, winter,summer, spring) - consider this guide on PCA for context {guide_content} and the color of the eyes, hair and skin of the image. Write the result in this format going to a new line every time there is a comma: Color palette:, Eye Color:, Hair Color:, Skin Color:"}

    message_list = [{"role": 'user', "content": image_contents + [text_content]}]

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=2048,
        messages=message_list)

    # Display the response from color analysis
    if response and response.content and isinstance(response.content, list) and len(response.content) > 0:
        color_analysis_result = response.content[0].text
        st.write(color_analysis_result)
    else:
        st.write("Unexpected response format or empty response.")
else:
    st.write("Please upload an image to continue.")


# Step 2: Outfit Recommendation according to PCA (This will be executed only after the color analysis step is completed)
if 'color_analysis_result' in locals():
    # Folder with outfit pictures
    folder_path = "ZClosetbcn"

    st.markdown("<h1> MATCH MAKER </h1>", unsafe_allow_html=True) # display title

    # # Display images on Streamlit in four columns
    # columns = st.columns(4)
    # for idx, image in enumerate(image_files):
    #     with columns[idx % 4]:
    #         st.image(os.path.join(folder_path, image), width=120)

    # Streamlit text input for location
    st.markdown("<h3>Where are you going today?</h3>", unsafe_allow_html=True)
    location = st.text_input("Location and activity:", "")
    age = st.text_input("How old are you?", "")
    preference = st.text_input("Is there any color or garment you do not like?", "")
    weather = st.text_input("Is it cold or warm?", "")

    # Choose the most appropiate subfolder according to the occasion 
    subfolders = [f.name for f in os.scandir(folder_path) if f.is_dir()]
    print(f'subfolders list:{subfolders}')
    
    if subfolders and weather:
        # prompt for finding the best folder
        text_content = f"You are a fashion designer. You have at your disposal a huge group of items to dress your client of age {age} for the occasion to go to {location} with {weather} weather. They want to avoid this {preference}. To simplify your task, all clothes have been divided into different groups. Your task is to answer ONLY WITH THE ITEM IN THE LIST subfolders: {subfolders} THAT YOU DEEM MORE APPROPRIATE FOR THE OCCASION. YOU CAN ONLY CHOOSE ONE."                          
        message_sub = [{"role": 'user', "content": text_content}]

        # invoking Claude to have the answer 
        subfolder_response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=2048,
            messages=message_sub)
        print(f'subfolder response:{subfolder_response}')

        if subfolder_response and subfolder_response.content and isinstance(subfolder_response.content, list) and len(response.content) > 0:
            chosen_folder_text = subfolder_response.content[0].text
            st.write(chosen_folder_text)
            
            # Find and display the chosen folder
            chosen_folder = None
            print(chosen_folder_text.lower())
            for folder in subfolders:
                if folder in chosen_folder_text.lower():
                    chosen_folder = folder
                    break

            if chosen_folder:
                # Update the folder_path to the chosen subfolder
                folder_path = os.path.join(folder_path, chosen_folder)
                print(folder_path)

# From the images in the subfolder selected, find the most appropiate one 
    # Get a list of all image files in the folder and sort them to ensure consistent order
    image_files = sorted([f for f in os.listdir(folder_path) if f.endswith(('.png', '.jpg', '.jpeg'))])
    print(F'IMAGES IN THE SUBFOLDER: {image_files}')
    # Create the exact format list of image file names
    image_files_formatted = sorted([f"{filename}" for filename in image_files])
    # Encode all images to base64
    encoded_images = ([encode_image_to_base64(os.path.join(folder_path, image)) for image in image_files_formatted])

    # Prepare the image contents for the request
    image_contents = [
        {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": encoded_image}}
        for encoded_image in encoded_images]

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

    # Prepare the prompt content with user input
    text_content = {
        "type": "text",
        "text": f"You are a fashion designer. Focus only on the clothes. I will show some images in a given order, the first image is named image01.png, the second one image02.png and so on./"
                f"Your task is to tell me which image has the better outfit for the client of age {age} going to the location {location} with this weather {weather}. You have to avoid {preference}. Moreover, consider my color palette {color_analysis_result}. VERY IMPORTANT, you need to tell me as first thing the image title ONLY OF THE CHOSEN IMAGE. DO NOT SAY OTHER IMAGE NAMES"
    }

    # Message list for the request
    message_list = [
        {"role": 'user', "content": image_contents + [text_content]}
    ]

    # Invoke Claude to create the response when the user enters a location
    if weather and chosen_folder:
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
            print(chosen_outfit_text.lower())
            for image in image_files:
                if image in chosen_outfit_text.lower():
                    chosen_image = image
                    break
            
            if chosen_image:
                print(chosen_image)
                st.image(os.path.join(folder_path, chosen_image), caption="Chosen for your location", width=150)
            else:
                st.write("Could not determine the chosen outfit from the response.")
        else:
            st.write("Unexpected response format or empty response.")

















