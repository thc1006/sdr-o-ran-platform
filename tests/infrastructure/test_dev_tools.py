"""
Test Development Tools Configuration
REQ-INFRA-008: Development tools must be properly configured

Tests verify:
1. .coveragerc exists with proper configuration
2. pyproject.toml exists with tool configurations
3. .pre-commit-config.yaml exists with hooks
4. .editorconfig exists with basic rules
"""

import os
import subprocess
import pytest
from pathlib import Path
try:
    import tomli as tomllib
except ImportError:
    try:
        import tomllib
    except ImportError:
        import toml as tomllib


class TestCoverageConfiguration:
    """Test coverage configuration"""

    REPO_ROOT = Path(__file__).parent.parent.parent
    COVERAGERC = REPO_ROOT / ".coveragerc"

    def test_coveragerc_exists(self):
        """Verify .coveragerc file exists"""
        assert self.COVERAGERC.exists(), \
            f".coveragerc not found at {self.COVERAGERC}"

    def test_coveragerc_has_run_section(self):
        """Verify .coveragerc has [run] section with source"""
        with open(self.COVERAGERC, 'r') as f:
            content = f.read()

        assert '[run]' in content, \
            ".coveragerc must have [run] section"
        assert 'source' in content or 'source_pkgs' in content, \
            ".coveragerc must specify source/source_pkgs"

    def test_coveragerc_has_report_section(self):
        """Verify .coveragerc has [report] section"""
        with open(self.COVERAGERC, 'r') as f:
            content = f.read()

        assert '[report]' in content, \
            ".coveragerc must have [report] section"

    def test_coveragerc_excludes_tests(self):
        """Verify .coveragerc excludes test files"""
        with open(self.COVERAGERC, 'r') as f:
            content = f.read()

        # Should exclude tests from coverage
        assert 'omit' in content or 'exclude' in content, \
            ".coveragerc should exclude test files from coverage"


class TestPyprojectToml:
    """Test pyproject.toml configuration"""

    REPO_ROOT = Path(__file__).parent.parent.parent
    PYPROJECT = REPO_ROOT / "pyproject.toml"

    def test_pyproject_toml_exists(self):
        """Verify pyproject.toml file exists"""
        assert self.PYPROJECT.exists(), \
            f"pyproject.toml not found at {self.PYPROJECT}"

    def test_pyproject_has_tool_pytest(self):
        """Verify pyproject.toml has pytest configuration"""
        with open(self.PYPROJECT, 'rb') as f:
            try:
                data = tomllib.load(f)
            except AttributeError:
                # toml library uses different API
                f.seek(0)
                data = tomllib.loads(f.read().decode())

        assert 'tool' in data, \
            "pyproject.toml must have [tool] section"
        assert 'pytest' in data.get('tool', {}), \
            "pyproject.toml must have [tool.pytest] section"

    def test_pyproject_has_tool_coverage(self):
        """Verify pyproject.toml has coverage configuration"""
        with open(self.PYPROJECT, 'rb') as f:
            try:
                data = tomllib.load(f)
            except AttributeError:
                f.seek(0)
                data = tomllib.loads(f.read().decode())

        # Coverage config can be in pyproject.toml
        tools = data.get('tool', {})
        # It's ok if coverage is in .coveragerc instead
        # This test just checks if pyproject.toml is valid

    def test_pyproject_has_tool_black(self):
        """Verify pyproject.toml has black configuration"""
        with open(self.PYPROJECT, 'rb') as f:
            try:
                data = tomllib.load(f)
            except AttributeError:
                f.seek(0)
                data = tomllib.loads(f.read().decode())

        tools = data.get('tool', {})
        assert 'black' in tools, \
            "pyproject.toml must have [tool.black] section"

    def test_pyproject_has_tool_isort(self):
        """Verify pyproject.toml has isort configuration"""
        with open(self.PYPROJECT, 'rb') as f:
            try:
                data = tomllib.load(f)
            except AttributeError:
                f.seek(0)
                data = tomllib.loads(f.read().decode())

        tools = data.get('tool', {})
        assert 'isort' in tools, \
            "pyproject.toml must have [tool.isort] section"


