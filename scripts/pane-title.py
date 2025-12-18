#!/usr/bin/env python3
"""
tmux-pane-title: Generate title for a specific pane based on its directory
"""

import os
import sys
from pathlib import Path

from peacock_utils import (
    get_git_toplevel,
    get_git_branch,
    get_worktree_info,
    normalize_path,
)


def main():
    directory = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    if not os.path.isdir(directory):
        directory = os.getcwd()

    git_root = get_git_toplevel(directory)

    if git_root:
        worktree_name, subdir = get_worktree_info(directory, git_root)
        branch = get_git_branch(directory)

        title = worktree_name or Path(git_root).name
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
