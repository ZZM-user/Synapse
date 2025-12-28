// frontend/src/utils/auth.ts
/**
 * 认证工具函数
 * 管理 JWT Token 的存储、读取和验证
 */

const TOKEN_KEY = 'synapse_access_token';
const USER_KEY = 'synapse_current_user';

export interface User {
  id: number;
  username: string;
  role: 'admin' | 'user';
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
}

/**
 * 保存 Token 到 localStorage
 */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

/**
 * 获取存储的 Token
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

/**
 * 移除 Token
 */
export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/**
 * 检查是否已登录（有 Token）
 */
export function isAuthenticated(): boolean {
  return !!getToken();
}

/**
 * 保存当前用户信息
 */
export function setCurrentUser(user: User): void {
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

/**
 * 获取当前用户信息
 */
export function getCurrentUser(): User | null {
  const userJson = localStorage.getItem(USER_KEY);
  if (!userJson) return null;

  try {
    return JSON.parse(userJson);
  } catch {
    return null;
  }
}

/**
 * 移除用户信息
 */
export function removeCurrentUser(): void {
  localStorage.removeItem(USER_KEY);
}

/**
 * 登出（清除所有认证信息）
 */
export function logout(): void {
  removeToken();
  removeCurrentUser();
}

/**
 * 检查当前用户是否是管理员
 */
export function isAdmin(): boolean {
  const user = getCurrentUser();
  return user?.role === 'admin';
}
