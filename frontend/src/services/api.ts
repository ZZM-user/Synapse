// frontend/src/services/api.ts

const BASE_URL = 'http://localhost:8000'; // Backend API base URL

/**
 * Fetches the MCP tools for a given OpenAPI specification URL.
 *
 * @param openapiUrl The URL of the OpenAPI spec.
 * @returns A promise that resolves to the MCP tools definition.
 */
export async function getMcpTools(openapiUrl: string) {
  const response = await fetch(`${BASE_URL}/mcp/v1/tools?openapi_url=${encodeURIComponent(openapiUrl)}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Fetches the API endpoints for a given OpenAPI specification URL.
 *
 * @param url The URL of the OpenAPI spec.
 * @returns A promise that resolves to a list of API endpoints.
 */
export async function getApiEndpoints(url: string) {
  const response = await fetch(`${BASE_URL}/api/v1/endpoints?url=${encodeURIComponent(url)}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

// ============= Combination API =============

export interface CombinationEndpoint {
  serviceName: string;
  serviceUrl: string;
  path: string;
  method: string;
  summary: string;
}

export interface Combination {
  id: number;
  name: string;
  description: string;
  status: 'active' | 'inactive';
  endpoints: CombinationEndpoint[];
  createdAt: string;
  updatedAt: string;
}

export interface CombinationCreate {
  name: string;
  description: string;
  endpoints: CombinationEndpoint[];
}

export interface CombinationUpdate {
  name?: string;
  description?: string;
  endpoints?: CombinationEndpoint[];
}

/**
 * 获取所有组合列表
 */
export async function getCombinations(): Promise<Combination[]> {
  const response = await fetch(`${BASE_URL}/api/v1/combinations`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 根据 ID 获取单个组合
 */
export async function getCombination(id: number): Promise<Combination> {
  const response = await fetch(`${BASE_URL}/api/v1/combinations/${id}`);

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 创建新组合
 */
export async function createCombination(combination: CombinationCreate): Promise<Combination> {
  const response = await fetch(`${BASE_URL}/api/v1/combinations`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(combination),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 更新组合
 */
export async function updateCombination(id: number, combination: CombinationUpdate): Promise<Combination> {
  const response = await fetch(`${BASE_URL}/api/v1/combinations/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(combination),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 切换组合状态
 */
export async function toggleCombinationStatus(id: number, status: 'active' | 'inactive'): Promise<Combination> {
  const response = await fetch(`${BASE_URL}/api/v1/combinations/${id}/status?status=${status}`, {
    method: 'PATCH',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * 删除组合
 */
export async function deleteCombination(id: number): Promise<void> {
  const response = await fetch(`${BASE_URL}/api/v1/combinations/${id}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'An unknown error occurred' }));
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }
}

