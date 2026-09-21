# 🍱 Smart-Dining · 智能餐饮推荐系统

> 面向学校 / 团餐场景的**营养餐智能推荐与膳食管理**系统：基于多维度权重评分（营养达标率 · 成本控制 · 食材多样性），结合《学生餐营养指南》自动生成早 / 午 / 晚餐推荐方案，并配套菜品管理、食材价格、采购单、发布计划等一体化后台。

---

## 📌 项目简介

Smart-Dining 是一套前后端分离的餐饮推荐与管理平台：

- **后端**：基于 FastAPI 构建 RESTful API，提供推荐引擎、JWT 鉴权、菜品 / 食材 / 采购 / 计划等数据管理，并通过 SQLAlchemy 操作 MySQL。
- **前端**：基于 Vue 3 + Vite + Element Plus 的管理后台，覆盖菜谱制定、菜品库、食材价格、营养分析、发布计划等页面。
- **推荐内核**：自研**加权评分推荐算法**，在候选菜品组合中按「营养 40% · 成本 35% · 食材多样性 25%」综合打分，返回最优 Top-N 方案。

---

## ✨ 功能特性

| 模块 | 关键能力 |
|------|----------|
| 🤖 智能推荐 | 按年龄段（小学 / 初中 / 高中）生成早午晚三餐推荐；支持单餐、套餐、多日计划 |
| ⚖️ 权重评分 | 营养达标率 40% + 成本控制 35% + 食材多样性 25%，可动态查看权重与评分明细 |
| 🍽️ 菜品管理 | 菜品 CRUD、分类（主食 / 荤菜 / 素菜 / 汤类）、营养与成本信息维护 |
| 💰 食材价格 | 食材价格维护、供应商价格批量导入（Excel）、别名映射 |
| 🧾 采购管理 | 采购单生成与管理 |
| 📅 发布计划 | 膳食计划制定、发布、按用户隔离查看 |
| 🥗 营养指南 | 基于《学生餐营养指南》的营养目标与达标分析 |
| 👥 用户与权限 | JWT 鉴权、管理员 / 普通用户角色、学校维度隔离 |
| 🧩 AI 扩展 | 可选接入 Dify 智能体，提供 AI 推荐与菜品分析能力 |

---

## 🧱 技术架构

### 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 前端 | Vue 3 / Vite 7 / TypeScript | 组件化 SPA，开发服务器默认 `:5173` |
| 前端 UI | Element Plus / Pinia / Vue Router / Axios | 企业级 UI、状态管理、路由、HTTP |
| 后端 | FastAPI / Uvicorn | 异步 Web 框架，自动生成 OpenAPI 文档 |
| 数据校验 | Pydantic / pydantic-settings | 请求 / 响应模型、环境变量管理 |
| 数据库 | MySQL + SQLAlchemy | ORM 持久化，支持 `pymysql` 驱动 |
| 鉴权 | python-jose (JWT) / passlib (bcrypt) | 令牌签发与密码哈希 |
| AI（可选） | Dify API | 智能体推荐与菜品分析 |

### 系统架构图

```mermaid
flowchart LR
    U["👤 浏览器 / 用户"] -->|"HTTP / HTTPS"| FE["Vue3 前端<br/>Vite 开发 :5173<br/>构建后为静态文件"]
    FE -->|"REST API → :8000"| BE["FastAPI 后端<br/>:8000"]
    BE -->|"SQLAlchemy ORM"| DB[("MySQL<br/>food_recommended")]
    BE -->|"HTTP 调用（可选）"| DIFY["Dify 智能体<br/>AI 推荐 / 菜品分析"]
    BE -->|"JWT 鉴权"| AUTH["用户 / 角色<br/>学校隔离"]
```

### 推荐算法流程（加权评分）

```mermaid
flowchart TD
    A["候选菜品池<br/>按餐次 + 分类规则筛选"] --> B["组合生成器<br/>CombinationGenerator"]
    B --> C["枚举 ≤ 100 种组合<br/>保证多样性"]
    C --> D1["营养评分 0–100<br/>达标率 90–110% 满分"]
    C --> D2["成本评分 0–100<br/>预算 50–85% 满分"]
    C --> D3["多样性评分 0–100<br/>食材数 / 颜色 / 分类"]
    D1 --> E["综合评分 = 营养×0.40<br/>+ 成本×0.35 + 多样性×0.25"]
    D2 --> E
    D3 --> E
    E --> F["按综合评分降序排序"]
    F --> G["返回 Top-N 最优方案<br/>默认 3 套 + 备选"]
```

