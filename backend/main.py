# backend/main.py
from typing import Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Path
from starlette.middleware.cors import CORSMiddleware

from mcp.openapi_to_mcp import convert_openapi_to_mcp
from services.openapi_fetcher import fetch_openapi_spec, extract_api_endpoints
from models.combination import Combination, CombinationCreate, CombinationUpdate

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

# 内存存储（临时方案，后续可替换为数据库）
combinations_db: dict[int, Combination] = {}
combination_id_counter = 1


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


# ============= Combination Management API =============

@app.get("/api/v1/combinations", response_model=list[Combination])
async def get_combinations():
    """
    获取所有组合列表
    """
    return list(combinations_db.values())


@app.get("/api/v1/combinations/{combination_id}", response_model=Combination)
async def get_combination(combination_id: int = Path(..., description="组合 ID")):
    """
    根据 ID 获取单个组合
    """
    if combination_id not in combinations_db:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")
    return combinations_db[combination_id]


@app.post("/api/v1/combinations", response_model=Combination, status_code=201)
async def create_combination(combination: CombinationCreate):
    """
    创建新组合
    """
    global combination_id_counter

    new_combination = Combination(
        id=combination_id_counter,
        name=combination.name,
        description=combination.description,
        endpoints=combination.endpoints,
        status="active",
        createdAt=datetime.now(),
        updatedAt=datetime.now()
    )

    combinations_db[combination_id_counter] = new_combination
    combination_id_counter += 1

    return new_combination


@app.put("/api/v1/combinations/{combination_id}", response_model=Combination)
async def update_combination(
    combination_id: int = Path(..., description="组合 ID"),
    combination_update: CombinationUpdate = None
):
    """
    更新组合信息
    """
    if combination_id not in combinations_db:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    existing_combination = combinations_db[combination_id]

    # 更新字段
    if combination_update.name is not None:
        existing_combination.name = combination_update.name
    if combination_update.description is not None:
        existing_combination.description = combination_update.description
    if combination_update.endpoints is not None:
        existing_combination.endpoints = combination_update.endpoints

    existing_combination.updatedAt = datetime.now()

    return existing_combination


@app.patch("/api/v1/combinations/{combination_id}/status", response_model=Combination)
async def toggle_combination_status(
    combination_id: int = Path(..., description="组合 ID"),
    status: str = Query(..., description="新状态：active 或 inactive")
):
    """
    切换组合状态（启用/停用）
    """
    if combination_id not in combinations_db:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    if status not in ["active", "inactive"]:
        raise HTTPException(status_code=400, detail="状态值必须为 'active' 或 'inactive'")

    existing_combination = combinations_db[combination_id]
    existing_combination.status = status
    existing_combination.updatedAt = datetime.now()

    return existing_combination


@app.delete("/api/v1/combinations/{combination_id}", status_code=204)
async def delete_combination(combination_id: int = Path(..., description="组合 ID")):
    """
    删除组合
    """
    if combination_id not in combinations_db:
        raise HTTPException(status_code=404, detail=f"组合 ID {combination_id} 不存在")

    del combinations_db[combination_id]
    return None


if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=8000)
