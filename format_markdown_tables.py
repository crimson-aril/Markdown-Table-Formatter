
#!/usr/bin/env python3
"""Format Markdown tables with consistent column widths and alignment.

Features:
    - Left, center, and right column alignment.
    - Escaped pipe handling.
    - Fenced code block protection.
    - Unicode-aware display width calculation.
    - LF, CRLF, and CR newline preservation.
    - UTF-8 and UTF-8 BOM support.
    - Original trailing newline preservation.
    - Automatic backup creation.
    - Check-only mode for CI workflows.

Only Python's standard library is required.
"""

import argparse
import re
import sys
import unicodedata
from pathlib import Path


FENCE_PATTERN = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
SEPARATOR_PATTERN = re.compile(r":?-{3,}:?")


def display_width(value):
    """Calculate the approximate display width of Unicode text."""
    width = 0

    for char in value:
        category = unicodedata.category(char)

        if category in {"Mn", "Me", "Cf", "Cc"}:
            continue

        if unicodedata.east_asian_width(char) in {"W", "F"}:
            width += 2
        else:
            width += 1

    return width


def is_escaped(value, position):
    """Determine whether a character is escaped by preceding backslashes."""
    backslashes = 0
    position -= 1

    while position >= 0 and value[position] == "\\":
        backslashes += 1
        position -= 1

    return backslashes % 2 == 1


def has_unescaped_pipe(line):
    """Check whether a line contains an unescaped pipe character."""
    return any(
        char == "|" and not is_escaped(line, index)
        for index, char in enumerate(line)
    )


def split_row(line):
    """Split a Markdown table row while preserving escaped pipes."""
    line = line.strip()

    if line.startswith("|") and not is_escaped(line, 0):
        line = line[1:]

    if line.endswith("|") and not is_escaped(line, len(line) - 1):
        line = line[:-1]

    cells = []
    current = []

    for index, char in enumerate(line):
        if char == "|" and not is_escaped(line, index):
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)

    cells.append("".join(current).strip())

    return cells


def is_separator(line):
    """Check whether a row contains valid Markdown alignment markers."""
    cells = split_row(line)

    return bool(cells) and all(
        SEPARATOR_PATTERN.fullmatch(cell)
        for cell in cells
    )


def get_alignment(separator):
    """Return the alignment of a Markdown table column."""
    if separator.startswith(":") and separator.endswith(":"):
        return "center"

    if separator.endswith(":"):
        return "right"

    return "left"


def format_cell(value, width, alignment):
    """Pad a table cell according to its alignment and display width."""
    padding = max(0, width - display_width(value))

    if alignment == "center":
        left = padding // 2
        right = padding - left
    elif alignment == "right":
        left = padding
        right = 0
    else:
        left = 0
        right = padding

    return f" {' ' * left}{value}{' ' * right} "


def format_separator(width, alignment):
    """Generate an alignment-aware Markdown separator cell."""
    if alignment == "center":
        return ":" + "-" * width + ":"

    if alignment == "right":
        return "-" * (width + 1) + ":"

    return ":" + "-" * (width + 1)


def format_table(lines):
    """Format a Markdown table while preserving column alignment."""
    rows = [split_row(line) for line in lines]

    if len(rows) < 2 or not is_separator(lines[1]):
        return lines

    column_count = len(rows[0])

    if any(len(row) != column_count for row in rows):
        return lines

    alignments = [
        get_alignment(cell)
        for cell in rows[1]
    ]

    widths = [
        max(
            3,
            max(
                display_width(row[index])
                for row_index, row in enumerate(rows)
                if row_index != 1
            ),
        )
        for index in range(column_count)
    ]

    output = []

    for row_index, row in enumerate(rows):
        if row_index == 1:
            cells = [
                format_separator(width, alignment)
                for width, alignment in zip(widths, alignments)
            ]
        else:
            cells = [
                format_cell(value, width, alignment)
                for value, width, alignment in zip(
                    row, widths, alignments
                )
            ]

        output.append("|" + "|".join(cells) + "|")

    return output


