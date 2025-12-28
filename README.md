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

## ✨ 核心功能 (v0.7.0)

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
- **标准 MCP Server 协议** ⭐ **v0.5.1 功能**：
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
- **多数据库持久化** ⭐ **v0.6.0 功能**：
    - **✅ 多数据库支持**：支持 SQLite、MySQL、PostgreSQL、Oracle、DM8（达梦）五种数据库。
    - **✅ 灵活配置**：通过 `config.yaml` 配置文件自主选择数据库类型。
    - **✅ 自动迁移**：首次启动时自动从 JSON 文件迁移数据到数据库，并生成带时间戳的备份。
    - **✅ 异步 ORM**：基于 SQLAlchemy 2.0 的完整异步数据库操作。
    - **✅ 数据库迁移**：使用 Alembic 管理数据库版本和迁移脚本。
    - **✅ Repository 模式**：清晰的数据访问层，便于维护和测试。
    - **✅ 环境变量支持**：敏感信息（如数据库密码）通过环境变量配置。
    - **零停机切换**：可随时切换数据库类型，运行迁移即可。
- **现代化数据面板** ⭐ **v0.6.1 新增**：
    - **📊 实时统计卡片**：服务总数、组合总数、MCP 服务数、接口总数一目了然。
    - **📈 最近项目时间线**：显示最近创建的组合和 MCP 服务，支持智能时间显示。
    - **🎨 渐变色设计**：每个统计卡片采用不同渐变色，视觉层次分明。
    - **⚡ 快捷操作**：一键跳转到创建组合或创建 MCP 服务页面。
    - **📉 状态分布**：实时显示活跃/停用的组合和服务数量。
    - **🔄 自动刷新**：数据实时从数据库加载，确保准确性。
- **模块化 API 架构** ⭐ **v0.6.2 新增**：
    - **🏗️ 清晰的代码组织**：API 路由按功能模块分离，main.py 从 939 行精简至 98 行（减少 89.6%）。
    - **📦 独立路由模块**：6 个独立的 API 路由文件（services、combinations、mcp_servers、dashboard、tools、mcp_protocol）。
    - **🔧 易于维护**：每个模块职责单一，修改和扩展更加便捷。
    - **👥 团队协作友好**：不同开发者可以同时修改不同的 API 模块，减少代码冲突。
    - **♻️ 代码复用**：每个路由模块都是独立的 APIRouter，可在其他项目中轻松复用。
    - **✅ 零影响升级**：所有 API 路径保持不变，前端无需任何修改。
- **企业级用户认证系统** ⭐ **v0.7.0 新增**：
    - **🔐 JWT 认证机制**：基于 JSON Web Token 的现代化认证系统，Token 有效期 24 小时。
    - **👥 完整用户管理**：支持用户的增删改查（CRUD），包括用户名、密码、角色、状态管理。
    - **🎭 角色权限控制**：支持管理员（admin）和普通用户（user）两种角色，基于 RBAC 的权限控制。
    - **🔒 密码安全**：使用 bcrypt 进行密码哈希，确保密码安全存储。
    - **🖥️ 现代化登录页面**：全新设计的登录界面，支持渐变背景、动画效果、响应式布局。
    - **👤 用户管理界面**：可视化的用户管理页面，支持创建用户、编辑用户、删除用户、状态控制。
    - **🛡️ 智能路由守卫**：未登录用户自动跳转到登录页，已登录用户访问登录页自动跳转首页。
    - **🚫 管理员专属**：用户管理功能仅管理员可访问，普通用户无权限。
    - **📦 自动初始化**：首次启动自动创建默认管理员账户（admin/admin123）。
    - **🎯 选择性保护**：仅管理 API（`/api/v1/*`）需要认证，MCP 协议端点（`/mcp/*`）保持开放。
    - **✅ 生产就绪**：支持通过环境变量配置 JWT 密钥和默认管理员密码。

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

### ~~数据持久化~~ ✅ 已修复 (v0.6.0)
- **状态**：✅ 已完全修复
- **修复内容**：
  - 实现了多数据库支持（SQLite、MySQL、PostgreSQL、Oracle、DM8）
  - 基于 SQLAlchemy 2.0 的异步 ORM 架构
  - 使用 Alembic 进行数据库迁移管理
  - 自动从 JSON 文件迁移数据并生成备份
  - Repository 模式的数据访问层
