import subprocess
import sys
from pathlib import Path


def _ruff_cmd(*args: str) -> list[str]:
    return [sys.executable, "-m", "ruff", *args]


def validate_lint(file_path: Path) -> tuple[bool, str]:
    subprocess.run(
        _ruff_cmd("format", str(file_path)),
        capture_output=True,
        text=True,
    )
    subprocess.run(
        _ruff_cmd("check", "--fix", "--unsafe-fixes", str(file_path)),
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        _ruff_cmd("check", str(file_path)),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True, ""
    return False, (result.stdout + result.stderr).strip()


def validate_lint_directory(directory: Path) -> tuple[bool, str]:
    subprocess.run(
        _ruff_cmd("format", str(directory)),
        capture_output=True,
        text=True,
    )
    subprocess.run(
        _ruff_cmd("check", "--fix", "--unsafe-fixes", str(directory)),
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        _ruff_cmd("check", str(directory)),
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True, ""
    return False, (result.stdout + result.stderr).strip()
