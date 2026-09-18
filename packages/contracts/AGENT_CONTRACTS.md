# AI Engineering Project OS - Agent Contracts

## 六大核心智能体职责边界

---

## 1. ProjectAuditorAgent (项目审计智能体)

### 职责
理解并审计用户导入的项目，建立事实清单，判断成熟度，识别缺口。

### 输入
```typescript
interface AuditorInput {
  project_path: string;
  github_url?: string;
  user_goals?: string[];
}
```

### 输出
```typescript
interface AuditorOutput {
  project_facts: ProjectFacts;
  maturity_assessment: MaturityAssessment;
  gaps: Gap[];
  raw_observations: RawObservation[];
}

interface RawObservation {
  category: string;
  finding: string;
  evidence: Evidence[];
  source_file?: string;
  source_lines?: [number, number];
}
```

### 职责边界
- ✅ 读取并理解项目代码
- ✅ 建立项目事实清单
- ✅ 判断当前成熟度
- ✅ 识别能力缺口
- ❌ 不修改代码
- ❌ 不生成升级计划
- ❌ 不执行任务

---

## 2. UpgradePlannerAgent (升级规划智能体)

### 职责
根据当前项目状态和用户目标，决定下一步最值得做什么。

### 输入
```typescript
interface PlannerInput {
  project_facts: ProjectFacts;
  maturity_assessment: MaturityAssessment;
  gaps: Gap[];
  user_goals: string[];
  user_constraints?: {
    time_available?: string;
    skill_level?: "junior" | "mid" | "senior";
    target_maturity?: MaturityLevel;
  };
}
```

### 输出
```typescript
interface PlannerOutput {
  recommended_tasks: UpgradeTask[];
  prioritization_rationale: string;
  immediate_next_steps: string[];
  estimated_total_effort: string;
}
```

### 职责边界
- ✅ 分析缺口优先级
- ✅ 生成升级任务
- ✅ 决定任务顺序
- ✅ 解释为什么选择这些任务
- ❌ 不解释技术细节
- ❌ 不执行代码修改
- ❌ 不验证任务完成

---

## 3. EngineeringMentorAgent (工程导师智能体)

### 职责
在每个升级任务开始前，解释为什么需要做这个改动，如何做，生产环境怎么处理。

### 输入
```typescript
interface MentorInput {
  upgrade_task: UpgradeTask;
  project_context: {
    tech_stack: string[];
    existing_patterns: string[];
    project_type: ProjectType;
  };
}
```

### 输出
```typescript
interface MentorOutput {
  learning_content: LearningContent;
  code_examples?: {
    before: string;
    after: string;
    explanation: string;
  };
  related_concepts: {
    concept: string;
    explanation: string;
    relevance: string;
  }[];
  common_pitfalls: string[];
}
```

### 职责边界
- ✅ 解释问题背景
- ✅ 解释最简单的解决方案
- ✅ 解释为什么简单方案不够
- ✅ 解释生产环境通常做法
- ✅ 推荐适合该项目的方案
- ✅ 解释如何验证
- ✅ 提供面试问题预览
- ❌ 不直接写生产代码
- ❌ 不执行任何操作

---

## 4. ExecutionAgent (工程执行智能体)

### 职责
安全地修改代码，执行命令，运行测试。

### 输入
```typescript
interface ExecutionInput {
  task: UpgradeTask;
  project_path: string;
  learning_content: LearningContent;
  save_baseline: boolean;
}
```

### 输出
```typescript
interface ExecutionOutput {
  execution_record: ExecutionRecord;
  changes_summary: {
    files_added: string[];
    files_modified: string[];
    files_deleted: string[];
  };
  test_results: TestResult[];
  baseline_saved: boolean;
  error?: string;
}
```

### 职责边界
- ✅ 修改代码
- ✅ 新增测试
- ✅ 执行命令
- ✅ 运行测试
- ✅ 保存基线
- ✅ 记录所有变更
- ❌ 不能跳过失败测试
- ❌ 不能删除质量门
- ❌ 不能修改标准答案
- ❌ 不能不保存基线就修改

---

## 5. VerificationAgent (验证智能体)

### 职责
验证任务是否真正完成，不是读 README，而是检查真实证据。

### 输入
```typescript
interface VerificationInput {
  task: UpgradeTask;
  execution_record: ExecutionRecord;
  project_path: string;
}
```

### 输出
```typescript
interface VerificationOutput {
  verification_results: {
    criterion: string;
    status: "passed" | "failed" | "partial" | "unverifiable";
    evidence: Evidence[];
    details: string;
  }[];
  overall_status: "passed" | "partial" | "failed" | "unverifiable";
  missing_evidence: {
    type: string;
    description: string;
  }[];
  recommendations: string[];
}
```

### 职责边界
- ✅ 检查代码实现
- ✅ 运行验证测试
- ✅ 检查测试通过
- ✅ 检查运行证据
- ✅ 给出通过/失败/部分/无法验证
- ❌ 不能没有证据就判定通过
- ❌ 不能只看 README
- ❌ 不能修改代码来"通过"验证

---

## 6. InterviewAgent (面试智能体)

### 职责
基于真实项目、代码、决策、实验，进行连续技术追问。

### 输入
```typescript
interface InterviewInput {
  project_facts: ProjectFacts;
  execution_records: ExecutionRecord[];
  architecture_decisions: ArchitectureDecision[];
  current_maturity: MaturityAssessment;
}
```

### 输出
```typescript
interface InterviewOutput {
  session: InterviewSession;
  initial_questions: InterviewQuestion[];
  gap_analysis: {
    gap_type: "knowledge" | "engineering" | "evidence" | "experiment";
    description: string;
    related_task_id?: string;
  }[];
}
```

### 职责边界
- ✅ 生成基于真实代码的问题
- ✅ 连续追问
- ✅ 映射回答质量到缺口
- ✅ 发现知识/工程/证据/实验缺口
- ❌ 不能只问标准面试题
- ❌ 不能不问代码细节
- ❌ 不能不记录回答质量

---

## 智能体间契约

### 数据流
```
User Project
    ↓
[ProjectAuditorAgent] → ProjectFacts + MaturityAssessment + Gaps
    ↓
[UpgradePlannerAgent] → UpgradeTask[]
    ↓
[EngineeringMentorAgent] → LearningContent
    ↓
[ExecutionAgent] → ExecutionRecord
    ↓
[VerificationAgent] → VerificationOutput
    ↓
[InterviewAgent] → InterviewSession + GapAnalysis
```

### 状态持久化

每个智能体完成工作后，必须持久化：
- 输入参数
- 输出结果
- 执行时间
- 错误信息（如有）

这样可以：
1. 支持断点续传
2. 支持审计
3. 支持能力档案生成

---

## 验证标准

### 每个智能体必须满足

1. **可重复性**: 相同输入必须产生相同输出
2. **可审计性**: 所有操作必须可追溯
3. **失败安全**: 失败时必须保存状态
4. **证据驱动**: 所有判断必须有证据支持
