
# IMPORTS
import os
import shutil
import numpy as np
from PIL import Image
from transformers import CLIPProcessor, CLIPModel, BlipProcessor, BlipForConditionalGeneration
from sklearn.cluster import KMeans

# LOAD MODELS & PROCESSOR
    # BLIP - used to generate descriptive captions for images
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
    # CLIP - used to convert the generated captions into vector representations
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")


# FUNCTIONS 
#   -- to improve - (add more specifc prompt)
def generate_caption(image_path):
    image = Image.open(image_path)
    inputs = blip_processor(images=image, return_tensors="pt")
    out = blip_model.generate(**inputs)
    caption = blip_processor.decode(out[0], skip_special_tokens=True)
    return caption

def vectorize_caption(caption):
    inputs = clip_processor(text=[caption], return_tensors="pt", padding=True)
    outputs = clip_model.get_text_features(**inputs)
    return outputs.detach().numpy().flatten()

def process_images(folder_path):
    image_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(folder_path) for f in filenames if f.endswith(('.png', '.jpg', '.jpeg'))]
    captions = []
    vectors = []
    for image_file in image_files:
        caption = generate_caption(image_file)
        vector = vectorize_caption(caption)
        captions.append((image_file, caption))
        vectors.append(vector)
    return captions, np.array(vectors)


# FINAL FUNCTION 
   
def categorize_images(folder_path, target_folder_path, num_categories=5):  # change number of categories according to number of images (never go over 20 iamges per folder)

    # create the new folder where subfolders will be generated
    if not os.path.exists(target_folder_path):
        os.makedirs(target_folder_path)
    
    # create the caption of the image and the vector for that caption
    captions, vectors = process_images(folder_path)

    # Cluster images using K-means
    kmeans = KMeans(n_clusters=num_categories, random_state=0).fit(vectors)
    labels = kmeans.labels_ # in which group each image belongs to 

    # Create subfolders and distribute images
    for label in range(num_categories):
        subfolder_path = os.path.join(target_folder_path, f"subfolder_{label}")
        os.makedirs(subfolder_path, exist_ok=True)
        for (image_file, caption), image_label in zip(captions, labels):
            if image_label == label:
                shutil.copy(image_file, subfolder_path)
                with open(os.path.join(subfolder_path, f"{os.path.basename(image_file)}.txt"), 'w') as f:
                    f.write(caption)

    print(f"Images categorized into {num_categories} subfolders.")

if __name__ == "__main__":
    # Folder path with images
    folder_path = "ZClosetbcn" 
    # Target folder for subfolders
    target_folder_path = "ZClosetbcn2_categorized"   
    # Categorize images
    categorize_images(folder_path, target_folder_path, num_categories=5)
