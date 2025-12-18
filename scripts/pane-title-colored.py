#!/usr/bin/env python3
"""
tmux-pane-title-colored: Generate colored title for a specific pane based on its directory
"""

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Convert RGB tuple to hex color"""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def hsl_to_hex(h, s, l):
    """Convert HSL to hex color"""
    h = h / 360.0
    s = s / 100.0
    l = l / 100.0

    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p

    if s == 0:
        r = g = b = l
    else:
        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)

    return rgb_to_hex((int(r * 255), int(g * 255), int(b * 255)))


def generate_color_for_name(name):
    """Generate a distinctive color for a given name using golden ratio"""
    hash_val = hashlib.md5(name.encode()).hexdigest()
    seed = int(hash_val[:8], 16)

    golden_ratio_conjugate = 0.618033988749895
    hue = (seed * golden_ratio_conjugate) % 1.0
    hue = hue * 360

    saturation = 70
    lightness = 50

    return hsl_to_hex(hue, saturation, lightness)


def load_color_cache():
    """Load cached color assignments"""
    cache_file = Path.home() / '.config' / 'tmux-peacock-colors.json'
    try:
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError):
        pass
    return {}


def save_color_cache(cache):
    """Save color assignments to cache"""
    cache_file = Path.home() / '.config' / 'tmux-peacock-colors.json'
    try:
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
    except IOError:
        pass


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


def get_peacock_color(directory):
    """Get peacock color from VSCode settings, generating one if needed"""
    target_directory = directory
    git_root = get_git_toplevel(directory)
    if git_root:
        target_directory = git_root

    vscode_settings = Path(target_directory) / ".vscode" / "settings.json"
    existing_color = None

    if vscode_settings.exists():
        try:
            with open(vscode_settings, 'r') as f:
                settings = json.load(f)
            existing_color = settings.get('peacock.color')
        except (json.JSONDecodeError, IOError):
            pass

    if existing_color:
        return existing_color

    color_key = Path(target_directory).name

    cache = load_color_cache()
    if color_key in cache:
        return cache[color_key]

    generated_color = generate_color_for_name(color_key)
    cache[color_key] = generated_color
    save_color_cache(cache)

    return generated_color


def main():
    """Generate colored title for the given directory"""
    directory = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

    git_root = get_git_toplevel(directory)
    color = get_peacock_color(directory)

    if git_root:
        worktree_name, subdir = get_worktree_info(directory, git_root)
        branch = get_git_branch(directory)

        title = worktree_name
        if branch:
            title += f"@{branch}"
        if subdir:
            title += f":{subdir}"
    else:
        normalized_path = normalize_path(directory)
        if normalized_path == "~":
            title = "~"
        else:
            title = Path(normalized_path).name or normalized_path

    # Output with tmux color formatting
    print(f"#[fg={color}]{title}#[default]")


if __name__ == "__main__":
    main()
