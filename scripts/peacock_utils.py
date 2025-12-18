#!/usr/bin/env python3
"""
peacock_utils.py - Shared utilities for tmux-peacock plugin

This module contains common functions for color manipulation, caching,
and git operations used by both peacock-sync.py and pane-title-colored.py.
"""

import fcntl
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Optional, Tuple

# Constants
SUBPROCESS_TIMEOUT = 5  # seconds
HEX_COLOR_RE = re.compile(r"^#?([0-9a-fA-F]{6})$")
MAX_JSON_SIZE = 1024 * 1024  # 1MB
LOCK_TIMEOUT = 10  # seconds


# =============================================================================
# Color Utilities
# =============================================================================


def validate_hex_color(color: str) -> Optional[str]:
    """
    Validate and normalize hex color format.

    Args:
        color: Color string to validate (with or without #)

    Returns:
        Normalized hex color (#RRGGBB) or None if invalid
    """
    if not isinstance(color, str):
        return None
    match = HEX_COLOR_RE.match(color.strip())
    if match:
        return f"#{match.group(1).lower()}"
    return None


def hex_to_rgb(hex_color: str) -> Optional[Tuple[int, int, int]]:
    """
    Convert hex color to RGB tuple.

    Args:
        hex_color: Hex color string (#RRGGBB or RRGGBB)

    Returns:
        RGB tuple (r, g, b) or None if invalid
    """
    normalized = validate_hex_color(hex_color)
    if not normalized:
        return None
    hex_str = normalized.lstrip("#")
    return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def mute_color(hex_color: str, factor: float = 0.3) -> Optional[str]:
    """
    Mute a color by blending it with black.

    Args:
        hex_color: Hex color to mute
        factor: Brightness factor (0.0 = black, 1.0 = original)

    Returns:
        Muted hex color or None if input invalid
    """
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return None
    r, g, b = rgb
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return rgb_to_hex((r, g, b))


def create_background_tint(hex_color: str, factor: float = 0.05) -> Optional[str]:
    """
    Create a very subtle background tint from a color.

    Args:
        hex_color: Base color for tint
        factor: Tint intensity (0.0 = no tint, 1.0 = full color)

    Returns:
        Tinted background hex color or None if input invalid
    """
    rgb = hex_to_rgb(hex_color)
    if not rgb:
        return None
    r, g, b = rgb
    bg_r, bg_g, bg_b = 30, 30, 30  # Dark background RGB

    r = int(bg_r + (r - bg_r) * factor)
    g = int(bg_g + (g - bg_g) * factor)
    b = int(bg_b + (b - bg_b) * factor)

    return rgb_to_hex((r, g, b))


def hsl_to_hex(h: float, s: float, l: float) -> str:
    """
    Convert HSL to hex color.

    Args:
        h: Hue (0-360)
        s: Saturation (0-100)
        l: Lightness (0-100)

    Returns:
        Hex color string
    """
    h = h / 360.0
    s = s / 100.0
    l = l / 100.0

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1 / 3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1 / 3)

    return rgb_to_hex((int(r * 255), int(g * 255), int(b * 255)))


def generate_color_for_name(name: str) -> str:
    """
    Generate a distinctive color for a given name using golden ratio.

    Args:
        name: String to generate color for

    Returns:
        Hex color string
    """
    if not name:
        name = "default"
    hash_val = hashlib.md5(name.encode()).hexdigest()
    seed = int(hash_val[:8], 16)

    golden_ratio_conjugate = 0.618033988749895
    hue = (seed * golden_ratio_conjugate) % 1.0
    hue = hue * 360

    saturation = 70
    lightness = 50

    return hsl_to_hex(hue, saturation, lightness)


# =============================================================================
# File Operations (with security protections)
# =============================================================================


def get_cache_file_path() -> Path:
    """Get the path to the color cache file."""
    return Path.home() / ".config" / "tmux-peacock-colors.json"


def safe_read_json(path: Path, max_size: int = MAX_JSON_SIZE) -> Optional[dict]:
    """
    Safely read JSON file with symlink and size checks.

    Args:
        path: Path to JSON file
        max_size: Maximum allowed file size in bytes

    Returns:
        Parsed JSON dict or None on error
    """
    try:
        # Reject symlinks
        if path.is_symlink():
            return None
        if not path.exists():
            return None
        # Check file size
        if path.stat().st_size > max_size:
            return None
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return None


def safe_write_json(path: Path, data: dict) -> bool:
    """
    Atomically write JSON file with symlink protection.

    Args:
        path: Path to write to
        data: Dictionary to write as JSON

    Returns:
        True on success, False on error
    """
    # Reject if path is a symlink
    if path.exists() and path.is_symlink():
        return False

    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write to temp file first (atomic)
        fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, indent=2)
            # Set secure permissions
            os.chmod(tmp_path, 0o600)
            # Atomic rename
            os.rename(tmp_path, path)
            return True
        except Exception:
            # Clean up temp file on error
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            return False
    except OSError:
        return False


def load_color_cache() -> dict:
    """Load cached color assignments."""
    cache = safe_read_json(get_cache_file_path())
    return cache if cache is not None else {}


def save_color_cache(cache: dict) -> bool:
    """Save color assignments to cache."""
    return safe_write_json(get_cache_file_path(), cache)


# =============================================================================
# Locking (proper fcntl-based implementation)
# =============================================================================


