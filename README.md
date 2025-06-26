# BigItems - Find Your Biggest Data Sins

BigItems is a small Bash utility that lists the largest files and directories in a given location. It is useful for quickly discovering what is consuming disk space.

## Prerequisites

- Bash
- GNU core utilities (`du`, `find`, `sort`, `head`, `numfmt`)
- Tested on Linux and macOS

## Installation

Clone this repository and make the script executable:

```bash
git clone <repo-url>
cd bigdata-sins
chmod +x bigitems.sh
```

## Usage

```bash
./bigitems.sh [--files | --dirs | --both] [--top N] [target_directory]
```

### Options

- `--files`  – show the largest files only
- `--dirs`   – show the largest directories only
- `--both`   – show both files and directories (default)
- `--top N`  – number of results to display (default: 10)
- `target_directory` – directory to analyse (defaults to current directory)
- `--help`   – display help

## Examples

**1. Find the 5 largest files in a directory**

```bash
./bigitems.sh --files --top 5 /path/to/dir
```

**2. Show the largest directories under `/var/log`**

```bash
./bigitems.sh --dirs --top 10 /var/log
```

**3. Display both files and directories in the current directory**

```bash
./bigitems.sh
```

## Tips

Use this script periodically to locate and clean up large items before backups or when sharing disk space with others.