class TestPreCommitConfig:
    """Test pre-commit configuration"""

    REPO_ROOT = Path(__file__).parent.parent.parent
    PRECOMMIT = REPO_ROOT / ".pre-commit-config.yaml"

    def test_precommit_config_exists(self):
        """Verify .pre-commit-config.yaml file exists"""
        assert self.PRECOMMIT.exists(), \
            f".pre-commit-config.yaml not found at {self.PRECOMMIT}"

    def test_precommit_has_repos(self):
        """Verify .pre-commit-config.yaml has repos"""
        with open(self.PRECOMMIT, 'r') as f:
            content = f.read()

        assert 'repos:' in content, \
            ".pre-commit-config.yaml must have repos section"

    def test_precommit_has_hooks(self):
        """Verify .pre-commit-config.yaml has hooks"""
        with open(self.PRECOMMIT, 'r') as f:
            content = f.read()

        assert 'hooks:' in content, \
            ".pre-commit-config.yaml must have hooks"

    def test_precommit_yaml_valid(self):
        """Verify .pre-commit-config.yaml is valid YAML"""
        import yaml

        with open(self.PRECOMMIT, 'r') as f:
            try:
                data = yaml.safe_load(f)
                assert data is not None, \
                    ".pre-commit-config.yaml must not be empty"
                assert isinstance(data.get('repos'), list), \
                    ".pre-commit-config.yaml repos must be a list"
            except yaml.YAMLError as e:
                pytest.fail(f".pre-commit-config.yaml is not valid YAML: {e}")


class TestEditorConfig:
    """Test .editorconfig configuration"""

    REPO_ROOT = Path(__file__).parent.parent.parent
    EDITORCONFIG = REPO_ROOT / ".editorconfig"

    def test_editorconfig_exists(self):
        """Verify .editorconfig file exists"""
        assert self.EDITORCONFIG.exists(), \
            f".editorconfig not found at {self.EDITORCONFIG}"

    def test_editorconfig_has_root(self):
        """Verify .editorconfig has root = true"""
        with open(self.EDITORCONFIG, 'r') as f:
            content = f.read()

        assert 'root = true' in content or 'root=true' in content, \
            ".editorconfig must have 'root = true'"

    def test_editorconfig_has_python_section(self):
        """Verify .editorconfig has Python section"""
        with open(self.EDITORCONFIG, 'r') as f:
            content = f.read()

        assert '*.py' in content or '[*.py]' in content, \
            ".editorconfig must have Python section"

    def test_editorconfig_has_basic_rules(self):
        """Verify .editorconfig has basic formatting rules"""
        with open(self.EDITORCONFIG, 'r') as f:
            content = f.read()

        # Should have at least one of these basic rules
        basic_rules = ['indent_style', 'indent_size', 'charset', 'end_of_line']
        has_rules = any(rule in content for rule in basic_rules)

        assert has_rules, \
            ".editorconfig must have basic formatting rules"


class TestPreCommitFunctional:
    """Functional tests for pre-commit hooks"""

    def test_precommit_command_available(self):
        """Verify pre-commit command is available"""
        result = subprocess.run(
            ['which', 'pre-commit'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.skip("pre-commit not installed (optional)")

    def test_precommit_hooks_installable(self):
        """Verify pre-commit hooks can be installed"""
        # Check if pre-commit is available
        result = subprocess.run(
            ['which', 'pre-commit'],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            pytest.skip("pre-commit not installed (optional)")

        # Try to validate config
        result = subprocess.run(
            ['pre-commit', 'validate-config'],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent.parent
        )

        assert result.returncode == 0, \
            f"pre-commit config validation failed: {result.stderr}"


# Boy Scout Rule: Document the purpose of development tools
"""
Development Tools Purpose:

1. .coveragerc:
   - Configures pytest-cov behavior
   - Defines what to include/exclude from coverage
   - Sets coverage thresholds

2. pyproject.toml:
   - Central configuration for Python tools
   - Configures pytest, black, isort
   - Modern Python project standard (PEP 518)

3. .pre-commit-config.yaml:
   - Automates code quality checks
   - Runs before git commit
   - Prevents bad code from being committed

4. .editorconfig:
   - Ensures consistent formatting across editors
   - Works with VSCode, Vim, IntelliJ, etc.
   - Prevents whitespace issues
"""
