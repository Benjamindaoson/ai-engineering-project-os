# 现有资产审计报告

**日期**: 2026-09-18
**审计范围**: ai-agent-engineering-lab, agentic-delivery-os, AIEduRAG

---

## 一、ai-agent-engineering-lab 审计

### 1.1 目录结构
```
ai-agent-engineering-lab/
├── AI_Agent_Builder/         # 核心产品目录
│   ├── apps/
│   │   ├── web/              # Next.js 前端
│   │   ├── api/              # API 服务
│   │   ├── agent-runner/     # Agent 运行环境
│   │   └── worker/           # 后台任务处理
│   ├── infra/                # 基础设施配置
│   └── docs/                 # 文档
├── production-platform/      # 生产平台检查清单
├── case-studies/             # 案例研究
├── frameworks/               # 框架示例
├── protocols/                # 协议定义
└── [40+ 框架演示项目]
```

### 1.2 可复用能力

| 能力模块 | 位置 | 可复用程度 | 说明 |
|---------|------|-----------|------|
| Next.js Web 框架 | `AI_Agent_Builder/apps/web/` | 高 | 完整的页面结构和组件 |
| 学习路线组件 | `web/app/learning-plan/` | 中 | 需要改造为项目升级路线 |
| 能力图谱组件 | `web/app/skill-map/` | 中 | 需要改造为项目成熟度图 |
| Evidence Store | `web/app/projects/` | 中 | 项目证据存储模式可参考 |
| Skill Passport | `web/app/passport/` | 中 | 能力档案模式可参考 |
| Agent Review | `web/app/reviews/` | 中 | 代码审查模式可参考 |
| 项目实验室 | `web/app/lab/` | 中 | 沙箱运行模式可参考 |

### 1.3 不可直接复用

- 课程和关卡系统（与新产品定位冲突）
- 学习计划生成逻辑（需要重新设计）
- 固定项目训练（需要改为用户项目导入）

### 1.4 技术栈
- Frontend: Next.js 15, TypeScript, TailwindCSS
- Backend: FastAPI (Python)
- Database: SQLite / PostgreSQL
- Agent: 自研 Agent 框架

---

## 二、agentic-delivery-os 审计

### 2.1 目录结构
```
agentic-delivery-os/
├── backend/
│   ├── orchestration/        # 任务编排
│   ├── api/                  # API 端点
│   ├── schemas/              # 数据模型
│   └── [其他模块]
├── runtime/                  # 核心运行时
│   ├── execution_graph/      # 执行图
│   ├── contracts/            # 组件契约
│   ├── governance/           # 治理引擎
│   ├── agents/               # 各类型 Agent
│   ├── planning/             # 规划器
│   ├── learning/             # 学习系统
│   ├── evaluation/           # 评测引擎
│   └── [50+ 子模块]
├── frontend/                 # 前端
├── configs/                  # 配置文件
├── tests/                    # 测试
└── docs/                     # 文档
```

### 2.2 可复用能力

| 能力模块 | 位置 | 可复用程度 | 说明 |
|---------|------|-----------|------|
| 执行引擎 | `runtime/execution_graph/execution_engine.py` | 高 | 任务执行和跟踪模式 |
| 组件契约 | `runtime/contracts/` | 高 | 显式组件契约定义 |
| 治理检查点 | `runtime/governance/` | 高 | 质量门和成本门模式 |
| 执行图 DAG | `runtime/execution_graph/` | 高 | 可进化 DAG 模式 |
| 状态管理 | `runtime/state/` | 高 | 任务状态迁移 |
| Trace 记录 | `runtime/platform/` | 高 | 执行轨迹存储 |
| 任务规格 | `backend/` | 高 | 任务定义模式 |
| 执行计划 | `runtime/execution_plan/` | 高 | 条件执行计划模式 |
| 评测反馈 | `runtime/evaluation/` | 中 | 评测反馈循环 |

### 2.3 需要提取核心概念，重新实现

- L5/L6/L7/L8 成熟度定义 → 改为：想法→演示版→最小可用→准生产→生产
- 多租户系统（对于第一阶段过于复杂）
- 分布式执行（对于第一阶段过于复杂）
- 学习控制器（可以后期加入）
- 策略学习（可以后期加入）

### 2.4 核心模式提炼

1. **任务规格 → 执行 → 验证 → 交付** 的完整闭环
2. **治理检查点**：在关键节点进行质量/成本验证
3. **执行图**：用 DAG 表示任务依赖关系
4. **显式契约**：组件之间通过明确接口交互
5. **轨迹记录**：所有操作都有可追溯的记录

---

## 三、AIEduRAG 审计

### 3.1 目录结构
```
AIEduRAG/
├── api/                      # API 端点
├── core/                     # 核心逻辑
│   ├── evidence.py           # 证据模型
│   ├── retrieval_gate.py     # 证据门
│   ├── reranker.py           # 重新排序
│   ├── code_retriever.py     # 代码检索
│   └── [其他模块]
├── evaluation/               # 评测模块
├── ingestion/                # 数据摄入
├── models/                  # 数据模型
├── services/                 # 服务层
├── scripts/                  # 脚本
└── docs/                     # 文档
```

### 3.2 可复用能力

