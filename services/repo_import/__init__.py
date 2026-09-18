"""
Repository Import Service

Handles importing projects from local paths or GitHub URLs.
"""

import os
import re
import shutil
import subprocess
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import httpx

# Configuration
WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT", "./workspaces")
MAX_REPO_SIZE_MB = int(os.getenv("MAX_REPO_SIZE_MB", "500"))
CLONE_TIMEOUT = int(os.getenv("CLONE_TIMEOUT_SECONDS", "300"))


@dataclass
class ImportResult:
    """Result of a repository import"""
    success: bool
    project_id: str
    workspace_path: str
    commit_sha: str
    branch: str
    repo_url: str
    error: str | None = None


class RepoImportService:
    """
    Service for importing repositories from:
    1. Local paths (already on disk)
    2. GitHub URLs (clone to workspace)
    """
    
    def __init__(self, workspace_root: str = WORKSPACE_ROOT):
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
    
    def import_local(
        self,
        local_path: str,
        project_name: str | None = None,
    ) -> ImportResult:
        """
        Import a project from a local path.
        
        Args:
            local_path: Path to the project on disk
            project_name: Optional name override
        
        Returns:
            ImportResult with workspace details
        """
        local_path = Path(local_path).resolve()
        
        if not local_path.exists():
            return ImportResult(
                success=False,
                project_id="",
                workspace_path="",
                commit_sha="",
                branch="",
                repo_url="",
                error=f"Path does not exist: {local_path}",
            )
        
        if not local_path.is_dir():
            return ImportResult(
                success=False,
                project_id="",
                workspace_path="",
                commit_sha="",
                branch="",
                repo_url="",
                error=f"Path is not a directory: {local_path}",
            )
        
        # Generate project ID
        project_id = str(uuid.uuid4())
        
        # Create workspace copy
        workspace_path = self.workspace_root / project_id
        
        try:
            # Copy to workspace (source repo stays read-only)
            shutil.copytree(local_path, workspace_path, symlinks=False, 
                         ignore=self._get_ignore_func())
            
            # Get git info if available
            commit_sha, branch = self._get_git_info(workspace_path)
            
            return ImportResult(
                success=True,
                project_id=project_id,
                workspace_path=str(workspace_path),
                commit_sha=commit_sha or "no-git",
                branch=branch or "main",
                repo_url=f"local://{local_path}",
            )
            
        except Exception as e:
            # Cleanup on failure
            if workspace_path.exists():
                shutil.rmtree(workspace_path, ignore_errors=True)
            
            return ImportResult(
                success=False,
                project_id="",
                workspace_path="",
                commit_sha="",
                branch="",
                repo_url="",
                error=str(e),
            )
    
    def import_github(
        self,
        github_url: str,
        branch: str = "main",
    ) -> ImportResult:
        """
        Import a project from a GitHub URL.
        
        Args:
            github_url: GitHub repository URL
            branch: Branch to checkout (default: main)
        
        Returns:
            ImportResult with workspace details
        """
        # Parse GitHub URL
        parsed = self._parse_github_url(github_url)
        if not parsed:
            return ImportResult(
                success=False,
                project_id="",
                workspace_path="",
                commit_sha="",
                branch="",
                repo_url=github_url,
                error="Invalid GitHub URL format",
            )
        
        owner, repo = parsed
        
        # Generate project ID
        project_id = str(uuid.uuid4())
        
        # Create workspace directory
        workspace_path = self.workspace_root / project_id
        
        try:
            # Clone repository
            clone_url = f"https://github.com/{owner}/{repo}.git"
            
            result = subprocess.run(
                ["git", "clone", "--depth", "1", "-b", branch, clone_url, str(workspace_path)],
                capture_output=True,
                text=True,
                timeout=CLONE_TIMEOUT,
            )
            
            if result.returncode != 0:
                # Try with default branch if specified branch not found
                if "not found" in result.stderr.lower() or "couldn't find" in result.stderr.lower():
                    result = subprocess.run(
                        ["git", "clone", "--depth", "1", clone_url, str(workspace_path)],
                        capture_output=True,
                        text=True,
                        timeout=CLONE_TIMEOUT,
                    )
                    
                    if result.returncode != 0:
                        raise Exception(f"Git clone failed: {result.stderr}")
                    
                    branch = "main"  # Default fallback
                else:
                    raise Exception(f"Git clone failed: {result.stderr}")
            
            # Get commit SHA
            commit_sha, _ = self._get_git_info(workspace_path)
            
            # Check repo size
            size_mb = self._get_directory_size(workspace_path) / (1024 * 1024)
            if size_mb > MAX_REPO_SIZE_MB:
                shutil.rmtree(workspace_path, ignore_errors=True)
                return ImportResult(
                    success=False,
                    project_id="",
                    workspace_path="",
                    commit_sha="",
                    branch="",
                    repo_url=github_url,
                    error=f"Repository too large: {size_mb:.1f}MB (max: {MAX_REPO_SIZE_MB}MB)",
                )
            
            return ImportResult(
                success=True,
                project_id=project_id,
                workspace_path=str(workspace_path),
                commit_sha=commit_sha or "unknown",
                branch=branch,
                repo_url=github_url,
            )
            
        except subprocess.TimeoutExpired:
            if workspace_path.exists():
                shutil.rmtree(workspace_path, ignore_errors=True)
            return ImportResult(
                success=False,
                project_id="",
                workspace_path="",
                commit_sha="",
                branch="",
                repo_url=github_url,
                error=f"Clone timed out after {CLONE_TIMEOUT} seconds",
            )
        except Exception as e:
            if workspace_path.exists():
                shutil.rmtree(workspace_path, ignore_errors=True)
            return ImportResult(
                success=False,
                project_id="",
                workspace_path="",
                commit_sha="",
                branch="",
                repo_url=github_url,
                error=str(e),
            )
    
    def _parse_github_url(self, url: str) -> tuple[str, str] | None:
        """Parse GitHub URL to extract owner and repo"""
        # Handle various GitHub URL formats
        patterns = [
            r"github\.com[:/]([^/]+)/([^/.]+?)(?:\.git)?$",
            r"github\.com/([^/]+)/([^/]+?)(?:\.git)?(?:/.*)?$",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1), match.group(2)
        
        return None
    
    def _get_git_info(self, repo_path: str) -> tuple[str | None, str | None]:
        """Get current commit SHA and branch from git repo"""
        try:
            # Get commit SHA
            sha_result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            commit_sha = sha_result.stdout.strip() if sha_result.returncode == 0 else None
            
            # Get branch name
            branch_result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
            
            return commit_sha, branch
            
        except Exception:
            return None, None
    
    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory in bytes"""
        total = 0
        for item in path.rglob("*"):
            if item.is_file():
                try:
                    total += item.stat().st_size
                except:
                    pass
        return total
    
    def _get_ignore_func(self):
        """Get function to ignore certain files during copy"""
        ignore_patterns = {
            ".git", ".github", ".gitignore",
            "node_modules", "__pycache__", ".venv", "venv",
            ".pytest_cache", ".mypy_cache", ".tox",
            "dist", "build", ".next", ".nuxt",
            ".DS_Store", "Thumbs.db",
            "*.pyc", "*.pyo", "*.so", "*.dll",
            ".coverage", "htmlcov",
            ".env", ".env.local",
        }
        
        def ignore_func(dir, files):
            return [f for f in files if f in ignore_patterns or 
                   any(f.endswith(p.replace("*", "")) for p in ignore_patterns if "*" in p)]
        
        return ignore_func
    
    def delete_workspace(self, project_id: str) -> bool:
        """Delete a workspace by project ID"""
        workspace_path = self.workspace_root / project_id
        if workspace_path.exists():
            shutil.rmtree(workspace_path, ignore_errors=True)
            return True
        return False
    
    def get_workspace_path(self, project_id: str) -> str | None:
        """Get workspace path for a project"""
        workspace_path = self.workspace_root / project_id
        if workspace_path.exists():
            return str(workspace_path)
        return None
