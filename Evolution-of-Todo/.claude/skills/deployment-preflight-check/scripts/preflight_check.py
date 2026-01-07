#!/usr/bin/env python3
"""
Deployment Pre-Flight Check Script

Validates deployment artifacts before pushing to Vercel or other serverless platforms.
Prevents common deployment failures like lock file conflicts, credential leaks, and env var issues.

Usage:
    python preflight_check.py --path ./backend
    python preflight_check.py --path ./backend --check credentials
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class PreflightChecker:
    """Runs deployment pre-flight checks."""

    def __init__(self, path: str):
        self.path = Path(path).resolve()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed: List[str] = []

    def check_lockfiles(self) -> bool:
        """Check for lock files that may conflict with requirements.txt."""
        print("\n[1/5] Checking lock file conflicts...")
        
        lockfiles = ["uv.lock", "poetry.lock", "Pipfile.lock"]
        found_lockfiles = []
        
        for lockfile in lockfiles:
            lockfile_path = self.path / lockfile
            if lockfile_path.exists():
                found_lockfiles.append(lockfile)
        
        pyproject = self.path / "pyproject.toml"
        if pyproject.exists():
            # Check if it's a UV/Poetry project file
            content = pyproject.read_text()
            if "[tool.uv]" in content or "[tool.poetry]" in content:
                found_lockfiles.append("pyproject.toml (with uv/poetry config)")
        
        requirements = self.path / "requirements.txt"
        if not requirements.exists():
            self.errors.append("requirements.txt not found - Vercel needs this file")
            return False
        
        if found_lockfiles:
            self.warnings.append(
                f"Found lock files that may override requirements.txt: {', '.join(found_lockfiles)}. "
                "Consider renaming to .bak extension for Vercel deployment."
            )
        else:
            self.passed.append("No conflicting lock files found")
        
        return len(self.errors) == 0

    def check_credentials(self) -> bool:
        """Scan for accidentally committed secrets."""
        print("\n[2/5] Checking for credential leaks...")
        
        # Patterns that indicate credentials
        patterns = [
            (r"npg_[A-Za-z0-9]{20,}", "Neon database password"),
            (r"sk-[A-Za-z0-9]{40,}", "OpenAI/Anthropic API key"),
            (r"password\s*=\s*['\"][^'\"]{8,}['\"]", "Hardcoded password"),
            (r"SECRET_KEY\s*=\s*['\"][^'\"]{16,}['\"]", "Hardcoded secret key"),
            (r"api[_-]?key\s*=\s*['\"][^'\"]{16,}['\"]", "Hardcoded API key"),
        ]
        
        found_credentials = []
        
        # Check tracked files only
        try:
            result = subprocess.run(
                ["git", "ls-files"],
                cwd=self.path,
                capture_output=True,
                text=True
            )
            tracked_files = result.stdout.strip().split("\n")
        except Exception:
            # If not a git repo, scan all Python/config files
            tracked_files = [
                str(p.relative_to(self.path))
                for p in self.path.rglob("*")
                if p.suffix in [".py", ".json", ".yaml", ".yml", ".toml", ".env"]
                and ".venv" not in str(p)
                and "node_modules" not in str(p)
            ]
        
        for file_path in tracked_files:
            full_path = self.path / file_path
            if not full_path.exists() or not full_path.is_file():
                continue
            
            try:
                content = full_path.read_text(errors="ignore")
                for pattern, desc in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        found_credentials.append(f"{file_path}: {desc}")
            except Exception:
                continue
        
        if found_credentials:
            self.errors.append(
                f"Potential credentials found in tracked files:\n  - " +
                "\n  - ".join(found_credentials)
            )
            return False
        
        self.passed.append("No credentials found in tracked files")
        return True

    def check_env_schema(self) -> bool:
        """Validate .env.example matches config.py types."""
        print("\n[3/5] Checking environment variable schema...")
        
        env_example = self.path / ".env.example"
        config_py = None
        
        # Find config.py
        for possible_path in [
            self.path / "app" / "core" / "config.py",
            self.path / "config.py",
            self.path / "src" / "config.py",
        ]:
            if possible_path.exists():
                config_py = possible_path
                break
        
        if not env_example.exists():
            self.warnings.append(".env.example not found - cannot validate env schema")
            return True
        
        if not config_py:
            self.warnings.append("config.py not found - cannot validate env schema")
            return True
        
        # Parse config.py for type hints
        config_content = config_py.read_text()
        list_str_vars = re.findall(r"(\w+)\s*:\s*list\[str\]", config_content, re.IGNORECASE)
        
        # Parse .env.example
        env_content = env_example.read_text()
        
        for var in list_str_vars:
            # Find the variable in .env.example
            match = re.search(rf"^{var}\s*=\s*(.+)$", env_content, re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Check if it's JSON array format
                if not (value.startswith("[") and value.endswith("]")):
                    self.warnings.append(
                        f"{var} should be JSON array format: [\"{value}\"] not {value}"
                    )
        
        self.passed.append("Environment schema validation complete")
        return True

    def check_cors(self) -> bool:
        """Validate CORS_ORIGINS format specifically."""
        print("\n[4/5] Checking CORS_ORIGINS format...")
        
        env_example = self.path / ".env.example"
        if not env_example.exists():
            self.warnings.append(".env.example not found - cannot validate CORS format")
            return True
        
        env_content = env_example.read_text()
        match = re.search(r"^CORS_ORIGINS\s*=\s*(.+)$", env_content, re.MULTILINE)
        
        if not match:
            self.passed.append("CORS_ORIGINS not defined in .env.example")
            return True
        
        value = match.group(1).strip()
        
        # Should be JSON array
        if not (value.startswith("[") and value.endswith("]")):
            self.errors.append(
                f"CORS_ORIGINS must be JSON array format.\n"
                f"  Current: {value}\n"
                f"  Expected: [\"https://example.com\",\"http://localhost:3000\"]"
            )
            return False
        
        # Validate JSON
        try:
            parsed = json.loads(value)
            if not isinstance(parsed, list):
                raise ValueError("Not a list")
            self.passed.append(f"CORS_ORIGINS is valid JSON array with {len(parsed)} origins")
        except (json.JSONDecodeError, ValueError) as e:
            self.errors.append(f"CORS_ORIGINS is not valid JSON: {e}")
            return False
        
        return True

    def check_gitignore(self) -> bool:
        """Verify .gitignore completeness."""
        print("\n[5/5] Checking .gitignore completeness...")
        
        gitignore = self.path / ".gitignore"
        if not gitignore.exists():
            # Check parent directory
            gitignore = self.path.parent / ".gitignore"
        
        if not gitignore.exists():
            self.errors.append(".gitignore not found")
            return False
        
        content = gitignore.read_text()
        
        required_patterns = [
            (".env", "Environment files"),
            ("__pycache__", "Python cache"),
            (".venv", "Virtual environment"),
            ("node_modules", "Node modules"),
        ]
        
        recommended_patterns = [
            ("uv.lock", "UV lock file"),
            ("*.local", "Local config files"),
        ]
        
        missing_required = []
        missing_recommended = []
        
        for pattern, desc in required_patterns:
            if pattern not in content:
                missing_required.append(f"{pattern} ({desc})")
        
        for pattern, desc in recommended_patterns:
            if pattern not in content:
                missing_recommended.append(f"{pattern} ({desc})")
        
        if missing_required:
            self.errors.append(
                f"Missing required .gitignore patterns:\n  - " +
                "\n  - ".join(missing_required)
            )
        
        if missing_recommended:
            self.warnings.append(
                f"Missing recommended .gitignore patterns:\n  - " +
                "\n  - ".join(missing_recommended)
            )
        
        if not missing_required:
            self.passed.append(".gitignore contains all required patterns")
        
        return len(missing_required) == 0

    def run_all(self) -> bool:
        """Run all preflight checks."""
        print(f"Running preflight checks for: {self.path}")
        print("=" * 60)
        
        results = [
            self.check_lockfiles(),
            self.check_credentials(),
            self.check_env_schema(),
            self.check_cors(),
            self.check_gitignore(),
        ]
        
        print("\n" + "=" * 60)
        print("PREFLIGHT CHECK RESULTS")
        print("=" * 60)
        
        if self.passed:
            print("\nPASSED:")
            for msg in self.passed:
                print(f"  [OK] {msg}")
        
        if self.warnings:
            print("\nWARNINGS:")
            for msg in self.warnings:
                print(f"  [WARN] {msg}")
        
        if self.errors:
            print("\nERRORS:")
            for msg in self.errors:
                print(f"  [FAIL] {msg}")
        
        all_passed = all(results)
        
        print("\n" + "=" * 60)
        if all_passed:
            print("STATUS: READY FOR DEPLOYMENT")
        else:
            print("STATUS: DEPLOYMENT BLOCKED - FIX ERRORS ABOVE")
        print("=" * 60)
        
        return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Deployment Pre-Flight Check"
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to the deployment directory (e.g., ./backend)"
    )
    parser.add_argument(
        "--check",
        choices=["lockfiles", "credentials", "env-schema", "cors", "gitignore"],
        help="Run only a specific check"
    )
    
    args = parser.parse_args()
    
    checker = PreflightChecker(args.path)
    
    if args.check:
        check_map = {
            "lockfiles": checker.check_lockfiles,
            "credentials": checker.check_credentials,
            "env-schema": checker.check_env_schema,
            "cors": checker.check_cors,
            "gitignore": checker.check_gitignore,
        }
        result = check_map[args.check]()
    else:
        result = checker.run_all()
    
    sys.exit(0 if result else 1)


if __name__ == "__main__":
    main()
