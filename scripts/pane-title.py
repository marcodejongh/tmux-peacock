#!/usr/bin/env python3
"""
tmux-pane-title: Generate title for a specific pane based on its directory
"""

import os
import subprocess
import sys
from pathlib import Path


def get_git_toplevel(directory):
    """Get git repository toplevel using git rev-parse"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=directory,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def get_git_branch(directory):
    """Get current git branch name"""
    try:
        result = subprocess.run(
            ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
            cwd=directory,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            # HEAD means detached, get short SHA instead
            if branch == 'HEAD':
                result = subprocess.run(
                    ['git', 'rev-parse', '--short', 'HEAD'],
                    cwd=directory,
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            return branch
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def get_worktree_info(directory, git_root):
    """Get worktree/repo name and relative path within it"""
    if not git_root:
        return None, None

    git_root_path = Path(git_root)
    current_path = Path(directory)

    try:
        git_path = git_root_path / '.git'
        if git_path.exists() and git_path.is_file():
            repo_name = git_root_path.name
        else:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=directory,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                repo_name = url.rstrip('/').rstrip('.git').split('/')[-1]
            else:
                repo_name = git_root_path.name
    except (subprocess.SubprocessError, FileNotFoundError):
        repo_name = git_root_path.name

    try:
        rel_path = current_path.relative_to(git_root_path)
        if str(rel_path) == '.':
            return repo_name, None
        else:
            rel_str = str(rel_path)
            if len(rel_str) > 20:
                rel_str = '...' + rel_str[-17:]
            return repo_name, rel_str
    except ValueError:
        return repo_name, None


def normalize_path(directory):
    """Normalize path by replacing home directory with ~"""
    home = str(Path.home())
    if directory.startswith(home):
        return directory.replace(home, "~", 1)
    return directory


def main():
    """Generate title for the given directory"""
    directory = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    git_root = get_git_toplevel(directory)

    if git_root:
        worktree_name, subdir = get_worktree_info(directory, git_root)
        branch = get_git_branch(directory)

        # Build title: repo@branch:subdir
        title = worktree_name
        if branch:
            title += f"@{branch}"
        if subdir:
            title += f":{subdir}"
        print(title)
    else:
        normalized_path = normalize_path(directory)
        if normalized_path == "~":
            print("~")
        else:
            print(Path(normalized_path).name or normalized_path)


if __name__ == "__main__":
    main()
