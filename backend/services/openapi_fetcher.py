# backend/services/openapi_fetcher.py

import httpx
import yaml
import json
import copy
from pathlib import Path


def _resolve_schema_ref(ref_schema: dict, openapi_spec: dict, visited_refs: set = None) -> dict:
    """
    Recursively resolves $ref references within an OpenAPI schema snippet.
    """
    if visited_refs is None:
        visited_refs = set()

    if "$ref" in ref_schema:
        ref_path = ref_schema["$ref"]
        if ref_path in visited_refs:
            return {"$ref": ref_path, "description": "Circular reference detected"}

        visited_refs.add(ref_path)
        path_parts = ref_path.lstrip("#/").split("/")
        
        resolved_definition = openapi_spec
        try:
            for part in path_parts:
                resolved_definition = resolved_definition[part]
        except (KeyError, TypeError):
            return {"description": f"Error: Reference '{ref_path}' not found", **ref_schema}
        
        resolved_definition = _resolve_schema_ref(copy.deepcopy(resolved_definition), openapi_spec, visited_refs)
        visited_refs.remove(ref_path)
        return resolved_definition
    
    if isinstance(ref_schema, dict):
        new_schema = copy.deepcopy(ref_schema)
        for key, value in ref_schema.items():
            if isinstance(value, dict) and "$ref" in value:
                new_schema[key] = _resolve_schema_ref(value, openapi_spec, visited_refs)
            elif isinstance(value, dict):
                new_schema[key] = _resolve_schema_ref(value, openapi_spec, visited_refs)
            elif isinstance(value, list):
                new_list = []
                for item in value:
                    new_list.append(_resolve_schema_ref(item, openapi_spec, visited_refs))
                new_schema[key] = new_list
        return new_schema
        
    return ref_schema


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


def extract_api_endpoints(spec: dict):
    """
    Extracts API endpoints from a parsed OpenAPI 3.0 specification.

    Args:
        spec (dict): The parsed OpenAPI specification.

    Returns:
        list: A list of dictionaries, each representing an API endpoint.
    """
    endpoints = []
    paths = spec.get("paths", {})
    for path, path_item in paths.items():
        for method, operation in path_item.items():
            if method in ["get", "put", "post", "delete", "patch", "head", "options", "trace"]:
                # Resolve parameters
                resolved_parameters = []
                for param in operation.get("parameters", []):
                    param_copy = copy.deepcopy(param)
                    if "schema" in param_copy:
                        param_copy["schema"] = _resolve_schema_ref(param_copy["schema"], spec)
                    resolved_parameters.append(param_copy)

                # Resolve request body
                resolved_request_body = None
                req_body = operation.get("requestBody")
                if req_body:
                    req_body_copy = copy.deepcopy(req_body)
                    content = req_body_copy.get("content", {})
                    for media_type in content.values():
                        if "schema" in media_type:
                            media_type["schema"] = _resolve_schema_ref(media_type["schema"], spec)
                    resolved_request_body = req_body_copy

                endpoints.append({
                    "path": path,
                    "method": method.upper(),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "operationId": operation.get("operationId", ""),
                    "parameters": resolved_parameters,
                    "requestBody": resolved_request_body
                })
    return endpoints

