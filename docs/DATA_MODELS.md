# 数据模型定义

## 核心实体

### 1. User (用户)
```typescript
interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
  updated_at: string;
}
```

### 2. Project (项目)
```typescript
interface Project {
  id: string;
  user_id: string;
  name: string;
  description: string;
  github_url: string | null;
  local_path: string | null;
  tech_stack: string[];
  current_maturity: MaturityLevel;
  created_at: string;
  updated_at: string;
}
```

### 3. ProjectSnapshot (项目快照)
```typescript
interface ProjectSnapshot {
  id: string;
  project_id: string;
  commit_hash: string;
  snapshot_path: string;
  created_at: string;
  facts: ProjectFacts;
  maturity: MaturityAssessment;
}
```

### 4. ProjectFacts (项目事实)
```typescript
interface ProjectFacts {
  // 项目基本信息
  project_name: string;
  project_type: "rag" | "agent" | "chatbot" | "api" | "fullstack" | "other";
  main_language: string[];
  frameworks: string[];
  database: string[];
  deployment: string[];
  
  // 代码规模
  total_files: number;
  total_lines: number;
  code_lines: number;
  test_files: number;
  test_lines: number;
  config_files: number;
  
  // 实现状态
  implementation_status: {
    core_features: ImplementationStatus[];
    data_layer: ImplementationStatus[];
    api_layer: ImplementationStatus[];
    auth: ImplementationStatus[];
    error_handling: ImplementationStatus[];
    testing: ImplementationStatus[];
    evaluation: ImplementationStatus[];
    deployment: ImplementationStatus[];
    monitoring: ImplementationStatus[];
  };
  
  // 文档状态
  has_readme: boolean;
  has_api_docs: boolean;
  has_deployment_docs: boolean;
  has_contributing: boolean;
}

type ImplementationStatus = {
  feature: string;
  status: "fully_implemented" | "partially_implemented" | "documented_only" | "planned" | "missing";
  evidence: Evidence[];
  verification_method: string;
};
```

### 5. MaturityLevel (成熟度级别)
```typescript
type MaturityLevel = "idea" | "demo" | "mvp" | "pre_production" | "production";

interface MaturityCriteria {
  idea: {
    problem_defined: boolean;
    target_users_defined: boolean;
    inputs_defined: boolean;
    outputs_defined: boolean;
    data_source_defined: boolean;
    core_tech_feasible: boolean;
  };
  
  demo: {
    end_to_end_flow: boolean;
    basic_io: boolean;
    key_features_demoable: boolean;
    not_fake_data: boolean;
  };
  
  mvp: {
    real_user_flow: boolean;
    data_persistence: boolean;
    error_handling: boolean;
    basic_tests: boolean;
    basic_evaluation: boolean;
    repeatable: boolean;
    basic_deployment: boolean;
  };
  
  pre_production: {
    evaluation_system: boolean;
    permissions: boolean;
    security: boolean;
    monitoring: boolean;
    logging: boolean;
    tracing: boolean;
    data_versioning: boolean;
    model_versioning: boolean;
    failure_recovery: boolean;
    timeout: boolean;
    retry: boolean;
    fallback: boolean;
    caching: boolean;
    rate_limiting: boolean;
    cost_control: boolean;
    automated_tests: boolean;
    regression_tests: boolean;
    load_tests: boolean;
    sensitive_data_handling: boolean;
  };
  
  production: {
    real_environment: boolean;
    continuous_monitoring: boolean;
    capacity: boolean;
    stability: boolean;
    fault_recovery: boolean;
    version_release: boolean;
    rollback: boolean;
    data_governance: boolean;
    audit: boolean;
    cost_governance: boolean;
    online_error_closure: boolean;
    continuous_evaluation: boolean;
    security_governance: boolean;
    multi_tenant: boolean;
  };
}
```

### 6. MaturityAssessment (成熟度评估)
```typescript
interface MaturityAssessment {
  overall_level: MaturityLevel;
  dimension_scores: {
    core_features: DimensionScore;
    data: DimensionScore;
    model: DimensionScore;
    retrieval: DimensionScore;
    agent: DimensionScore;
    evaluation: DimensionScore;
    security: DimensionScore;
    permissions: DimensionScore;
    reliability: DimensionScore;
    monitoring: DimensionScore;
    deployment: DimensionScore;
    cost: DimensionScore;
    maintainability: DimensionScore;
  };
  evidence: Evidence[];
  blockers: Gap[];
}

interface DimensionScore {
  level: MaturityLevel;
  progress: number; // 0-100
  criteria_met: string[];
  criteria_missing: string[];
}
```

### 7. Gap (能力缺口)
```typescript
interface Gap {
  id: string;
  project_id: string;
  dimension: string;
  description: string;
  current_state: string;
  target_state: string;
  priority: "critical" | "high" | "medium" | "low";
  effort_estimate: "small" | "medium" | "large";
  risk: "low" | "medium" | "high";
  related_criteria: string[];
}
```

