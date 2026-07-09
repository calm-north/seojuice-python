from __future__ import annotations

import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    tomllib = None  # type: ignore[assignment]

import seojuice

PYPROJECT_PATH = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _pyproject_version() -> str:
    if tomllib is not None:
        with PYPROJECT_PATH.open("rb") as f:
            data = tomllib.load(f)
        return data["project"]["version"]

    text = PYPROJECT_PATH.read_text()
    match = re.search(r'(?m)^version\s*=\s*"([^"]+)"', text)
    assert match, "Could not find version in pyproject.toml"
    return match.group(1)


class TestVersion:
    def test_package_version_matches_pyproject(self):
        assert seojuice.__version__ == _pyproject_version()

    def test_user_agent_embeds_version(self):
        from seojuice._async import _USER_AGENT as async_ua
        from seojuice._sync import _USER_AGENT as sync_ua

        assert sync_ua == f"seojuice-python/{seojuice.__version__}"
        assert async_ua == f"seojuice-python/{seojuice.__version__}"

    def test_user_agent_is_not_stale_0_1_0(self):
        from seojuice._sync import _VERSION

        assert _VERSION != "0.1.0"
        assert _VERSION == seojuice.__version__
