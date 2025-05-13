import os
import warnings
import requests
import base64
import io
import json
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO
import time

warnings.filterwarnings("ignore")

import asyncio
import os
import shutil
import warnings

import aiohttp
import requests
from bs4 import BeautifulSoup
import ollama

warnings.filterwarnings("ignore")


class WikipediaImageScrapper:
    """Simple scrapper for fetching image data from Wikipedia pages."""

    def __init__(self, url):
        self.url = url

    async def fetch_content(self, session, url):
        """Fetch HTML content from a URL asynchronously."""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.text()
        except Exception as e:
            print(f"Error fetching content from {url}: {e}")
        return None

    def get_all_images(self, html_content):
        """Extract image information from HTML content."""
        soup = BeautifulSoup(html_content, "html.parser")
        images = soup.find_all("img")
        return [
            {"link": img["src"].strip("//"), "description": img.get("alt", "No description available.")}
            for img in images if "src" in img.attrs
        ]

    def is_image_link(self, link):
        """Check if the link is an image link."""
        return link.endswith((".jpg", ".jpeg", ".png", ".gif"))

    async def download_image(self, session, url):
        """Download an image from a URL asynchronously."""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    filename = os.path.basename(url)
                    file_path = os.path.join("images_wiki", filename)
                    with open(file_path, "wb") as f:
                        f.write(await response.read())
                    return file_path, url
        except Exception as e:
            print(f"Error downloading image from {url}: {e}")
        return None, None

    @staticmethod
    def clean_filename(filename):
        """Clean filename by removing its extension."""
        return os.path.splitext(filename)[0]


class MetadataImageCaptioner:
    """Generate captions for images using title and metadata."""

    def __init__(self, url):
        self.url = url
        self.image_folder = "images_wiki"
        self.captions = {}

    def generate_caption(self, context, full_description):
        """Generate a caption for an image using the LLM model."""
        prompt = (
            "You are an intelligent assistant. Based on the given title and metadata, "
            "generate a descriptive caption for the image. Title: {context}. Metadata: {full_description}."
        ).format(context=context, full_description=full_description)

        try:
            print("Generated prompt:", prompt)  # Debugging
            response = ollama.generate(model="wizardlm2", prompt=prompt)
            return response.get("response", "No response generated.")
        except Exception as e:
            print(f"Error generating caption: {e}")
            return "Caption generation failed."

    def gather_image_metadata(self, filename):
        """Gather metadata about an image from Wikimedia or Wikipedia."""
        for base_url in ["https://commons.wikimedia.org/wiki/File:", "https://en.wikipedia.org/wiki/File:"]:
            try:
                response = requests.get(base_url + filename)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    title = soup.find("h1", {"id": "firstHeading"}).get_text(strip=True) if soup.find("h1", {"id": "firstHeading"}) else "Unknown Title"
                    metadata = soup.find("div", {"class": "description"}).get_text(strip=True) if soup.find("div", {"class": "description"}) else "No metadata found."
                    return {"title": title, "description": metadata}
            except Exception as e:
                print(f"Error fetching metadata: {e}")
        return {"title": "Unknown Title", "description": "No metadata found."}


    async def process_single_image(self, image_url):
        """Process a single image URL asynchronously and return a dictionary with the image URL as the key and the generated caption as the value."""
        async with aiohttp.ClientSession() as session:
            os.makedirs(self.image_folder, exist_ok=True)
            scrapper = WikipediaImageScrapper(self.url)
            file_path, url = await scrapper.download_image(session, image_url)
            if not file_path:
                return {}

            filename = os.path.basename(file_path)
            title, metadata = self.gather_image_metadata(filename)
            caption = self.generate_caption(title, full_description=metadata)
            self.captions[url] = caption

            shutil.rmtree(self.image_folder, ignore_errors=True)
            return self.captions












def select_captioner(metadata, image_url, threshold_length=20):
    start_time = time.time() 
    """
    Selects a captioner based on metadata, image quality, and other factors.
    :param metadata: Dictionary containing image metadata.
    :param image_url: URL of the image for quality checks.
    :param threshold_length: Minimum length of metadata description for using simpler captioners.
    :return: Selected captioner class.
    """
    description = metadata.get("description", "").strip()
    title = metadata.get("title", "").strip()

    # Debug: Print metadata fields
    print(f"Debug - Description: '{description}', Title: '{title}'")

    # Step 1: If either title or description is missing, use LlavaImageCaptioner
    if not description or not title:
        print("Either description or title is missing, using LlavaImageCaptioner for rich caption generation.")
        elapsed_time = time.time() - start_time
        print(f"Execution time: {elapsed_time:.6f} seconds")

        return LlavaImageCaptioner

    # Step 2: Proceed to other factors if both title and description are available
    # Factor 1: If the description is short (based on threshold length), use LlavaImageCaptioner
    if len(description) < threshold_length:
        print(" using LlavaImageCaptioner for rich caption generation.")
        elapsed_time = time.time() - start_time
        print(f"Execution time: {elapsed_time:.6f} seconds")
        return LlavaImageCaptioner

    # Factor 2: Check if image resolution is high, use LlavaImageCaptioner for high-res images
    if is_high_resolution(image_url):
        print("Using LlavaImageCaptioner for high-resolution image.")
        elapsed_time = time.time() - start_time
        print(f"Execution time: {elapsed_time:.6f} seconds")
        return LlavaImageCaptioner

    # Factor 3: If metadata indicates a complex context, use LlavaImageCaptioner
    if is_complex_context(metadata):
        print("Using LlavaImageCaptioner for complex image context.")
        elapsed_time = time.time() - start_time
        print(f"Execution time: {elapsed_time:.6f} seconds")
        return LlavaImageCaptioner

    # Final fallback: Use MetadataImageCaptioner
    print("Using MetadataImageCaptioner for general images.")
    elapsed_time = time.time() - start_time
    print(f"Execution time: {elapsed_time:.6f} seconds")
    return MetadataImageCaptioner