### 8. UpgradeTask (升级任务)
```typescript
interface UpgradeTask {
  id: string;
  project_id: string;
  gap_id: string;
  title: string;
  description: string;
  learning_content: LearningContent;
  completion_criteria: CompletionCriterion[];
  estimated_effort: string;
  prerequisites: string[];
  status: "pending" | "in_progress" | "completed" | "failed";
  created_at: string;
  completed_at: string | null;
}

interface LearningContent {
  problem_explanation: string;
  why_important: string;
  simple_solution: string;
  why_simple_not_enough: string;
  production_approach: string;
  recommended_solution: string;
  reasoning: string;
  verification_method: string;
  interview_questions: string[];
}

interface CompletionCriterion {
  criterion: string;
  verification_method: string;
  evidence_type: "code" | "test" | "run_result" | "benchmark" | "config";
}
```

### 9. ExecutionRecord (执行记录)
```typescript
interface ExecutionRecord {
  id: string;
  task_id: string;
  project_id: string;
  before_snapshot: ProjectSnapshot;
  after_snapshot: ProjectSnapshot | null;
  changes: CodeChange[];
  execution_log: string;
  test_results: TestResult[];
  benchmark_results: BenchmarkResult[];
  status: "running" | "completed" | "failed";
  started_at: string;
  completed_at: string | null;
  error: string | null;
}

interface CodeChange {
  file_path: string;
  change_type: "added" | "modified" | "deleted";
  diff: string;
  purpose: string;
}

interface TestResult {
  test_name: string;
  passed: boolean;
  duration_ms: number;
  error: string | null;
}

interface BenchmarkResult {
  metric: string;
  before_value: number | null;
  after_value: number | null;
  improvement: number | null;
  unit: string;
}
```

### 10. Evidence (证据)
```typescript
interface Evidence {
  id: string;
  type: "code" | "test" | "run_result" | "benchmark" | "config" | "architecture_decision" | "commit" | "deployment" | "user_explanation" | "interview_answer";
  source_path: string;
  title: string;
  description: string;
  content: string;
  line_start: number | null;
  line_end: number | null;
  score: number;
  created_at: string;
}

interface EvidencePacket {
  query: string;
  evidence: Evidence[];
  confidence: number;
  blocked_evidence: BlockedEvidence[];
}
```

### 11. ArchitectureDecision (架构决策)
```typescript
interface ArchitectureDecision {
  id: string;
  project_id: string;
  task_id: string | null;
  title: string;
  context: string;
  decision: string;
  consequences: string;
  alternatives_considered: string[];
  created_at: string;
}
```

### 12. InterviewSession (面试会话)
```typescript
interface InterviewSession {
  id: string;
  project_id: string;
  task_id: string | null;
  started_at: string;
  ended_at: string | null;
  questions: InterviewQuestion[];
  status: "in_progress" | "completed";
}

interface InterviewQuestion {
  id: string;
  session_id: string;
  question: string;
  context: string;
  user_answer: string | null;
  follow_ups: string[];
  current_follow_up: number;
  gap_type: "knowledge" | "engineering" | "evidence" | "experiment" | null;
  status: "pending" | "answered" | "skipped";
}
```

### 13. CapabilityProfile (能力档案)
```typescript
interface CapabilityProfile {
  user_id: string;
  project_id: string;
  capabilities: {
    dimension: string;
    level: MaturityLevel;
    evidence_ids: string[];
    interview_performance: {
      total_questions: number;
      answered_correctly: number;
      gaps: string[];
    };
  }[];
  overall_score: number;
  strengths: string[];
  weaknesses: string[];
  updated_at: string;
}
```

## 枚举定义

```typescript
enum ProjectType {
  RAG = "rag",
  AGENT = "agent",
  CHATBOT = "chatbot",
  API = "api",
  FULLSTACK = "fullstack",
  OTHER = "other"
}

enum ImplementationStatusType {
  FULLY_IMPLEMENTED = "fully_implemented",
  PARTIALLY_IMPLEMENTED = "partially_implemented",
  DOCUMENTED_ONLY = "documented_only",
  PLANNED = "planned",
  MISSING = "missing"
}

enum TaskStatus {
  PENDING = "pending",
  IN_PROGRESS = "in_progress",
  COMPLETED = "completed",
  FAILED = "failed"
}

enum GapPriority {
  CRITICAL = "critical",
  HIGH = "high",
  MEDIUM = "medium",
  LOW = "low"
}

enum EffortEstimate {
  SMALL = "small",
  MEDIUM = "medium",
  LARGE = "large"
}

enum GapRisk {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high"
}

enum EvidenceType {
  CODE = "code",
  TEST = "test",
  RUN_RESULT = "run_result",
  BENCHMARK = "benchmark",
  CONFIG = "config",
  ARCHITECTURE_DECISION = "architecture_decision",
  COMMIT = "commit",
  DEPLOYMENT = "deployment",
  USER_EXPLANATION = "user_explanation",
  INTERVIEW_ANSWER = "interview_answer"
}
```
