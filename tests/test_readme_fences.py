from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"
EXAMPLES_DIR = REPO_ROOT / "examples"

_FENCE_RE = re.compile(r"```python\n(.*?)```", re.DOTALL)


def _python_fences() -> list[str]:
    return _FENCE_RE.findall(README.read_text())


def _compiles(src: str, filename: str) -> tuple[bool, SyntaxError | None]:
    """Compile ``src`` as a module; if that fails only because it uses a
    statement that is legal inside a function body (bare ``return``, or
    ``await``/``async for`` outside an ``async def``), retry wrapped in an
    ``async def`` so intentionally partial "excerpt inside your handler"
    fences aren't flagged. Any other SyntaxError (real typos, mismatched
    parens, bad indentation) still fails.
    """
    try:
        compile(src, filename, "exec")
        return True, None
    except SyntaxError as exc:
        partial_excerpt_markers = ("outside function", "outside async function")
        if not any(marker in str(exc) for marker in partial_excerpt_markers):
            return False, exc
        wrapped = "async def __readme_fence_wrapper__():\n" + "\n".join(
            f"    {line}" if line.strip() else line for line in src.splitlines()
        )
        try:
            compile(wrapped, filename, "exec")
            return True, None
        except SyntaxError as wrapped_exc:
            return False, wrapped_exc


class TestReadmeFencesCompile:
    def test_every_python_fence_compiles(self):
        fences = _python_fences()
        assert fences, "expected at least one python fence in README"
        for i, src in enumerate(fences):
            ok, exc = _compiles(src, f"<readme-fence-{i}>")
            if not ok:  # pragma: no cover - failure path
                pytest.fail(f"README fence {i} has a syntax error: {exc}\n---\n{src}")


class TestWritePathKwargsCorrect:
    def _all_kwargs_for_call(self, func_name: str) -> set[str]:
        found: set[str] = set()
        for src in _python_fences():
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == func_name
                ):
                    found.update(kw.arg for kw in node.keywords if kw.arg)
        return found

    def test_bulk_change_action_uses_ids_not_change_ids(self):
        kwargs = self._all_kwargs_for_call("bulk_change_action")
        assert "ids" in kwargs
        assert "change_ids" not in kwargs

    def test_update_action_item_uses_action_not_status(self):
        kwargs = self._all_kwargs_for_call("update_action_item")
        assert "action" in kwargs
        assert "status" not in kwargs


class TestExamplesImportClean:
    @pytest.mark.parametrize(
        "example_path",
        sorted(EXAMPLES_DIR.glob("*.py")),
        ids=lambda p: p.name,
    )
    def test_example_imports_without_error(
        self, example_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        # Stub network + required env so import-time code (module-level clients,
        # os.environ reads) cannot hit the network or KeyError.
        monkeypatch.setenv("SEOJUICE_WEBHOOK_SECRET", "whsec_test")
        monkeypatch.setenv("SEOJUICE_API_KEY", "sk_test")
        monkeypatch.setattr(
            httpx.Client,
            "request",
            lambda self, *a, **k: httpx.Response(200, json={}),
        )
        spec = importlib.util.spec_from_file_location(
            f"seojuice_example_{example_path.stem}", example_path
        )
        assert spec and spec.loader
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
        except ModuleNotFoundError as exc:
            # Optional framework deps (flask/fastapi/celery/redis/django) may be
            # absent in the test venv — that is not an SDK drift failure.
            pytest.skip(f"optional dependency missing for {example_path.name}: {exc}")
