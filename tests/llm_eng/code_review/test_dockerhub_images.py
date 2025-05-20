import os
import tempfile
from pathlib import Path

from llm_eng.code_review.dockerhub_images import get_file_age


def test_get_file_age():
    """Test the get_file_age function."""
    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file_path = Path(temp_file.name)
        temp_file.write(b"test")
        temp_file.flush()
        temp_file.close()
    
    # Get the file age
    f = Path("/home/luiscberrocal/Downloads/Managing Multiple Django Versions with Gitflow.md")
    age = get_file_age(f)

    # Check if the age is greater than or equal to 0
    assert age >= 0

    # Clean up the temporary file
    os.remove(temp_file_path)