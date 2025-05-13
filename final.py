import os
import warnings
import requests
import base64
import io
import json
from bs4 import BeautifulSoup
from PIL import Image

import requests
from io import BytesIO

warnings.filterwarnings("ignore")


class MetadataImageCaptioner:
    def __init__(self, image_url, prompt_template):
        self.image_url = image_url  # Use the image URL passed to the constructor
        self.image_folder = "images_wiki"
        self.image_data = []
        self.captions = {}
        self.prompt_template = prompt_template

    def fetch_content(self, url):
        """Fetch the HTML content of a webpage."""
        try:
            response = requests.get(url)
            return response.text if response.status_code == 200 else None
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
            return None

    def extract_images(self, html_content):
        """Extract image links and descriptions from the HTML content."""
        soup = BeautifulSoup(html_content, "html.parser")
        images = []
        for img_tag in soup.find_all("img"):
            img_src = img_tag.get("src")
            if img_src and img_src.startswith("//upload.wikimedia.org"):
                img_link = "https:" + img_src
                description = img_tag.get("alt", "No description available")
                images.append({"link": img_link, "description": description})
        return images

    def download_image(self, url):
        """Download an image and save it locally."""
        try:
            response = requests.get(url)
            if response.status_code == 200:
                filename = os.path.basename(url)
                filepath = os.path.join(self.image_folder, filename)
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return filepath, url
        except Exception as e:
            print(f"Error downloading image {url}: {e}")
        return None, url

    def generate_caption(self, context, full_description):
        """Generate a caption for an image using a placeholder model."""
        prompt = self.prompt_template.format(Title=context, Description=full_description)
        response = f"Generated caption for '{context}': {full_description[:50]}..."
        return response

    def gather_image_metadata(self):
        """Skip metadata gathering from the webpage, and just use the provided image URL."""
        metadata = {"title": "No title", "description": "No description"}  # Initialize metadata dictionary
        metadata["title"] = os.path.basename(self.image_url)  # Use the image filename as the title
        metadata["description"] = "Description for image not available."  # Add a default description or any info you have
        return metadata


class LlavaImageCaptioner:
    @staticmethod
    def download_image(url):
        """Downloads an image from a URL and returns a PIL Image object."""
        response = requests.get(url)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
        else:
            msg = f"Failed to download image. Status code: {response.status_code}"
            raise Exception(msg)

    @staticmethod
    def encode_image(image):
        """Encodes a PIL Image object to base64."""
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    @staticmethod
    def create_prompt(metadata, prompt_template):
        """Dynamically inserts metadata into the provided prompt template."""
        title = metadata.get("title", "No title")
        description = metadata.get("description", "No description")
        return prompt_template.format(Title=title, Description=description)

    @classmethod
    def test_model_with_image_url_and_text(cls, image_url, prompt_template, page_url, model_name, model_url):
        """Tests the model by sending an image and prompt to the API."""
        try:
            # Download the image
            image = cls.download_image(image_url)

            # Get metadata
            metadata = MetadataImageCaptioner(image_url, "").gather_image_metadata()

            # Encode the image to base64
            encoded_image = cls.encode_image(image)

            # Create the final prompt
            full_prompt = cls.create_prompt(metadata, prompt_template)
            print("Full prompt being sent to the model:")
            print(full_prompt)

            # Define the payload
            payload = json.dumps(
                {
                    "model": model_name,
                    "prompt": full_prompt,
                    "images": [encoded_image],
                    "stream": False,
                }
            )

            # Send the request to the model API
            response = requests.post(model_url, data=payload, headers={"Content-Type": "application/json"})

            # Check if the request was successful
            if response.status_code == 200:
                result = response.json()
                print("Response from model:")
                print(result["response"])
            else:
                print(f"Error: Received status code {response.status_code}")
                print(response.text)

        except Exception as e:
            print(f"An error occurred: {e}")


