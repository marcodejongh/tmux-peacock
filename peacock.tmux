#!/usr/bin/env bash
#
# tmux-peacock - Sync tmux pane colors with VS Code Peacock extension
#
# This plugin automatically syncs tmux pane border colors with the
# VS Code Peacock extension color for the current directory's project.
#

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

get_tmux_option() {
    local option=$1
    local default_value=$2
    local option_value
    option_value=$(tmux show-option -gqv "$option")
    if [ -z "$option_value" ]; then
        echo "$default_value"
    else
        echo "$option_value"
    fi
}

setup_peacock_hooks() {
    # Use -ga (append) to not clobber other plugins' hooks
    # Use -b (background) to not block tmux during script execution
    # Use #{q:...} to safely quote paths with spaces/special chars
    tmux set-hook -ga after-select-pane "run-shell -b \"$CURRENT_DIR/scripts/peacock-sync.py '#{q:pane_current_path}' 2>/dev/null\""
    tmux set-hook -ga after-split-window "run-shell -b \"$CURRENT_DIR/scripts/peacock-sync.py '#{q:pane_current_path}' 2>/dev/null\""
    tmux set-hook -ga after-new-window "run-shell -b \"$CURRENT_DIR/scripts/peacock-sync.py '#{q:pane_current_path}' 2>/dev/null\""
}

setup_pane_borders() {
    tmux set-option -g pane-border-status top
    # Use #{q:...} to safely quote paths with spaces/special chars
    tmux set-option -g pane-border-format " #($CURRENT_DIR/scripts/pane-title-colored.py '#{q:pane_current_path}') "
}

initialize_colors() {
    # Run via tmux run-shell so #{pane_current_path} gets expanded properly
    # Use -b for background execution
    tmux run-shell -b "$CURRENT_DIR/scripts/peacock-sync.py '#{q:pane_current_path}' 2>/dev/null || true"
}

main() {
    setup_peacock_hooks
    setup_pane_borders
    initialize_colors
}

main