---

## 📂 目录结构

```
Smart-Dining/
├── app/                         # FastAPI 后端
│   ├── main.py                  # 应用入口（uvicorn app.main:app）
│   ├── config/                  # 配置：权重、营养标准、餐次规则
│   ├── core/                    # 异常处理、统一响应
│   ├── models/                  # SQLAlchemy 数据模型
│   ├── routers/                 # 路由：认证/推荐/菜单/营养/采购…
│   ├── schemas/                 # Pydantic 数据模型
│   ├── services/                # 业务逻辑（Dify / DB / 推荐）
│   ├── utils/                   # 工具：评分器、成本计算、组合生成
│   ├── static/                  # 静态资源
│   └── templates/               # Jinja2 模板（内置管理页）
├── frontend/                    # Vue3 + Vite 前端
│   ├── src/
│   │   ├── views/               # 页面视图（推荐/菜品/价格/计划…）
│   │   ├── components/          # 通用组件
│   │   ├── router/              # 前端路由
│   │   ├── stores/              # Pinia 状态（含 API 客户端）
│   │   └── utils/               # 工具函数
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── scripts/                     # 数据导入与维护脚本（Python / SQL）
├── docs/                        # 项目文档（食材成本说明等）
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量示例（复制为 .env 使用）
└── README.md
```

---

## 🚀 安装与使用

### 环境要求

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| Python | 3.9+（推荐 3.11） | 后端运行环境 |
| Node.js | 20+（Vite 7 要求） | 前端构建 / 开发服务器 |
| MySQL | 5.7+ / 8.0 | 业务数据库 |
| pip / npm | 最新 | 依赖安装 |

### 1️⃣ 后端启动

```bash
# 进入项目根目录
cd Smart-Dining

# （建议）创建并激活虚拟环境
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env             # 然后编辑 .env 填入真实数据库 / 密钥

# 准备数据库（MySQL 中先建库）
#   CREATE DATABASE food_recommended CHARACTER SET utf8mb4;
#   应用启动时会自动建表并做轻量迁移

# 启动服务（开发模式，热重载）
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动成功后：

- API 根地址：`http://localhost:8000`
- 交互式文档（Swagger）：`http://localhost:8000/docs`
- 默认自动创建管理员账号：**`admin` / `admin123`**（学校：测试学校），首次启动后请尽快修改密码。

### 2️⃣ 前端启动

```bash
cd frontend

# 安装依赖（首次或依赖变更时）
npm install

# 配置后端地址（可选）
#   前端默认请求 http://localhost:8000，
#   如需自定义，在 frontend/ 下创建 .env 并写入：
#   VITE_API_BASE_URL=http://localhost:8000

# 启动开发服务器
npm run dev
```

- 开发服务器地址：`http://localhost:5173`
- 生产构建：`npm run build`（产物在 `frontend/dist/`，可交由 Nginx / 后端静态托管）

> 前后端默认已配置 CORS（允许 `localhost:5173`），开发联调开箱即用。

### 3️⃣ 访问与使用

1. 打开 `http://localhost:5173`，使用 `admin / admin123` 登录。
2. 进入「菜谱制定 / 推荐查询」，选择年龄段、学校、饮食偏好，点击获取推荐。
3. 在「菜品管理」「食材价格」「发布计划」等页面维护基础数据与膳食计划。

---

## 🔌 API 接口速览

