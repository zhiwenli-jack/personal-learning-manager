# 后端API文档

<cite>
**本文引用的文件**
- [backend/app/main.py](file://backend/app/main.py)
- [backend/app/api/directions.py](file://backend/app/api/directions.py)
- [backend/app/api/materials.py](file://backend/app/api/materials.py)
- [backend/app/api/questions.py](file://backend/app/api/questions.py)
- [backend/app/api/exams.py](file://backend/app/api/exams.py)
- [backend/app/api/mistakes.py](file://backend/app/api/mistakes.py)
- [backend/app/api/parse.py](file://backend/app/api/parse.py)
- [backend/app/api/gamification.py](file://backend/app/api/gamification.py)
- [backend/app/models/models.py](file://backend/app/models/models.py)
- [backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py)
- [backend/app/core/config.py](file://backend/app/core/config.py)
- [backend/app/services/qwen_service.py](file://backend/app/services/qwen_service.py)
- [backend/app/services/parse_service.py](file://backend/app/services/parse_service.py)
- [backend/app/services/gamification_service.py](file://backend/app/services/gamification_service.py)
- [backend/app/core/achievements.py](file://backend/app/core/achievements.py)
- [backend/app/core/daily_tasks.py](file://backend/app/core/daily_tasks.py)
- [backend/app/core/level_config.py](file://backend/app/core/level_config.py)
- [backend/pyproject.toml](file://backend/pyproject.toml)
- [backend/test_api.py](file://backend/test_api.py)
- [backend/test_full_flow.py](file://backend/test_full_flow.py)
</cite>

## 目录
1. [简介](#简介)
2. [项目结构](#项目结构)
3. [核心组件](#核心组件)
4. [架构总览](#架构总览)
5. [详细组件分析](#详细组件分析)
6. [依赖关系分析](#依赖关系分析)
7. [性能考虑](#性能考虑)
8. [故障排查指南](#故障排查指南)
9. [结论](#结论)
10. [附录](#附录)

## 简介
本项目为个人学习管理系统的后端API，采用FastAPI框架构建，提供学习方向管理、学习资料与内容解析、题目生成与管理、测验系统、错题管理、**游戏化系统**等核心能力。系统通过SSE（Server-Sent Events）实现资料处理进度的流式推送，并集成通义千问（DashScope）进行知识点提炼、题目生成与主观题评分。

- 版本：0.1.0
- 文档路径：/docs、/redoc
- 健康检查：/health
- 根信息：/

## 项目结构
后端采用按功能模块划分的API路由组织方式，核心模块如下：
- 路由注册：在应用启动时注册各模块路由，统一前缀为/api
- 数据模型：基于SQLAlchemy定义实体及枚举类型
- 数据模式：基于Pydantic定义请求/响应结构
- 服务层：封装外部API调用（通义千问）、解析服务（文本/文件/URL）、**游戏化服务**
- 配置：集中管理应用配置（数据库、DashScope、上传目录等）

```mermaid
graph TB
subgraph "应用入口"
MAIN["app/main.py<br/>注册路由/健康检查"]
end
subgraph "API模块"
DIR["api/directions.py<br/>学习方向"]
MAT["api/materials.py<br/>学习资料/SSE"]
QUE["api/questions.py<br/>题目管理"]
EXAM["api/exams.py<br/>测验/评分"]
MIS["api/mistakes.py<br/>错题管理"]
PAR["api/parse.py<br/>知识解析"]
GAM["api/gamification.py<br/>游戏化系统"]
end
subgraph "模型与模式"
MODELS["models/models.py<br/>数据模型/枚举"]
SCHEMAS["schemas/schemas.py<br/>请求/响应模式"]
end
subgraph "服务层"
QWEN["services/qwen_service.py<br/>DashScope封装"]
PARSE["services/parse_service.py<br/>解析协调"]
GAMSERV["services/gamification_service.py<br/>游戏化服务"]
end
MAIN --> DIR
MAIN --> MAT
MAIN --> QUE
MAIN --> EXAM
MAIN --> MIS
MAIN --> PAR
MAIN --> GAM
DIR --> MODELS
MAT --> MODELS
QUE --> MODELS
EXAM --> MODELS
MIS --> MODELS
PAR --> MODELS
GAM --> MODELS
DIR --> SCHEMAS
MAT --> SCHEMAS
QUE --> SCHEMAS
EXAM --> SCHEMAS
MIS --> SCHEMAS
PAR --> SCHEMAS
GAM --> SCHEMAS
MAT --> QWEN
EXAM --> QWEN
PAR --> PARSE
PARSE --> QWEN
GAM --> GAMSERV
```

**图表来源**
- [backend/app/main.py](file://backend/app/main.py#L1-L68)
- [backend/app/api/directions.py](file://backend/app/api/directions.py#L1-L51)
- [backend/app/api/materials.py](file://backend/app/api/materials.py#L1-L203)
- [backend/app/api/questions.py](file://backend/app/api/questions.py#L1-L90)
- [backend/app/api/exams.py](file://backend/app/api/exams.py#L1-L240)
- [backend/app/api/mistakes.py](file://backend/app/api/mistakes.py#L1-L90)
- [backend/app/api/parse.py](file://backend/app/api/parse.py#L1-L77)
- [backend/app/api/gamification.py](file://backend/app/api/gamification.py#L1-L129)
- [backend/app/models/models.py](file://backend/app/models/models.py#L1-L321)
- [backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L1-L371)
- [backend/app/services/qwen_service.py](file://backend/app/services/qwen_service.py#L1-L156)
- [backend/app/services/parse_service.py](file://backend/app/services/parse_service.py#L1-L163)
- [backend/app/services/gamification_service.py](file://backend/app/services/gamification_service.py#L1-L482)

**章节来源**
- [backend/app/main.py](file://backend/app/main.py#L1-L68)
- [backend/pyproject.toml](file://backend/pyproject.toml#L1-L29)

## 核心组件
- 应用入口与路由注册：统一前缀/api，CORS允许跨域，启动时创建数据库表与上传目录
- 数据模型：学习方向、学习资料、题目、测验、答题记录、错题、解析任务、知识点、最佳实践、**用户档案、成就、每日任务、经验日志、方向进度**
- 数据模式：定义请求/响应结构，支持from_attributes映射
- 服务层：
  - DashScope封装：知识点提炼、题目生成、主观题评分
  - 解析服务：协调文本抽取与大模型分析，保存摘要、知识点与最佳实践
  - **游戏化服务：经验值管理、等级称号、成就系统、每日任务、方向探索进度**
- 配置中心：应用名、数据库URL、DashScope密钥/模型/基础地址、上传目录与文件大小限制

**章节来源**
- [backend/app/main.py](file://backend/app/main.py#L1-L68)
- [backend/app/models/models.py](file://backend/app/models/models.py#L1-L321)
- [backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L1-L371)
- [backend/app/services/qwen_service.py](file://backend/app/services/qwen_service.py#L1-L156)
- [backend/app/services/parse_service.py](file://backend/app/services/parse_service.py#L1-L163)
- [backend/app/services/gamification_service.py](file://backend/app/services/gamification_service.py#L1-L482)
- [backend/app/core/config.py](file://backend/app/core/config.py#L1-L34)

## 架构总览
系统采用分层架构：
- 表现层：FastAPI路由与响应模型
- 业务层：各模块API控制器
- 服务层：外部API与内部解析协调、**游戏化服务**
- 数据访问层：SQLAlchemy模型与数据库

```mermaid
graph TB
CLIENT["客户端/前端"] --> API["FastAPI 路由层"]
API --> CONTROLLER["控制器(各模块)"]
CONTROLLER --> SERVICE["服务层(Qwen/解析/游戏化)"]
SERVICE --> MODEL["模型(ORM)"]
MODEL --> DB["SQLite/数据库"]
subgraph "外部服务"
DASH["DashScope API"]
END
SERVICE -.-> DASH
```

**图表来源**
- [backend/app/main.py](file://backend/app/main.py#L1-L68)
- [backend/app/api/materials.py](file://backend/app/api/materials.py#L1-L203)
- [backend/app/api/exams.py](file://backend/app/api/exams.py#L1-L240)
- [backend/app/services/qwen_service.py](file://backend/app/services/qwen_service.py#L1-L156)
- [backend/app/models/models.py](file://backend/app/models/models.py#L1-L321)

## 详细组件分析

### 学习方向管理
- 功能：增删改查学习方向
- 认证与权限：无显式鉴权装饰器
- 错误处理：重复名称、不存在时返回400/404
- SSE：无

接口定义
- GET /api/directions
  - 响应：学习方向数组
- POST /api/directions
  - 请求体：DirectionCreate
  - 响应：DirectionResponse
- GET /api/directions/{direction_id}
  - 响应：DirectionResponse
- DELETE /api/directions/{direction_id}
  - 响应：{"message": "删除成功"}

**章节来源**
- [backend/app/api/directions.py](file://backend/app/api/directions.py#L1-L51)
- [backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L17-L34)
- [backend/app/models/models.py](file://backend/app/models/models.py#L63-L76)

### 学习资料与题目生成（含SSE）
- 功能：上传资料并同步处理（提炼知识点、生成题目、保存），支持SSE进度流
- 认证与权限：无显式鉴权装饰器
- 错误处理：方向不存在、API密钥未配置、处理异常回滚状态
- SSE：/api/materials/{material_id}/progress

接口定义
- GET /api/materials
  - 查询参数：direction_id(int, 可选)
  - 响应：MaterialResponse数组
- POST /api/materials
  - 请求体：MaterialCreate
  - 响应：MaterialResponse
  - 说明：同步处理，完成后状态为processed
- GET /api/materials/{material_id}/progress
  - 响应：text/event-stream
  - 事件：extracting/extracted/generating/generated/saving/completed/error
- DELETE /api/materials/{material_id}
  - 响应：{"message": "删除成功"}

SSE事件结构
- step: 步骤标识
- progress: 进度百分比
- message: 描述
- data/material_id: 额外数据（如知识点数量、题目数量、材料ID）

**章节来源**
- [backend/app/api/materials.py](file://backend/app/api/materials.py#L1-L203)
- [backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L38-L58)
- [backend/app/models/models.py](file://backend/app/models/models.py#L78-L93)
- [backend/app/services/qwen_service.py](file://backend/app/services/qwen_service.py#L1-L156)

SSE处理序列图
```mermaid
sequenceDiagram
participant Client as "客户端"
participant API as "materials.get_material_progress"
participant Stream as "generate_material_stream"
participant Qwen as "qwen_service"
Client->>API : GET /api/materials/{material_id}/progress
API->>API : 查询材料状态
alt 已完成
API-->>Client : SSE : completed(100%)
else 处理中
API->>Stream : 启动流
Stream->>Qwen : extract_key_points()
Qwen-->>Stream : 知识点列表
Stream-->>Client : SSE : extracting/extracted
Stream->>Qwen : generate_questions()
Qwen-->>Stream : 题目数组
Stream-->>Client : SSE : generating/generated
Stream-->>Client : SSE : saving(逐题进度)
Stream-->>API : 更新材料状态为processed
API-->>Client : SSE : completed
end
```

**图表来源**
- [backend/app/api/materials.py](file://backend/app/api/materials.py#L164-L185)
- [backend/app/api/materials.py](file://backend/app/api/materials.py#L27-L80)
- [backend/app/services/qwen_service.py](file://backend/app/services/qwen_service.py#L37-L114)

### 题目管理
- 功能：按条件筛选、详情、更新、评价、删除
- 认证与权限：无显式鉴权装饰器
- 错误处理：不存在返回404

接口定义
- GET /api/questions
  - 查询参数：material_id(int, 可选)、direction_id(int, 可选)、question_type(str, 可选)
  - 响应：QuestionResponse数组
- GET /api/questions/{question_id}
  - 响应：QuestionResponse
- PATCH /api/questions/{question_id}
  - 请求体：QuestionUpdate
  - 响应：QuestionResponse
- PATCH /api/questions/{question_id}/rate
  - 请求体：QuestionRateRequest
  - 响应：QuestionResponse
- DELETE /api/questions/{question_id}
  - 响应：{"message": "删除成功"}

**章节来源**
- [backend/app/api/questions.py](file://backend/app/api/questions.py#L1-L90)
- [backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L62-L100)
- [backend/app/models/models.py](file://backend/app/models/models.py#L95-L114)

### 测验系统
- 功能：创建测验（随机抽题）、获取测验详情、提交并评分（客观题精确匹配、主观题AI评分）、查看结果
- 认证与权限：无显式鉴权装饰器
- 错误处理：方向无题、不存在、已完成再次提交、未完成就取结果

接口定义
- GET /api/exams
  - 查询参数：direction_id(int, 可选)、status(str, 可选)
  - 响应：ExamResponse数组
- POST /api/exams
  - 请求体：ExamCreate
  - 响应：ExamWithQuestions
- GET /api/exams/{exam_id}
  - 响应：ExamWithQuestions
- POST /api/exams/{exam_id}/submit
  - 请求体：ExamSubmit
  - 响应：ExamResult
- GET /api/exams/{exam_id}/result
  - 响应：ExamResult

评分规则
- 客观题：答案去空白后完全一致得满分
- 主观题：调用DashScope评分，≥60视为正确

**章节来源**
- [backend/app/api/exams.py](file://backend/app/api/exams.py#L1-L240)
- [backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L103-L169)
- [backend/app/models/models.py](file://backend/app/models/models.py#L116-L153)
- [backend/app/services/qwen_service.py](file://backend/app/services/qwen_service.py#L115-L151)

测验提交序列图
```mermaid
sequenceDiagram
participant Client as "客户端"
participant API as "exams.submit_exam"
participant Qwen as "qwen_service.evaluate_answer"
participant DB as "数据库"
Client->>API : POST /api/exams/{exam_id}/submit
API->>DB : 查询题目与答案
loop 遍历每题
API->>Qwen : 仅对主观题调用评分
Qwen-->>API : {score, feedback}
API->>DB : 保存Answer(含is_correct/score/feedback)
API->>DB : 若错误则写入Mistake
end
API->>DB : 更新Exam状态为completed/分数/等级/完成时间
API-->>Client : ExamResult
```

**图表来源**
- [backend/app/api/exams.py](file://backend/app/api/exams.py#L127-L217)
- [backend/app/services/qwen_service.py](file://backend/app/services/qwen_service.py#L115-L151)
- [backend/app/models/models.py](file://backend/app/models/models.py#L136-L169)

### 错题管理
- 功能：按方向与掌握状态筛选、详情、更新（掌握状态/复习次数自增）、删除
- 认证与权限：无显式鉴权装饰器
- 错误处理：不存在返回404

接口定义
- GET /api/mistakes
  - 查询参数：direction_id(int, 可选)、mastered(bool, 可选)
  - 响应：MistakeResponse数组（包含question关联）
- GET /api/mistakes/{mistake_id}
  - 响应：MistakeResponse（包含question关联）
- PATCH /api/mistakes/{mistake_id}
  - 请求体：MistakeUpdate
  - 响应：MistakeResponse
- DELETE /api/mistakes/{mistake_id}
  - 响应：{"message": "删除成功"}

**章节来源**
- [backend/app/api/mistakes.py](file://backend/app/api/mistakes.py#L1-L90)
- [backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L173-L191)
- [backend/app/models/models.py](file://backend/app/models/models.py#L155-L169)

### 知识解析（文本/文件/URL）
- 功能：解析纯文本、上传文件、解析URL，支持任务列表、详情、删除；内部调用解析服务与DashScope
- 认证与权限：无显式鉴权装饰器
- 错误处理：空输入、不存在返回400/404

接口定义
- POST /api/parse/text
  - 请求体：ParseTextRequest
  - 响应：ParseTaskResponse
- POST /api/parse/file
  - 表单：title、direction_id、file
  - 响应：ParseTaskResponse
- POST /api/parse/url
  - 请求体：ParseUrlRequest
  - 响应：ParseTaskResponse
- GET /api/parse/tasks
  - 查询参数：skip(int)、limit(int)、direction_id(int, 可选)
  - 响应：TaskListResponse数组
- GET /api/parse/tasks/{task_id}
  - 响应：ParseTaskResponse
- DELETE /api/parse/tasks/{task_id}
  - 响应：{"message": "删除成功"}

**章节来源**
- [backend/app/api/parse.py](file://backend/app/api/parse.py#L1-L77)
- [backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L194-L265)
- [backend/app/services/parse_service.py](file://backend/app/services/parse_service.py#L1-L163)

### 游戏化系统（新增）
- 功能：用户档案管理、成就系统、每日任务、经验日志、方向探索进度
- 认证与权限：无显式鉴权装饰器
- 错误处理：无特殊错误处理逻辑

接口定义
- GET /api/gamification/profile
  - 响应：UserProfileResponse
  - 说明：获取用户游戏化档案，自动更新连续登录天数
- GET /api/gamification/achievements
  - 响应：AchievementsListResponse
  - 说明：获取成就列表（已解锁 + 未解锁）
- GET /api/gamification/daily-tasks
  - 响应：DailyTaskResponse数组
  - 说明：获取今日任务列表（自动生成）
- GET /api/gamification/direction-progress
  - 查询参数：direction_id(int, 可选)
  - 响应：DirectionProgressResponse数组
  - 说明：获取方向探索进度
- GET /api/gamification/exp-logs
  - 查询参数：limit(int, 默认20, 范围1-100)、offset(int, 默认0)
  - 响应：ExpLogResponse数组
  - 说明：获取经验获取日志

**章节来源**
- [backend/app/api/gamification.py](file://backend/app/api/gamification.py#L1-L129)
- [backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L268-L371)
- [backend/app/models/models.py](file://backend/app/models/models.py#L225-L321)
- [backend/app/services/gamification_service.py](file://backend/app/services/gamification_service.py#L1-L482)
- [backend/app/core/achievements.py](file://backend/app/core/achievements.py#L1-L121)
- [backend/app/core/daily_tasks.py](file://backend/app/core/daily_tasks.py#L1-L53)
- [backend/app/core/level_config.py](file://backend/app/core/level_config.py#L1-L59)

## 依赖关系分析
- 外部依赖：FastAPI、SQLAlchemy、Pydantic、DashScope(httpx)、文件解析库(pymupdf/docx/beautifulsoup/lxml)
- 内部耦合：API层依赖模型与模式；服务层依赖配置；资料与测验模块依赖DashScope；解析模块依赖抽取与知识服务；**游戏化模块依赖成就配置、每日任务配置、等级配置**

```mermaid
graph LR
PY["pyproject.toml 依赖声明"] --> FAST["fastapi"]
PY --> SQL["sqlalchemy"]
PY --> PYD["pydantic"]
PY --> HTTPX["httpx(DashScope)"]
PY --> DOCX["python-docx"]
PY --> PDF["pymupdf"]
PY --> BS["beautifulsoup4/lxml"]
API_DIR["api/directions"] --> MODELS
API_MAT["api/materials"] --> MODELS
API_QUE["api/questions"] --> MODELS
API_EXAM["api/exams"] --> MODELS
API_MIS["api/mistakes"] --> MODELS
API_PAR["api/parse"] --> MODELS
API_GAM["api/gamification"] --> MODELS
API_MAT --> QWEN
API_EXAM --> QWEN
API_PAR --> PARSE
API_GAM --> GAMSERV
PARSE --> QWEN
GAMSERV --> ACHIEVEMENTS["core/achievements"]
GAMSERV --> DAILYTASKS["core/daily_tasks"]
GAMSERV --> LEVELCONFIG["core/level_config"]
```

**图表来源**
- [backend/pyproject.toml](file://backend/pyproject.toml#L1-L29)
- [backend/app/api/directions.py](file://backend/app/api/directions.py#L1-L51)
- [backend/app/api/materials.py](file://backend/app/api/materials.py#L1-L203)
- [backend/app/api/questions.py](file://backend/app/api/questions.py#L1-L90)
- [backend/app/api/exams.py](file://backend/app/api/exams.py#L1-L240)
- [backend/app/api/mistakes.py](file://backend/app/api/mistakes.py#L1-L90)
- [backend/app/api/parse.py](file://backend/app/api/parse.py#L1-L77)
- [backend/app/api/gamification.py](file://backend/app/api/gamification.py#L1-L129)
- [backend/app/services/qwen_service.py](file://backend/app/services/qwen_service.py#L1-L156)
- [backend/app/services/parse_service.py](file://backend/app/services/parse_service.py#L1-L163)
- [backend/app/services/gamification_service.py](file://backend/app/services/gamification_service.py#L1-L482)
- [backend/app/core/achievements.py](file://backend/app/core/achievements.py#L1-L121)
- [backend/app/core/daily_tasks.py](file://backend/app/core/daily_tasks.py#L1-L53)
- [backend/app/core/level_config.py](file://backend/app/core/level_config.py#L1-L59)

**章节来源**
- [backend/pyproject.toml](file://backend/pyproject.toml#L1-L29)

## 性能考虑
- 异步与并发
  - 资料处理与测验评分使用异步调用DashScope，避免阻塞
  - SSE流式返回处理进度，降低长耗时请求的等待成本
- 数据库优化
  - 使用joinedload加载关联（错题详情），减少N+1查询
  - 条件查询时尽量使用索引列（如direction_id、material_id）
  - **游戏化模块使用批量查询优化成就和任务获取**
- 外部服务
  - DashScope调用设置合理超时，避免长时间挂起
  - 对返回结果做健壮解析，失败时降级为默认值
- 文件解析
  - 限制上传文件大小，避免过大文件导致内存压力
- 缓存与复用
  - 配置中心使用LRU缓存获取Settings实例
  - **游戏化模块使用配置缓存（等级阈值、称号映射）**
- 最佳实践
  - 在生产环境开启CORS白名单，避免"*"
  - 对敏感操作（如删除）建议增加鉴权中间件
  - 对高频接口增加限流策略

## 故障排查指南
- 常见错误码
  - 400：参数非法（如空文本、空URL、方向无题）
  - 404：资源不存在（方向/资料/题目/测验/错题/任务）
  - 500：服务器内部错误（如DashScope密钥未配置、处理异常）
- DashScope相关
  - 检查QWEN_API_KEY是否配置
  - 确认QWEN_MODEL与QWEN_BASE_URL正确
  - 观察SSE流是否正常返回error事件
- 资料处理
  - 若状态长期为pending，检查SSE流是否被消费
  - 处理失败会回滚状态为failed，可查看错误信息
- 测验评分
  - 主观题评分失败会返回默认结果，建议重试或检查输入格式
- 游戏化系统
  - **用户档案初始化失败时检查数据库连接**
  - **成就检测异常时检查ACHIEVEMENTS配置**
  - **每日任务生成异常时检查DAILY_TASKS配置**
  - **经验日志查询异常时检查ExpSourceType枚举**
- 日志
  - 解析服务与资料处理均有日志记录，便于定位问题
  - **游戏化服务包含详细的事件处理日志**

**章节来源**
- [backend/app/api/materials.py](file://backend/app/api/materials.py#L88-L160)
- [backend/app/api/exams.py](file://backend/app/api/exams.py#L134-L140)
- [backend/app/services/parse_service.py](file://backend/app/services/parse_service.py#L72-L78)
- [backend/app/core/config.py](file://backend/app/core/config.py#L16-L20)
- [backend/app/services/gamification_service.py](file://backend/app/services/gamification_service.py#L1-L482)

## 结论
本API提供了完整的个人学习管理能力，覆盖从资料解析、题目生成、测验评测到错题巩固的闭环，以及**完整的游戏化系统**。通过SSE实现流畅的处理体验，结合DashScope实现智能化内容处理。**游戏化系统包含用户档案、成就系统、每日任务、经验管理、方向探索进度等功能**，为用户提供持续的学习动力和成就感。建议在生产环境中完善鉴权、限流与监控，并持续优化数据库索引与外部服务调用策略。

## 附录

### API版本控制与兼容性
- 当前版本：0.1.0
- 版本位置：应用元数据与路由注册处
- 兼容性建议：
  - 新增字段使用可选字段，保持向后兼容
  - 修改现有字段需引入新版本端点或迁移脚本
  - 保持SSE事件结构稳定，新增字段需向后兼容
  - **游戏化API作为新增模块，不影响现有API兼容性**

**章节来源**
- [backend/app/main.py](file://backend/app/main.py#L19-L25)

### 认证与授权
- 当前实现：无显式鉴权装饰器
- 建议方案：
  - JWT令牌：登录接口返回token，后续请求在Header携带Authorization
  - 中间件：全局校验token有效性与权限
  - 资源级权限：按用户隔离方向/资料/测验等资源
  - **游戏化模块建议添加用户ID验证，确保数据隔离**

### SSE（Server-Sent Events）说明
- 用途：资料处理进度实时推送
- 响应类型：text/event-stream
- 事件格式：JSON对象，包含step、progress、message、data/material_id等字段
- 客户端消费：使用EventSource监听，注意断线重连与错误处理

**章节来源**
- [backend/app/api/materials.py](file://backend/app/api/materials.py#L164-L185)
- [backend/app/api/materials.py](file://backend/app/api/materials.py#L27-L80)

### 数据模型概览
```mermaid
erDiagram
DIRECTION ||--o{ MATERIAL : "拥有"
DIRECTION ||--o{ EXAM : "拥有"
DIRECTION ||--o{ PARSETASK : "拥有"
DIRECTION ||--o{ DIRECTIONPROGRESS : "拥有"
MATERIAL ||--o{ QUESTION : "生成"
MATERIAL ||--o{ ANSWER : "被回答(间接)"
QUESTION ||--o{ ANSWER : "被回答"
QUESTION ||--o{ MISTAKE : "产生"
EXAM ||--o{ ANSWER : "包含"
ANSWER ||--|| MISTAKE : "对应"
USERPROFILE ||--o{ USERACHIEVEMENT : "解锁"
USERPROFILE ||--o{ USERDAILYTASK : "拥有"
USERPROFILE ||--o{ EXPMLOG : "获得"
USERPROFILE ||--o{ DIRECTIONPROGRESS : "探索"
```

**图表来源**
- [backend/app/models/models.py](file://backend/app/models/models.py#L63-L321)

### 示例请求与响应（路径指引）
- 学习方向
  - POST /api/directions
    - 请求体参考：DirectionCreate
    - 响应体参考：DirectionResponse
  - 参考路径：[backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L23-L34)
- 学习资料
  - POST /api/materials
    - 请求体参考：MaterialCreate
    - 响应体参考：MaterialResponse
  - GET /api/materials/{material_id}/progress
    - 响应类型：text/event-stream
  - 参考路径：[backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L44-L58)
- 题目
  - PATCH /api/questions/{question_id}
    - 请求体参考：QuestionUpdate
  - 参考路径：[backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L92-L99)
- 测验
  - POST /api/exams
    - 请求体参考：ExamCreate
  - POST /api/exams/{exam_id}/submit
    - 请求体参考：ExamSubmit
  - 参考路径：[backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L103-L110)
- 错题
  - PATCH /api/mistakes/{mistake_id}
    - 请求体参考：MistakeUpdate
  - 参考路径：[backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L186-L189)
- 知识解析
  - POST /api/parse/file
    - 表单字段：title、direction_id、file
  - 参考路径：[backend/app/api/parse.py](file://backend/app/api/parse.py#L26-L37)
- 游戏化系统
  - GET /api/gamification/profile
    - 响应体参考：UserProfileResponse
  - GET /api/gamification/achievements
    - 响应体参考：AchievementsListResponse
  - GET /api/gamification/daily-tasks
    - 响应体参考：DailyTaskResponse数组
  - GET /api/gamification/exp-logs?limit=20&offset=0
    - 响应体参考：ExpLogResponse数组
  - 参考路径：[backend/app/schemas/schemas.py](file://backend/app/schemas/schemas.py#L268-L371)

### 游戏化系统详细说明

#### 用户档案（UserProfile）
- 功能：存储用户基本信息、等级、经验值、称号、连续登录天数
- 关键字段：user_id、username、level、exp、total_exp、title、streak_days、last_login_date
- 自动更新：每次获取档案时自动更新连续登录天数

#### 成就系统（UserAchievement）
- 功能：记录用户已解锁的成就
- 成就类型：测验类、错题类、资料类、探索类、连续学习类
- 解锁条件：基于用户统计数据自动检测
- 稀有度：common、rare、epic、legendary，对应不同经验奖励

#### 每日任务（UserDailyTask）
- 功能：为用户生成每日可完成的任务
- 任务类型：测验、完美成绩、错题复习、资料上传、题海战术
- 随机生成：每天从任务池中随机选择3个任务
- 进度跟踪：自动更新任务完成进度

#### 经验管理系统（ExpLog）
- 功能：记录所有经验值获取来源
- 来源类型：测验完成、错题掌握、资料上传、解析完成、每日任务、成就解锁、连续登录奖励
- 日志查询：支持分页查询，按时间倒序排列

#### 方向探索进度（DirectionProgress）
- 功能：跟踪用户在各个学习方向的探索进度
- 指标：题目总数、已答题目数、答对题目数、已掌握知识点数、探索率
- 实时计算：未记录的进度实时计算

**章节来源**
- [backend/app/models/models.py](file://backend/app/models/models.py#L238-L321)
- [backend/app/core/achievements.py](file://backend/app/core/achievements.py#L1-L121)
- [backend/app/core/daily_tasks.py](file://backend/app/core/daily_tasks.py#L1-L53)
- [backend/app/core/level_config.py](file://backend/app/core/level_config.py#L1-L59)
- [backend/app/services/gamification_service.py](file://backend/app/services/gamification_service.py#L1-L482)