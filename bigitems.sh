#!/bin/bash

# bigitems.sh
# Description: A user-friendly script to find and display the largest files and directories in a specified target directory (or the current directory if none is provided).
# Useful for identifying "data sins"—unusually large files or directories taking up space.

# Default values
NUM_RESULTS=10
TARGET_DIR="."

# Help message
usage() {
    echo "Usage: $0 [--files | --dirs | --both] [--top N] [target_directory]"
    echo
    echo "Options:"
    echo "  --files       Show the largest files only."
    echo "  --dirs        Show the largest directories only."
    echo "  --both        Show both the largest files and directories (default)."
    echo "  --top N       Show the top N results (default is 10)."
    echo "  --help        Display this help message."
    echo
    echo "Example:"
    echo "  $0 --files --top 5 /path/to/directory"
    exit 1
}

# Parse command-line arguments
MODE="both"
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --files) MODE="files"; shift ;;
        --dirs) MODE="dirs"; shift ;;
        --both) MODE="both"; shift ;;
        --top) NUM_RESULTS="$2"; shift 2 ;;
        --help) usage ;;
        *) TARGET_DIR="$1"; shift ;;
    esac
done

# Check if target directory exists
if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Error: Directory '$TARGET_DIR' does not exist."
    exit 1
fi

# Function to display largest directories
show_dirs() {
    echo "Largest Directories in '$TARGET_DIR':"
    # Find directories within TARGET_DIR, calculate their sizes, sort by size, and show the top results
    find "$TARGET_DIR" -type d -exec du -h {} + | sort -hr | head -n "$NUM_RESULTS" | awk '
    {
        printf "%-10s\t%-50s\n", $1, $2
    }'
    echo
}

# Function to display largest files
show_files() {
    echo "Largest Files in '$TARGET_DIR':"
    # Find files within TARGET_DIR, calculate their sizes, sort by size, and show the top results
    find "$TARGET_DIR" -type f -exec du -h {} + | sort -hr | head -n "$NUM_RESULTS" | awk '
    {
        printf "%-10s\t%-50s\n", $1, $2
    }'
    echo
}

# Execute based on selected mode
if [ "$MODE" = "dirs" ]; then
    show_dirs
elif [ "$MODE" = "files" ]; then
    show_files
else
    show_dirs
    show_files
fi
