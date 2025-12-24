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
