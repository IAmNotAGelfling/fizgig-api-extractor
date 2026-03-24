"""
Test helper utilities.
"""


def normalize_rich_output(output: str) -> str:
    """
    Normalize Rich console output for cross-platform testing.

    Rich may wrap long lines differently on different platforms (especially macOS).
    This function removes line breaks within logical lines to make assertions
    consistent across platforms.

    Args:
        output: The CLI output string to normalize

    Returns:
        Normalized output with line wraps removed

    Example:
        # Original output (macOS with wrapping):
        "Saved to \\n/var/folders/very/long/path.json"

        # Normalized output:
        "Saved to /var/folders/very/long/path.json"
    """
    # Replace newlines that appear to be mid-sentence wrapping
    # Keep paragraph breaks (double newlines)
    lines = output.split("\n")
    normalized_lines = []

    for i, line in enumerate(lines):
        # If line doesn't start with whitespace and previous line didn't end with punctuation,
        # it's likely a wrapped line - join with previous
        if (
            normalized_lines
            and line
            and not line[0].isspace()
            and normalized_lines[-1]
            and not normalized_lines[-1]
            .rstrip()
            .endswith((".", "!", "?", ":", "✓", "✗", "❌", "⚠️"))
        ):
            # Join with previous line
            normalized_lines[-1] = normalized_lines[-1].rstrip() + " " + line.lstrip()
        else:
            normalized_lines.append(line)

    return "\n".join(normalized_lines)


def assert_in_output(substring: str, output: str, normalize: bool = True):
    """
    Assert that a substring appears in CLI output, with optional normalization.

    Args:
        substring: The string to search for
        output: The CLI output to search in
        normalize: Whether to normalize Rich console wrapping (default True)

    Raises:
        AssertionError: If substring not found in output

    Example:
        result = runner.invoke(app, ["extract", url, "--save-url", path])
        assert_in_output(f"Saved to {path}", result.output)
    """
    if normalize:
        output = normalize_rich_output(output)

    assert substring in output, f"Expected '{substring}' in output:\n{output}"


def assert_all_in_output(substrings: list[str], output: str, normalize: bool = True):
    """
    Assert that all substrings appear in CLI output.

    More flexible than exact string matching - checks each component separately.
    Useful for paths and multi-part messages that may wrap.

    Args:
        substrings: List of strings that should all appear in output
        output: The CLI output to search in
        normalize: Whether to normalize Rich console wrapping (default True)

    Example:
        result = runner.invoke(app, ["extract", url, "--save-url", path])
        assert_all_in_output(["Saved to", path], result.output)
    """
    if normalize:
        output = normalize_rich_output(output)

    for substring in substrings:
        assert substring in output, f"Expected '{substring}' in output:\n{output}"
