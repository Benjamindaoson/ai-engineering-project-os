"""
Engineering Mentor Service

Responsible for explaining why upgrades are needed, how to do them properly,
and what production considerations apply.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from packages.contracts.models import (
    LearningContent,
    ProjectFacts,
    ProjectType,
    UpgradeTask,
)


@dataclass
class MentorOutput:
    """Output from the mentor agent"""
    learning_content: LearningContent
    code_examples: list[dict[str, str]] | None = None
    related_concepts: list[dict[str, str]] = field(default_factory=list)
    common_pitfalls: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "learning_content": self.learning_content.to_dict() if isinstance(self.learning_content, LearningContent) else self.learning_content,
            "code_examples": self.code_examples,
            "related_concepts": self.related_concepts,
            "common_pitfalls": self.common_pitfalls,
        }


class EngineeringMentor:
    """
    Mentors users through upgrade tasks by explaining:
    - What the problem is
    - Why it's a problem
    - Simplest solution
    - Why simplest isn't enough
    - Production approach
    - Recommended solution for this project
    - How to verify
    - Interview questions
    """
    
    def __init__(self):
        self.concept_library = self._build_concept_library()
    
    def _build_concept_library(self) -> dict[str, dict[str, str]]:
        """Build a library of concept explanations"""
        return {
            "testing": {
                "definition": "测试是通过自动化手段验证代码行为是否符合预期。",
                "why_important": "测试能及早发现bug，保证代码质量，让重构更安全。",
                "production_consideration": "生产项目需要分层测试：单元测试、集成测试、端到端测试。",
                "best_practices": [
                    "测试应该是快速、独立、可重复的",
                    "测试应该覆盖正常路径和边界情况",
                    "测试应该有自己的命名约定",
                    "不要测试实现细节，要测试行为",
                ],
            },
            "error_handling": {
                "definition": "错误处理是程序运行时遇到异常情况时的应对策略。",
                "why_important": "好的错误处理能防止程序崩溃，提供有用的错误信息，便于调试。",
                "production_consideration": "生产环境需要区分错误类型、实现重试机制、考虑降级方案。",
                "best_practices": [
                    "不要 bare except，捕获具体异常",
                    "异常信息要包含上下文",
                    "考虑重试策略（指数退避）",
                    "实现降级和熔断机制",
                ],
            },
            "monitoring": {
                "definition": "监控是持续收集系统运行数据，以便了解系统状态和发现问题。",
                "why_important": "没有监控就像盲人开车，不知道系统是否正常。",
                "production_consideration": "生产环境需要日志、指标、追踪三位一体的可观测性。",
                "best_practices": [
                    "使用结构化日志，便于搜索和分析",
                    "选择合适的日志级别",
                    "记录关键业务指标",
                    "实现分布式追踪",
                ],
            },
            "deployment": {
                "definition": "部署是将代码发布到运行环境的过程。",
                "why_important": "可靠的部署流程支撑持续交付，加快迭代速度。",
                "production_consideration": "生产环境需要自动化、容器化、可回滚的部署。",
                "best_practices": [
                    "使用容器化保证环境一致",
                    "实现自动化CI/CD",
                    "支持蓝绿部署或金丝雀发布",
                    "保留快速回滚能力",
                ],
            },
            "data": {
                "definition": "数据管理包括数据的存储、版本、迁移和保护。",
                "why_important": "数据是核心资产，数据丢失或损坏可能是灾难性的。",
                "production_consideration": "生产环境需要数据备份、版本控制、迁移策略。",
                "best_practices": [
                    "实施数据版本化",
                    "编写数据迁移脚本",
                    "定期备份和恢复测试",
                    "考虑数据生命周期管理",
                ],
            },
            "security": {
                "definition": "安全是保护系统免受未授权访问和攻击的措施。",
                "why_important": "安全漏洞可能导致数据泄露、系统被控，造成严重损失。",
                "production_consideration": "生产环境需要纵深防御、最小权限、定期审计。",
                "best_practices": [
                    "输入验证和清理",
                    "输出编码防止XSS",
                    "参数化查询防止SQL注入",
                    "使用HTTPS加密传输",
                ],
            },
            "auth": {
                "definition": "认证是验证用户身份，授权是决定用户可以访问什么。",
                "why_important": "没有正确的权限控制，用户可能访问不该访问的数据或功能。",
                "production_consideration": "生产环境需要细粒度权限控制、会话管理、审计日志。",
                "best_practices": [
                    "使用成熟的认证库",
                    "密码加盐哈希存储",
                    "实现最小权限原则",
                    "记录权限变更审计",
                ],
            },
            "caching": {
                "definition": "缓存是将频繁访问的数据存储在快速存储中。",
                "why_important": "好的缓存策略能显著提升性能，减少数据库负载。",
                "production_consideration": "生产环境需要考虑缓存失效、一致性、分布式缓存。",
                "best_practices": [
                    "选择合适的缓存粒度",
                    "实现缓存失效策略",
                    "考虑缓存穿透和雪崩",
                    "监控缓存命中率",
                ],
            },
        }
    
    def mentor(
        self,
        task: UpgradeTask,
        project_context: dict[str, Any],
    ) -> MentorOutput:
        """
        Provide mentoring for an upgrade task.
        
        Args:
            task: The upgrade task to mentor
            project_context: Context about the project (tech stack, patterns, etc.)
        
        Returns:
            MentorOutput with learning content and guidance
        """
        # Get dimension and feature from task
        dimension = self._extract_dimension(task.title)
        feature = task.description
        
        # Get base learning content
        learning = task.learning_content
        if isinstance(learning, dict):
            learning = LearningContent(**learning)
        
        # Enhance with project-specific context
        learning = self._enhance_learning_content(learning, dimension, project_context)
        
        # Generate code examples if relevant
        code_examples = self._generate_code_examples(dimension, project_context)
        
        # Get related concepts
        related_concepts = self._get_related_concepts(dimension)
        
        # Get common pitfalls
        common_pitfalls = self._get_common_pitfalls(dimension)
        
        return MentorOutput(
            learning_content=learning,
            code_examples=code_examples,
            related_concepts=related_concepts,
            common_pitfalls=common_pitfalls,
        )
    
    def _extract_dimension(self, title: str) -> str:
        """Extract the dimension from task title"""
        dimension_keywords = {
            "testing": ["测试", "test"],
            "error_handling": ["错误", "error", "异常", "exception"],
            "monitoring": ["监控", "monitor", "日志", "log"],
            "deployment": ["部署", "deploy", "容器", "docker"],
            "data": ["数据", "data", "数据库", "database"],
            "security": ["安全", "security"],
            "auth": ["权限", "auth", "认证", "permission"],
            "caching": ["缓存", "cache"],
        }
        
        title_lower = title.lower()
        for dim, keywords in dimension_keywords.items():
            if any(kw in title_lower for kw in keywords):
                return dim
        
        return "general"
    
    def _enhance_learning_content(
        self,
        learning: LearningContent,
        dimension: str,
        context: dict[str, Any],
    ) -> LearningContent:
        """Enhance learning content with project-specific details"""
        tech_stack = context.get("tech_stack", [])
        
        # Add tech-stack specific advice
        if tech_stack:
            stack_specific = self._get_stack_specific_advice(dimension, tech_stack)
            if stack_specific:
                learning.production_approach += f"\n\n针对 {', '.join(tech_stack[:2])}：{stack_specific}"
        
        return learning
    
    def _get_stack_specific_advice(self, dimension: str, tech_stack: list[str]) -> str:
        """Get stack-specific implementation advice"""
        advice_map = {
            "python": {
                "testing": "使用 pytest 框架，编写 conftest.py 共享 fixtures。",
                "error_handling": "使用 custom exception classes，配置日志格式。",
                "monitoring": "使用 logging 模块，配合 structlog 增强结构化。",
                "deployment": "使用 Docker 多阶段构建，考虑 uvicorn/gunicorn。",
            },
            "javascript": {
                "testing": "使用 Jest 或 Vitest，编写单元测试和集成测试。",
                "error_handling": "使用 Error boundaries (React) 或全局错误处理。",
                "monitoring": "使用 Winston 或 Pino 日志库，集成 Sentry。",
                "deployment": "使用 Docker 或 Vercel/Netlify 部署。",
            },
            "typescript": {
                "testing": "使用 Vitest 或 Jest，配合 Testing Library。",
                "error_handling": "使用 custom error classes，TypeScript 类型安全。",
                "monitoring": "使用 Pino 或 Winston，结构化日志。",
                "deployment": "编译为 JavaScript 后部署到 Node.js 环境。",
            },
        }
        
        for stack in tech_stack:
            stack_lower = stack.lower()
            if stack_lower in advice_map:
                if dimension in advice_map[stack_lower]:
                    return advice_map[stack_lower][dimension]
        
        return ""
    
    def _generate_code_examples(
        self,
        dimension: str,
        context: dict[str, Any],
    ) -> list[dict[str, str]] | None:
        """Generate before/after code examples"""
        examples_map = {
            "testing": [
                {
                    "before": "# 没有测试\ndef add(a, b):\n    return a + b",
                    "after": "# 有测试\nimport pytest\n\ndef add(a, b):\n    return a + b\n\ndef test_add():\n    assert add(1, 2) == 3\n    assert add(-1, 1) == 0",
                    "explanation": "添加基本的单元测试，验证函数行为。",
                },
            ],
            "error_handling": [
                {
                    "before": "# 没有错误处理\ndef get_user(user_id):\n    return db.query(user_id)",
                    "after": "# 有错误处理\nfrom exceptions import UserNotFoundError\n\ndef get_user(user_id):\n    try:\n        return db.query(user_id)\n    except ConnectionError as e:\n        raise UserNotFoundError(f\"Database error for {user_id}\") from e",
                    "explanation": "添加 try-except 处理，明确错误类型，提供上下文。",
                },
            ],
            "monitoring": [
                {
                    "before": "# 没有日志\ndef process():\n    result = do_work()\n    return result",
                    "after": "import logging\nlogger = logging.getLogger(__name__)\n\ndef process():\n    logger.info(\"Starting process\")\n    result = do_work()\n    logger.info(\"Process completed\", extra={\"result_size\": len(result)})\n    return result",
                    "explanation": "添加结构化日志，记录关键事件和上下文。",
                },
            ],
        }
        
        return examples_map.get(dimension)
    
    def _get_related_concepts(self, dimension: str) -> list[dict[str, str]]:
        """Get related concepts to learn"""
        concepts_map = {
            "testing": [
                {"concept": "测试金字塔", "explanation": "单元测试多、集成测试中、端到端测试少的理想分布。", "relevance": "帮助设计合适的测试策略。"},
                {"concept": "TDD", "explanation": "先写测试再写代码的开发方式。", "relevance": "可以尝试但不强制。"},
                {"concept": "Mock/Stub", "explanation": "用假对象替代真实依赖的测试技术。", "relevance": "隔离被测代码，控制测试环境。"},
            ],
            "error_handling": [
                {"concept": "重试模式", "explanation": "失败后自动重试的策略，常配合指数退避。", "relevance": "处理瞬时故障。"},
                {"concept": "熔断器模式", "explanation": "失败率过高时快速失败，防止级联故障。", "relevance": "保护系统稳定性。"},
                {"concept": "降级", "explanation": "服务不可用时提供简化功能。", "relevance": "保证核心功能可用。"},
            ],
            "monitoring": [
                {"concept": "结构化日志", "explanation": "日志以 JSON 格式输出，便于搜索和分析。", "relevance": "生产环境必需。"},
                {"concept": "RED 指标", "explanation": "Rate, Errors, Duration 三个核心指标。", "relevance": "API 服务监控标准。"},
                {"concept": "分布式追踪", "explanation": "追踪请求在多个服务间的调用路径。", "relevance": "微服务必备。"},
            ],
            "deployment": [
                {"concept": "容器化", "explanation": "将应用及其依赖打包成容器镜像。", "relevance": "保证环境一致性。"},
                {"concept": "CI/CD", "explanation": "持续集成/持续部署自动化流程。", "relevance": "提高交付效率。"},
                {"concept": "蓝绿部署", "explanation": "新旧版本同时运行，通过路由切换。", "relevance": "实现零停机部署。"},
            ],
        }
        
        return concepts_map.get(dimension, [])
    
    def _get_common_pitfalls(self, dimension: str) -> list[str]:
        """Get common pitfalls for this dimension"""
        pitfalls_map = {
            "testing": [
                "测试写得太多太细，维护成本高",
                "测试依赖外部服务，网络不稳定",
                "测试覆盖了实现细节，代码重构就失败",
                "忘记测试边界情况和错误路径",
            ],
            "error_handling": [
                "捕获所有异常但不处理",
                "异常信息暴露内部实现细节",
                "重试次数过多导致延迟过高",
                "没有考虑幂等性导致重复操作",
            ],
            "monitoring": [
                "日志级别使用不当，太多噪音",
                "敏感信息写入日志",
                "日志格式不统一，难以解析",
                "监控指标太多，无从下手",
            ],
            "deployment": [
                "镜像太大，启动时间长",
                "配置硬编码在镜像里",
                "没有健康检查或检查不充分",
                "回滚流程没有测试过",
            ],
            "data": [
                "数据迁移没有备份",
                "迁移脚本不能重复运行",
                "数据库连接没有池化",
                "没有考虑数据清理策略",
            ],
        }
        
        return pitfalls_map.get(dimension, [
            "低估了实现复杂度",
            "没有考虑与其他组件的集成",
            "实现后没有充分测试",
        ])
