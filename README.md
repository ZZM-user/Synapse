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

## ✨ 核心功能 (v0.5.1)

- **动态 OpenAPI 到 MCP 转换**：核心引擎可以从任何 URL 获取 OpenAPI 3.0 规范，并将其即时转换为符合 MCP v1 的工具集。
- **全面的 Schema 解析**：
    - 正确处理 OpenAPI 的 `paths`、`methods`、`parameters` (query, header, path) 和 `requestBody`。
    - 递归解析 `$ref` 引用，允许 `components/schemas` 中的复杂对象 schema 准确地表示为工具的输入参数。
- **动态 MCP 端点**：一个中央 API 端点 `/mcp/v1/tools`，它接收 `openapi_url` 并提供转换后的工具，充当您服务的实时桥梁。
- **现代化管理界面**：一个使用 **Vue 3** 和 **Naive UI** 构建的时尚且响应迅速的管理界面。
- **可视化服务管理**：
    - **添加/列表/删除服务**：通过 UI 轻松管理您的微服务列表，并支持多种文档类型（`OpenAPI 3.0`, `Swagger 2.0`, `AsyncAPI`）。
    - **实时 API 检查与搜索**：对于任何已注册的服务，单击"查看 API"可即时获取、转换并显示其 OpenAPI 规范中所有可用的 AI 工具（MCP
      工具）列表。新增的**搜索框**可让您按 API 路径或描述快速筛选，**关闭图标**让弹窗操作更便捷。
- **MCP 组合管理** ⭐ **v0.2 功能**：
    - **创建组合**：从多个服务中选择任意接口，组合成一个逻辑服务单元（类似"工具包"概念）。
    - **接口管理**：为每个组合添加、查看、搜索和删除接口，支持跨服务组合。
    - **状态控制**：通过开关快速启用或停用组合。
    - **灵活搜索**：支持按组合名称、描述、接口路径等多维度搜索。
    - **完整的 CRUD 操作**：提供 RESTful API 和可视化界面完整支持组合的增删改查。
- **MCP 服务管理** ⭐ **v0.3 功能**：
    - **创建 MCP 服务**：将多个组合打包成完整的 MCP Server，每个服务有唯一的前缀标识。
    - **前缀管理**：MCP 前缀创建后不可修改，确保服务标识的稳定性（支持字母、数字、下划线、连字符）。
    - **组合编排**：为每个 MCP 服务自由选择和组合多个组合，实现灵活的服务编排。
    - **独立管理界面**：专门的组合管理界面，支持查看、添加、删除服务中的组合。
    - **状态控制**：快速启用或停用整个 MCP 服务。
    - **完整的 CRUD 操作**：提供 RESTful API 和可视化界面完整支持 MCP 服务的增删改查。
- **标准 MCP Server 协议** ⭐ **v0.5.1 已完成**：
    - **✅ 符合官方标准**：完全符合 MCP 官方 HTTP + SSE 传输规范。
    - **✅ 单一端点设计**：`/mcp/{prefix}` 端点同时支持 GET（SSE流）和 POST（JSON-RPC）。
    - **✅ 完整会话管理**：支持 `Mcp-Session-Id` 头，实现标准的会话生命周期管理。
    - **✅ 协议版本协商**：支持 `MCP-Protocol-Version` 头，确保客户端兼容性。
    - **✅ 实时通知机制**：通过 SSE 流推送 `notifications/tools/list_changed` 等实时通知。
    - **✅ 远程服务模式**：Synapse 作为中心化 MCP Server，团队成员只需配置 URL 即可使用。
    - **✅ 客户端兼容**：支持 Claude Desktop、Cursor 等主流 MCP 客户端。
    - **自动工具聚合**：根据组合自动聚合所有接口，转换为 MCP 工具定义。
    - **代理执行**：自动代理 API 调用，支持 GET/POST/PUT/DELETE/PATCH 等 HTTP 方法。
    - **配置生成**：一键生成标准 MCP 配置，可直接用于 Claude Desktop、Cursor 等 AI 工具。

## ⚠️ 已知问题与限制

### ~~MCP Server 协议兼容性~~ ✅ 已修复 (v0.5.1)
- **状态**：✅ 已完全修复
- **修复内容**：
  - 实现了符合官方标准的 HTTP + SSE 传输层
  - 单一端点 `/mcp/{prefix}` 同时支持 GET 和 POST
  - 添加标准的 `Mcp-Session-Id` 和 `MCP-Protocol-Version` 头处理
  - 完整的会话管理和实时通知机制
- **测试状态**：已通过协议层面测试，等待真实客户端验证
- **配置示例**：
  ```json
  {
    "mcpServers": {
      "synapse": {
        "type": "sse",
        "url": "http://localhost:8000/mcp/synapse"
      }
    }
  }
  ```

### 数据持久化
- **问题**：所有数据存储在内存中，重启后端服务会丢失
- **影响**：创建的组合和 MCP 服务在服务重启后需要重新创建
- **解决方案**（阶段 4）：集成数据库（SQLite/PostgreSQL）实现持久化存储