> 完整接口见 `http://localhost:8000/docs`（Swagger）。核心端点如下：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/auth/token` | POST | 登录获取 JWT（表单：username / password） |
| `/auth/register` | POST | 注册用户 |
| `/recommendation/generate` | POST | 生成推荐（表单：age_group / school / preference） |
| `/recommendation/get-recommendation` | POST | 前端获取推荐（JSON） |
| `/recommendation/database-recommendation` | POST | 基于数据库的推荐 |
| `/recommendation/meal-set-recommendation` | POST | 加权套餐推荐 |
| `/recommendation/analyze-dishes` | POST | 菜品营养 / 成本分析 |
| `/api/v2/recommendation/weighted-scoring` | POST | 单餐权重评分推荐 |
| `/api/v2/recommendation/weighted-meal-plan` | POST | 多日权重评分计划 |
| `/api/v2/recommendation/weights-info` | GET | 查看当前权重配置 |
| `/menu_items` | CRUD | 菜品管理 |
| `/meal_plans` | CRUD | 膳食发布计划 |
| `/ingredient_prices` | CRUD | 食材价格 |
| `/ingredient_nutritions` | CRUD | 食材营养 |
| `/supplier-price-import` | POST | 供应商价格批量导入 |
| `/purchase_orders` | CRUD | 采购单 |
| `/system` / `/nutrition` | GET/POST | 系统 / 用户 / 角色 / 营养指南 |

### 推荐调用示例（前端 / 任意 HTTP 客户端）

```js
// 默认后端地址 http://localhost:8000，可通过 VITE_API_BASE_URL 覆盖
const api = axios.create({ baseURL: 'http://localhost:8000', timeout: 15000 });

const { data } = await api.post('/recommendation/generate',
  new URLSearchParams({
    age_group: 'JUNIOR',   // PRIMARY | JUNIOR | SENIOR
    school: '某某学校',
    preference: '喜欢清淡'
  }).toString(),
  { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
);

// data.recommendation 为 JSON 字符串，解析后得到 breakfast / lunch / dinner 数组
const plan = JSON.parse(data.recommendation);
```

---

## ⚙️ 配置说明（`.env`）

| 变量 | 说明 | 示例 |
|------|------|------|
| `DATABASE_URL` | 数据库连接串（MySQL） | `mysql+pymysql://root:pass@localhost:3306/food_recommended` |
| `SECRET_KEY` | JWT 签名密钥（≥32 位） | 随机长字符串 |
| `ALGORITHM` | JWT 算法 | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token 有效期（分钟） | `10080`（7 天） |
| `DIFY_API_KEY` / `DIFY_API_URL` | 可选，AI 推荐智能体 | 见 `.env.example` |
| `CORS_ORIGINS` | 允许跨域来源 | `http://localhost:5173` |

> ⚠️ **安全提醒**：`.env` 含有数据库密码等敏感信息，**已被 `.gitignore` 忽略，切勿提交到仓库**。请基于 `.env.example` 在本地创建。

---

## 🗄️ 数据库与数据初始化

- 应用启动时通过 `Base.metadata.create_all` **自动建表**，并做轻量字段迁移（如补齐 `delivery_status`、`total_cost` 等列）。
- 食材价格等历史数据可通过 `scripts/` 目录下的脚本批量导入（支持 Excel），详见 `docs/` 与 `scripts/` 中的说明文档。
- 如需手动初始化库：`CREATE DATABASE food_recommended CHARACTER SET utf8mb4;`

---

## 🔧 开发指南

- 后端热重载：`uvicorn app.main:app --reload`
- 前端热更新：`npm run dev`（Vite HMR）
- 接口调试：访问 `/docs`（Swagger UI）
- 日志：控制台 + `app.log`（`LOG_LEVEL` 可在 `.env` 调整）

---

## 📦 部署建议

1. **后端**：使用 `uvicorn app.main:app --host 0.0.0.0 --port 8000` 或经 Gunicorn / Supervisor 守护；生产环境关闭 `DEBUG`、使用强 `SECRET_KEY`。
2. **前端**：`npm run build` 生成 `dist/`，用 Nginx 托管静态文件，并将 `/api` 反向代理到后端 `:8000`。
3. **数据库**：独立 MySQL 实例，定期备份 `food_recommended`。
4. **安全**：不要将 `.env`、密钥、上传文件（`uploads/`）提交到代码仓库。

---

## 📄 许可证

本项目仅供学习 / 演示使用，许可证详见仓库内 `LICENSE`（如未提供，默认保留所有权利）。

---

## 🤝 贡献

欢迎提 Issue 与 Pull Request。提交前请确保：

- 后端依赖变更同步更新 `requirements.txt`；
- 前端变更通过 `npm run build` 验证；
- 不要提交 `.env`、密钥、产物（`node_modules/`、`__pycache__/`、`dist/`）。
