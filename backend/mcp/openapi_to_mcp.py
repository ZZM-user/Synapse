# backend/mcp/openapi_to_mcp.py

import json # For deep copying
import copy # For deep copying

def _resolve_schema_ref(ref_schema: dict, openapi_spec: dict, visited_refs: set = None) -> dict:
    """
    Recursively resolves $ref references within an OpenAPI schema snippet.

    Args:
        ref_schema (dict): The schema snippet that might contain a $ref.
        openapi_spec (dict): The full OpenAPI specification.
        visited_refs (set): A set to keep track of visited references to prevent infinite recursion.

    Returns:
        dict: The schema with $ref resolved to its actual definition.
    """
    if visited_refs is None:
        visited_refs = set()

    if "$ref" in ref_schema:
        ref_path = ref_schema["$ref"]
        if ref_path in visited_refs:
            # Handle circular reference: return a placeholder or stop recursion
            # For now, return a simplified reference to break the cycle
            return {"$ref": ref_path, "description": "Circular reference detected"}

        visited_refs.add(ref_path)

        # Example: '#/components/schemas/MyModel' -> ['components', 'schemas', 'MyModel']
        path_parts = ref_path.lstrip("#/").split("/")
        
        resolved_definition = openapi_spec
        try:
            for part in path_parts:
                resolved_definition = resolved_definition[part]
        except (KeyError, TypeError):
            # Reference not found, return original schema with error description
            return {"description": f"Error: Reference '{ref_path}' not found", **ref_schema}
        
        # Recursively resolve any $ref within the resolved definition
        resolved_definition = _resolve_schema_ref(copy.deepcopy(resolved_definition), openapi_spec, visited_refs)
        
        visited_refs.remove(ref_path) # Remove from visited after resolving this branch
        return resolved_definition
    
    # If not a ref, check nested schemas (properties, items)
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

def convert_openapi_to_mcp(openapi_spec: dict) -> dict:
    """
    Converts an OpenAPI 3.0 specification dictionary into an MCP Tools definition dictionary.

    Args:
        openapi_spec (dict): The parsed OpenAPI specification as a dictionary.

    Returns:
        dict: The converted MCP Tools definition.
    """
    mcp_tools = {
        "mcp_version": "v1", # Assuming v1 for now
        "tools": []
    }

    for path, path_item in openapi_spec.get("paths", {}).items():
        for method, operation in path_item.items():
            if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                continue # Skip non-HTTP methods or other definitions

            tool_name = operation.get("operationId")
            if not tool_name:
                # Generate a name if operationId is missing (e.g., get_users, post_items)
                tool_name = f"{method.lower()}_{path.replace('/', '_').strip('_')}"

            tool_description = operation.get("summary") or operation.get("description", "")

            input_schema = {
                "type": "object",
                "properties": {},
                "required": []
            }

            for param in operation.get("parameters", []):
                param_name = param.get("name")
                if not param_name:
                    continue

                param_schema = _resolve_schema_ref(param.get("schema", {}), openapi_spec)
                param_description = param.get("description", "")
                param_required = param.get("required", False)

                # Map OpenAPI parameter schema to MCP property
                # For now, we'll directly copy OpenAPI's type.
                # More robust type mapping will be handled in a later step.
                input_schema["properties"][param_name] = {
                    "type": param_schema.get("type"),
                    "format": param_schema.get("format"),
                    "description": param_description,
                    **{k: v for k, v in param_schema.items() if k not in ["type", "format", "description"]} # Add other schema properties
                }
                if param_required:
                    input_schema["required"].append(param_name)

            request_body = operation.get("requestBody")
            if request_body:
                content = request_body.get("content", {})
                json_content = content.get("application/json")
                if json_content and "schema" in json_content:
                    body_schema = _resolve_schema_ref(json_content["schema"], openapi_spec)
                    body_description = request_body.get("description", "Request body for the operation.")
                    body_required = request_body.get("required", False)

                    # For now, we map the entire request body as a 'body' property.
                    # The schema resolution for complex types will be handled later.
                    input_schema["properties"]["body"] = {
                        "type": "object", # The body itself is an object or its ref
                        "description": body_description,
                        **body_schema # Merge the actual resolved schema of the request body
                    }
                    if body_required:
                        input_schema["required"].append("body")



            mcp_tools["tools"].append({
                "name": tool_name,
                "description": tool_description,
                "input_schema": input_schema,
                "metadata": {
                    "path": path,
                    "method": method.upper(),
                    "operation_id": operation.get("operationId"),
                    "tags": operation.get("tags", [])
                }
            })

    return mcp_tools
