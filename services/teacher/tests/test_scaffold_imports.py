"""Scaffold import and domain isolation checks."""

from __future__ import annotations

import ast
from pathlib import Path

FORBIDDEN = frozenset(
    {
        "electron",
        "vue",
        "fastapi",
        "uvicorn",
        "langgraph",
        "langchain",
        "langchain_core",
        "openai",
        "anthropic",
        "telegram",
        "aiogram",
        "telebot",
    }
)

ADAPTER_FORBIDDEN = frozenset({"fastapi", "uvicorn"})

REPO_ROOT = Path(__file__).resolve().parents[3]
TEACHER_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = TEACHER_ROOT / "src" / "teacher_service"
DESKTOP_ROOT = REPO_ROOT / "apps" / "desktop"
SKIP_DIR_NAMES = frozenset({".venv", "node_modules"})


def test_import_teacher_service_domain() -> None:
    import teacher_service.domain  # noqa: F401


def _top_level_imports(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                names.add(alias.name.split(".", 1)[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                names.add(node.module.split(".", 1)[0])
            elif node.level and node.level > 0:
                # Relative import with module is None (e.g. `from . import foo`)
                for alias in node.names:
                    names.add(alias.name.split(".", 1)[0])
    return names


def _has_fastapi_app_assignment(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(t, ast.Name) and t.id == "app" for t in node.targets
        ):
            continue
        value = node.value
        if isinstance(value, ast.Call):
            func = value.func
            if isinstance(func, ast.Name) and func.id == "FastAPI":
                return True
            if isinstance(func, ast.Attribute) and func.attr == "FastAPI":
                return True
    return False


def test_domain_has_no_forbidden_imports() -> None:
    domain_root = PACKAGE_ROOT / "domain"
    assert domain_root.is_dir(), f"missing domain package at {domain_root}"

    hits: list[str] = []
    for path in sorted(domain_root.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        found = sorted(_top_level_imports(tree) & FORBIDDEN)
        for name in found:
            rel = path.relative_to(domain_root)
            hits.append(f"{rel}: {name}")

    assert not hits, "forbidden imports in domain:\n" + "\n".join(hits)


def test_adapters_have_no_fastapi_app() -> None:
    adapters_root = PACKAGE_ROOT / "adapters"
    assert adapters_root.is_dir(), f"missing adapters package at {adapters_root}"

    hits: list[str] = []
    for path in sorted(adapters_root.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        rel = path.relative_to(adapters_root)
        for name in sorted(_top_level_imports(tree) & ADAPTER_FORBIDDEN):
            hits.append(f"{rel}: forbidden import {name}")
        if _has_fastapi_app_assignment(tree):
            hits.append(f"{rel}: app = FastAPI(...)")

    assert not hits, "adapter FastAPI stubs not allowed in 1.1:\n" + "\n".join(hits)


def test_hexagonal_stub_layout_complete() -> None:
    """Complete seed layout — success state after create or delete-and-recreate."""
    root = PACKAGE_ROOT
    required = [
        root / "__init__.py",
        root / "domain" / "__init__.py",
        root / "ports" / "__init__.py",
        root / "graphs" / "__init__.py",
        root / "adapters" / "__init__.py",
        root / "adapters" / "api" / "__init__.py",
        root / "adapters" / "persistence" / "__init__.py",
        root / "adapters" / "llm" / "__init__.py",
        root / "adapters" / "voice" / "__init__.py",
        root / "adapters" / "telegram" / "__init__.py",
        root / "adapters" / "config" / "__init__.py",
    ]
    missing = [str(p.relative_to(root.parent)) for p in required if not p.is_file()]
    assert not missing, "incomplete teacher_service layout:\n" + "\n".join(missing)


def _unexpected_env_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    found: list[Path] = []
    for path in root.rglob(".env*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.name == ".env.example":
            continue
        if path.name == ".env" or path.name.startswith(".env."):
            found.append(path)
    return sorted(found)


def test_no_dotenv_secrets_in_scaffold_trees() -> None:
    unexpected: list[Path] = []
    for root in (TEACHER_ROOT, DESKTOP_ROOT, REPO_ROOT):
        unexpected.extend(_unexpected_env_files(root))
    # Repo-root scan already covers nested trees; dedupe
    unique = sorted(set(unexpected))
    assert unique == [], f"unexpected .env files: {unique}"
