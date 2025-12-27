# backend/main.py
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from starlette.middleware.cors import CORSMiddleware

from mcp.openapi_to_mcp import convert_openapi_to_mcp
from services.openapi_fetcher import fetch_openapi_spec, extract_api_endpoints

app = FastAPI(
    title="Synapse MCP Gateway",
    description="Converts OpenAPI specifications to AI Agent callable tools (MCP format).",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock OpenAPI spec for development/testing if no URL is provided
MOCK_OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {"title": "Mock API", "version": "1.0.0"},
    "paths": {
        "/items": {
            "get": {
                "operationId": "getItems",
                "summary": "Get a list of items",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer"},
                        "description": "Limit the number of items returned"
                    }
                ],
                "responses": {
                    "200": {"description": "A list of items"}
                }
            },
            "post": {
                "operationId": "createItem",
                "summary": "Create a new item",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "price": {"type": "number"}
                                },
                                "required": ["name"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Item created"}
                }
            }
        }
    }
}


@app.get("/api/v1/endpoints")
async def get_api_endpoints(url: str = Query(..., description="URL to the OpenAPI 3.0 specification.")):
    """
    Fetches an OpenAPI 3.0 specification and returns a simplified list of its endpoints.
    """
    try:
        openapi_spec = await fetch_openapi_spec(url)
        endpoints = extract_api_endpoints(openapi_spec)
        return endpoints
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/v1/tools")
async def get_mcp_tools(openapi_url: Optional[str] = Query(
    None,
    description="URL to the OpenAPI 3.0 specification. If not provided, a mock spec will be used."
)):
    """
    Exposes converted MCP Tools from an OpenAPI 3.0 specification.
    """
    try:
        if openapi_url:
            openapi_spec = await fetch_openapi_spec(openapi_url)
        else:
            # Use the mock spec if no URL is provided
            openapi_spec = MOCK_OPENAPI_SPEC
            print("Using mock OpenAPI spec.")

        mcp_tools = convert_openapi_to_mcp(openapi_spec)
        return mcp_tools
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"OpenAPI spec file not found: {e}")
    except Exception as e:
        # Catch other potential errors during fetch or conversion
        print(f"An unexpected error occurred: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process OpenAPI spec: {e}")


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
