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
                    return title, metadata
            except Exception as e:
                print(f"Error fetching metadata: {e}")
        return "Unknown Title", "No metadata found."

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


if __name__ == "__main__":
    path = "https://en.wikipedia.org/wiki/James_Bond"
    scrapper = WikipediaImageScrapper(path)
    cap = MetadataImageCaptioner(path)

    single_image_caption = asyncio.run(
        cap.process_single_image("https://upload.wikimedia.org/wikipedia/commons/c/c3/Hoagy_Carmichael_-_1947.jpg")
    )
    print(single_image_caption)
