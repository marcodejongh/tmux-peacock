#!/usr/bin/env bash
#
# tmux-peacock - Sync tmux pane colors with VS Code Peacock extension
#
# This plugin automatically syncs tmux pane border colors with the
# VS Code Peacock extension color for the current directory's project.
#

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Get plugin directory
get_tmux_option() {
    local option=$1
    local default_value=$2
    local option_value=$(tmux show-option -gqv "$option")
    if [ -z "$option_value" ]; then
        echo "$default_value"
    else
        echo "$option_value"
    fi
}

# Setup hooks for peacock color sync
setup_peacock_hooks() {
    # Hook to update colors when switching panes
    tmux set-hook -g after-select-pane "run-shell \"$CURRENT_DIR/scripts/peacock-sync.py '#{pane_current_path}' 2>/dev/null\""

    # Hook to sync colors when creating new panes
    tmux set-hook -g after-split-window "run-shell \"$CURRENT_DIR/scripts/peacock-sync.py '#{pane_current_path}' 2>/dev/null\""
    tmux set-hook -g after-new-window "run-shell \"$CURRENT_DIR/scripts/peacock-sync.py '#{pane_current_path}' 2>/dev/null\""
}

# Setup pane border format with title
setup_pane_borders() {
    tmux set-option -g pane-border-status top
    tmux set-option -g pane-border-format " #($CURRENT_DIR/scripts/pane-title.py '#{pane_current_path}') "
}

main() {
    setup_peacock_hooks
    setup_pane_borders
}

main
