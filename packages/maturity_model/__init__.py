"""
Maturity Model Package

Defines the 5-level maturity model for AI engineering projects:
- idea: Just an idea or concept
- demo: Can demonstrate basic functionality
- mvp: Minimum viable product with real user flow
- pre_production: Ready for staging with production considerations
- production: Can run in production with all governance
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class MaturityLevel(str, Enum):
    IDEA = "idea"
    DEMO = "demo"
    MVP = "mvp"
    PRE_PRODUCTION = "pre_production"
    PRODUCTION = "production"
    
    @classmethod
    def from_string(cls, s: str) -> "MaturityLevel":
        s = s.lower().strip()
        for level in cls:
            if level.value == s:
                return level
        return cls.IDEA
    
    def next(self) -> Optional["MaturityLevel"]:
        order = [MaturityLevel.IDEA, MaturityLevel.DEMO, MaturityLevel.MVP, 
                 MaturityLevel.PRE_PRODUCTION, MaturityLevel.PRODUCTION]
        try:
            idx = order.index(self)
            if idx < len(order) - 1:
                return order[idx + 1]
        except ValueError:
            pass
        return None
    
    def display_name(self) -> str:
        names = {
            MaturityLevel.IDEA: "想法",
            MaturityLevel.DEMO: "演示版",
            MaturityLevel.MVP: "最小可用版本",
            MaturityLevel.PRE_PRODUCTION: "准生产级",
            MaturityLevel.PRODUCTION: "生产级",
        }
        return names.get(self, self.value)


@dataclass
class Criterion:
    """A single criterion that can be evaluated"""
    id: str
    name: str
    description: str
    category: str  # e.g., "core_features", "data", "security"
    
    def evaluate(self, project_facts: dict[str, Any]) -> bool:
        """Override in subclasses"""
        raise NotImplementedError


@dataclass
class MaturityCriteriaSet:
    """Set of criteria for a maturity level"""
    level: MaturityLevel
    criteria: list[Criterion] = field(default_factory=list)
    
    def add_criterion(self, criterion: Criterion):
        self.criteria.append(criterion)
    
    def evaluate(self, project_facts: dict[str, Any]) -> dict[str, bool]:
        """Evaluate all criteria, return mapping of criterion_id -> passed"""
        results = {}
        for c in self.criteria:
            try:
                results[c.id] = c.evaluate(project_facts)
            except Exception:
                results[c.id] = False
        return results
    
    def score(self, project_facts: dict[str, Any]) -> float:
        """Calculate score (0-100) for this level"""
        results = self.evaluate(project_facts)
        if not results:
            return 0.0
        passed = sum(1 for v in results.values() if v)
        return (passed / len(results)) * 100


@dataclass 
class DimensionScore:
    """Score for a specific dimension (e.g., security, monitoring)"""
    dimension: str
    level: MaturityLevel
    progress: float  # 0-100
    criteria_met: list[str] = field(default_factory=list)
    criteria_missing: list[str] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MaturityAssessment:
    """Complete maturity assessment result"""
    overall_level: MaturityLevel
    dimension_scores: dict[str, DimensionScore]
    evidence: list[dict[str, Any]] = field(default_factory=list)
    blockers: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "overall_level": self.overall_level.value,
            "dimension_scores": {
                k: {
                    "dimension": v.dimension,
                    "level": v.level.value,
                    "progress": v.progress,
                    "criteria_met": v.criteria_met,
                    "criteria_missing": v.criteria_missing,
                }
                for k, v in self.dimension_scores.items()
            },
            "evidence": self.evidence,
            "blockers": self.blockers,
            "recommendations": self.recommendations,
        }


class MaturityEvaluator:
    """Evaluates project maturity against criteria"""
    
    # Dimension definitions
    DIMENSIONS = {
        "core_features": {
            "name": "核心功能",
            "categories": ["idea", "demo", "mvp", "pre_production", "production"],
        },
        "data": {
            "name": "数据层",
            "categories": ["persistence", "versioning", "quality"],
        },
        "api": {
            "name": "API层",
            "categories": ["restfulness", "validation", "error_handling"],
        },
        "auth": {
            "name": "权限",
            "categories": ["authentication", "authorization"],
        },
        "security": {
            "name": "安全",
            "categories": ["input_validation", "data_protection", "injection_prevention"],
        },
        "error_handling": {
            "name": "错误处理",
            "categories": ["retry", "fallback", "timeout"],
        },
        "testing": {
            "name": "测试",
            "categories": ["unit", "integration", "e2e"],
        },
        "evaluation": {
            "name": "评测",
            "categories": ["metrics", "benchmarking", "monitoring"],
        },
        "deployment": {
            "name": "部署",
            "categories": ["containerization", "ci_cd", "infrastructure"],
        },
        "monitoring": {
            "name": "监控",
            "categories": ["logging", "tracing", "alerting"],
        },
        "reliability": {
            "name": "可靠性",
            "categories": ["availability", "fault_tolerance", "recovery"],
        },
        "cost": {
            "name": "成本",
            "categories": ["estimation", "control", "optimization"],
        },
        "maintainability": {
            "name": "可维护性",
            "categories": ["documentation", "code_quality", "technical_debt"],
        },
    }
    
    def __init__(self):
        self.criteria_sets: dict[MaturityLevel, MaturityCriteriaSet] = {}
        self._init_criteria()
    
    def _init_criteria(self):
        """Initialize criteria for each maturity level"""
        # IDEA level criteria
        idea_set = MaturityCriteriaSet(MaturityLevel.IDEA)
        idea_set.add_criterion(Criterion(
            "idea_problem", "问题定义",
            "项目解决的问题是否清晰定义",
            "core_features"
        ))
        idea_set.add_criterion(Criterion(
            "idea_users", "目标用户",
            "目标用户群体是否明确",
            "core_features"
        ))
        idea_set.add_criterion(Criterion(
            "idea_io", "输入输出",
            "输入和输出是否定义",
            "core_features"
        ))
        idea_set.add_criterion(Criterion(
            "idea_data_source", "数据来源",
            "数据来源是否明确",
            "data"
        ))
        idea_set.add_criterion(Criterion(
            "idea_tech", "技术可行性",
            "核心技术方案是否可行",
            "core_features"
        ))
        self.criteria_sets[MaturityLevel.IDEA] = idea_set
        
        # DEMO level criteria
        demo_set = MaturityCriteriaSet(MaturityLevel.DEMO)
        demo_set.add_criterion(Criterion(
            "demo_e2e", "端到端流程",
            "核心流程是否可以端到端运行",
            "core_features"
        ))
        demo_set.add_criterion(Criterion(
            "demo_io", "基本IO",
            "是否存在基本输入输出",
            "core_features"
        ))
        demo_set.add_criterion(Criterion(
            "demo_demoable", "可演示",
            "关键能力是否可以实际演示",
            "core_features"
        ))
        demo_set.add_criterion(Criterion(
            "demo_real_data", "真实数据",
            "不是纯页面假数据",
            "data"
        ))
        demo_set.add_criterion(Criterion(
            "demo_code_exists", "代码存在",
            "存在可运行的代码",
            "core_features"
        ))
        self.criteria_sets[MaturityLevel.DEMO] = demo_set
        
        # MVP level criteria
        mvp_set = MaturityCriteriaSet(MaturityLevel.MVP)
        mvp_set.add_criterion(Criterion(
            "mvp_user_flow", "用户主流程",
            "真实用户主流程可用",
            "core_features"
        ))
        mvp_set.add_criterion(Criterion(
            "mvp_persistence", "数据持久化",
            "数据可以持久化",
            "data"
        ))
        mvp_set.add_criterion(Criterion(
            "mvp_error_handling", "错误处理",
            "有基本的错误处理",
            "error_handling"
        ))
        mvp_set.add_criterion(Criterion(
            "mvp_tests", "基本测试",
            "有测试代码",
            "testing"
        ))
        mvp_set.add_criterion(Criterion(
            "mvp_evaluation", "基本评测",
            "有基本的评测机制",
            "evaluation"
        ))
        mvp_set.add_criterion(Criterion(
            "mvp_repeatable", "可重复",
            "可以重复运行",
            "core_features"
        ))
        mvp_set.add_criterion(Criterion(
            "mvp_deploy", "部署方式",
            "有基本的部署方式",
            "deployment"
        ))
        self.criteria_sets[MaturityLevel.MVP] = mvp_set
        
        # PRE_PRODUCTION level criteria
        preprod_set = MaturityCriteriaSet(MaturityLevel.PRE_PRODUCTION)
        preprod_set.add_criterion(Criterion(
            "preprod_eval_system", "评测体系",
            "有完整的评测体系",
            "evaluation"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_permissions", "权限控制",
            "有权限控制",
            "auth"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_security", "安全措施",
            "有安全措施（输入验证等）",
            "security"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_monitoring", "监控",
            "有监控",
            "monitoring"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_logging", "日志",
            "有日志记录",
            "monitoring"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_tracing", "链路追踪",
            "有链路追踪",
            "monitoring"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_data_version", "数据版本",
            "有数据版本控制",
            "data"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_model_version", "模型版本",
            "有模型版本控制",
            "data"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_recovery", "失败恢复",
            "有失败恢复机制",
            "reliability"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_timeout", "超时处理",
            "有超时处理",
            "error_handling"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_retry", "重试机制",
            "有重试机制",
            "error_handling"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_fallback", "降级方案",
            "有降级方案",
            "error_handling"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_caching", "缓存",
            "有缓存机制",
            "core_features"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_rate_limit", "限流",
            "有限流",
            "api"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_cost_control", "成本控制",
            "有成本控制",
            "cost"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_auto_tests", "自动化测试",
            "有自动化测试",
            "testing"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_regression", "回归测试",
            "有回归测试",
            "testing"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_load_test", "负载测试",
            "有负载测试",
            "testing"
        ))
        preprod_set.add_criterion(Criterion(
            "preprod_sensitive_data", "敏感数据",
            "敏感数据有处理",
            "security"
        ))
        self.criteria_sets[MaturityLevel.PRE_PRODUCTION] = preprod_set
        
        # PRODUCTION level criteria
        prod_set = MaturityCriteriaSet(MaturityLevel.PRODUCTION)
        prod_set.add_criterion(Criterion(
            "prod_real_env", "真实环境",
            "在真实环境运行",
            "deployment"
        ))
        prod_set.add_criterion(Criterion(
            "prod_continuous_monitoring", "持续监控",
            "有持续监控",
            "monitoring"
        ))
        prod_set.add_criterion(Criterion(
            "prod_capacity", "容量规划",
            "有容量规划",
            "reliability"
        ))
        prod_set.add_criterion(Criterion(
            "prod_stability", "稳定性",
            "系统稳定",
            "reliability"
        ))
        prod_set.add_criterion(Criterion(
            "prod_fault_recovery", "故障恢复",
            "有故障恢复能力",
            "reliability"
        ))
        prod_set.add_criterion(Criterion(
            "prod_version_release", "版本发布",
            "有版本发布流程",
            "deployment"
        ))
        prod_set.add_criterion(Criterion(
            "prod_rollback", "回滚",
            "支持回滚",
            "deployment"
        ))
        prod_set.add_criterion(Criterion(
            "prod_data_governance", "数据治理",
            "有数据治理",
            "data"
        ))
        prod_set.add_criterion(Criterion(
            "prod_audit", "审计",
            "有审计机制",
            "security"
        ))
        prod_set.add_criterion(Criterion(
            "prod_cost_governance", "成本治理",
            "有成本治理",
            "cost"
        ))
        prod_set.add_criterion(Criterion(
            "prod_error_closure", "错误闭环",
            "线上错误有闭环",
            "monitoring"
        ))
        prod_set.add_criterion(Criterion(
            "prod_continuous_eval", "持续评测",
            "持续评测",
            "evaluation"
        ))
        prod_set.add_criterion(Criterion(
            "prod_security_governance", "安全治理",
            "有安全治理",
            "security"
        ))
        prod_set.add_criterion(Criterion(
            "prod_multi_tenant", "多租户",
            "支持多租户（如需要）",
            "auth"
        ))
        self.criteria_sets[MaturityLevel.PRODUCTION] = prod_set
    
    def evaluate(self, project_facts: dict[str, Any]) -> MaturityAssessment:
        """
        Evaluate project maturity based on project facts.
        
        Returns the highest level where most criteria are met.
        """
        # Evaluate each level
        level_scores = {}
        level_details = {}
        
        for level in [MaturityLevel.PRODUCTION, MaturityLevel.PRE_PRODUCTION,
                      MaturityLevel.MVP, MaturityLevel.DEMO, MaturityLevel.IDEA]:
            criteria_set = self.criteria_sets[level]
            results = criteria_set.evaluate(project_facts)
            score = criteria_set.score(project_facts)
            level_scores[level] = score
            level_details[level] = results
        
        # Determine overall level (highest level with >60% criteria met)
        overall_level = MaturityLevel.IDEA
        for level in [MaturityLevel.PRODUCTION, MaturityLevel.PRE_PRODUCTION,
                       MaturityLevel.MVP, MaturityLevel.DEMO, MaturityLevel.IDEA]:
            if level_scores[level] >= 60:
                overall_level = level
                break
        
        # Calculate dimension scores
        dimension_scores = {}
        for dim_id, dim_info in self.DIMENSIONS.items():
            # Find criteria related to this dimension
            dim_criteria = [
                c for c in self.criteria_sets[overall_level].criteria
                if c.category == dim_id
            ]
            if dim_criteria:
                met = [c.name for c in dim_criteria if level_details[overall_level].get(c.id, False)]
                missing = [c.name for c in dim_criteria if not level_details[overall_level].get(c.id, False)]
                progress = (len(met) / len(dim_criteria)) * 100 if dim_criteria else 0
                
                # Determine dimension level
                dim_level = MaturityLevel.IDEA
                for lvl in [MaturityLevel.PRODUCTION, MaturityLevel.PRE_PRODUCTION,
                            MaturityLevel.MVP, MaturityLevel.DEMO, MaturityLevel.IDEA]:
                    dim_results = self.criteria_sets[lvl].evaluate(project_facts)
                    dim_criteria_met = sum(1 for c in dim_criteria if dim_results.get(c.id, False))
                    if dim_criteria_met >= len(dim_criteria) * 0.6:
                        dim_level = lvl
                        break
                
                dimension_scores[dim_id] = DimensionScore(
                    dimension=dim_info["name"],
                    level=dim_level,
                    progress=progress,
                    criteria_met=met,
                    criteria_missing=missing,
                )
        
        # Collect evidence
        evidence = project_facts.get("evidence", [])
        
        # Identify blockers
        blockers = []
        missing_criteria = level_details[overall_level]
        for crit_id, passed in missing_criteria.items():
            if not passed:
                for level in self.criteria_sets:
                    for c in self.criteria_sets[level].criteria:
                        if c.id == crit_id:
                            blockers.append({
                                "criterion_id": crit_id,
                                "criterion_name": c.name,
                                "category": c.category,
                                "level_required": level.value,
                            })
                            break
        
        # Generate recommendations
        recommendations = []
        if overall_level == MaturityLevel.IDEA:
            recommendations.append("需要将想法转化为可运行的演示版本")
        elif overall_level == MaturityLevel.DEMO:
            recommendations.append("演示版本需要完善用户主流程和数据持久化")
        elif overall_level == MaturityLevel.MVP:
            recommendations.append("MVP需要增加测试覆盖和评测机制")
        elif overall_level == MaturityLevel.PRE_PRODUCTION:
            recommendations.append("需要完善监控、日志和生产级错误处理")
        elif overall_level == MaturityLevel.PRODUCTION:
            recommendations.append("需要建立持续监控和成本治理")
        
        return MaturityAssessment(
            overall_level=overall_level,
            dimension_scores=dimension_scores,
            evidence=evidence,
            blockers=blockers,
            recommendations=recommendations,
        )
    
    def get_upgrade_path(self, current_level: MaturityLevel) -> list[MaturityLevel]:
        """Get the upgrade path from current level to production"""
        path = []
        next_level = current_level.next()
        while next_level:
            path.append(next_level)
            next_level = next_level.next()
        return path
