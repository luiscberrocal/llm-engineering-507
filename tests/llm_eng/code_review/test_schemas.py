import pytest

from llm_eng.code_review.schemas import DockerHubImage


class TestDockerHubImage:
    @pytest.mark.parametrize(
        "image",
        [
            "3.12.8-windowsservercore-ltsc2025",
            "3.12.8-windowsservercore-ltsc2022",
            "3.12.8-windowsservercore-1809",
            "3.12.8-windowsservercore",
            "3.12.8-slim-bullseye",
            "3.12.8-slim-bookworm",
            "3.12.8-alpine3.21",
            "3.12.8-alpine3.20",
            "3.12.8-alpine3.19",
        ],
    )
    def test_parse_string_python(self, image):
        """Test parsing a DockerHub image string."""
        name = "python"
        docker_image = DockerHubImage.from_string(image, name)
        assert docker_image.name == name
        assert docker_image.version == (3, 12, 8)
        assert (
            docker_image.distro == "windowsservercore-ltsc2025"
            or docker_image.distro == "windowsservercore-ltsc2022"
            or docker_image.distro == "windowsservercore-1809"
            or docker_image.distro == "windowsservercore"
            or docker_image.distro == "slim-bullseye"
            or docker_image.distro == "slim-bookworm"
            or docker_image.distro == "alpine3.21"
            or docker_image.distro == "alpine3.20"
            or docker_image.distro == "alpine3.19"
        )
        assert docker_image.image_name() == image

    @pytest.mark.parametrize(
        "image",
        [
            "3.12.0b1-windowsservercore-ltsc2025",
        ],
    )
    def test_not_parse_string_python(self, image):
        name = "python"
        docker_image = DockerHubImage.from_string(image, name)
        assert docker_image is None


    @pytest.mark.parametrize(
        "image",
        [
            "16.3-bullseye",
            "16.3-bookworm",
            "16.3-alpine3.20",
            "16.3-alpine3.19",
            "16.3-alpine3.18",
            "16.3-alpine",
        ],
    )
    def test_parse_string_postgres(self, image):
        name = "posttgres"
        docker_image = DockerHubImage.from_string(image, name)

        assert docker_image.name == name
        assert docker_image.version == (16, 3)
        assert (
            docker_image.distro == "bullseye"
            or docker_image.distro == "bookworm"
            or docker_image.distro == "alpine3.20"
            or docker_image.distro == "alpine3.19"
            or docker_image.distro == "alpine3.18"
            or docker_image.distro == "alpine"
        )
        assert docker_image.image_name() == image

    def test_ordering(self):
        images = [
            DockerHubImage(name="python", version=(3, 8, 10), distro="alpine3.2"),
            DockerHubImage(name="python", version=(3, 9), distro="bookworm"),
            DockerHubImage(name="python", version=(3, 12, 3), distro="bookworm"),
            DockerHubImage(name="python", version=(3, 8, 10), distro="bookworm"),
            DockerHubImage(name="python", version=(3, 7), distro="alpine3.2"),
        ]

        ordered_images = sorted(images, reverse=True)
        assert ordered_images[0].image_name() == "3.12.3-bookworm"
        assert ordered_images[1].image_name() == "3.9-bookworm"

