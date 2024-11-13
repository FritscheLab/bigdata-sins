# BigItems - Find Your Biggest Data Sins

`bigitems.sh` is a script designed to help users easily identify the largest files and directories in a specified directory or in the current working directory by default. Perfect for students, teachers, and administrators looking to understand what’s taking up the most disk space!

## Features

- **Target Directory**: Specify a directory to search, or let it default to the current directory.
- **Largest Files or Directories**: Choose to display the largest files, directories, or both in a user-friendly format.
- **Customizable Number of Results**: Specify how many results to display (default is the top 10).
- **Human-Readable Sizes**: Outputs in kilobytes, megabytes, gigabytes, etc., for easy understanding.
- **Clear Layout**: Results are displayed in a neat table format for quick interpretation.

## Usage

Place the `bigitems.sh` script in a location accessible from the terminal. Make sure it’s executable:

```bash
chmod +x bigitems.sh
```

### Command Syntax

```bash
./bigitems.sh [--files | --dirs | --both] [--top N] [target_directory]
```

### Options

- **`--files`**: Show the largest files only.
- **`--dirs`**: Show the largest directories only.
- **`--both`**: Show both the largest files and directories (this is the default).
- **`--top N`**: Specify the number of top results to display (default is 10).
- **`target_directory`**: The directory to analyze (default is the current directory if not specified).
- **`--help`**: Display this help message.

### Examples

#### 1. Find the 5 Largest Files in a Specific Directory

```bash
./bigitems.sh --files --top 5 /path/to/directory
```

Output:
```
Largest Files in '/path/to/directory':
1.2G       ./path/to/largefile1
934M       ./another/path/largefile2
...
```

#### 2. Find the Top 10 Largest Directories in `/var/log`

```bash
./bigitems.sh --dirs --top 10 /var/log
```

Output:
```
Largest Directories in '/var/log':
2.5G       ./log/some/huge/directory
1.1G       ./log/another/big/directory
...
```

#### 3. Show Both Largest Files and Directories in the Current Directory (Default)

```bash
./bigitems.sh
```

Output:
```
Largest Directories in '.':
2.5G       ./some/huge/directory
1.1G       ./another/big/directory
...

Largest Files in '.':
1.2G       ./path/to/largefile1
934M       ./another/path/largefile2
...
```

## Tips

- Use this script to periodically review large items on your system, especially before backing up files or sharing storage spaces with others.
- Help students learn about effective storage management by encouraging them to identify and clean up large files that are no longer needed.
