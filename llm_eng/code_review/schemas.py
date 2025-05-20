from pydantic import BaseModel, Field


class DockerHubImage(BaseModel):
    """Model for Docker Hub image information."""

    name: str = Field(description="Docker Hub image name", examples=["python", "node"])
    version: int | tuple[int, int] | tuple[int, int, int] = Field(
        description="Docker Hub image version", examples=[3, (3, 8), (3, 8, 10)]
    )
    distro: str = Field(
        description="Linux or Windows distribution name",
        examples=[
            "alpine3.2",
            "bookworn",
        ],
    )

    def image_name(self):
        """Return the name of the Docker image."""
        return f"{'.'.join(map(str, self.version))}-{self.distro}"

    def __str__(self):
        return self.image_name()

    @classmethod
    def from_string(cls, string: str, name: str) -> "DockerHubImage":
        """Create a DockerHubImage instance from a string."""
        version_part, distro = string.split("-", 1)
        version = tuple(map(int, version_part.split(".")))
        return cls(name=name, version=version, distro=distro)