from types import SimpleNamespace

import pytest

from audiobookdl import args


def test_missing_input_file_exits_cleanly():
    """A missing --input-file must exit with a message, not a traceback."""
    options = SimpleNamespace(urls=[], input_file="does-not-exist-12345.txt")
    with pytest.raises(SystemExit) as exc_info:
        args.get_urls(options)
    assert exc_info.value.code != 0
    assert "does-not-exist-12345.txt" in str(exc_info.value.code)


def test_input_file_urls_are_combined(tmp_path):
    """Urls from args and a valid input file are combined."""
    input_file = tmp_path / "urls.txt"
    input_file.write_text("https://example.com/a\nhttps://example.com/b\n")
    options = SimpleNamespace(
        urls=["https://example.com/zero"], input_file=str(input_file)
    )
    assert args.get_urls(options) == [
        "https://example.com/zero",
        "https://example.com/a",
        "https://example.com/b",
    ]
