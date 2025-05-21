import re
import time
from functools import lru_cache
from pathlib import Path

import requests
import json
import logging

from llm_eng.code_review.schemas import DockerHubImage
from llm_eng.handlers import get_file_age
from llm_eng.settings import IMAGE_LIST

# Apply the logging configuration
logger = logging.getLogger("__main__")

class DockerHubSerializer:

    def __init__(self, folder_path: Path, max_age: int = 48):
        """Constructor for DockerHubSerializer.

        Args:
            folder_path (Path): The path to the folder where JSON files will be stored.
            max_age (int): The maximum age of the JSON files in hours. Default is 48 hours.
        """
        self.folder_path = folder_path
        self.max_age = max_age

    def serialize(self, images: list[DockerHubImage], image_type:str) -> Path | None:
        """
        Serializes a list of DockerHubImage objects to JSON files.

        Args:
            images (list[DockerHubImage]): List of DockerHubImage objects to serialize.
            image_type: str: The type of image to filter by (e.g., "python", "postgres").
        """

        file_path = self.folder_path / f"{image_type}.json"
        if file_path.exists() and get_file_age(file_path) < self.max_age:
            image_list = [image.model_dump() for image in images if image.name == image_type]
            with open(file_path, "w") as f:
                json.dump(image_list, f)
            return file_path
        else:
            return None

    def deserialize(self, image_type:str) -> list[DockerHubImage]:
        """
        Deserializes a JSON file to a list of DockerHubImage objects.

        Args:
            image_type: str: The type of image to filter by (e.g., "python", "postgres").
        """
        file_path = self.folder_path / f"{image_type}.json"
        if file_path.exists():
            with open(file_path, "r") as f:
                data = json.load(f)
            return [DockerHubImage(**item) for item in data]
        else:
            return []

class DockerHubClient:
    """
    A client for interacting with the Docker Hub API to fetch available Python versions (tags).
    """

    def __init__(self, serializer: DockerHubSerializer | None, base_url: str = None,page_size: int = 100):
        if base_url is None:
            # Base URL for the official Python image tags on Docker Hub V2 API
            base_url = "https://hub.docker.com/v2/repositories/library/"
        self.base_url = base_url
        self.page_size = page_size
        self.serializer = serializer

    def get_versions(self, image_type:str) -> list[DockerHubImage]:
        """
        Fetches a list of available Python versions (tags) from Docker Hub.

        Returns:
            list: A list of strings, where each string is a Python version tag.
                  Returns an empty list if an error occurs or no tags are found.
        """
        if self.serializer:
            # Check if the data is already serialized
            images = self.serializer.deserialize(image_type)
            if images:
                return images

        url = f"{self.base_url}{image_type}/tags/"
        all_tags = []
        next_page = url
        while next_page:
            try:
                # Make the GET request to the API endpoint
                # Include page_size and sort by last_updated in descending order (most recent first)
                params = {"page_size": self.page_size, "ordering": "last_updated"}
                response = requests.get(next_page, params=params)

                # Check if the request was successful (status code 200)
                response.raise_for_status()

                # Parse the JSON response
                data = response.json()

                # Extract tag names from the 'results' list
                for result in data.get("results", []):
                    tag_name = result.get("name")
                    if tag_name:
                        try:
                            image = DockerHubImage.from_string(tag_name, image_type)
                            print(f"Image {image_type} found: {image}")
                            all_tags.append(image)
                        except ValueError as e:
                            print(f"Error parsing tag name '{tag_name}': {e}")
                            continue

                # Get the URL for the next page
                next_page = data.get("next")

            except requests.exceptions.RequestException as e:
                print(f"Error fetching data from Docker Hub API: {e}")
                return all_tags
        all_tags = sorted(all_tags, reverse=True)
        if self.serializer:
            # Serialize the images to JSON files
            self.serializer.serialize(all_tags, image_type)
        return all_tags


