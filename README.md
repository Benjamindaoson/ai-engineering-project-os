# AI Engineering Project OS

中文暂定名：**AI 工程项目升级系统**

把用户已经做过的 AI 项目，或者只有一个想法的 AI 项目，从当前状态一步步推进到演示版、最小可用版本、准生产级、生产级。

## 核心价值

> **真正的产品核心是：用户自己的项目**

```
用户自己的项目
↓
自动审计
↓
判断当前成熟度
↓
识别工程缺口
↓
生成下一阶段升级路线
↓
解释为什么需要升级
↓
用户 + AI 完成工程改造
↓
自动测试 / 运行 / 评测
↓
证据门验收
↓
记录改造前后差异
↓
更新项目成熟度
↓
模拟真实技术面试连续追问
↓
发现理解缺口
↓
继续学习和改造
↓
形成可验证的工程能力档案
```

## 六大核心智能体

1. **项目审计智能体** - 读取项目，理解项目，建立事实清单，判断当前成熟度，找出缺口
2. **升级规划智能体** - 根据当前项目状态和用户目标，决定下一步最值得做什么
3. **工程导师智能体** - 在每个升级任务开始前解释为什么需要做这个改动
4. **工程执行智能体** - 安全地修改代码，执行命令，运行测试
5. **验证智能体** - 验证任务是否真正完成，不是读 README，而是检查真实证据
6. **面试智能体** - 基于真实项目、代码、决策、实验，进行连续技术追问

## 成熟度模型

每一级必须有清晰证据：

- **第一级：想法** - 问题、用户、输入、输出、数据来源、核心技术
- **第二级：演示版** - 核心流程可端到端运行，关键能力可演示
- **第三级：最小可用版本** - 真实用户主流程，数据持久化，错误处理，基本测试
- **第四级：准生产级** - 评测体系、权限、安全、监控、日志、链路追踪、失败恢复
- **第五级：生产级** - 真实运行环境，持续监控，容量规划，故障恢复，版本发布，回滚

## 项目结构

```
ai-engineering-project-os/
├── apps/
│   ├── web/              # Next.js 前端
│   └── api/              # FastAPI 后端
├── services/              # 六个核心智能体服务
│   ├── project-auditor/  # 项目审计
│   ├── upgrade-planner/  # 升级规划
│   ├── engineering-mentor/  # 工程导师
│   ├── execution-runtime/   # 执行运行
│   ├── verification-engine/ # 验证引擎
│   └── interview-engine/    # 面试引擎
├── packages/              # 核心包
│   ├── contracts/        # 数据模型
│   ├── maturity-model/   # 成熟度模型
│   ├── evidence-model/   # 证据模型
│   └── project-intelligence/  # 项目理解
├── data/                 # 数据目录
│   ├── fixtures/        # 测试数据
│   └── benchmarks/      # 评测基准
├── docs/                 # 文档
├── tests/                # 测试
└── scripts/              # 脚本
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- npm 或 pnpm

### 安装

```bash
# 克隆仓库
git clone https://github.com/Benjamindaoson/ai-engineering-project-os.git
cd ai-engineering-project-os

# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd apps/web
npm install
```

### 运行

```bash
# 启动后端 API
cd apps/api
python main.py

# 启动前端开发服务器 (另一个终端)
cd apps/web
npm run dev
```

## 六个核心页面

1. **项目导入** - 导入 GitHub 仓库或本地项目
2. **项目体检** - 显示当前成熟度和各维度评分
3. **升级地图** - 展示当前位置和升级路线
4. **工程任务** - 当前任务的详情和执行
5. **证据墙** - 项目版本的变更和证据记录
6. **面试工作台** - 基于真实项目的技术面试

## 开发原则

1. **先审计，后写代码** - 首先输出能力复用矩阵和产品差距分析
2. **不允许假成功** - 未验证的必须明确标记
3. **不允许编指标** - 所有数据必须来自真实运行
4. **不允许 README 驱动判断** - README 只能作为声明，必须检查代码
5. **用户已有仓库默认只读** - 源仓库保持原始状态
6. **不要为了多智能体而多智能体** - 六个核心智能体足够

## 端到端质量门

每一阶段交付前必须运行：

- 后端单元测试
- 前端类型检查
- 前端构建
- 接口冒烟测试
- 数据库迁移测试
- 至少一个真实仓库导入测试
- 项目审计测试
- 升级计划测试
- 证据写入测试
- 面试追问测试

## 公开数据与评测

- **SWE-bench Verified**: 500 条经过人工确认的软件工程任务
- **RepoBench Python**: 跨文件代码理解评测

## 参考项目

- [OpenHands](https://github.com/OpenHands/OpenHands) - 代码智能体运行方式参考
- [SWE-bench](https://github.com/SWE-bench/SWE-bench) - 真实软件工程任务定义参考
- [RepoBench](https://github.com/Leolty/repobench) - 仓库级代码理解参考

## License

MIT
