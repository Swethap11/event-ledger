import subprocess
from pathlib import Path


def validate_lint(file_path: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["ruff", "check", str(file_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True, ""
    return False, (result.stdout + result.stderr).strip()


def validate_lint_directory(directory: Path) -> tuple[bool, str]:
    result = subprocess.run(
        ["ruff", "check", str(directory)],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        return True, ""
    return False, (result.stdout + result.stderr).strip()
