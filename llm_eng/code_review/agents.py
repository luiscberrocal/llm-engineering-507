import re
from pathlib import Path

from openai import OpenAI

from llm_eng.code_review.dockerhub_images import DockerHubSerializer, DockerHubClient
from llm_eng.code_review.schemas import DockerHubImage
from llm_eng.settings import IMAGE_LIST, API_KEY


def build_user_prompt(versions: list[DockerHubImage], image_type: str, distro: str) -> str:
    images = [str(image) for image in versions]
    image_list = ",".join(images)
    user_prompt = f"""Find the closest, preceding major version tag for the target tag from the following list for a 
    distribution {distro} for a {image_type}.
        Tags: [{image_list}]
        Target: '{image_list[0]}'"""
    return user_prompt

def build_system_prompt(file_path: Path) -> str:
    with open(file_path, "r") as file:
        system_prompt = file.read()
    return system_prompt


def classify_version(image_type: str, distro: str):
    file = Path(__file__).parent / "python_system_prompt.md"
    system_prompt = build_system_prompt(file_path=file)

    serializer = DockerHubSerializer(Path(__file__).parent.parent.parent / "output")
    dockerhub_client = DockerHubClient(serializer=serializer)

    all_tags = dockerhub_client.get_versions(image_type=image_type)
    print(f"Fetching '{image_type.upper()}' versions from Docker Hub...")
    config = IMAGE_LIST.get(image_type)
    image_filter = config.get("image_filter")
    filtered_tags = [tag for tag in all_tags if re.match(image_filter, str(tag))]
    tags = sorted(filtered_tags, reverse=True)

    user_prompt = build_user_prompt(versions=tags, image_type=image_type, distro=distro)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    open_ai = OpenAI(api_key=API_KEY)
    model = "gpt-4o-mini"
    response = open_ai.chat.completions.create(model=model, messages=messages)

    print(response.choices[0].message.content)
    user_prompt_file = (
        Path(__file__).parent / f"{model}_user_prompt_{image_type}_{distro.lower()}.txt"
    )
    with open(user_prompt_file, "w") as f:
        f.write(user_prompt)

if __name__ == "__main__":
    classify_version(image_type="python", distro="Debian")


