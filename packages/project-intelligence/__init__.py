"""
Project Intelligence Package

Tools for analyzing and understanding project codebases.
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from packages.contracts.models import ProjectFacts, ProjectType, ImplementationStatusType
from packages.evidence-model import EvidenceBuilder, EvidenceType


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
    " Railway": ["railway.toml"],
}


@dataclass
class FileInfo:
    """Information about a file"""
    path: str
    relative_path: str
    extension: str
    size: int
    lines: int
    content_preview: str
    

@dataclass
class CodeAnalysisResult:
    """Result of code analysis"""
    files: List[FileInfo] = field(default_factory=list)
    language_stats: Dict[str, int] = field(default_factory=dict)
    framework_stats: Dict[str, bool] = field(default_factory=dict)
    database_stats: Dict[str, bool] = field(default_factory=dict)
    deployment_stats: Dict[str, bool] = field(default_factory=dict)
    test_files: List[str] = field(default_factory=list)
    config_files: List[str] = field(default_factory=list)
    readme_found: bool = False
    api_docs_found: bool = False
    deployment_docs_found: bool = False
    contributing_found: bool = False


def analyze_directory(
    root_path: str,
    exclude_patterns: Optional[List[str]] = None
) -> CodeAnalysisResult:
    """
    Analyze a project directory and extract information.
    
    Args:
        root_path: Path to project root
        exclude_patterns: Patterns to exclude (e.g., ["node_modules", "__pycache__"])
    
    Returns:
        CodeAnalysisResult with analysis findings
    """
    if exclude_patterns is None:
        exclude_patterns = [
            "node_modules", ".git", "__pycache__", ".venv", "venv",
            ".pytest_cache", ".mypy_cache", "dist", "build", ".next",
            ".idea", ".vscode", "coverage", ".tox", "vendor"
        ]
    
    result = CodeAnalysisResult()
    root_path = Path(root_path)
    
    # Track file counts by language
    language_counts: Dict[str, int] = {}
    all_files: List[FileInfo] = []
    
    # Walk directory
    for item in root_path.rglob("*"):
        # Skip excluded patterns
        if any(pattern in str(item) for pattern in exclude_patterns):
            continue
        
        if item.is_file():
            try:
                relative = item.relative_to(root_path)
                ext = item.suffix.lower()
                
                # Count lines
                lines = 0
                content_preview = ""
                try:
                    with open(item, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        lines = len(content.splitlines())
                        content_preview = content[:500]
                except:
                    pass
                
                file_info = FileInfo(
                    path=str(item),
                    relative_path=str(relative),
                    extension=ext,
                    size=item.stat().st_size,
                    lines=lines,
                    content_preview=content_preview,
                )
                all_files.append(file_info)
                
                # Track language
                for lang, exts in LANGUAGE_EXTENSIONS.items():
                    if ext in exts:
                        language_counts[lang] = language_counts.get(lang, 0) + 1
                        break
                
                # Detect test files
                test_patterns = ["test_", "_test.", ".test.", "spec_", "_spec.", ".spec."]
                if any(p in item.name for p in test_patterns) or "/test" in str(item) or "/tests" in str(item):
                    result.test_files.append(str(relative))
                
                # Detect config files
                config_patterns = [".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf"]
                if ext in config_patterns or item.name.startswith("."):
                    result.config_files.append(str(relative))
                
                # Check for specific files
                name_lower = item.name.lower()
                if name_lower == "readme.md" or name_lower == "readme":
                    result.readme_found = True
                if "api" in name_lower or "swagger" in name_lower or "openapi" in name_lower:
                    result.api_docs_found = True
                if "deploy" in name_lower or "deployment" in name_lower:
                    result.deployment_docs_found = True
                if "contributing" in name_lower:
                    result.contributing_found = True
                
            except Exception:
                pass
    
    result.files = all_files
    result.language_stats = language_counts
    
    # Analyze for frameworks
    all_content = " ".join(f.content_preview for f in all_files[:100])  # Sample first 100 files
    for framework, patterns in FRAMEWORK_PATTERNS.items():
        if any(p in all_content for p in patterns):
            result.framework_stats[framework] = True
    
    # Analyze for databases
    for db, patterns in DATABASE_PATTERNS.items():
        if any(p in all_content for p in patterns):
            result.database_stats[db] = True
    
    # Analyze for deployment
    for deploy, patterns in DEPLOYMENT_PATTERNS.items():
        if any(p in all_content for p in patterns):
            result.deployment_stats[deploy] = True
    
    return result


def detect_project_type(
    language_stats: Dict[str, int],
    framework_stats: Dict[str, bool],
) -> ProjectType:
    """Detect the type of project based on analysis"""
    # RAG/LLM projects
    if any(f in framework_stats for f in ["langchain", "llamaindex", "autogen"]):
        if "milvus" in str(framework_stats) or "chroma" in str(framework_stats):
            return ProjectType.RAG
        return ProjectType.AGENT
    
    # Chatbot
    if any(f in framework_stats for f in ["react", "vue", "nextjs"]):
        if framework_stats.get("express"):
            return ProjectType.FULLSTACK
        return ProjectType.CHATBOT
    
    # API
    if any(f in framework_stats for f in ["fastapi", "django", "flask", "nestjs", "spring"]):
        return ProjectType.API
    
    # Fullstack
    if framework_stats.get("nextjs") or (framework_stats.get("react") and framework_stats.get("express")):
        return ProjectType.FULLSTACK
    
    return ProjectType.OTHER


def count_code_lines(files: List[FileInfo]) -> int:
    """Count total lines of code (excluding comments and blank lines)"""
    total = 0
    for f in files:
        # Simple heuristic: count non-blank, non-comment lines
        lines = f.content_preview.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and not stripped.startswith("//"):
                total += 1
    return total


def build_project_facts(
    project_path: str,
    project_name: str,
) -> ProjectFacts:
    """
    Build a ProjectFacts object from a project analysis.
    
    Args:
        project_path: Path to project root
        project_name: Name of the project
    
    Returns:
        ProjectFacts with all extracted information
    """
    analysis = analyze_directory(project_path)
    
    facts = ProjectFacts()
    facts.project_name = project_name
    
    # Language stats
    if analysis.language_stats:
        # Get top 3 languages by file count
        sorted_langs = sorted(analysis.language_stats.items(), key=lambda x: x[1], reverse=True)
        facts.main_language = [lang for lang, count in sorted_langs[:3]]
    
    # Frameworks
    facts.frameworks = list(analysis.framework_stats.keys())
    
    # Databases
    facts.database = list(analysis.database_stats.keys())
    
    # Deployment
    facts.deployment = list(analysis.deployment_stats.keys())
    
    # File counts
    facts.total_files = len(analysis.files)
    facts.total_lines = sum(f.lines for f in analysis.files)
    facts.code_lines = count_code_lines(analysis.files)
    facts.test_files = len(analysis.test_files)
    facts.config_files = len(analysis.config_files)
    
    # Documentation
    facts.has_readme = analysis.readme_found
    facts.has_api_docs = analysis.api_docs_found
    facts.has_deployment_docs = analysis.deployment_docs_found
    facts.has_contributing = analysis.contributing_found
    
    # Detect project type
    facts.project_type = detect_project_type(
        analysis.language_stats,
        analysis.framework_stats,
    )
    
    return facts


def extract_function_signatures(content: str, language: str) -> List[Dict[str, str]]:
    """Extract function signatures from code content"""
    signatures = []
    
    if language == "python":
        # Match def and async def
        pattern = r"(?:async\s+)?def\s+(\w+)\s*\((.*?)\)"
        for match in re.finditer(pattern, content):
            signatures.append({
                "name": match.group(1),
                "params": match.group(2),
            })
    
    elif language in ["javascript", "typescript"]:
        # Match function declarations and arrow functions
        patterns = [
            r"(?:async\s+)?function\s+(\w+)\s*\((.*?)\)",
            r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?\((.*?)\)\s*=>",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                signatures.append({
                    "name": match.group(1),
                    "params": match.group(2),
                })
    
    return signatures


def find_imports(content: str, language: str) -> List[str]:
    """Find import statements in code"""
    imports = []
    
    if language == "python":
        # Match import and from ... import
        patterns = [
            r"^import\s+([\w.]+)",
            r"^from\s+([\w.]+)\s+import",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                imports.append(match.group(1))
    
    elif language in ["javascript", "typescript"]:
        # Match import statements
        patterns = [
            r"^import\s+.*?from\s+['\"]([^'\"]+)['\"]",
            r"^import\s+['\"]([^'\"]+)['\"]",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, content, re.MULTILINE):
                imports.append(match.group(1))
    
    return imports
