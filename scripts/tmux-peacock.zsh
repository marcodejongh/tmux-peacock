#!/usr/bin/env zsh
#
# tmux-peacock.zsh - Shell integration for tmux-peacock color synchronization
#
# This script automatically updates tmux pane colors when changing directories
# using zsh's chpwd hook system.
#
# Usage: source this file in your .zshrc:
#   source ~/.tmux/plugins/tmux-peacock/scripts/tmux-peacock.zsh
#
# Features:
# - Updates tmux colors when entering different git repositories
# - Minimal performance impact with directory caching
# - Works with all directory change methods (cd, pushd, popd, z, etc.)
# - Only runs when inside a tmux session
#

# Global variable to track current directory for change detection
typeset -g _tmux_peacock_last_dir=""

# Function to update tmux peacock colors on directory change
_tmux_peacock_update() {
    emulate -L zsh
    
    # Only run if we're inside tmux
    [[ -n "$TMUX" ]] || return 0
    
    # Only update if directory actually changed
    [[ "$PWD" != "$_tmux_peacock_last_dir" ]] || return 0
    
    # Update the tracked directory
    _tmux_peacock_last_dir="$PWD"
    
    # Find the peacock-sync script
    local peacock_script=""
    
    # Try common plugin locations
    local possible_paths=(
        "${TMUX_PLUGIN_MANAGER_PATH}/tmux-peacock/scripts/peacock-sync.py"
        "$HOME/.tmux/plugins/tmux-peacock/scripts/peacock-sync.py"
        "${0:A:h}/peacock-sync.py"  # Same directory as this script
    )
    
    for path in $possible_paths; do
        if [[ -f "$path" ]]; then
            peacock_script="$path"
            break
        fi
    done
    
    # If we found the script, run it
    if [[ -n "$peacock_script" ]] && [[ -f "$peacock_script" ]]; then
        "$peacock_script" "$PWD" 2>/dev/null &!
    fi
}

# Load the hook system and register our function
autoload -Uz add-zsh-hook
add-zsh-hook chpwd _tmux_peacock_update

# Initialize colors for current directory when sourcing this file
_tmux_peacock_update

# Optional: Provide a command to manually refresh colors
tmux-peacock-refresh() {
    _tmux_peacock_last_dir=""
    _tmux_peacock_update
    echo "tmux-peacock colors refreshed"
}