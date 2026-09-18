"""
Upgrade Planner Service

Responsible for determining the next best upgrade tasks based on project state and user goals.
"""

import uuid
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from packages.contracts.models import (
    Gap, UpgradeTask, LearningContent, CompletionCriterion,
    GapPriority, EffortEstimate, TaskStatus,
    MaturityLevel
)
from packages.maturity-model import MaturityEvaluator


@dataclass
class TaskRecommendation:
    """A recommended task with reasoning"""
    task: UpgradeTask
    reasoning: str
    dependencies: List[str] = field(default_factory=list)


class UpgradePlanner:
    """
    Plans upgrade tasks based on:
    - Current project state
    - Identified gaps
    - User goals and constraints
    """
    
    def __init__(self):
        self.evaluator = MaturityEvaluator()
    
    def plan(
        self,
        project_facts: Dict[str, Any],
        maturity_assessment: Dict[str, Any],
        gaps: List[Dict[str, Any]],
        user_goals: List[str],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an upgrade plan.
        
        Args:
            project_facts: Project facts from auditor
            maturity_assessment: Maturity assessment result
            gaps: List of identified gaps
            user_goals: User's stated goals
            constraints: Optional constraints (time, skill level, target maturity)
        
        Returns:
            Dictionary with:
            - recommended_tasks: List of UpgradeTask
            - prioritization_rationale: Why these tasks were chosen
            - immediate_next_steps: What to do first
            - estimated_total_effort: Rough estimate of total work
        """
        if constraints is None:
            constraints = {}
        
        # Convert gaps to Gap objects
        gap_objects = [Gap(**g) for g in gaps]
        
        # Determine target maturity
        current_level = MaturityLevel(maturity_assessment.get("overall_level", "idea"))
        target_level = self._determine_target_level(
            current_level, 
            constraints.get("target_maturity")
        )
        
        # Generate tasks for gaps
        tasks = self._generate_tasks(
            gap_objects, 
            project_facts,
            current_level,
            target_level,
        )
        
        # Prioritize tasks
        prioritized = self._prioritize_tasks(
            tasks, 
            constraints.get("skill_level", "mid"),
            constraints.get("time_available"),
        )
        
        # Generate rationale
        rationale = self._generate_rationale(
            prioritized,
            current_level,
            target_level,
            user_goals,
        )
        
        # Determine next steps
        next_steps = self._determine_next_steps(prioritized[:3])
        
        return {
            "recommended_tasks": [t.to_dict() for t in prioritized],
            "prioritization_rationale": rationale,
            "immediate_next_steps": next_steps,
            "estimated_total_effort": self._estimate_total_effort(prioritized),
            "current_level": current_level.value,
            "target_level": target_level.value,
            "upgrade_path": [l.value for l in self.evaluator.get_upgrade_path(current_level)],
        }
    
    def _determine_target_level(
        self,
        current: MaturityLevel,
        user_target: Optional[str]
    ) -> MaturityLevel:
        """Determine the target maturity level"""
        if user_target:
            try:
                target = MaturityLevel(user_target)
                # Can't target below current
                order = [MaturityLevel.IDEA, MaturityLevel.DEMO, MaturityLevel.MVP, 
                        MaturityLevel.PRE_PRODUCTION, MaturityLevel.PRODUCTION]
                if order.index(target) >= order.index(current):
                    return target
            except:
                pass
        
        # Default: next level
        next_level = current.next()
        return next_level if next_level else MaturityLevel.PRODUCTION
    
    def _generate_tasks(
        self,
        gaps: List[Gap],
        facts: Dict[str, Any],
        current: MaturityLevel,
        target: MaturityLevel,
    ) -> List[UpgradeTask]:
        """Generate upgrade tasks for gaps"""
        tasks = []
        
        for gap in gaps:
            task = self._create_task_for_gap(gap, facts, current, target)
            if task:
                tasks.append(task)
        
        return tasks
    
    def _create_task_for_gap(
        self,
        gap: Gap,
        facts: Dict[str, Any],
        current: MaturityLevel,
        target: MaturityLevel,
    ) -> Optional[UpgradeTask]:
        """Create an upgrade task for a gap"""
        # Generate learning content based on gap type
        learning = self._generate_learning_content(gap, facts)
        
        # Generate completion criteria
        criteria = self._generate_criteria(gap)
        
        # Estimate effort
        effort = self._estimate_task_effort(gap)
        
        task = UpgradeTask(
            id=str(uuid.uuid4()),
            project_id=gap.project_id,
            gap_id=gap.id,
            title=f"升级 {gap.dimension}: {gap.description}",
            description=gap.description,
            learning_content=learning,
            completion_criteria=criteria,
            estimated_effort=effort,
            prerequisites=self._get_prerequisites(gap, facts),
            status=TaskStatus.PENDING,
        )
        
        return task
    
    def _generate_learning_content(
        self,
        gap: Gap,
        facts: Dict[str, Any]
    ) -> LearningContent:
        """Generate learning content for a gap"""
        dimension = gap.dimension
        feature = gap.description
        
        # Template learning content based on dimension
        content_map = {
            "testing": LearningContent(
                problem_explanation=f"项目缺少{feature}，无法验证代码正确性。",
                why_important=f"没有{feature}意味着无法确保代码质量，容易引入bug。",
                simple_solution="添加基本的测试文件，使用框架自带的测试工具。",
                why_simple_not_enough="简单测试可能无法覆盖边界情况，无法在CI/CD中自动运行。",
                production_approach="建立完整的测试金字塔：单元测试、集成测试、端到端测试。",
                recommended_solution=f"添加{facts.get('main_language', ['Python'])[0]}的测试框架，编写核心功能的测试用例。",
                reasoning="测试是代码质量的基础，也是自信修改代码的前提。",
                verification_method="运行 `pytest` 或 `npm test`，确保所有测试通过。",
                interview_questions=[
                    "你如何决定哪些功能需要写测试？",
                    "什么是测试金字塔？你项目中测试的分布是怎样的？",
                    "如果测试失败但代码似乎没问题，你如何排查？",
                ],
            ),
            "error_handling": LearningContent(
                problem_explanation=f"项目缺少{feature}，遇到错误时程序可能崩溃或行为不可预测。",
                why_important="没有好的错误处理，系统故障难以诊断，用户体验差。",
                simple_solution="添加 try-except 捕获异常，返回友好错误信息。",
                why_simple_not_enough="简单的异常捕获不够，需要考虑错误恢复、重试、降级等策略。",
                production_approach="实现分层错误处理：输入验证、业务异常、系统异常的区分处理。",
                recommended_solution="建立统一的错误处理层，实现重试机制和降级方案。",
                reasoning="生产环境错误是常态，需要优雅处理而不是崩溃。",
                verification_method="模拟各种错误场景，验证系统行为是否符合预期。",
                interview_questions=[
                    "你如何设计错误处理策略？",
                    "什么时候应该重试？什么时候应该快速失败？",
                    "什么是降级？你的项目中如何实现降级？",
                ],
            ),
            "monitoring": LearningContent(
                problem_explanation=f"项目缺少{feature}，无法知道系统运行状态。",
                why_important="没有监控意味着无法发现问题，也无法优化性能。",
                simple_solution="添加基本的日志记录。",
                why_simple_not_enough="简单日志不够，需要结构化日志、指标收集、告警等。",
                production_approach="建立完整的可观测性体系：日志、指标、追踪。",
                recommended_solution="集成日志框架，添加关键指标埋点，建立仪表盘。",
                reasoning="可观测性是运维的基础，也是快速定位问题的关键。",
                verification_method="在测试环境触发各种场景，验证日志和指标是否正确收集。",
                interview_questions=[
                    "可观测性三要素是什么？你的项目如何实现它们？",
                    "你如何选择日志级别？",
                    "什么是结构化日志？为什么重要？",
                ],
            ),
            "deployment": LearningContent(
                problem_explanation=f"项目缺少{feature}，无法可靠部署。",
                why_important="没有好的部署方式，团队协作困难，无法快速迭代。",
                simple_solution="手动部署代码到服务器。",
                why_simple_not_enough="手动部署容易出错，无法回滚，难以扩展。",
                production_approach="实现容器化、基础设施即代码、CI/CD流水线。",
                recommended_solution="添加 Dockerfile 和 CI/CD 配置，实现自动化部署。",
                reasoning="可靠的部署是持续交付的基础，也是快速迭代的保障。",
                verification_method="在CI/CD环境中验证构建和部署流程。",
                interview_questions=[
                    "你如何设计部署流水线？",
                    "什么是蓝绿部署和金丝雀发布？",
                    "如何实现零停机部署？",
                ],
            ),
            "data": LearningContent(
                problem_explanation=f"项目缺少{feature}，数据管理混乱。",
                why_important="没有好的数据管理，数据一致性无法保证，难以扩展。",
                simple_solution="使用基本的数据存储。",
                why_simple_not_enough="简单存储不够，需要考虑版本管理、迁移、回滚等。",
                production_approach="建立完整的数据治理体系。",
                recommended_solution="添加数据版本控制、迁移脚本、备份策略。",
                reasoning="数据是核心资产，需要认真对待。",
                verification_method="测试数据迁移、回滚场景。",
                interview_questions=[
                    "你如何处理数据库迁移？",
                    "什么是数据版本化？为什么重要？",
                    "如何设计数据备份策略？",
                ],
            ),
        }
        
        # Get specific content or use generic
        specific = content_map.get(dimension)
        if specific:
            return specific
        
        # Generic learning content
        return LearningContent(
            problem_explanation=f"项目缺少{feature}，这是{gap.dimension}维度的缺口。",
            why_important=f"{gap.dimension}对于生产级应用至关重要。",
            simple_solution="实现基本版本的feature。",
            why_simple_not_enough="基本实现可能无法应对生产环境的挑战。",
            production_approach="参考业界最佳实践进行实现。",
            recommended_solution="根据项目技术栈选择合适方案。",
            reasoning="生产级应用需要完整的功能。",
            verification_method="通过测试验证功能正确性。",
            interview_questions=[
                f"为什么需要{feature}？",
                f"你如何实现{feature}？",
                f"{feature}在生产环境可能遇到什么问题？",
            ],
        )
    
    def _generate_criteria(self, gap: Gap) -> List[CompletionCriterion]:
        """Generate completion criteria for a task"""
        dimension = gap.dimension
        
        criteria_map = {
            "testing": [
                CompletionCriterion(
                    criterion="添加测试文件",
                    verification_method="检查测试文件存在",
                    evidence_type="test",
                ),
                CompletionCriterion(
                    criterion="核心功能有测试覆盖",
                    verification_method="运行测试并检查覆盖率",
                    evidence_type="test",
                ),
                CompletionCriterion(
                    criterion="测试可以通过",
                    verification_method="运行测试并验证通过",
                    evidence_type="run_result",
                ),
            ],
            "error_handling": [
                CompletionCriterion(
                    criterion="关键路径有异常处理",
                    verification_method="代码审查",
                    evidence_type="code",
                ),
                CompletionCriterion(
                    criterion="异常情况有友好错误信息",
                    verification_method="模拟异常并验证响应",
                    evidence_type="run_result",
                ),
            ],
            "monitoring": [
                CompletionCriterion(
                    criterion="添加日志记录",
                    verification_method="检查日志代码",
                    evidence_type="code",
                ),
                CompletionCriterion(
                    criterion="日志格式正确",
                    verification_method="验证日志输出",
                    evidence_type="run_result",
                ),
            ],
            "deployment": [
                CompletionCriterion(
                    criterion="添加 Dockerfile",
                    verification_method="检查文件存在",
                    evidence_type="config",
                ),
                CompletionCriterion(
                    criterion="容器可以构建",
                    verification_method="运行 docker build",
                    evidence_type="run_result",
                ),
                CompletionCriterion(
                    criterion="应用可以运行",
                    verification_method="运行容器并验证",
                    evidence_type="run_result",
                ),
            ],
        }
        
        specific = criteria_map.get(dimension)
        if specific:
            return specific
        
        return [
            CompletionCriterion(
                criterion="功能实现",
                verification_method="代码审查和测试",
                evidence_type="code",
            ),
            CompletionCriterion(
                criterion="功能可用",
                verification_method="运行验证",
                evidence_type="run_result",
            ),
        ]
    
    def _estimate_task_effort(self, gap: Gap) -> str:
        """Estimate effort for a task"""
        effort = gap.effort_estimate
        if hasattr(effort, 'value'):
            effort = effort.value
        
        effort_map = {
            "small": "0.5-1天",
            "medium": "1-3天",
            "large": "3-5天",
        }
        
        return effort_map.get(effort, "1-3天")
    
    def _get_prerequisites(self, gap: Gap, facts: Dict[str, Any]) -> List[str]:
        """Get prerequisites for a task"""
        # In a real implementation, this would analyze dependencies
        # For now, return empty
        return []
    
    def _prioritize_tasks(
        self,
        tasks: List[UpgradeTask],
        skill_level: str,
        time_available: Optional[str],
    ) -> List[UpgradeTask]:
        """Prioritize tasks based on various factors"""
        # Score each task
        scored_tasks = []
        
        for task in tasks:
            score = 0
            
            # Priority weight
            priority_weights = {
                "critical": 100,
                "high": 70,
                "medium": 40,
                "low": 10,
            }
            
            # Effort weight (prefer smaller tasks first)
            effort_weights = {
                "small": 30,
                "medium": 20,
                "large": 10,
            }
            
            # Calculate base score
            if hasattr(task.completion_criteria[0], 'criterion'):
                # Get related gap for priority
                score += priority_weights.get("high", 50)  # Default to high
            
            # Adjust for skill level
            if skill_level == "junior":
                # Prefer smaller tasks
                score += effort_weights.get("small", 0)
            elif skill_level == "senior":
                # Can handle larger tasks
                score += effort_weights.get("large", 0)
            
            scored_tasks.append((score, task))
        
        # Sort by score descending
        scored_tasks.sort(key=lambda x: x[0], reverse=True)
        
        return [t for _, t in scored_tasks]
    
    def _generate_rationale(
        self,
        tasks: List[UpgradeTask],
        current: MaturityLevel,
        target: MaturityLevel,
        goals: List[str],
    ) -> str:
        """Generate explanation for why these tasks were chosen"""
        rationale_parts = [
            f"当前项目处于「{current.display_name()}」阶段，目标是将项目提升到「{target.display_name()}」。",
        ]
        
        if tasks:
            rationale_parts.append(
                f"根据分析，推荐优先完成以下 {len(tasks)} 个升级任务："
            )
            
            for i, task in enumerate(tasks[:3], 1):
                rationale_parts.append(
                    f"{i}. {task.title}（预计 {task.estimated_effort}）"
                )
        
        if goals:
            rationale_parts.append(
                f"这些任务与您的目标「{'、'.join(goals[:2])}」直接相关。"
            )
        
        return "\n".join(rationale_parts)
    
    def _determine_next_steps(self, tasks: List[UpgradeTask]) -> List[str]:
        """Determine immediate next steps"""
        steps = []
        
        if tasks:
            steps.append(f"选择「{tasks[0].title}」作为第一个升级任务")
            steps.append("仔细阅读工程导师提供的学习内容")
            steps.append("按照任务要求修改代码")
            steps.append("运行测试验证修改")
            steps.append("让验证智能体检查是否完成")
        
        if len(tasks) > 1:
            steps.append(f"完成后，继续处理「{tasks[1].title}」")
        
        return steps
    
    def _estimate_total_effort(self, tasks: List[UpgradeTask]) -> str:
        """Estimate total effort for all tasks"""
        if not tasks:
            return "无法估计"
        
        # Simple sum of efforts
        effort_map = {
            "0.5-1天": 0.75,
            "1-3天": 2,
            "3-5天": 4,
        }
        
        total_days = 0
        for task in tasks:
            days = effort_map.get(task.estimated_effort, 2)
            total_days += days
        
        if total_days <= 5:
            return f"约 {total_days} 天"
        elif total_days <= 20:
            return f"约 {total_days//5} 周"
        else:
            return f"约 {total_days//20} 个月"
