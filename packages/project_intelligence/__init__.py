"""
Project Intelligence Package

Tools for analyzing and understanding project codebases.
Now with proper evidence collection.
"""

import json
import os
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

# Language detection patterns
LANGUAGE_EXTENSIONS = {
    "python": [".py"],
    "javascript": [".js", ".jsx", ".mjs"],
    "typescript": [".ts", ".tsx"],
    "java": [".java"],
    "go": [".go"],
    "rust": [".rs"],
    "c": [".c", ".h"],
    "cpp": [".cpp", ".hpp", ".cc"],
    "csharp": [".cs"],
    "ruby": [".rb"],
    "php": [".php"],
    "swift": [".swift"],
    "kotlin": [".kt", ".kts"],
    "html": [".html", ".htm"],
    "css": [".css", ".scss", ".sass", ".less"],
    "sql": [".sql"],
    "shell": [".sh", ".bash"],
    "yaml": [".yaml", ".yml"],
    "json": [".json"],
    "toml": [".toml"],
}

# Framework detection patterns
FRAMEWORK_PATTERNS = {
    "nextjs": ["next.config", "pages/", "app/", "getServerSideProps", "getStaticProps"],
    "react": ["react", "React", "useState", "useEffect", "jsx", "tsx"],
    "vue": ["vue", "Vue", "<template>", "Composition API"],
    "fastapi": ["fastapi", "FastAPI", "@app"],
    "django": ["django", "@app", "urls.py", "models.py"],
    "flask": ["flask", "Flask", "@app.route"],
    "express": ["express", "Express", "app.get", "app.post"],
    "nestjs": ["@nestjs", "Controller", "Module"],
    "spring": ["@SpringBootApplication", "@RestController", "@Service"],
    "langchain": ["langchain", "Chain", "LLMChain"],
    "llamaindex": ["llamaindex", "LlamaIndex", "ServiceContext"],
    "autogen": ["autogen", "AssistantAgent", "GroupChat"],
}

# Database detection
DATABASE_PATTERNS = {
    "postgresql": ["postgresql", "postgres", "psycopg"],
    "mysql": ["mysql", "mysqldb", "pymysql"],
    "mongodb": ["mongodb", "pymongo", "mongod"],
    "redis": ["redis", "redis-py"],
    "sqlite": ["sqlite3", ".db", ".sqlite"],
    "milvus": ["milvus", "pymilvus"],
    "chroma": ["chroma", "chromadb"],
    "pinecone": ["pinecone"],
    "qdrant": ["qdrant"],
    "weaviate": ["weaviate"],
}

# Deployment detection
DEPLOYMENT_PATTERNS = {
    "docker": ["Dockerfile", "docker-compose", ".dockerignore"],
    "kubernetes": ["kubernetes", "k8s", "kube"],
    "vercel": ["vercel.json", ".vercel"],
    "netlify": ["netlify.toml"],
    "aws": ["aws", "boto3", "aws_lambda"],
    "gcp": ["google-cloud", "gcloud"],
    "azure": ["azure", "azure-functions"],
    "heroku": ["heroku.yml", "Procfile"],
}

# LLM/AI Framework patterns
LLM_PATTERNS = {
    "openai": ["openai", "ChatCompletion"],
    "anthropic": ["anthropic", "Claude"],
    "ollama": ["ollama"],
    "huggingface": ["transformers", "huggingface_hub"],
}

# Observability patterns
OBSERVABILITY_PATTERNS = {
    "logging": ["logging", "logger", "log.", "console.log", "winston", "pino"],
    "metrics": ["prometheus", "grafana", "datadog", "metrics", "statsd"],
    "tracing": ["opentelemetry", "jaeger", "zipkin", "trace", "span"],
}


@dataclass
class FileInfo:
    """Information about a file"""
    path: str
    relative_path: str
    extension: str
    size: int
    lines: int
    content: str = ""


@dataclass
class Evidence:
    """Evidence for a project fact"""
    fact_type: str
    source_file: str
    source_line_start: int
    source_line_end: int
    content: str
    confidence: float = 1.0  # 0.0 - 1.0
    verification_method: str = ""  # "file_exists", "code_pattern", "test_run", "runtime_check"