- **默认配置**：SQLite（无需额外安装，开箱即用）

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

导航到后端目录，安装依赖项，配置数据库，并运行服务器。

```bash
# 从项目根目录
cd backend

# 使用 uv 安装 Python 依赖项
uv sync

# （可选）配置数据库
# 默认使用 SQLite，无需额外配置
# 如需使用其他数据库，请编辑 config.yaml 文件

# 运行数据库迁移（可选，应用启动时会自动创建表）
.venv/bin/alembic upgrade head

# 运行 FastAPI 服务器
.venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

后端现在运行在 `http://localhost:8000`。

#### 数据库配置说明

Synapse 默认使用 **SQLite** 数据库，数据存储在 `backend/data/synapse.db`，开箱即用无需配置。

如需使用其他数据库，请按以下步骤操作：

1. **复制环境变量模板**：
   ```bash
   cp .env.example .env
   ```

2. **编辑 `config.yaml`** 文件，修改 `database.type` 字段：
   ```yaml
   database:
     type: mysql  # 可选：sqlite, mysql, postgresql, oracle, dm8
   ```

3. **配置数据库连接**（以 MySQL 为例）：
   ```yaml
   mysql:
     host: localhost
     port: 3306
     database: synapse
     username: synapse_user
     password: ${MYSQL_PASSWORD}  # 从环境变量读取
   ```

4. **设置环境变量**（编辑 `.env` 文件）：
   ```env
   MYSQL_PASSWORD=your_password
   ```

5. **运行数据库迁移**：
   ```bash
   .venv/bin/alembic upgrade head
   ```

6. **启动应用**，首次启动时会自动从 JSON 文件迁移数据（如果存在）。

更多详细配置请参考 `backend/config.yaml` 文件中的注释。

#### 用户认证配置

Synapse v0.7.0 提供了完整的 **JWT 用户认证系统**来保护管理 API。

**核心特性**：
- ✅ **自动初始化**：首次启动时自动创建默认管理员账户（`admin` / `admin123`）
- ✅ **JWT 认证**：基于 JSON Web Token 的现代化认证，Token 有效期 24 小时
- ✅ **角色权限**：支持管理员（admin）和普通用户（user）两种角色
- ✅ **密码安全**：使用 bcrypt 哈希算法安全存储密码
- ✅ **可视化管理**：提供用户管理界面，支持创建、编辑、删除用户

**受保护的 API**：
- 🔒 **管理 API**（`/api/v1/*`）需要 JWT 认证：
  - 认证管理（`/api/v1/auth/*`）
  - 用户管理（`/api/v1/users/*`）- 仅管理员
  - 服务管理（`/api/v1/services`）
  - 组合管理（`/api/v1/combinations`）
  - MCP 服务管理（`/api/v1/mcp-servers`）
  - 仪表盘（`/api/v1/dashboard`）
  - 工具转换（`/api/v1/endpoints`, `/mcp/v1/tools`）
- ✅ **MCP 协议端点**（`/mcp/*`）保持开放，不受认证影响

**环境变量配置**（可选）：

编辑 `.env` 文件自定义配置：

```env
# JWT 密钥（生产环境务必修改为随机强密码）
JWT_SECRET_KEY=your-secret-key-change-in-production

# 默认管理员账户（可自定义，首次启动时创建）
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
```

**生成安全的 JWT 密钥**：

```bash
# macOS/Linux
openssl rand -hex 32

# 或者使用 Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**使用 API 进行认证**：

```bash
# 1. 登录获取 Token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 返回：
# {
#   "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "token_type": "bearer",
#   "user": {...}
# }

# 2. 使用 Token 访问受保护的 API
curl -X GET http://localhost:8000/api/v1/services \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**前端自动处理**：
- 前端会自动在所有 API 请求中添加 `Authorization` 头
- Token 存储在浏览器 localStorage 中
- Token 过期或无效时自动跳转到登录页

**安全建议**：
- 🔐 生产环境务必修改默认管理员密码
- 🔑 生产环境务必设置强随机 JWT 密钥（至少 32 字节）
- 🚫 不要将密钥和密码提交到版本控制系统（`.env` 已在 `.gitignore` 中）
- 🔄 定期更换密钥和密码（尤其是怀疑泄露时）
- 📦 部署时通过环境变量或密钥管理系统注入敏感信息

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

