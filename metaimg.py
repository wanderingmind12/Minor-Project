import asyncio
import os
import shutil
import warnings

import aiohttp
import requests
from bs4 import BeautifulSoup

warnings.filterwarnings("ignore")


class MetadataImageCaptioner:
    def __init__(self, url, prompt_template):
        self.url = url
        self.image_folder = "images_wiki"
        self.image_data = []
        self.captions = {}
        self.prompt_template = prompt_template

    async def fetch_content(self, session, url):
        """Fetch the HTML content of a webpage."""
        try:
            async with session.get(url) as response:
                return await response.text() if response.status == 200 else None
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

    async def download_image(self, session, url):
        """Download an image and save it locally."""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    filename = os.path.basename(url)
                    filepath = os.path.join(self.image_folder, filename)
                    with open(filepath, "wb") as f:
                        f.write(await response.read())
                    return filepath, url
        except Exception as e:
            print(f"Error downloading image {url}: {e}")
        return None, url

    def generate_caption(self, context, full_description):
        """Generate a caption for an image using a placeholder model."""
        prompt = self.prompt_template.format(context=context, full_description=full_description)
        # Placeholder response; replace with actual model API call as needed
        response = f"Generated caption for '{context}': {full_description[:50]}..."  # Simulated response
        return response

    def gather_image_metadata(self, filename):
        """Fetch metadata about an image from Wikimedia or Wikipedia."""
        for base_url in ["https://commons.wikimedia.org/wiki/File:", "https://en.wikipedia.org/wiki/File:"]:
            try:
                response = requests.get(base_url + filename)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, "html.parser")
                    return soup.get_text(separator="\n", strip=True).lower()
            except Exception as e:
                print(f"Error gathering metadata: {e}")
        return ""

    async def process_images(self, show=False):
        """Fetch images from the URL, download them, and generate captions."""
        async with aiohttp.ClientSession() as session:
            html_content = await self.fetch_content(session, self.url)
            if not html_content:
                return {}
            
            self.image_data = self.extract_images(html_content)
            os.makedirs(self.image_folder, exist_ok=True)
            
            tasks = [self.download_image(session, img["link"]) for img in self.image_data]
            download_results = await asyncio.gather(*tasks)

            for file_path, url in download_results:
                if file_path:
                    filename = os.path.basename(file_path)
                    full_info = self.gather_image_metadata(filename)
                    clean_name = os.path.splitext(filename)[0]
                    description = next(
                        (img["description"] for img in self.image_data if img["link"] == url),
                        "Description not found."
                    )
                    caption = self.generate_caption(f"{clean_name} {description}", full_description=full_info)
                    if show:
                        print(f"{filename}: {caption}")
                    self.captions[url] = caption

            shutil.rmtree(self.image_folder, ignore_errors=True)
            return self.captions


if __name__ == "__main__":
    url = "https://en.wikipedia.org/wiki/James_Bond"
    prompt_template = "Context: {context}\nDescription: {full_description}"

    cap = MetadataImageCaptioner(url, prompt_template)
    captions = asyncio.run(cap.process_images(show=True))
    print(captions)