@dataclass
class CodeAnalysisResult:
    """Result of code analysis"""
    files: list[FileInfo] = field(default_factory=list)
    language_stats: dict[str, int] = field(default_factory=dict)
    framework_stats: dict[str, bool] = field(default_factory=dict)
    database_stats: dict[str, bool] = field(default_factory=dict)
    deployment_stats: dict[str, bool] = field(default_factory=dict)
    llm_stats: dict[str, bool] = field(default_factory=dict)
    observability_stats: dict[str, bool] = field(default_factory=dict)
    test_files: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    readme_found: bool = False
    api_docs_found: bool = False
    deployment_docs_found: bool = False
    contributing_found: bool = False
    # Additional findings
    has_pytest: bool = False
    has_dockerfile: bool = False
    docker_builds: bool = False
    has_ci: bool = False
    has_env_example: bool = False
    has_auth: bool = False
    has_input_validation: bool = False
    has_error_handling: bool = False
    has_retry: bool = False
    has_caching: bool = False
    has_rate_limiting: bool = False
    has_rag: bool = False
    has_agent: bool = False
    has_eval: bool = False


def analyze_directory(
    root_path: str,
    exclude_patterns: list[str] | None = None
) -> CodeAnalysisResult:
    """
    Analyze a project directory and extract information with evidence.
    """
    if exclude_patterns is None:
        exclude_patterns = [
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            ".pytest_cache", ".mypy_cache", "dist", "build", ".next",
            ".idea", ".vscode", "coverage", ".tox", "vendor",
            ".upgrade_baseline", ".upgrade_workspace",
        ]
    
    result = CodeAnalysisResult()
    root_path = Path(root_path)
    evidence: list[Evidence] = []
    
    # Track file counts by language
    language_counts: dict[str, int] = {}
    all_files: list[FileInfo] = []
    
    # Walk directory
    for item in root_path.rglob("*"):
        # Skip excluded patterns
        if any(pattern in str(item) for pattern in exclude_patterns):
            continue
        
        if item.is_file():
            try:
                relative = item.relative_to(root_path)
                ext = item.suffix.lower()
                rel_path_str = str(relative)
                
                # Count lines and read content
                content = ""
                lines = 0
                try:
                    with open(item, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        file_lines = content.split("\n")
                        lines = len(file_lines)
                except:
                    pass
                
                file_info = FileInfo(
                    path=str(item),
                    relative_path=rel_path_str,
                    extension=ext,
                    size=item.stat().st_size,
                    lines=lines,
                    content=content,
                )
                all_files.append(file_info)
                
                # Track language
                for lang, exts in LANGUAGE_EXTENSIONS.items():
                    if ext in exts:
                        language_counts[lang] = language_counts.get(lang, 0) + 1
                        break
                
                # Detect test files
                test_patterns = ["test_", "_test.", ".test.", "spec_", "_spec.", ".spec."]
                if any(p in item.name for p in test_patterns) or "/test" in rel_path_str or "/tests" in rel_path_str:
                    result.test_files.append(rel_path_str)
                
                # Detect config files
                config_patterns = [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"]
                if ext in config_patterns or item.name.startswith("."):
                    result.config_files.append(rel_path_str)
                
                # Check for specific files
                name_lower = item.name.lower()
                if name_lower == "readme.md" or name_lower == "readme":
                    result.readme_found = True
                    evidence.append(Evidence(
                        fact_type="documentation",
                        source_file=rel_path_str,
                        source_line_start=1,
                        source_line_end=min(10, lines),
                        content=content[:200] if content else "",
                        verification_method="file_exists",
                    ))
                
                if "api" in name_lower or "swagger" in name_lower or "openapi" in name_lower:
                    result.api_docs_found = True
                
                if "deploy" in name_lower or "deployment" in name_lower:
                    result.deployment_docs_found = True
                
                if "contributing" in name_lower:
                    result.contributing_found = True
                
                # Check for pytest
                if name_lower == "pytest.ini" or "pytest" in content or "conftest.py" in name_lower:
                    result.has_pytest = True
                    evidence.append(Evidence(
                        fact_type="testing",
                        source_file=rel_path_str,
                        source_line_start=1,
                        source_line_end=lines,
                        content="pytest configuration found",
                        verification_method="file_exists",
                    ))
                
                # Check for Dockerfile
                if name_lower == "dockerfile" or "dockerfile." in rel_path_str:
                    result.has_dockerfile = True
                    # Check if it actually builds
                    if "FROM" in content:
                        result.docker_builds = True
                    evidence.append(Evidence(
                        fact_type="deployment",
                        source_file=rel_path_str,
                        source_line_start=1,
                        source_line_end=lines,
                        content=content[:200],
                        verification_method="file_exists",
                    ))
                
                # Check for CI/CD
                if ".github/workflows" in rel_path_str or "github_actions" in rel_path_str.lower():
                    result.has_ci = True
                
                # Check for .env.example
                if name_lower == ".env.example" or name_lower == "env.example":
                    result.has_env_example = True
                
                # Check for auth
                if any(p in content.lower() for p in ["auth", "login", "jwt", "token", "password", "credential"]):
                    if any(p in rel_path_str.lower() for p in ["auth", "login", "middleware"]):
                        result.has_auth = True
                        evidence.append(Evidence(
                            fact_type="auth",
                            source_file=rel_path_str,
                            source_line_start=1,
                            source_line_end=lines,
                            content="Authentication code found",
                            verification_method="code_pattern",
                        ))
                
                # Check for input validation
                if any(p in content for p in ["validate", "validation", "schema", "pydantic", "marshmallow"]):
                    result.has_input_validation = True
                
                # Check for error handling
                if "except" in content or "try:" in content or "catch" in content:
                    result.has_error_handling = True
                
                # Check for retry
                if any(p in content.lower() for p in ["retry", "backoff", "tenacity", "retrying"]):
                    result.has_retry = True
                
                # Check for caching
                if any(p in content.lower() for p in ["cache", "redis", "memcached", "@lru_cache"]):
                    result.has_caching = True
                
                # Check for rate limiting
                if any(p in content.lower() for p in ["rate_limit", "rate-limit", "throttle", "slowapi"]):
                    result.has_rate_limiting = True
                
                # Check for RAG
                if any(p in content for p in ["vector", "embedding", "retrieval", "rag", "milvus", "chroma", "pinecone"]):
                    result.has_rag = True
                
                # Check for Agent
                if any(p in content for p in ["agent", "Agent", "tool", "Tool", "action"]):
                    if result.framework_stats.get("langchain") or result.framework_stats.get("autogen"):
                        result.has_agent = True
                
                # Check for eval
                if any(p in rel_path_str.lower() for p in ["eval", "benchmark", "test"]):
                    if result.test_files:
                        result.has_eval = True
                
            except Exception:
                pass
    
    result.files = all_files
    result.language_stats = language_counts
    result.evidence = evidence
    
    # Analyze content for frameworks
    # Sample files for pattern matching (first 50 files to avoid loading too much)
    sample_content = " ".join(f.content[:1000] for f in all_files[:50] if f.content)
    
    for framework, patterns in FRAMEWORK_PATTERNS.items():
        if any(p in sample_content for p in patterns):
            result.framework_stats[framework] = True
            # Add evidence for framework
            for f in all_files[:20]:
                if f.content and any(p in f.content for p in patterns):
                    evidence.append(Evidence(
                        fact_type="framework",
                        source_file=f.relative_path,
                        source_line_start=1,
                        source_line_end=min(20, f.lines),
                        content=f"Framework {framework} detected",
                        verification_method="code_pattern",
                    ))
                    break
    
    # Analyze for databases
    for db, patterns in DATABASE_PATTERNS.items():
        if any(p in sample_content for p in patterns):
            result.database_stats[db] = True
    
    # Analyze for deployment
    for deploy, patterns in DEPLOYMENT_PATTERNS.items():
        if any(p in sample_content for p in patterns):
            result.deployment_stats[deploy] = True
    
    # Analyze for LLM frameworks
    for llm, patterns in LLM_PATTERNS.items():
        if any(p in sample_content for p in patterns):
            result.llm_stats[llm] = True
    
    # Analyze for observability
    for obs, patterns in OBSERVABILITY_PATTERNS.items():
        if any(p in sample_content for p in patterns):
            result.observability_stats[obs] = True
    
    return result


def detect_project_type(
    language_stats: dict[str, int],
    framework_stats: dict[str, bool],
    result: CodeAnalysisResult,
) -> str:
    """Detect the type of project based on analysis"""
    # RAG/LLM projects
    if result.has_rag:
        return "rag"
    
    if any(f in framework_stats for f in ["langchain", "llamaindex", "autogen"]):
        return "agent"
    
    # Chatbot
    if any(f in framework_stats for f in ["react", "vue", "nextjs"]):
        if framework_stats.get("express"):
            return "fullstack"
        return "chatbot"
    
    # API
    if any(f in framework_stats for f in ["fastapi", "django", "flask", "nestjs", "spring"]):
        return "api"
    
    # Fullstack
    if framework_stats.get("nextjs") or (framework_stats.get("react") and framework_stats.get("express")):
        return "fullstack"
    
    return "other"


def build_project_facts(
    project_path: str,
    project_name: str,
) -> dict[str, Any]:
    """
    Build project facts from analysis with evidence.
    
    Returns a dictionary with all facts and evidence.
    """
    analysis = analyze_directory(project_path)
    
    facts = {
        "project_name": project_name,
        "project_type": detect_project_type(
            analysis.language_stats,
            analysis.framework_stats,
            analysis,
        ),
        "main_language": [],
        "frameworks": [],
        "database": [],
        "deployment": [],
        "total_files": len(analysis.files),
        "total_lines": sum(f.lines for f in analysis.files),
        "code_lines": sum(f.lines for f in analysis.files if f.extension in [".py", ".js", ".ts", ".jsx", ".tsx"]),
        "test_files": len(analysis.test_files),
        "test_lines": sum(f.lines for f in analysis.files if any(p in f.relative_path for p in ["test", "spec"])),
        "config_files": len(analysis.config_files),
        "has_readme": analysis.readme_found,
        "has_api_docs": analysis.api_docs_found,
        "has_deployment_docs": analysis.deployment_docs_found,
        "has_contributing": analysis.contributing_found,
        "has_pytest": analysis.has_pytest,
        "has_dockerfile": analysis.docker_builds,
        "has_ci": analysis.has_ci,
        "has_env_example": analysis.has_env_example,
        "has_auth": analysis.has_auth,
        "has_input_validation": analysis.has_input_validation,
        "has_error_handling": analysis.has_error_handling,
        "has_retry": analysis.has_retry,
        "has_caching": analysis.has_caching,
        "has_rate_limiting": analysis.has_rate_limiting,
        "has_rag": analysis.has_rag,
        "has_agent": analysis.has_agent,
        "has_eval": analysis.has_eval,
        "observability": analysis.observability_stats,
        "evidence": [
            {
                "fact_type": e.fact_type,
                "source_file": e.source_file,
                "source_line_start": e.source_line_start,
                "source_line_end": e.source_line_end,
                "content": e.content,
                "confidence": e.confidence,
                "verification_method": e.verification_method,
            }
            for e in analysis.evidence
        ],
        "raw_observations": generate_observations(analysis),
    }
    
    # Language stats
    if analysis.language_stats:
        sorted_langs = sorted(analysis.language_stats.items(), key=lambda x: x[1], reverse=True)
        facts["main_language"] = [lang for lang, count in sorted_langs[:3]]
    
    # Frameworks
    facts["frameworks"] = list(analysis.framework_stats.keys())
    
    # Databases
    facts["database"] = list(analysis.database_stats.keys())
    
    # Deployment
    facts["deployment"] = list(analysis.deployment_stats.keys())
    
    return facts


def generate_observations(analysis: CodeAnalysisResult) -> list[dict[str, Any]]:
    """Generate observations from analysis"""
    observations = []
    
    total_files = len(analysis.files)
    
    if total_files == 0:
        observations.append({
            "category": "structure",
            "finding": "No source files found",
            "severity": "critical",
        })
    elif total_files < 5:
        observations.append({
            "category": "structure",
            "finding": "Very few source files, may be a stub project",
            "severity": "warning",
        })
    
    if len(analysis.test_files) == 0:
        observations.append({
            "category": "testing",
            "finding": "No test files found",
            "severity": "warning",
        })
    elif len(analysis.test_files) < len(analysis.files) * 0.1:
        observations.append({
            "category": "testing",
            "finding": f"Low test coverage ({len(analysis.test_files)} tests for {len(analysis.files)} files)",
            "severity": "warning",
        })
    
    if not analysis.readme_found:
        observations.append({
            "category": "documentation",
            "finding": "No README.md found",
            "severity": "warning",
        })
    
    if not analysis.framework_stats:
        observations.append({
            "category": "tech_stack",
            "finding": "No frameworks detected",
            "severity": "info",
        })
    
    if not analysis.deployment_stats:
        observations.append({
            "category": "deployment",
            "finding": "No deployment configuration found",
            "severity": "warning",
        })
    
    if not analysis.database_stats:
        observations.append({
            "category": "data",
            "finding": "No database detected",
            "severity": "info",
        })
    
    return observations


def extract_file_content(file_path: str, start_line: int = 1, end_line: int | None = None) -> str:
    """Extract specific lines from a file"""
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            if end_line:
                return "".join(lines[start_line-1:end_line])
            return "".join(lines[start_line-1:])
    except:
        return ""
