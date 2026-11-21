import ast
import importlib
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT_DIR = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".venv", ".git", ".pytest_cache", "__pycache__", ".venv-verify"}


def _collect_files(extensions: tuple[str, ...]) -> list[Path]:
    matched: list[Path] = []
    for root, dirs, files in os.walk(ROOT_DIR):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            path = Path(root) / f
            if any(path.name.endswith(ext) for ext in extensions):
                matched.append(path)
    return matched


def test_rule_3a_no_em_dash_or_en_dash():
    em_dash = chr(0x2014)
    en_dash = chr(0x2013)
    extensions = (".py", ".md", ".txt", ".toml", ".ini", ".example", ".yml")
    offenders: list[str] = []

    for file_path in _collect_files(extensions):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                for line_no, line in enumerate(fh, 1):
                    if em_dash in line or en_dash in line:
                        rel = file_path.relative_to(ROOT_DIR)
                        offenders.append(f"{rel}:{line_no}: {line.strip()}")
        except Exception as exc:
            offenders.append(f"Error reading {file_path}: {exc}")

    assert not offenders, (
        f"Found em-dash or en-dash characters in files:\n" + "\n".join(offenders)
    )


def test_rule_3b_requirements_pinned():
    req_path = ROOT_DIR / "requirements.txt"
    assert req_path.is_file(), "requirements.txt not found"
    unpinned: list[str] = []

    with open(req_path, "r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                if "==" not in stripped:
                    unpinned.append(f"requirements.txt:{line_no}: {stripped}")

    assert not unpinned, (
        "Every dependency in requirements.txt must be pinned with '==':\n"
        + "\n".join(unpinned)
    )


def test_rule_3c_env_example_no_comments_and_vars_in_config():
    env_example = ROOT_DIR / ".env.example"
    config_file = ROOT_DIR / "src" / "config.py"
    assert env_example.is_file(), ".env.example not found"
    assert config_file.is_file(), "src/config.py not found"

    config_content = config_file.read_text(encoding="utf-8")
    comment_lines: list[str] = []
    missing_vars: list[str] = []

    with open(env_example, "r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, 1):
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                comment_lines.append(f".env.example:{line_no}: {stripped}")
                continue
            var_name = stripped.split("=", 1)[0].strip()
            if var_name not in config_content:
                missing_vars.append(
                    f".env.example:{line_no}: '{var_name}' not in src/config.py"
                )

    assert not comment_lines, (
        ".env.example contains comment lines:\n" + "\n".join(comment_lines)
    )
    assert not missing_vars, (
        "Variables from .env.example missing in src/config.py:\n"
        + "\n".join(missing_vars)
    )


def test_rule_3d_no_hardcoded_api_keys_or_gsk():
    extensions = (".py", ".md", ".txt", ".toml", ".ini", ".example", ".yml")
    target_prefix = "".join(["g", "s", "k", "_"])
    offenders: list[str] = []

    for file_path in _collect_files(extensions):
        if file_path.name == ".env" or file_path.name == "test_project_rules.py":
            continue
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as fh:
                for line_no, line in enumerate(fh, 1):
                    if target_prefix in line:
                        rel = file_path.relative_to(ROOT_DIR)
                        offenders.append(f"{rel}:{line_no}: contains API key prefix")
        except Exception as exc:
            offenders.append(f"Error reading {file_path}: {exc}")

    assert not offenders, (
        "Found hardcoded API keys or key prefix strings:\n" + "\n".join(offenders)
    )


def test_rule_3e_config_import_without_secrets_or_env():
    import src.config

    clean_env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("GROQ_")
        and k
        not in (
            "MAX_AGENT_STEPS",
            "REQUEST_TIMEOUT",
            "MAX_TOKENS",
            "TEMPERATURE",
            "USER_AGENT",
        )
    }

    with patch.dict(os.environ, clean_env, clear=True):
        if "src.config" in sys.modules:
            del sys.modules["src.config"]
        imported = importlib.import_module("src.config")
        assert hasattr(imported, "GROQ_API_KEY")
        assert hasattr(imported, "GROQ_MODEL")


def test_rule_3f_with_groq_api_key_set_st_secrets_never_consulted():
    test_env = dict(os.environ)
    test_env["GROQ_API_KEY"] = "dummy_test_key_for_rule_check"

    import streamlit as st

    mock_secrets = MagicMock()
    mock_secrets.__getitem__.side_effect = RuntimeError("st.secrets accessed!")
    mock_secrets.get.side_effect = RuntimeError("st.secrets accessed!")

    with patch.dict(os.environ, test_env, clear=True):
        with patch.object(st, "secrets", mock_secrets):
            if "src.config" in sys.modules:
                del sys.modules["src.config"]
            imported = importlib.import_module("src.config")
            assert imported.GROQ_API_KEY == "dummy_test_key_for_rule_check"
            mock_secrets.get.assert_not_called()
            mock_secrets.__getitem__.assert_not_called()


def test_rule_3g_function_type_hints_and_length():
    py_files: list[Path] = []
    for root, dirs, files in os.walk(ROOT_DIR / "src"):
        for f in files:
            if f.endswith(".py"):
                py_files.append(Path(root) / f)
    app_py = ROOT_DIR / "app.py"
    if app_py.is_file():
        py_files.append(app_py)

    violations: list[str] = []

    for file_path in py_files:
        rel = file_path.relative_to(ROOT_DIR)
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(rel))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                line_count = (node.end_lineno - node.lineno) + 1 if hasattr(node, "end_lineno") else 0
                if line_count > 50:
                    violations.append(
                        f"{rel}:{node.lineno}: function '{node.name}' is {line_count} lines (> 50)"
                    )
                if node.returns is None:
                    violations.append(
                        f"{rel}:{node.lineno}: function '{node.name}' missing return type hint"
                    )
                for arg in node.args.args:
                    if arg.arg in ("self", "cls"):
                        continue
                    if arg.annotation is None:
                        violations.append(
                            f"{rel}:{node.lineno}: function '{node.name}' param '{arg.arg}' missing type hint"
                        )

    assert not violations, (
        "Functions must have type hints on parameters/return and be <= 50 lines:\n"
        + "\n".join(violations)
    )


def test_rule_3h_no_langchain_or_llama_index():
    py_files = _collect_files((".py",))
    violations: list[str] = []

    for file_path in py_files:
        rel = file_path.relative_to(ROOT_DIR)
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(rel))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name_lower = alias.name.lower()
                    if "langchain" in name_lower or "llama_index" in name_lower:
                        violations.append(
                            f"{rel}:{node.lineno}: forbidden import '{alias.name}'"
                        )
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod_lower = node.module.lower()
                    if "langchain" in mod_lower or "llama_index" in mod_lower:
                        violations.append(
                            f"{rel}:{node.lineno}: forbidden import from '{node.module}'"
                        )

    assert not violations, (
        "langchain and llama_index are strictly forbidden:\n" + "\n".join(violations)
    )
