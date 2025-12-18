# tmux-peacock

A tmux plugin that syncs pane border colors with the [VS Code Peacock extension](https://marketplace.visualstudio.com/items?itemName=johnpapa.vscode-peacock).

When you switch between panes in different project directories, tmux-peacock automatically updates the pane border colors to match your VS Code workspace colors, making it easy to identify which project you're working in.

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

## Shell Integration (Optional but Recommended)

For automatic color updates when changing directories, add the zsh plugin to your shell configuration:

### Setup

1. **If using TPM**, add to your `~/.zshrc`:
```bash
# Add to your ~/.zshrc
source ~/.tmux/plugins/tmux-peacock/scripts/tmux-peacock.zsh
```

2. **If manually installed**, adjust the path accordingly:
```bash
# Add to your ~/.zshrc (adjust path as needed)
source ~/path/to/tmux-peacock/scripts/tmux-peacock.zsh
```

3. **Reload your shell configuration**:
```bash
source ~/.zshrc
```

### Features

With shell integration enabled:
- **Automatic color updates** when you `cd` into different projects
- **Instant color changes** when switching between git worktrees
- **Works with all directory navigation** tools (cd, pushd, popd, z, autojump, etc.)
- **Manual refresh command** available:
  ```bash
  tmux-peacock-refresh
  ```

### How It Works

The shell integration uses zsh's `chpwd` hook to detect directory changes and automatically triggers the peacock color sync. This ensures your tmux pane colors always reflect your current project context without any manual intervention.

## Color Generation

For projects without VS Code Peacock configured, tmux-peacock generates distinctive colors using:
- MD5 hash of the directory name for consistency
- Golden ratio distribution in HSL color space for visual distinction
- Muted variants for pane borders

## License

MIT
