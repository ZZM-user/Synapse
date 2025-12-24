# Synapse - 面向 AI业务 的智能 MCP 网关

Synapse 是一个轻量级、高性能的协议转换网关。它旨在通过将企业现有服务能力（如 OpenAPI/Swagger）转换为模型内循环通信协议（MCP）格式，无缝连接企业与
AI 智能体世界。

## 🌟 愿景

在企业内部署 AI 智能体的过程中，开发者面临着巨大的挑战：

- **协议鸿沟**：大量的内部 RESTful/RPC API 无法被 AI 智能体直接理解或调用。手动编写适配层是重复且维护成本高昂的工作。
- **管理鸿沟**：面对数千个微服务，如何决定哪些 API 应暴露给 AI？如何像搭建乐高积木一样，对它们进行逻辑分组和管理？
- **适配鸿沟**：私有或内部 AI 平台通常具有非标准化的认证和通信协议，而通用网关难以适配。

Synapse 旨在成为您 AI 架构中“业务感知”的突触。它不试图成为一个笨重、无所不包的 API 网关。相反，它专注于**自动化协议转换**、*
*细粒度工具管理**和**极致适应性**。

## ✨ 核心功能 (v0.1 已实现)

- **动态 OpenAPI 到 MCP 转换**：核心引擎可以从任何 URL 获取 OpenAPI 3.0 规范，并将其即时转换为符合 MCP v1 的工具集。
- **全面的 Schema 解析**：
    - 正确处理 OpenAPI 的 `paths`、`methods`、`parameters` (query, header, path) 和 `requestBody`。
    - 递归解析 `$ref` 引用，允许 `components/schemas` 中的复杂对象 schema 准确地表示为工具的输入参数。
- **动态 MCP 端点**：一个中央 API 端点 `/mcp/v1/tools`，它接收 `openapi_url` 并提供转换后的工具，充当您服务的实时桥梁。
- **现代化管理界面**：一个使用 **Vue 3** 和 **Naive UI** 构建的时尚且响应迅速的管理界面。
- **可视化服务管理**：
    - **添加/列出/删除服务**：通过 UI 轻松管理您的微服务列表。
    - **实时 API 检查**：对于任何已注册的服务，单击“查看 API”可即时获取、转换并显示其 OpenAPI 规范中所有可用的 AI 工具（MCP
      工具）列表。

## 🚀 快速开始

在几分钟内启动您的 Synapse 实例。

### 先决条件

- [Node.js](https://nodejs.org/) (推荐 v24+)
- [Python](https://www.python.org/) (推荐 v3.12+) 和 `uv` 包管理器

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/Synapse.git
cd Synapse
```

### 2. 设置后端

导航到后端目录，安装依赖项，并运行服务器。

```bash
# 从项目根目录
cd backend

# 使用 uv 安装 Python 依赖项
uv pip sync pyproject.toml

# 运行 FastAPI 服务器
# 您也可以从根目录使用以下命令: ./.venv/bin/uvicorn backend.main:app --reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端现在运行在 `http://localhost:8000`。

### 3. 设置前端

打开一个新终端，导航到前端目录，安装依赖项，并运行开发服务器。

```bash
# 从项目根目录
cd frontend

# 安装 Node.js 依赖项
pnpm install

# 运行 Vue 开发服务器
pnpm run dev
```

前端现在运行，通常在 `http://localhost:5173`。

### 4. 探索！

在浏览器中打开前端地址。您现在可以添加服务（使用 Petstore URL
进行快速测试：`https://petstore3.swagger.io/api/v3/openapi.json`）并查看转换后的 AI 工具。

## 🛠️ 技术栈

- **后端框架**：**FastAPI**
- **Python 包管理器**：**uv**
- **前端框架**：**Vue 3 + Vite + TypeScript**
- **UI 组件库**：**Naive UI**
- **异步 Web 服务器**：**Uvicorn**
- **HTTP 客户端**：**httpx** (后端), `fetch` (前端)

## 🏗️ 路线图

- **✅ 阶段 1：核心引擎与 MVP (已完成)**
    - `[x]` 设置后端 (FastAPI) 和前端 (Vue 3) 项目。
    - `[x]` 实现核心 OpenAPI 到 MCP 转换引擎。
    - `[x]` 实现动态 MCP 端点。
    - `[x]` 构建用于服务管理和 API 查看的基本 UI。

- **🔲 阶段 2：服务发现与配置 (下一步)**
    - `[ ]` 集成 Nacos SDK 以实现自动服务发现。
    - `[ ]` 使用数据库或文件存储（例如 Redis、YAML）持久化服务配置。
    - `[ ]` 实现安全层（白名单）以过滤暴露的 API。

- **🔲 阶段 3：高级工具管理**
    - `[ ]` 实现 UI 以创建“工具包”（API 的逻辑分组）。
    - `[ ]` 允许将每个工具包作为唯一的 MCP 端点暴露。
    - `[ ]` 支持工具包的编辑和版本控制。

- **🔲 阶段 4：生产就绪**
    - `[ ]` 实现可插拔的认证系统（拦截器）。
    - `[ ]` 编写全面的单元和集成测试。
    - `[ ]` 创建 `docker-compose.yml` 实现一键部署。
    - `[ ]` 添加结构化日志记录和基本可观测性。