@lru_cache(maxsize=5)
def get_versions_dockerhub(image_name: str, page_size: int = 100):
    """
    Fetches a list of available Python versions (tags) from Docker Hub.

    Args:
        page_size (int): The number of results to request per page from the API.
                         Defaults to 100.

    Returns:
        list: A list of strings, where each string is a Python version tag.
              Returns an empty list if an error occurs or no tags are found.
    """
    # Base URL for the official Python image tags on Docker Hub V2 API
    base_url = f"https://hub.docker.com/v2/repositories/library/{image_name}/tags/"
    all_tags = []
    next_page = base_url  # Start with the first page

    while next_page:
        try:
            # Make the GET request to the API endpoint
            # Include page_size and sort by last_updated in descending order (most recent first)
            params = {"page_size": page_size, "ordering": "last_updated"}
            response = requests.get(next_page, params=params)

            # Check if the request was successful (status code 200)
            response.raise_for_status()

            # Parse the JSON response
            data = response.json()

            # Extract tag names from the 'results' list
            for result in data.get("results", []):
                tag_name = result.get("name")
                if tag_name:
                    all_tags.append(tag_name)

            # Get the URL for the next page
            next_page = data.get("next")

        except requests.exceptions.RequestException as e:
            print(f"Error fetching data from Docker Hub API: {e}")
            return []  # Return empty list in case of error
        except json.JSONDecodeError:
            print("Error decoding JSON response from Docker Hub API.")
            return []  # Return empty list if JSON is invalid

    return all_tags


def get_versions(image_name: str, image_filter: str, page_size: int = 100) -> list[str]:
    """
    Fetches a list of available Python versions (tags) from Docker Hub.

    Args:
        image_name (str): The name of the Docker image to fetch versions for.
        image_filter (str): A regex pattern to filter the tags.
        page_size (int): The number of results to request per page from the API.
                         Defaults to 100.

    Returns:
        list: A list of strings, where each string is a Python version tag.
              Returns an empty list if an error occurs or no tags are found.
    """
    local_tags = get_local_versions(image_name, Path(__file__).parent, max_age=2)
    if local_tags:
        logger.debug("Using local tags")
        return sorted(local_tags, reverse=True)

    all_tags = get_versions_dockerhub(image_name, page_size)
    if image_filter:
        filtered_tags = [tag for tag in all_tags if re.match(image_filter, tag)]
    else:
        filtered_tags = all_tags
    logger.debug("TAGS: %s", len((filtered_tags)))
    tags =  sorted(filtered_tags, reverse=True)
    set_local_versions(image_name, Path(__file__).parent, tags)
    return tags


def get_local_versions(image: str, path: Path, max_age:int = 2) -> list[str]:
    """Get the local versions of a docker image."""
    json_file = path / f"{image}.json"
    age = get_file_age(json_file)
    if json_file.exists() and age < max_age:
        with open(json_file, "r") as f:
            data = json.load(f)
        return data
    else:
        return []

def set_local_versions(image: str, path: Path, data: list[str]) -> None:
    """Set the local versions of a docker image."""
    json_file = path / f"{image}.json"
    with open(json_file, "w") as f:
        json.dump(data, f)
    logger.debug("Saved %s versions to %s", image, json_file)


def old_main():
    for image in IMAGE_LIST:
        logger.debug("Testing Docker Hub API")
        print(f"Fetching {image['name']} versions from Docker Hub...")
        image_versions = get_versions(
            image["name"], image_filter=image["image_filter"]
        )  # Fetch 50 tags per page

        if image_versions:
            print(f"Found {len(image_versions)} Python versions:")
            # Print the first 20 versions as an example
            for version in image_versions:
                print(version)
            print("-" * 80)
        else:
            print("Could not retrieve Python versions.")
    print("Nama", __name__)

def main():
    serializer = DockerHubSerializer(Path(__file__).parent.parent.parent/ "output")
    dockerhub_client = DockerHubClient(serializer=serializer)
    for _, image in IMAGE_LIST.items():
        logger.debug("Testing Docker Hub API")
        start = time.time()
        print(f"Fetching {image['name']} versions from Docker Hub...")
        image_versions = dockerhub_client.get_versions(
            image["name"],
        )
        if image_versions:
            print(f"Found {len(image_versions)} Python versions:")
            # Print the first 20 versions as an example
            for version in image_versions:
                print(version)
            print("-" * 80)
        else:
            print(f"Could not find {image['name']} versions.")
        elapsed = time.time() - start
        print(f"Elapsed time: {elapsed:.2f} seconds")
        print("-" * 80)

if __name__ == "__main__":
    main()