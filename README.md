# tmux-peacock

<img width="2560" height="1440" alt="Screenshot 2025-12-19 at 10 53 59" src="https://github.com/user-attachments/assets/9dba82d4-3c9a-4de1-8c7b-156761244f5a" />

A tmux plugin that syncs pane border colors with the [VS Code Peacock extension](https://marketplace.visualstudio.com/items?itemName=johnpapa.vscode-peacock).

When you switch between panes in different project directories, tmux-peacock automatically updates the pane border colors to match your VS Code Peacock workspace colors, making it easy to identify which project you OR AI is working in.
If no peacock colour is set yet in the worktree, it automatically generates a colour for it.

## Features

- Syncs tmux pane border colors with VS Code Peacock `peacock.color` setting
- Automatically generates consistent colors for projects without Peacock configured
- Displays repository name and path in pane borders
- Subtle background tinting for active panes

## Requirements

- tmux 2.9+
- Python 3.6+
- git (for repository detection)

## Installation

### With [TPM](https://github.com/tmux-plugins/tpm) (recommended)

Add to your `~/.tmux.conf`:

```tmux
set -g @plugin 'mdejongh/tmux-peacock'
```

Then press `prefix + I` to install.

### Manual Installation

```bash
git clone https://github.com/mdejongh/tmux-peacock.git ~/.tmux/plugins/tmux-peacock
```

Add to your `~/.tmux.conf`:

```tmux
run-shell ~/.tmux/plugins/tmux-peacock/peacock.tmux
```

Reload tmux:

```bash
tmux source-file ~/.tmux.conf
```

## How It Works

1. When you switch panes or create new windows, tmux-peacock checks the current directory
2. If inside a git repository, it looks for `.vscode/settings.json` with a `peacock.color` property
3. If no Peacock color is set, it generates a consistent color based on the directory name using a hash function
4. Colors are cached in `~/.config/tmux-peacock-colors.json`

## Color Generation

For projects without VS Code Peacock configured, tmux-peacock generates distinctive colors using:
- MD5 hash of the directory name for consistency
- Golden ratio distribution in HSL color space for visual distinction
- Muted variants for pane borders

## License

MIT