### OpenAPI 参数解析
- **问题**：当前 MCP 工具的 inputSchema 为简化版本，未完整解析 OpenAPI 参数定义
- **影响**：工具调用时需要手动处理路径参数、查询参数等
- **解决方案**（优化中）：完善 OpenAPI schema 解析，生成完整的 JSON Schema

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

## 🔌 使用 MCP Server

Synapse v0.5.1 完全支持标准 MCP 协议，可以直接在 Claude Desktop、Cursor 等 AI 工具中使用。

### 配置 Claude Desktop

1. **创建 MCP 服务**：在 Synapse 管理界面中创建一个 MCP 服务（例如前缀为 `synapse`）

2. **获取配置**：在"MCP 管理"页面点击"查看配置"按钮，复制生成的配置

3. **编辑 Claude Desktop 配置文件**：
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

4. **添加配置**：
   ```json
   {
     "mcpServers": {
       "synapse": {
         "type": "sse",
         "url": "http://localhost:8000/mcp/synapse"
       }
     }
   }
   ```

5. **重启 Claude Desktop**：完全退出并重新启动 Claude Desktop

6. **验证**：在 Claude 对话中询问"请列出你可用的工具"，应该能看到以 `synapse_` 开头的工具

### 配置 Cursor

在 Cursor 的 Settings → MCP Servers 中添加相同的配置即可。

### 实时配置更新

得益于标准 MCP 协议的实时通知机制，当您在 Synapse 后台更新 MCP 服务配置（如添加/删除组合）时，已连接的客户端会自动收到通知并刷新工具列表，**无需重启后端服务或客户端**。

### 详细测试指南

查看 `backend/标准协议测试指南.md` 了解完整的测试步骤和故障排查方法。

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

- **✅ 阶段 2：MCP 组合管理 (已完成)**
    - `[x]` 实现 MCP 组合的数据模型（Pydantic）。
    - `[x]` 构建完整的组合 CRUD API（创建、读取、更新、删除、状态切换）。
    - `[x]` 实现可视化组合管理界面（列表、搜索、新增、编辑）。
    - `[x]` 实现接口管理功能（查看、添加、删除组合中的接口）。
    - `[x]` 支持从多个服务中选择接口组成组合。

- **✅ 阶段 3：MCP 服务管理 (已完成)**
    - `[x]` 实现 MCP 服务的数据模型（Pydantic）。
    - `[x]` 构建完整的 MCP 服务 CRUD API（创建、读取、更新、删除、状态切换）。
    - `[x]` 实现 MCP 前缀唯一性验证和格式验证。
    - `[x]` 实现可视化 MCP 服务管理界面（列表、搜索、新增、编辑）。
    - `[x]` 实现组合选择和管理功能（从组合中选择构建 MCP 服务）。
    - `[x]` 添加示例数据以便测试。

- **✅ 阶段 4：标准 MCP Server 协议 (已完成 v0.5.1)**
    - `[x]` 实现 JSON-RPC 2.0 协议处理（protocol.py）。
    - `[x]` 实现 MCP Server 核心逻辑（initialize、tools/list、tools/call）。
    - `[x]` 添加动态 MCP 端点 `/mcp/{prefix}`（支持 GET 和 POST）。
    - `[x]` 实现工具聚合和转换逻辑。
    - `[x]` 实现 API 代理执行功能。
    - `[x]` 添加配置生成和展示界面。
    - `[x]` 实现 stdio 传输方式（mcp_stdio_server.py）。
    - `[x]` 实现标准 HTTP + SSE 传输层（符合官方规范）。
    - `[x]` 实现完整的会话管理（Mcp-Session-Id）。
    - `[x]` 实现协议版本协商（MCP-Protocol-Version）。
    - `[x]` 实现实时通知机制（notifications/tools/list_changed）。
    - `[x]` 单一端点设计（GET 用于 SSE，POST 用于 JSON-RPC）。
    - `[ ]` 与 Claude Desktop、Cursor 等客户端的完整兼容性验证。
    - `[ ]` 添加 Origin 头验证（安全性增强）。
    - `[ ]` 添加身份验证机制。

- **🔲 阶段 5：服务发现与持久化 (下一步)**
    - `[ ]` 集成 Nacos SDK 以实现自动服务发现。
    - `[ ]` 使用数据库（例如 SQLite、PostgreSQL）持久化组合和服务配置。
    - `[ ]` 实现安全层（白名单）以过滤暴露的 API。
    - `[ ]` 完善 OpenAPI 参数解析，生成完整的 JSON Schema。

- **🔲 阶段 6：高级功能**
    - `[ ]` 支持组合和服务的版本控制和历史记录。
    - `[ ]` 实现组合和服务的导入/导出功能（YAML/JSON）。
    - `[ ]` 添加使用统计和监控功能。
    - `[ ]` 实现级联删除保护（删除组合前检查是否被服务使用）。

- **🔲 阶段 7：生产就绪**
    - `[ ]` 实现可插拔的认证系统（拦截器）。
    - `[ ]` 编写全面的单元和集成测试。
    - `[ ]` 创建 `docker-compose.yml` 实现一键部署。
    - `[ ]` 添加结构化日志记录和基本可观测性。