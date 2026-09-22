# BigItems — Find Your Biggest Data Sins

BigItems lists the largest files and directories in a location. By default it
ranks **allocated disk space**; use `--apparent-size` to rank logical file sizes.
It only reads filesystem metadata and never deletes or modifies scanned items.

## Requirements and installation

- Bash 3.2 or later, including the Bash shipped with macOS.
- GNU coreutils (`du`, `sort`, `head`, `numfmt`) and GNU findutils (`find`).
- Standard `mktemp`, `rm`, and `cat` utilities.

On macOS, install [coreutils](https://formulae.brew.sh/formula/coreutils) and
[findutils](https://formulae.brew.sh/formula/findutils) with Homebrew:

```bash
brew install coreutils findutils
```

BigItems detects GNU commands under their ordinary names or Homebrew's `g`
prefix (for example, `gdu` and `gfind`). No PATH changes or GNU `getopt` are needed
when Homebrew's executables are already on PATH. The macOS system utilities alone
do not supply the required GNU options.

On Debian/Ubuntu, install the dependencies if they are not already present:

```bash
sudo apt-get install coreutils findutils
```

Then clone and run:

```bash
git clone https://github.com/FritscheLab/bigdata-sins.git
cd bigdata-sins
./bigitems.sh --help
```

## Usage

```bash
./bigitems.sh [--files | --dirs | --both] [--top N] [--apparent-size] [target_directory]
```

| Option | Behavior |
| --- | --- |
| `-f`, `--files` | Show regular files only. |
| `-d`, `--dirs` | Show directories only. |
| `-b`, `--both` | Show both lists (default). |
| `-t N`, `--top N` | Show up to N entries **per list** (default: 10). N must be a positive integer supported by GNU `head`. |
| `--apparent-size` | Use logical bytes instead of allocated disk space. |
| `-h`, `--help` | Show help without requiring GNU tools. |
| `--` | End options, allowing a directory name beginning with `-`. |

The directory defaults to the current directory. Options may precede or follow
it; the last mode option wins. `--top=5`, `-t5`, and combined short options such
as `-ft5` are also accepted.

```bash
# Five files consuming the most allocated disk space
./bigitems.sh --files --top 5 /path/to/data

# Largest directory trees, ranked by logical size
./bigitems.sh --dirs --apparent-size /path/to/data

# Both lists in the current directory
./bigitems.sh

# A relative directory whose name starts with a dash
./bigitems.sh --files -- -archive
```

## Interpreting the results

- Sizes use binary units: 1 KiB = 1,024 bytes. Ranking uses the unrounded sizes;
  ties are ordered by path under the C locale.
- Directory entries include descendants and the target directory itself. Parent
  and child entries overlap, so adding the displayed directory sizes is not useful.
- Allocated size uses filesystem-reported blocks. Sparse files can have a large
  apparent size and consume very little space. `--apparent-size` restores the
  metric used by earlier versions of this script.
- Directory totals count a hard-linked inode once per directory scan, following
  GNU `du` behavior. The file list shows every regular-file path, including each
  hard link. Neither list guarantees how much space deleting an item will free;
  shared blocks, snapshots, and filesystem compression can affect that amount.
- A target that is itself a symbolic link to a directory is followed. Symbolic
  links encountered inside the tree are not followed. File lists exclude those
  links; directory totals include their own storage as reported by `du`.
- Names containing tabs, newlines, or ASCII control characters use Bash quoting
  so each entry remains on one line. This is a human-readable report, not a
  machine-readable interchange format.
- Scans include hidden entries and mounted filesystems below the target. Both
  mode scans directories and files separately; changes during scanning can make
  the lists differ. Large trees take time to scan and sort, even with `--top 1`.

## Errors and troubleshooting

Exit status is `0` on success, `2` for invalid arguments, and `1` for missing
dependencies or scan/display failures. Interrupts return `130` (SIGINT) or `143`
(SIGTERM). Diagnostics go to stderr and are not suppressed.

A failed scan produces no ranking for that list. In `--both` mode a directory
list may already have been printed before a file scan fails; always check the
exit status if using this in another script. An empty file list succeeds.

Sorted results are staged in a temporary file under `${TMPDIR:-/tmp}` and removed
on exit. GNU `sort` can also use temporary disk space for large trees. Ensure that
location has room. For a permission error, select a directory you can read and
rerun, for example:

```bash
./bigitems.sh --files --top 5 "$HOME"
```

To trace command execution on a small, non-sensitive test directory:

```bash
bash -x ./bigitems.sh --files --top 1 /path/to/test-directory
```

## Checks

With GNU dependencies and Python 3 installed:

```bash
bash -n bigitems.sh
python3 -m unittest discover -s tests -v
```

Tests use temporary synthetic files to check CLI behavior, ranking, sparse files,
unusual names, symbolic/hard links, and visible failures. GitHub Actions runs the
same checks on Linux and macOS.
