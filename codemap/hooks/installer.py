"""Git hook installation utilities."""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path


def install_pre_commit(repo_root: Path | None = None) -> None:
    """Install the CodeMap pre-commit hook.

    Args:
        repo_root: Optional repository root. Defaults to current directory.

    Raises:
        FileNotFoundError: If .git/hooks directory doesn't exist.
    """
    if repo_root is None:
        repo_root = Path.cwd()

    hooks_dir = repo_root / ".git" / "hooks"
    if not hooks_dir.exists():
        raise FileNotFoundError(
            f"Git hooks directory not found: {hooks_dir}\n"
            "Make sure you're in a git repository."
        )

    # Get the path to our pre-commit hook
    source_hook = Path(__file__).parent / "pre-commit"
    if not source_hook.exists():
        raise FileNotFoundError(f"Pre-commit hook not found: {source_hook}")

    target_hook = hooks_dir / "pre-commit"

    # Check if a pre-commit hook already exists
    if target_hook.exists():
        # Read existing hook to check if it's ours
        existing_content = target_hook.read_text()
        if "CodeMap pre-commit hook" in existing_content:
            # Our hook is already installed, update it
            pass
        else:
            # Another hook exists, we need to chain them
            _chain_hooks(target_hook, source_hook)
            return

    # Copy our hook
    shutil.copy(source_hook, target_hook)

    # Make it executable
    target_hook.chmod(target_hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def _chain_hooks(existing_hook: Path, new_hook: Path) -> None:
    """Chain a new hook with an existing one.

    Creates a wrapper that runs both hooks.

    Args:
        existing_hook: Path to existing pre-commit hook.
        new_hook: Path to our pre-commit hook.
    """
    # Backup existing hook
    backup_path = existing_hook.parent / "pre-commit.backup"
    shutil.copy(existing_hook, backup_path)

    # Read both hooks
    existing_content = existing_hook.read_text()
    new_content = new_hook.read_text()

    # Create chained hook
    chained_content = f"""#!/bin/bash
# Chained pre-commit hooks

# Run existing hook first
{existing_content}
EXISTING_RESULT=$?

# Run CodeMap hook
{new_content}
CODEMAP_RESULT=$?

# Exit with failure if either failed
if [ $EXISTING_RESULT -ne 0 ]; then
    exit $EXISTING_RESULT
fi
exit $CODEMAP_RESULT
"""

    existing_hook.write_text(chained_content)

    # Ensure executable
    existing_hook.chmod(
        existing_hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )


def uninstall_pre_commit(repo_root: Path | None = None) -> bool:
    """Uninstall the CodeMap pre-commit hook.

    Args:
        repo_root: Optional repository root. Defaults to current directory.

    Returns:
        True if hook was removed, False if it wasn't installed.
    """
    if repo_root is None:
        repo_root = Path.cwd()

    target_hook = repo_root / ".git" / "hooks" / "pre-commit"
    backup_hook = repo_root / ".git" / "hooks" / "pre-commit.backup"

    if not target_hook.exists():
        return False

    content = target_hook.read_text()
    if "CodeMap pre-commit hook" not in content:
        return False

    # Check if there's a backup (chained hooks)
    if backup_hook.exists():
        # Restore original hook
        shutil.move(backup_hook, target_hook)
    else:
        # Just remove our hook
        target_hook.unlink()

    return True
