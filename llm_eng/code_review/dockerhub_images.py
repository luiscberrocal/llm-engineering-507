import re
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import requests
import json
import logging

from llm_eng.settings import LOGGING_CONFIG, IMAGE_LIST

# Apply the logging configuration
logger = logging.getLogger("__main__")


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


def get_file_age(path: Path) -> float:
    """
    Get the age of a file in hours.

    Args:
        path (Path): The path to the file.

    Returns:
        int: The age of the file in days.
    """
    if path.exists():
        now = datetime.now().timestamp()
        return (now - path.stat().st_mtime) // 3600
    else:
        return 0.0

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

if __name__ == "__main__":
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
    logger.info("INFO ------------------")