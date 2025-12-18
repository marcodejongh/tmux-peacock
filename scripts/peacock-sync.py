#!/usr/bin/env python3
"""
tmux-peacock-sync: Sync tmux pane colors with VSCode Peacock extension colors
"""

import os
import subprocess
import sys
from pathlib import Path

from peacock_utils import (
    FileLock,
    get_peacock_color,
    mute_color,
    create_background_tint,
    SUBPROCESS_TIMEOUT,
)


def set_tmux_pane_colors(color):
    if color:
        muted = mute_color(color, 0.6)
        bright = mute_color(color, 0.8)
        bg_tint = create_background_tint(color, 0.08)

        if not muted or not bright or not bg_tint:
            return

        try:
            subprocess.run(
                [
                    "tmux",
                    "set-option",
                    "pane-border-style",
                    f"fg={muted}",
                    ";",
                    "set-option",
                    "pane-active-border-style",
                    f"fg={bright}",
                    ";",
                    "set-option",
                    "window-style",
                    f"bg={bg_tint}",
                    ";",
                    "set-option",
                    "window-active-style",
                    "bg=default",
                ],
                capture_output=True,
                timeout=SUBPROCESS_TIMEOUT,
            )
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
    else:
        try:
            subprocess.run(
                [
                    "tmux",
                    "set-option",
                    "pane-border-style",
                    "fg=colour240",
                    ";",
                    "set-option",
                    "pane-active-border-style",
                    "fg=colour250",
                    ";",
                    "set-option",
                    "window-style",
                    "bg=default",
                    ";",
                    "set-option",
                    "window-active-style",
                    "bg=default",
                ],
                capture_output=True,
                timeout=SUBPROCESS_TIMEOUT,
            )
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass


def main():
    if not os.environ.get("TMUX"):
        sys.exit(0)

    lock = FileLock()
    if not lock.acquire():
        sys.exit(0)

    try:
        directory = sys.argv[1] if len(sys.argv) > 1 else None
        if directory and not os.path.isdir(directory):
            directory = None
        peacock_color = get_peacock_color(directory)
        set_tmux_pane_colors(peacock_color)
    finally:
        lock.release()


if __name__ == "__main__":
    main()