def is_fence_opening(line):
    """Identify a valid Markdown fenced code block opening."""
    match = FENCE_PATTERN.match(line)

    if not match:
        return None

    fence = match.group(1)
    info = match.group(2)

    if fence.startswith("`") and "`" in info:
        return None

    return fence[0], len(fence)


def is_fence_closing(line, fence_char, fence_length):
    """Check whether a line closes an existing fenced code block."""
    pattern = (
        rf"^ {{0,3}}{re.escape(fence_char)}"
        rf"{{{fence_length},}}[ \t]*$"
    )

    return bool(re.fullmatch(pattern, line))


def format_document(text):
    """Format Markdown tables without modifying fenced code blocks."""
    lines = text.split("\n")
    output = []

    fence_char = None
    fence_length = 0
    index = 0

    while index < len(lines):
        line = lines[index]

        if fence_char is not None:
            output.append(line)

            if is_fence_closing(line, fence_char, fence_length):
                fence_char = None
                fence_length = 0

            index += 1
            continue

        opening = is_fence_opening(line)

        if opening:
            fence_char, fence_length = opening
            output.append(line)
            index += 1
            continue

        if (
            has_unescaped_pipe(line)
            and index + 1 < len(lines)
            and is_separator(lines[index + 1])
        ):
            table = [line, lines[index + 1]]
            index += 2

            while index < len(lines):
                current = lines[index]

                if not current.strip():
                    break

                if is_fence_opening(current):
                    break

                if not has_unescaped_pipe(current):
                    break

                table.append(current)
                index += 1

            output.extend(format_table(table))
        else:
            output.append(line)
            index += 1

    return "\n".join(output)


def get_backup_path(path):
    """Find an unused backup filename without overwriting existing backups."""
    backup = path.with_suffix(path.suffix + ".bak")

    if not backup.exists():
        return backup

    index = 1

    while True:
        candidate = path.with_suffix(
            path.suffix + f".bak.{index}"
        )

        if not candidate.exists():
            return candidate

        index += 1


def format_file(path, check_only=False, create_backup=True):
    """Format a UTF-8 Markdown file and optionally create a backup."""
    original_bytes = path.read_bytes()

    has_bom = original_bytes.startswith(b"\xef\xbb\xbf")
    content_bytes = original_bytes[3:] if has_bom else original_bytes

    original = content_bytes.decode("utf-8")

    newline_match = re.search(r"\r\n|\r|\n", original)
    newline = newline_match.group(0) if newline_match else "\n"

    has_trailing_newline = original.endswith(("\r", "\n"))

    normalized = original.replace("\r\n", "\n").replace("\r", "\n")
    formatted = format_document(normalized)

    if not has_trailing_newline:
        formatted = formatted.rstrip("\n")
    elif formatted and not formatted.endswith("\n"):
        formatted += "\n"

    formatted = formatted.replace("\n", newline)

    formatted_bytes = formatted.encode("utf-8")

    if has_bom:
        formatted_bytes = b"\xef\xbb\xbf" + formatted_bytes

    if original_bytes == formatted_bytes:
        print(f"Already formatted: {path}")
        return True

    if check_only:
        print(f"Formatting required: {path}")
        return False

    if create_backup:
        backup = get_backup_path(path)
        backup.write_bytes(original_bytes)
        print(f"Backup: {backup}")

    path.write_bytes(formatted_bytes)

    print(f"Formatted: {path}")
    return True


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Format Markdown tables automatically."
    )

    parser.add_argument(
        "file",
        type=Path,
        help="Path to the Markdown file.",
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Check formatting without modifying the file.",
    )

    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Modify the file without creating a backup.",
    )

    return parser.parse_args()


def main():
    """Run the Markdown table formatter."""
    args = parse_arguments()

    if not args.file.is_file():
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    try:
        success = format_file(
            args.file,
            check_only=args.check,
            create_backup=not args.no_backup,
        )

        return 0 if success else 1

    except (OSError, UnicodeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
