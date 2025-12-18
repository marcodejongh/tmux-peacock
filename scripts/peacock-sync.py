#!/usr/bin/env python3
"""
tmux-peacock-sync: Sync tmux pane colors with VSCode Peacock extension colors
"""

import json
import os
import subprocess
import sys
from pathlib import Path
import hashlib


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    """Convert RGB tuple to hex color"""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def mute_color(hex_color, factor=0.3):
    """Mute a color by blending it with black"""
    r, g, b = hex_to_rgb(hex_color)
    r = int(r * factor)
    g = int(g * factor)
    b = int(b * factor)
    return rgb_to_hex((r, g, b))


def create_background_tint(hex_color, factor=0.05):
    """Create a very subtle background tint from a color"""
    r, g, b = hex_to_rgb(hex_color)
    bg_r, bg_g, bg_b = 30, 30, 30  # Dark background RGB

    r = int(bg_r + (r - bg_r) * factor)
    g = int(bg_g + (g - bg_g) * factor)
    b = int(bg_b + (b - bg_b) * factor)

    return rgb_to_hex((r, g, b))


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


def get_peacock_color(directory=None):
    """Get peacock color from VSCode settings, generating one if needed"""
    if directory is None:
        directory = os.getcwd()

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


def set_tmux_pane_colors(color):
    """Set tmux pane border colors and background tints"""
    if color:
        muted_color = mute_color(color, 0.6)
        bright_color = mute_color(color, 0.8)
        bg_tint = create_background_tint(color, 0.08)

        subprocess.run(['tmux', 'set-option', 'pane-border-style', f'fg={muted_color}'],
                      capture_output=True)
        subprocess.run(['tmux', 'set-option', 'pane-active-border-style', f'fg={bright_color}'],
                      capture_output=True)
        subprocess.run(['tmux', 'set-option', 'window-style', f'bg={bg_tint}'],
                      capture_output=True)
        subprocess.run(['tmux', 'set-option', 'window-active-style', 'bg=default'],
                      capture_output=True)
    else:
        subprocess.run(['tmux', 'set-option', 'pane-border-style', 'fg=colour240'],
                      capture_output=True)
        subprocess.run(['tmux', 'set-option', 'pane-active-border-style', 'fg=colour250'],
                      capture_output=True)
        subprocess.run(['tmux', 'set-option', 'window-style', 'bg=default'],
                      capture_output=True)
        subprocess.run(['tmux', 'set-option', 'window-active-style', 'bg=default'],
                      capture_output=True)


def main():
    """Main function"""
    if not os.environ.get('TMUX'):
        sys.exit(0)

    lock_file = Path("/tmp/tmux-peacock-sync.lock")
    try:
        if lock_file.exists():
            if (Path.stat(lock_file).st_mtime + 5) < os.path.getmtime("/tmp"):
                lock_file.unlink()
            else:
                sys.exit(0)

        lock_file.touch()

        directory = sys.argv[1] if len(sys.argv) > 1 else None
        peacock_color = get_peacock_color(directory)
        set_tmux_pane_colors(peacock_color)

    finally:
        if lock_file.exists():
            lock_file.unlink()


if __name__ == "__main__":
    main()
