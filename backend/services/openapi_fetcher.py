# backend/services/openapi_fetcher.py

import httpx
import yaml
import json
from pathlib import Path

async def fetch_openapi_spec(source: str):
    """
    Fetches an OpenAPI 3.0 specification from a URL or a local file path.

    Args:
        source (str): The URL or local file path to the OpenAPI spec.

    Returns:
        dict: The parsed OpenAPI specification as a dictionary.

    Raises:
        ValueError: If the source is neither a valid URL nor a file path,
                    or if the content cannot be parsed.
        httpx.HTTPStatusError: If there's an HTTP error when fetching from a URL.
        FileNotFoundError: If the specified file path does not exist.
    """
    if source.startswith("http://") or source.startswith("https://"):
        async with httpx.AsyncClient() as client:
            response = await client.get(source)
            response.raise_for_status()  # Raise an exception for bad status codes
            content = response.text
    else:
        file_path = Path(source)
        if not file_path.is_file():
            raise FileNotFoundError(f"File not found at: {source}")
        content = file_path.read_text()

    # Try parsing as JSON first, then YAML
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        try:
            return yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Could not parse OpenAPI spec content from {source}: {e}")

