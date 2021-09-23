"""
Tests for documentation
"""
# stdlib
from pathlib import Path
import re
# third-party
import pytest

__authors__ = ("Dan Gunter",)


# root of documentation
docs_dir = Path(__file__).parent.parent.parent / "docs"
# generated by sphinx-apidoc command
apidoc = docs_dir / "apidoc"


def has_docs():
    # assume this file is under <root>/<package>/tests/ , docs in <root>/docs
    # check dir docs/apidoc dir
    if not apidoc.exists() or not apidoc.is_dir():
        return False
    # XXX: add test for Sphinx too?
    return True


def get_autodoc(pth):
    """Get the name, location, and options for all autodoc directives
    in the file at 'pth'.

    Yields:
        tuple of length 4: type of thing, name of it, filename, line number (from 1)
    """
    mode = "text"  # state machine with 2 states; other one is "autodoc"
    auto_what, auto_name, auto_options, auto_where = None, None, None, None
    with open(pth, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if mode == "text":
                match = re.match(r'..\s+auto(\w+)::\s*([a-zA-Z][a-zaA-Z_.0-9]*)', line)
                if match:
                    auto_what = match.group(1)
                    auto_name = match.group(2)
                    auto_where = f"{f.name}:{i + 1}"
                    auto_options = []
                    mode = "autodoc"
            elif mode == "autodoc":
                # blank or unindented line, back to text mode
                if not re.match(r'^\s\s', line):
                    yield auto_what, auto_name, auto_where, auto_options
                    auto_what = None
                    mode = "text"
                else:
                    # try to extract an option of the form '  :<name>:'
                    match = re.match(r"\s+:(\w+):", line)
                    if match:
                        auto_options.append(match.group(1))
            else:
                raise RuntimeError(f"unknown mode: {mode}")
        if auto_what:
            yield auto_what, auto_name, auto_where, auto_options


@pytest.mark.skipif(not has_docs(), reason="Docs not present")
def test_autodoc_has_noindex():
    bad = []  # is anyone truly bad or good? when it comes to autodocs: yes
    for p in docs_dir.glob("**/*.rst"):
        try:
            # If it is NOT a subdir of apidoc, raises ValueError
            p.relative_to(apidoc)
            # ignore anything under apidoc
        except ValueError:
            # not in apidoc, so look for autodoc sections
            for what, name, where, options in get_autodoc(p):
                if "noindex" not in options:
                    n = len(bad) + 1
                    bad.append(f"{n}) {what} '{name}' in {where}")
    if len(bad) > 0:
        bad_ones = "\n".join(bad)
        err = f"{len(bad)} 'autodoc' directive(s) missing 'noindex':\n{bad_ones}"
        assert False, err