def select_captioner(metadata, image_url, threshold_length=100):
    """
    Selects a captioner based on various factors such as metadata, image quality, description availability,
    and description length.
    :param metadata: Dictionary containing image metadata.
    :param image_url: URL of the image for quality checks.
    :param threshold_length: Minimum length of metadata description to use the slower captioner.
    :return: Selected captioner class.
    """
    description = metadata.get("description", "")
    
    # Factor 1: Check if description is available
    if not description or description.strip() == "":
        print("Description not available, using LlavaImageCaptioner for rich caption generation.")
        return LlavaImageCaptioner
    
    # Factor 2: Length of metadata description (short descriptions use simpler captioner)
    if len(description) < threshold_length:
        print("Using llavaImageCaptioner for minimal metadata.")
        return LlavaImageCaptioner

    # Factor 3: Image resolution (high resolution implies richer captions needed)
    if is_high_resolution(image_url):
        print("Using LlavaImageCaptioner for high-resolution image.")
        return LlavaImageCaptioner

    # Factor 4: Contextual relevance (e.g., complex technical content vs. generic content)
    if is_complex_context(metadata):
        print("Using LlavaImageCaptioner for complex image context.")
        return LlavaImageCaptioner

    # Default fallback to simpler captioner if no other conditions are met
    print("Using MetadataImageCaptioner for general images.")
    return MetadataImageCaptioner


def is_high_resolution(image_url, min_width=800, min_height=600):
    """Check if an image is high resolution based on URL."""
    try:
        # Download the image
        response = requests.get(image_url)
        if response.status_code == 200:
            # Open image with PIL
            img = Image.open(BytesIO(response.content))
            width, height = img.size  # Get image dimensions
            
            # Check if the resolution meets the threshold
            if width >= min_width and height >= min_height:
                print(f"Image is high resolution: {width}x{height}")
                return True
            else:
                print(f"Image is low resolution: {width}x{height}")
                return False
        else:
            print(f"Failed to download image from {image_url}")
            return False
    except Exception as e:
        print(f"Error checking resolution for {image_url}: {e}")
        return False


def is_complex_context(metadata):
    """Check if the metadata implies a complex image (like a diagram or scientific image)."""
    # Keywords related to complex or technical content
    complex_keywords = ["diagram", "chart", "scientific", "technical", "graph", "medical", "research","Delhi"]
    
    description = metadata.get("description", "").lower()
    
    # Check if any of the complex keywords are present in the description
    if any(keyword in description for keyword in complex_keywords):
        print("Description contains complex content, using LlavaImageCaptioner.")
        return True
    else:
        print("Description does not contain complex content.")
        return False



def generate_captions(image_url, page_url, prompt_template, model_name, model_url):
    """
    Fetch metadata, select captioner, and generate a caption for the image.
    """
    # Initialize captioner
    metadata_captioner = MetadataImageCaptioner(image_url, prompt_template)

    # Fetch metadata using the provided URL
    metadata = metadata_captioner.gather_image_metadata()

    # Select appropriate captioner
    Captioner = select_captioner(metadata, image_url)

    if Captioner == LlavaImageCaptioner:
        Captioner.test_model_with_image_url_and_text(image_url, prompt_template, page_url, model_name, model_url)
    else:
        # Generate caption using the MetadataImageCaptioner
        print("Generating caption using MetadataImageCaptioner...")
        caption = metadata_captioner.generate_caption(metadata["title"], metadata["description"])
        print(f"Generated caption: {caption}")


if __name__ == "__main__":
    page_url = "https://commons.wikimedia.org/wiki/File:Narendra_Modi_and_Prime_Minister_Atal_Bihari_Vajpayee_in_New_Delhi_in_October_12,_2001.jpg"
    image_url = "https://upload.wikimedia.org/wikipedia/commons/0/0f/Narendra_Modi_and_Prime_Minister_Atal_Bihari_Vajpayee_in_New_Delhi_in_October_12%2C_2001.jpg"
    prompt_template = "What is the image of? Title: {Title}. Description: {Description}"

    model_name = "LLaVA"
    model_url = "http://127.0.0.1:5000"

    generate_captions(image_url, page_url, prompt_template, model_name, model_url)
