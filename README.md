# BigItems - Find Your Biggest Data Sins

`bigitems.sh` is a script designed to help users easily identify the largest files and directories in their system. Perfect for students, teachers, and administrators looking to understand what’s taking up the most disk space!

## Features

- **Largest Files or Directories**: Shows the largest files, directories, or both in a user-friendly format.
- **Customizable Number of Results**: Allows users to specify how many results to display (default is the top 10).
- **Human-Readable Sizes**: Outputs in kilobytes, megabytes, gigabytes, etc., for easy understanding.
- **Clear Layout**: Results are displayed in a neat table format for quick interpretation.

## Usage

Place the `bigitems.sh` script in a location accessible by the terminal. Make sure it’s executable:

```bash
chmod +x bigitems.sh
```

### Command Syntax

```bash
./bigitems.sh [--files | --dirs | --both] [--top N] [--help]
```

### Options

- **`--files`**: Show the largest files only.
- **`--dirs`**: Show the largest directories only.
- **`--both`**: Show both the largest files and directories (this is the default).
- **`--top N`**: Specify the number of top results to display (default is 10).
- **`--help`**: Display this help message.

### Examples

#### 1. Find the 5 Largest Files

```bash
./bigitems.sh --files --top 5
```

Output:
```
Largest Files:
1.2G       ./path/to/largefile1
934M       ./another/path/largefile2
...
```

#### 2. Find the Top 10 Largest Directories

```bash
./bigitems.sh --dirs
```

Output:
```
Largest Directories:
2.5G       ./some/huge/directory
1.1G       ./another/big/directory
...
```

#### 3. Show Both Largest Files and Directories (Default)

```bash
./bigitems.sh --top 8
```

Output:
```
Largest Directories:
2.5G       ./some/huge/directory
1.1G       ./another/big/directory
...

Largest Files:
1.2G       ./path/to/largefile1
934M       ./another/path/largefile2
...
```

## Tips

- Use this script to periodically review large items on your system, especially before backing up files or sharing storage spaces with others.
- Help students learn about effective storage management by encouraging them to identify and clean up large files that are no longer needed.
