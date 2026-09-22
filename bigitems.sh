#!/bin/bash

# List the largest files and directories using GNU filesystem tools.
set -o pipefail
export LC_ALL=C

NUM_RESULTS=10
TARGET_DIR=.
MODE=both
APPARENT_SIZE=false
POSITIONAL=()

usage() {
    cat <<EOF
Usage: $0 [--files | --dirs | --both] [--top N] [--apparent-size] [target_directory]

Options:
  -f, --files          Show the largest regular files only.
  -d, --dirs           Show the largest directories only.
  -b, --both           Show both lists (default).
  -t, --top N          Show up to N entries per list (default: 10).
      --apparent-size  Rank by logical bytes instead of allocated disk space.
  -h, --help           Display this help message.
      --               End options; the next argument is a directory name.

Directory sizes include descendants, and the target directory is included.
Requires Bash 3.2+ and GNU coreutils/findutils. On macOS:
  brew install coreutils findutils

Example:
  $0 --files --top 5 /path/to/directory
EOF
}

die() {
    printf 'Error: %s\n' "$1" >&2
    exit "${2:-1}"
}

# Parse directly so --help and argument errors work without GNU getopt.
while (( $# )); do
    case "$1" in
        -f|--files) MODE=files; shift ;;
        -d|--dirs) MODE=dirs; shift ;;
        -b|--both) MODE=both; shift ;;
        -t|--top)
            (( $# >= 2 )) || die '--top requires a positive integer.' 2
            NUM_RESULTS=$2
            shift 2
            ;;
        --top=*) NUM_RESULTS=${1#*=}; shift ;;
        -t?*) NUM_RESULTS=${1#-t}; shift ;;
        --apparent-size) APPARENT_SIZE=true; shift ;;
        -h|--help) usage; exit 0 ;;
        --) shift; POSITIONAL+=("$@"); break ;;
        -[fdbh]?*) set -- "${1:0:2}" "-${1:2}" "${@:2}" ;;
        -?*) die "Unknown option: $1. Use --help for usage." 2 ;;
        *) POSITIONAL+=("$1"); shift ;;
    esac
done

(( ${#POSITIONAL[@]} <= 1 )) || die 'Only one target directory may be specified.' 2
if (( ${#POSITIONAL[@]} == 1 )); then
    TARGET_DIR=${POSITIONAL[0]}
fi
[[ $NUM_RESULTS =~ ^[1-9][0-9]*$ ]] || die '--top value must be a positive integer.' 2
[[ -d $TARGET_DIR ]] || die "Directory '$TARGET_DIR' does not exist or is inaccessible."

# GNU find treats some bare relative names as expressions, even after --.
SCAN_DIR=$TARGET_DIR
case "$SCAN_DIR" in
    /*|./*|../*|.) ;;
    *) SCAN_DIR="./$SCAN_DIR" ;;
esac

gnu_tool() {
    local candidate version
    for candidate in "$1" "g$1"; do
        if version=$("$candidate" --version 2>/dev/null) && [[ $version == *GNU* ]]; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    printf 'Error: GNU %s is required (tried %s and g%s).\n' "$1" "$1" "$1" >&2
    printf 'Install coreutils and findutils; on macOS: brew install coreutils findutils\n' >&2
    return 1
}

SORT=$(gnu_tool sort) || exit 1
HEAD=$(gnu_tool head) || exit 1
NUMFMT=$(gnu_tool numfmt) || exit 1
if [[ $MODE != files ]]; then
    DU=$(gnu_tool du) || exit 1
fi
if [[ $MODE != dirs ]]; then
    FIND=$(gnu_tool find) || exit 1
fi
# Let head validate its numeric range before starting an expensive scan.
"$HEAD" --lines="$NUM_RESULTS" </dev/null >/dev/null || die '--top value is too large.' 2

DU_OPTIONS=()
FILE_FORMAT='%b\t%p\0'
FILE_UNIT=512
SIZE_LABEL='allocated disk space'
if $APPARENT_SIZE; then
    DU_OPTIONS+=(--apparent-size)
    FILE_FORMAT='%s\t%p\0'
    FILE_UNIT=1
    SIZE_LABEL='apparent size'
fi

# Finish and check the scan before printing a ranking. Reading head from a file
# also avoids sort receiving SIGPIPE when only a small top-N list is requested.
RESULTS=$(mktemp "${TMPDIR:-/tmp}/bigitems.XXXXXXXX") || die 'Cannot create a temporary results file.'
trap 'rm -f -- "$RESULTS"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

scan_dirs() {
    "$DU" -H --null --block-size=1 "${DU_OPTIONS[@]}" -- "$SCAN_DIR"
}

scan_files() {
    "$FIND" -H "$SCAN_DIR" -type f -printf "$FILE_FORMAT"
}

show_largest() {
    local title=$1 scan=$2 unit=$3 record size path formatted
    if ! "$scan" | "$SORT" --zero-terminated --field-separator=$'\t' --key=1,1nr --key=2 >"$RESULTS"; then
        die "$title scan or sorting failed; no ranking was produced for this list."
    fi

    printf 'Largest %s in %q (%s):\n' "$title" "$TARGET_DIR" "$SIZE_LABEL"
    if ! "$HEAD" --zero-terminated --lines="$NUM_RESULTS" -- "$RESULTS" \
        | while IFS= read -r -d '' record; do
            size=${record%%$'\t'*}
            path=${record#*$'\t'}
            formatted=$("$NUMFMT" --from-unit="$unit" --to=iec-i --suffix=B "$size") || exit 1
            printf '%-10s\t' "$formatted" || exit 1
            # Keep unusual names on one line and prevent terminal control codes.
            if [[ $path == *[$'\001'-$'\037'$'\177']* ]]; then
                printf '%q\n' "$path" || exit 1
            else
                printf '%s\n' "$path" || exit 1
            fi
        done; then
        die "$title display failed; output may be incomplete."
    fi
    printf '\n'
}

if [[ $MODE != files ]]; then
    show_largest Directories scan_dirs 1 || exit 1
fi
if [[ $MODE != dirs ]]; then
    show_largest Files scan_files "$FILE_UNIT" || exit 1
fi