def is_high_resolution(image_url, min_width=1600, min_height=1600):
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
    def gather_image_metadata(image_url):
        """Fetches and returns metadata for an image from a Wikipedia/Wikimedia URL."""
        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                metadata = {}

                # Extract title
                title_tag = soup.find("h1", {"id": "firstHeading"})
                metadata["title"] = title_tag.text if title_tag else "No title"

                # Extract description (first paragraph)
                description_tag = soup.find("div", {"class": "description"})
                if description_tag:
                    paragraph = description_tag.find("p")
                    metadata["description"] = paragraph.text if paragraph else "No description"
                else:
                    metadata["description"] = "No description"

                print(f"Title: {metadata['title']}")
                print(f"Description: {metadata['description']}")
            else:
                print(f"Failed to fetch metadata, status code: {response.status_code}")
                metadata = {"title": "No title", "description": "No description"}

        except Exception as e:
            print(f"Error fetching metadata: {str(e)}")
            metadata = {"title": "No title", "description": "No description"}

        return metadata

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
            metadata = cls.gather_image_metadata(page_url)

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
def is_complex_context(metadata):
    """Check if the metadata implies a complex image (like a diagram or scientific image)."""
    # Keywords related to complex or technical content
    complex_keywords = ["data visualization","visualizations","data-driven images","plots","diagram", "chart", "scientific", "technical", "graph", "medical", "research", 
        "algorithm", "experiment", "data", "simulation", "genetics", "chemistry", "physics", 
        "map", "model", "equation", "code snippet", "infographic", "flowchart", 
        "study", "theory", "hypothesis", "analysis", "vector", "SVG", "historical", 
        "geography", "archaeological", "expedition", "journal", "conference", "paper", "patent", 
        "published", "resolution"]
    
    # Get both the description and title from metadata (converted to lowercase)
    description = metadata.get("description", "").lower()
    title = metadata.get("title", "").lower()

    # Check if any of the complex keywords are present in either the description or title
    if any(keyword in description for keyword in complex_keywords) or any(keyword in title for keyword in complex_keywords):
        print("Description or title contains complex content, using LlavaImageCaptioner.")
        return True
    else:
        print("Description and title do not contain complex content.")
        return False



def generate_captions(image_url, page_url, prompt_template, model_name, model_url):
    """
    Fetch metadata, select captioner, and generate a caption for the image.
    """
    # Initialize captioner
    metadata_captioner = MetadataImageCaptioner(page_url)

    # Extract the filename from the image URL
    filename = os.path.basename(image_url)

    # Fetch metadata using the filename
    metadata_text = metadata_captioner.gather_image_metadata(filename)
    # Fix here: Use 'description' from metadata_text
    metadata = {"title": "No title", "description": metadata_text.get("description", "No description")}

    # Select appropriate captioner
    Captioner = select_captioner(metadata, image_url)

    if Captioner == LlavaImageCaptioner:
        print("Using LlavaImageCaptioner for full caption generation.")
        LlavaImageCaptioner.test_model_with_image_url_and_text(
            image_url, prompt_template, page_url, model_name, model_url
        )
    else:
        print("Using MetadataImageCaptioner for simple caption generation.")
        caption = metadata_captioner.generate_caption(metadata["title"], metadata["description"])
        print("Generated Caption:", caption)




# Example usage:
page_url = "https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Images#/media/File:7.62x51_and_5.56x45_bullet_cartridges_compared_to_AA_battery.jpg"
image_url = "https://upload.wikimedia.org/wikipedia/commons/3/31/7.62x51_and_5.56x45_bullet_cartridges_compared_to_AA_battery.jpg"
    
prompt_template = "Here is the information about the image: Title: {Title} Description: {Description}"
model_name = "llama2"
model_url = "https://model-api.example.com/endpoint"

generate_captions(image_url, page_url, prompt_template, model_name, model_url)
