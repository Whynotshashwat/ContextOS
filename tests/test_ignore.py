import pytest
from pathlib import Path
from core.ignore import IgnoreRules


# --- Fixtures ---

@pytest.fixture
def project(tmp_path):
    return tmp_path


@pytest.fixture
def ignore_with_rules(tmp_path):
    ignore_file = tmp_path / ".contextosignore"
    ignore_file.write_text("""# Test ignore file
.venv/
__pycache__/
*.pyc
node_modules/
*.log
""")
    return IgnoreRules(tmp_path)


# --- Tests ---

def test_ignore_loads_default_rules(project):
    ignore = IgnoreRules(project)
    assert len(ignore.rules) > 0


def test_ignore_creates_default_file(project):
    ignore = IgnoreRules(project)
    path = ignore.create_default()
    assert path.exists()


def test_ignore_loads_custom_rules(ignore_with_rules):
    rules = ignore_with_rules.list_rules()
    assert ".venv/" in rules
    assert "__pycache__/" in rules


def test_ignore_skips_comments(ignore_with_rules):
    rules = ignore_with_rules.list_rules()
    assert not any(r.startswith("#") for r in rules)


def test_is_ignored_venv(ignore_with_rules):
    assert ignore_with_rules.is_ignored(".venv/scripts/python.exe") == True


def test_is_ignored_pycache(ignore_with_rules):
    assert ignore_with_rules.is_ignored("core/__pycache__/engine.pyc") == True


def test_is_ignored_pyc(ignore_with_rules):
    assert ignore_with_rules.is_ignored("core/engine.pyc") == True


def test_is_ignored_log(ignore_with_rules):
    assert ignore_with_rules.is_ignored("logs/2026-05-24.log") == True


def test_is_not_ignored_source(ignore_with_rules):
    assert ignore_with_rules.is_ignored("core/engine.py") == False


def test_is_not_ignored_readme(ignore_with_rules):
    assert ignore_with_rules.is_ignored("README.md") == False


def test_filter_paths(ignore_with_rules):
    paths = [
        "core/engine.py",
        ".venv/scripts/python.exe",
        "core/__pycache__/engine.pyc",
        "README.md",
        "cli/main.py"
    ]
    filtered = ignore_with_rules.filter_paths(paths)
    assert "core/engine.py" in filtered
    assert "README.md" in filtered
    assert "cli/main.py" in filtered
    assert ".venv/scripts/python.exe" not in filtered
    assert "core/__pycache__/engine.pyc" not in filtered


def test_add_rule(project):
    ignore = IgnoreRules(project)
    ignore.create_default()
    ignore.add_rule("custom_folder/")
    assert "custom_folder/" in ignore.list_rules()


def test_remove_rule(project):
    ignore = IgnoreRules(project)
    ignore.create_default()
    ignore.add_rule("custom_folder/")
    ignore.remove_rule("custom_folder/")
    assert "custom_folder/" not in ignore.list_rules()


def test_no_duplicate_rules(project):
    ignore = IgnoreRules(project)
    ignore.create_default()
    initial_count = len(ignore.list_rules())
    ignore.add_rule(".venv/")
    assert len(ignore.list_rules()) == initial_count