| 能力模块 | 位置 | 可复用程度 | 说明 |
|---------|------|-----------|------|
| 证据模型 | `core/evidence.py` | 高 | Evidence/EvidencePacket 数据结构 |
| 证据门 | `core/retrieval_gate.py` | 高 | 证据质量验证模式 |
| 访问控制 | `core/access_control.py` | 高 | 权限控制模式 |
| 检索评测 | `evaluation/` | 高 | 检索质量评估 |
| 知识检索 | `core/retrieval/` | 高 | 检索策略模式 |
| 错误匹配 | `core/error_matcher.py` | 中 | 错误诊断模式 |
| 意图路由 | `core/intent_router.py` | 中 | 查询分类模式 |
| 嵌入模型 | `core/embeddings.py` | 高 | 嵌入服务抽象 |
| LLM 调用 | `core/llm.py` | 高 | LLM 服务抽象 |

### 3.3 关键洞察

1. **Evidence 模型**：每个检索结果绑定证据（来源、分数、行号）
2. **Gate Decision**：通过显式决策（accept/retry/clarify_or_refuse）控制流程
3. **混合检索**：支持多种检索策略组合
4. **评测体系**：包含 retrieval_evaluator 和 ragas_evaluator

---

## 四、现有能力复用矩阵

### 4.1 新产品核心能力映射

| 新产品能力 | 来源仓库 | 复用模块 | 复用方式 |
|-----------|---------|---------|---------|
| 项目导入 | AIEduRAG | 知识检索模式 | 参考其索引和检索逻辑 |
| 代码分析 | AIEduRAG | code_retriever | 改造用于项目代码理解 |
| 证据存储 | AIEduRAG | evidence.py | 直接复用数据结构 |
| 任务执行 | agentic-delivery-os | execution_engine | 提取核心模式重新实现 |
| 执行图 | agentic-delivery-os | execution_graph | 简化后复用 DAG 模式 |
| 质量门 | agentic-delivery-os | governance | 提取验证模式 |
| 轨迹记录 | agentic-delivery-os | trace_store | 直接复用 |
| 前端框架 | ai-agent-engineering-lab | web/app | 参考页面结构 |
| 评测引擎 | AIEduRAG | evaluation/ | 复用评测逻辑 |

### 4.2 不能复用的部分

| 原能力 | 原因 |
|-------|------|
| 课程/关卡系统 | 与新产品定位冲突 |
| 固定学习路径 | 改为用户项目驱动 |
| L6/L7/L8 成熟度 | 改为5级通用模型 |
| 多租户隔离 | 第一阶段不需要 |
| 分布式执行 | 第一阶段不需要 |
| 策略学习 | 可后期加入 |

---

## 五、产品差距分析

### 5.1 已有能力

- ✅ 完整的 Web 前端框架
- ✅ 任务执行和跟踪
- ✅ 证据存储和验证
- ✅ 评测体系
- ✅ 代码检索
- ✅ 质量门模式
- ✅ 轨迹记录

### 5.2 缺失能力

| 能力 | 当前状态 | 需要实现 |
|------|---------|---------|
| GitHub 项目导入 | 无 | 全新开发 |
| 项目审计智能体 | 无 | 全新开发 |
| 成熟度评估 | 无 | 基于成熟度模型全新开发 |
| 升级规划智能体 | 无 | 全新开发 |
| 工程导师智能体 | 无 | 全新开发 |
| 验证智能体 | 部分 | 基于 AIEduRAG 扩展 |
| 面试智能体 | 无 | 全新开发 |
| 前后对比记录 | 无 | 全新开发 |

### 5.3 需要改造的部分

| 模块 | 现有状态 | 改造方向 |
|------|---------|---------|
| 前端页面 | 课程导向 | 改为项目导向 |
| 证据存储 | RAG 证据 | 扩展为工程证据 |
| 评测体系 | 检索评测 | 扩展为工程能力评测 |

---

## 六、新产品目标架构

### 6.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        Web UI (Next.js)                      │
├─────────────────────────────────────────────────────────────┤
│  项目导入 │ 项目体检 │ 升级地图 │ 工程任务 │ 证据墙 │ 面试台  │
├─────────────────────────────────────────────────────────────┤
│                      API Gateway (FastAPI)                   │
├──────────┬──────────┬──────────┬──────────┬──────────┬───────┤
│ 项目审计  │ 升级规划  │ 工程导师  │ 执行运行  │  验证    │ 面试  │
│  智能体   │  智能体   │  智能体   │  智能体   │  智能体  │ 智能体│
├──────────┴──────────┴──────────┴──────────┴──────────┴───────┤
│                    核心包 (packages/)                        │
│  contracts │ maturity-model │ evidence-model │ project-intel │
├─────────────────────────────────────────────────────────────┤
│                    数据层 (SQLite/JSON)                      │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 核心数据流

```
用户项目 → 导入 → 代码扫描 → 事实抽取 → 成熟度评估
                                           ↓
                                    缺口识别 → 升级规划
                                           ↓
                              用户选择任务 → 工程导师解释
                                           ↓
                              执行运行 → 自动验证 → 证据保存
                                           ↓
                              面试追问 → 能力档案
```

---

## 七、迁移方案

### 7.1 第一阶段（当前）

1. 复用 AIEduRAG 的 Evidence 模型和 Gate 模式
2. 复用 agentic-delivery-os 的执行图和轨迹记录模式
3. 参考 ai-agent-engineering-lab 的前端结构
4. 全部重新实现 6 个核心智能体

### 7.2 第二阶段（后续）

1. 引入 agentic-delivery-os 的治理检查点
2. 引入多租户支持
3. 引入学习控制器

### 7.3 不迁移的部分

1. 课程/关卡系统
2. 固定学习路径
3. L6/L7/L8 成熟度模型
4. 多租户隔离
5. 分布式执行
