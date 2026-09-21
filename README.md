> **Portfolio status / 作品集状态：FLAGSHIP · Agent Systems**
> Canonical independent flagship repository; cross-listed with Engineering Tools Lab.

# AI Engineering Project OS

**版本: v1.0.0**
**状态: CORE EXIT GATE PASSED**

> 把用户的 AI 项目从当前状态一步步推进到生产级。

## 一句话定位

**AI 工程升级教练**：不是课程平台，不是普通代码助手，而是把普通 AI 项目升级成有工程深度、有验证证据、能经得住技术面试的项目。

## 核心价值链

```
用户项目
  ↓
自动审计 → 判断成熟度
  ↓
识别缺口 → 生成升级任务
  ↓
AI 执行 → 真实代码改造
  ↓
自动测试 → 验证门验收
  ↓
保存证据 → 版本记录
  ↓
技术面试 → 连续追问
  ↓
形成可验证的工程能力档案
```

## 六大核心智能体

| 智能体 | 职责 |
|--------|------|
| **项目审计** | 读取代码，判断成熟度，识别缺口 |
| **升级规划** | 根据缺口生成升级任务，决定优先级 |
| **工程导师** | 解释为什么需要这个改动 |
| **执行运行** | 安全修改代码，执行命令，运行测试 |
| **验证引擎** | 检查真实证据，判断任务是否完成 |
| **面试引擎** | 基于真实代码进行技术追问 |

## 成熟度模型

| 级别 | 证据要求 |
|------|----------|
| **想法** | 问题、用户、输入、输出、数据来源、核心技术 |
| **演示版** | 核心流程可端到端运行 |
| **MVP** | 数据持久化、错误处理、基本测试 |
| **准生产** | 评测体系、安全、监控、日志、链路追踪 |
| **生产级** | 真实运行环境、容量规划、故障恢复 |

## 快速开始

```bash
# 1. 克隆仓库
git clone https://github.com/Benjamindaoson/ai-engineering-project-os.git
cd ai-engineering-project-os

# 2. 安装依赖
pip install -r requirements.txt
cd apps/web && npm install && cd ../..

# 3. 启动后端
cd apps/api && python -m uvicorn main:app --reload

# 4. 启动前端 (另一个终端)
cd apps/web && npm run dev
```

访问 `http://localhost:3000` 开始使用。

## 质量门验证

```bash
# 后端测试
pytest tests/ -v

# 前端类型检查
cd apps/web && npm run typecheck

# 前端构建
npm run build

# Playwright E2E
npm run test:e2e
```

**当前状态**: 46 passed | PASS | SUCCESS | 2 passed

## 项目结构

```
ai-engineering-project-os/
├── apps/
│   ├── api/              # FastAPI 后端
│   │   └── main.py       # 40+ API 端点
│   └── web/              # Next.js 14 前端
│       ├── app/          # 6个核心页面
│       └── tests/e2e/    # Playwright E2E 测试
├── services/              # 六大核心智能体
│   ├── project-auditor/   # 项目审计
│   ├── upgrade-planner/   # 升级规划
│   ├── engineering-mentor/ # 工程导师
│   ├── execution-runtime/ # 执行运行
│   ├── verification-engine/ # 验证引擎
│   └── interview-engine/  # 面试引擎
├── packages/              # 核心包
│   ├── contracts/         # 数据模型
│   ├── maturity-model/   # 成熟度模型
│   ├── evidence-model/   # 证据模型
│   └── project-intelligence/ # 项目理解
├── packages/database/     # 数据库层 (Alembic)
├── docs/                  # 文档
│   └── FINAL_PRODUCT_VALIDATION.md  # 完整验证报告
├── tests/                 # 后端测试
└── workspaces/           # 项目隔离工作区
```

## 已验证的三个真实项目

| 项目 | 文件数 | 代码行数 | 成熟度 |
|------|--------|----------|--------|
| AIEduRAG | 186 | 14,437 | MVP |
| enterprise-data-agent | 378 | 38,351 | MVP |
| SalesBoost | 1,424 | 167,189 | MVP |

## API 端点 (40+)

```bash
# 项目管理
POST   /api/projects/import          # 导入项目
POST   /api/projects/{id}/audit     # 项目审计
POST   /api/projects/{id}/plan     # 生成升级计划
GET    /api/projects/{id}/evidence # 获取证据
GET    /api/projects/{id}/versions # 获取版本

# 任务执行
POST   /api/tasks/{id}/execute     # 执行任务
POST   /api/executions/{id}/verify  # 验证结果

# 面试
POST   /api/projects/{id}/interview # 开始面试
POST   /api/interviews/{id}/answers # 提交回答

# 实验
POST   /api/projects/{id}/experiments
POST   /api/experiments/{id}/runs
```

## 核心技术栈

- **后端**: Python 3.12, FastAPI, SQLAlchemy, SQLite
- **前端**: Next.js 14, React, TypeScript, TailwindCSS
- **测试**: pytest, Playwright
- **数据库**: SQLite + Alembic (18 tables)

## License

MIT
