# Markdown Table Formatter

A lightweight, dependency-free Python utility for automatically
formatting Markdown tables with consistent column widths and alignment.

Designed to make Markdown documentation cleaner, more readable, and
easier to maintain.

## Features

- **Automatic formatting:** Detects and formats Markdown tables
    throughout a document.
- **Column alignment:** Preserves left, center, and right alignment.
- **Escaped pipes:** Handles escaped pipe characters (`\|`) inside
    table cells.
- **Code block protection:** Skips fenced code blocks using backticks
    or tildes.
- **Unicode support:** Accounts for combining characters and East
    Asian character widths.
- **Newline preservation:** Supports LF, CRLF, and CR line endings.
- **Backup creation:** Creates numbered backups without overwriting
    existing backups.
- **Check mode:** Detects formatting issues without modifying files.
- **Zero dependencies:** Uses only Python's standard library.

## Requirements

- Python 3.8 or later.
- No third-party packages required.

## Installation

Clone the repository:

``` bash
git clone https://github.com/<username>/<repository>.git
cd <repository>
```

Alternatively, download `format_markdown_tables.py` and run it directly.

## Usage

Format a Markdown file:

``` bash
python format_markdown_tables.py README.md
```

Format a file in another directory:

``` bash
python format_markdown_tables.py docs/README.md
```

### Command-line options

  Option           Description
  ---------------- ---------------------------------------------
  `file`           Path to the Markdown file (required)
  `--check`        Check formatting without modifying the file
  `--no-backup`    Format without creating a backup
  `-h`, `--help`   Display command-line help

### Check formatting

Use `--check` to determine whether a Markdown document needs formatting:

``` bash
python format_markdown_tables.py README.md --check
```

The command exits with:

- `0` when the document is already formatted.
- `1` when formatting is required or an error occurs.

This option is useful in automated workflows and CI pipelines.

### Skip backup creation

By default, the formatter creates a backup before modifying a document.

To disable backup creation:

``` bash
python format_markdown_tables.py README.md --no-backup
```

## Examples

### Before formatting

``` markdown
| Name | Description | Status |
|:---|:---:|---:|
| Python | Programming language | Active |
| Markdown | Lightweight markup language | Active |
| GitHub | Code hosting platform | Active |
```

### After formatting

``` markdown
| Name     | Description                  | Status |
|:---------|:----------------------------:|-------:|
| Python   | Programming language         | Active |
| Markdown | Lightweight markup language  | Active |
| GitHub   | Code hosting platform        | Active |
```

The formatter calculates column widths automatically and preserves the
original alignment settings.

## Alignment Support

The formatter recognizes three Markdown table alignment styles:

| Alignment | Syntax | Description |
| :---------- | :------: | :------------ |
| Left | `:---` | Aligns content to the left |
| Center | `:---:` | Centers content |
| Right | `---:` | Aligns content to the right |

## Backup Behavior

Before modifying a file, the formatter creates a backup of the original
content.

For example:

``` text
README.md
README.md.bak
```

Existing backups are never overwritten. Additional backups receive
numbered extensions:

``` text
README.md.bak
README.md.bak.1
README.md.bak.2
```

No backup is created when the document is already formatted or when
using `--check` or `--no-backup`.

## Markdownlint Compatibility

This project references the official markdownlint documentation:

[MD060 -- Table column
style](https://github.com/DavidAnson/markdownlint/blob/main/doc/md060.md)

MD060 describes three table formatting styles:

- `aligned`: Vertically aligned column separators.
- `compact`: Consistent single-space cell padding.
- `tight`: No additional cell padding.

This formatter focuses on aligned tables while preserving column
alignment markers. It is not a complete implementation of every MD060
style or a replacement for markdownlint.

## Limitations

- Does not process tables inside fenced code blocks.
- Does not support multiline table cells.
- Unicode display-width calculation is approximate, particularly for
    complex emoji sequences.
- Does not process indented code blocks as a separate protected
    region.
- Does not validate complete Markdown syntax.
- Does not implement every markdownlint MD060 formatting style.

## Contributing

Contributions, bug reports, and suggestions are welcome.

If you find an issue or have an idea for improvement, feel free to open
an issue or submit a pull request.

## License

See the [LICENSE](LICENSE) file if one is included in this repository.