class FileLock:
    """
    A proper file lock using fcntl.flock().

    This lock is:
    - Atomic (no TOCTOU race conditions)
    - Automatically released on process exit/crash
    - Non-blocking with immediate return
    """

    def __init__(self, lock_path: str = "/tmp/tmux-peacock-sync.lock"):
        self.lock_path = lock_path
        self.lock_fd = None
        self.acquired = False

    def acquire(self) -> bool:
        """
        Try to acquire the lock (non-blocking).

        Returns:
            True if lock acquired, False if already held by another process
        """
        try:
            # Open or create lock file
            self.lock_fd = open(self.lock_path, "w")

            # Try to acquire exclusive, non-blocking lock
            fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

            # Write PID for debugging
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()

            self.acquired = True
            return True

        except (IOError, OSError):
            # Lock is held by another process
            if self.lock_fd:
                self.lock_fd.close()
                self.lock_fd = None
            return False

    def release(self):
        """Release the lock."""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd.fileno(), fcntl.LOCK_UN)
                self.lock_fd.close()
            except (IOError, OSError):
                pass
            self.lock_fd = None
            self.acquired = False

    def __enter__(self):
        if not self.acquire():
            raise BlockingIOError("Could not acquire lock")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False


# =============================================================================
# Git Operations (with timeouts)
# =============================================================================


def get_git_toplevel(directory: str) -> Optional[str]:
    """
    Get git repository toplevel using git rev-parse.

    Args:
        directory: Directory to check

    Returns:
        Git root path or None if not in a git repo
    """
    if not directory or not os.path.isdir(directory):
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (
        subprocess.TimeoutExpired,
        subprocess.SubprocessError,
        FileNotFoundError,
        OSError,
    ):
        pass
    return None


def get_git_branch(directory: str) -> Optional[str]:
    """
    Get current git branch name.

    Args:
        directory: Directory to check

    Returns:
        Branch name, short SHA (if detached), or None
    """
    if not directory or not os.path.isdir(directory):
        return None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            if branch == "HEAD":
                # Detached HEAD, get short SHA
                result = subprocess.run(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=directory,
                    capture_output=True,
                    text=True,
                    timeout=SUBPROCESS_TIMEOUT,
                )
                if result.returncode == 0:
                    return result.stdout.strip()
            return branch
    except (
        subprocess.TimeoutExpired,
        subprocess.SubprocessError,
        FileNotFoundError,
        OSError,
    ):
        pass
    return None


def get_repo_name(directory: str, git_root: str) -> str:
    """
    Get repository name from remote URL or directory name.

    Args:
        directory: Current directory
        git_root: Git root directory

    Returns:
        Repository name
    """
    git_root_path = Path(git_root)

    try:
        # Check if it's a worktree (has .git file instead of directory)
        git_path = git_root_path / ".git"
        if git_path.exists() and git_path.is_file():
            return git_root_path.name

        # Try to get name from remote URL
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=directory,
            capture_output=True,
            text=True,
            timeout=SUBPROCESS_TIMEOUT,
        )
        if result.returncode == 0:
            url = result.stdout.strip()
            return url.rstrip("/").rstrip(".git").split("/")[-1]
    except (
        subprocess.TimeoutExpired,
        subprocess.SubprocessError,
        FileNotFoundError,
        OSError,
    ):
        pass

    return git_root_path.name


def get_worktree_info(
    directory: str, git_root: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Get worktree/repo name and relative path within it.

    Args:
        directory: Current directory
        git_root: Git root directory

    Returns:
        Tuple of (repo_name, relative_path) or (None, None)
    """
    if not git_root:
        return None, None

    git_root_path = Path(git_root)
    current_path = Path(directory)

    repo_name = get_repo_name(directory, git_root)

    try:
        rel_path = current_path.relative_to(git_root_path)
        if str(rel_path) == ".":
            return repo_name, None
        else:
            rel_str = str(rel_path)
            if len(rel_str) > 20:
                rel_str = "..." + rel_str[-17:]
            return repo_name, rel_str
    except ValueError:
        return repo_name, None


# =============================================================================
# Peacock Color Resolution
# =============================================================================


def get_peacock_color(directory: Optional[str] = None) -> str:
    """
    Get peacock color from VSCode settings, generating one if needed.

    Args:
        directory: Directory to check (defaults to cwd)

    Returns:
        Hex color string
    """
    if directory is None:
        directory = os.getcwd()

    # Resolve to git root if in a repo
    target_directory = directory
    git_root = get_git_toplevel(directory)
    if git_root:
        target_directory = git_root

    # Try to read from VSCode settings
    vscode_settings = Path(target_directory) / ".vscode" / "settings.json"
    settings = safe_read_json(vscode_settings)

    if settings:
        existing_color = settings.get("peacock.color")
        validated = validate_hex_color(existing_color) if existing_color else None
        if validated:
            return validated

    # Generate color from directory name
    color_key = Path(target_directory).name or "root"

    # Check cache
    cache = load_color_cache()
    if color_key in cache:
        cached = validate_hex_color(cache[color_key])
        if cached:
            return cached

    # Generate new color
    generated_color = generate_color_for_name(color_key)
    cache[color_key] = generated_color
    save_color_cache(cache)

    return generated_color


# =============================================================================
# Path Utilities
# =============================================================================


def normalize_path(directory: str) -> str:
    """Normalize path by replacing home directory with ~."""
    home = str(Path.home())
    if directory.startswith(home):
        return directory.replace(home, "~", 1)
    return directory
