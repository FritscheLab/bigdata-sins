#!/bin/bash

# bigitems.sh
# Description: A user-friendly script to find and display the largest files and directories in a specified target directory (or the current directory if none is provided).
# Useful for identifying "data sins"—unusually large files or directories taking up space.

# Default values
NUM_RESULTS=10
TARGET_DIR="."

# Help message
usage() {
    cat <<EOF
Usage: $0 [--files | --dirs | --both] [--top N] [target_directory]

Options:
  --files       Show the largest files only.
  --dirs        Show the largest directories only.
  --both        Show both the largest files and directories (default).
  --top N       Show the top N results (default is 10).
  --help        Display this help message.

Example:
  $0 --files --top 5 /path/to/directory
EOF
    exit 0
}

# Parse command-line arguments
MODE="both"

# Use GNU getopt for long option support
PARSED=$(getopt -o fdbt:h --long files,dirs,both,top:,help -- "$@") || {
    usage
}
eval set -- "$PARSED"

while true; do
    case "$1" in
        -f|--files) MODE="files"; shift ;;
        -d|--dirs)  MODE="dirs"; shift ;;
        -b|--both)  MODE="both"; shift ;;
        -t|--top)   NUM_RESULTS="$2"; shift 2 ;;
        -h|--help)  usage ;;
        --) shift; break ;;
        *) echo "Unknown option: $1" >&2; usage ;;
    esac
done

if [[ $# -gt 1 ]]; then
    echo "Error: Only one target directory may be specified." >&2
    exit 1
elif [[ $# -eq 1 ]]; then
    TARGET_DIR="$1"
fi

# Validate NUM_RESULTS
if ! [[ $NUM_RESULTS =~ ^[1-9][0-9]*$ ]]; then
    echo "Error: --top value must be a positive integer." >&2
    exit 1
fi

# Check if target directory exists
if [[ ! -d "$TARGET_DIR" ]]; then
    echo "Error: Directory '$TARGET_DIR' does not exist."
    exit 1
fi

# Function to display largest directories
show_dirs() {
    echo "Largest Directories in '$TARGET_DIR':"
    du -0 -b "$TARGET_DIR" 2>/dev/null \
        | sort -z -rn \
        | head -z -n "$NUM_RESULTS" \
        | while IFS=$'\t' read -r -d '' size path; do
            printf "%-10s\t%s\n" "$(numfmt --to=iec-i "$size")" "$path"
        done
    echo
}

# Function to display largest files
show_files() {
    echo "Largest Files in '$TARGET_DIR':"
    find "$TARGET_DIR" -type f -printf '%s\t%p\0' 2>/dev/null \
        | sort -z -rn \
        | head -z -n "$NUM_RESULTS" \
        | while IFS=$'\t' read -r -d '' size path; do
            printf "%-10s\t%s\n" "$(numfmt --to=iec-i "$size")" "$path"
        done
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