在浏览器中打开前端地址 `http://localhost:5173`。

**首次使用**：
1. 使用默认管理员账户登录：
   - 用户名：`admin`
   - 密码：`admin123`

2. 登录后您可以：
   - 添加服务（使用 Petstore URL 进行快速测试：`https://petstore3.swagger.io/api/v3/openapi.json`）
   - 创建组合（从多个服务中选择接口组合）
   - 创建 MCP 服务（将组合打包成 MCP Server）
   - 管理用户（仅管理员可访问）

**安全建议**：生产环境请立即修改默认管理员密码！

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

### 后端
- **框架**：**FastAPI** - 现代、快速的 Web 框架
- **架构模式**：**模块化 API Router** - 按功能分离的独立路由模块
- **Python 包管理器**：**uv** - 快速的 Python 包管理器
- **异步 Web 服务器**：**Uvicorn** - ASGI 服务器
- **HTTP 客户端**：**httpx** - 支持异步的 HTTP 客户端
- **数据库 ORM**：**SQLAlchemy 2.0** - 强大的异步 ORM
- **数据库迁移**：**Alembic** - SQLAlchemy 的数据库迁移工具
- **配置管理**：**PyYAML** + **python-dotenv** - YAML 配置和环境变量
- **数据验证**：**Pydantic v2** - 数据验证和设置管理
- **认证系统**：**python-jose** (JWT) + **passlib** (bcrypt) - 安全的用户认证

### 前端
- **框架**：**Vue 3** + **Vite** + **TypeScript**
- **UI 组件库**：**Naive UI** - Vue 3 的优雅 UI 组件库
- **HTTP 客户端**：**fetch** - 原生 Web API

### 数据库支持
- **SQLite** (默认) - aiosqlite
- **MySQL** - aiomysql + pymysql
- **PostgreSQL** - asyncpg + psycopg2
- **Oracle** - oracledb
- **DM8 (达梦)** - dmPython

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

- **🔄 阶段 5：服务发现与持久化 (进行中)**
    - `[x]` 使用数据库（SQLite、MySQL、PostgreSQL、Oracle、DM8）持久化组合和服务配置。
    - `[x]` 实现 SQLAlchemy 2.0 异步 ORM 架构。
    - `[x]` 实现 Alembic 数据库迁移管理。
    - `[x]` 实现自动 JSON 数据迁移和备份功能。
    - `[x]` 实现 Repository 模式的数据访问层。
    - `[ ]` 集成 Nacos SDK 以实现自动服务发现。
    - `[ ]` 实现安全层（白名单）以过滤暴露的 API。
    - `[ ]` 完善 OpenAPI 参数解析，生成完整的 JSON Schema。

- **✅ 阶段 6：用户认证系统 (已完成 v0.7.0)**
    - `[x]` 实现 JWT 认证机制（python-jose + HS256 算法）。
    - `[x]` 实现密码哈希和验证（bcrypt）。
    - `[x]` 创建用户数据模型和数据库迁移。
    - `[x]` 实现认证 API（login、logout、get current user）。
    - `[x]` 实现用户管理 API（CRUD、仅管理员）。
    - `[x]` 实现角色权限控制（admin/user）。
    - `[x]` 实现默认管理员自动初始化。
    - `[x]` 创建现代化登录页面（Vue 3 + Naive UI）。
    - `[x]` 创建用户管理界面（列表、创建、编辑、删除）。
    - `[x]` 实现前端路由守卫和自动重定向。
    - `[x]` 实现自动 Token 注入和过期处理。
    - `[ ]` 添加密码强度验证和复杂度要求。
    - `[ ]` 添加用户操作日志记录。
    - `[ ]` 实现 Token 刷新机制。

- **🔲 阶段 7：高级功能**
    - `[ ]` 支持组合和服务的版本控制和历史记录。
    - `[ ]` 实现组合和服务的导入/导出功能（YAML/JSON）。
    - `[ ]` 添加使用统计和监控功能。
    - `[ ]` 实现级联删除保护（删除组合前检查是否被服务使用）。

- **🔲 阶段 8：生产就绪**
    - `[ ]` 编写全面的单元和集成测试。
    - `[ ]` 创建 `docker-compose.yml` 实现一键部署。
    - `[ ]` 添加结构化日志记录和基本可观测性。
    - `[ ]` 性能优化和压力测试。