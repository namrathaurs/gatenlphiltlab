#!/usr/bin/env python3

import re
from collections import namedtuple


Regex = namedtuple(
    "Regex",
    [
        "name",
        "expression",
        "replacement",
    ]
)

#: The default regex replacements used by :func:`gatenlphiltlab.normalize`
regexes = (
    Regex(
        name="left_single_quote",
        expression=re.compile(".*\.\w\w+.*?"),
        replacement="",
    ),
    Regex(
        name="file_names",
        expression=re.compile(".*\.\w\w+.*?"),
        replacement="",
    ),
    Regex(
        name="file_names",
        expression=re.compile(".*\.\w\w+.*?"),
        replacement="",
    ),
    Regex(
        name="file_names",
        expression=re.compile(".*\.\w\w+.*?"),
        replacement="",
    ),
    Regex(
        name="file_names",
        expression=re.compile(".*\.\w\w+.*?"),
        replacement="",
    ),
    Regex(
        name="file_names",
        expression=re.compile(".*\.\w\w+.*?"),
        replacement="",
    ),
    Regex(
        name="file_names",
        expression=re.compile(".*\.\w\w+.*?"),
        replacement="",
    ),
    Regex(
        name="file_names",
        expression=re.compile(".*\.\w\w+.*?"),
        replacement="",
    ),
    Regex(
        name="speaker_tag",
        expression=re.compile("^.*?:", re.MULTILINE),
        replacement="",
    ),
    Regex(
        name="extralinguistic_tags",
        expression=re.compile("{.+?}"),
        replacement="",
    ),
    Regex(
        name="round_braces",
        expression=re.compile("[\(\)]"),
        replacement="",
    ),
    Regex(
        name="square_braces",
        expression=re.compile("[\[\]]"),
        replacement="",
    ),
    Regex(
        name="curly_braces",
        expression=re.compile("[{}]"),
        replacement="",
    ),
    Regex(
        name="tilde",
        expression=re.compile("~"),
        replacement="",
    ),
    Regex(
        name="backslash",
        expression=re.compile(r"\\"),
        replacement="",
    ),
    Regex(
        name="forward_slash",
        expression=re.compile("/"),
        replacement="",
    ),
    Regex(
        name="asterisk",
        expression=re.compile("\*"),
        replacement="",
    ),
    Regex(
        name="misc_characters",
        expression=re.compile("[\$\^\+@#`_=]|<>;"),
        replacement="",
    ),
    Regex(
        name="leading_spaces",
        expression=re.compile("^\s+?", re.MULTILINE),
        replacement="",
    ),
    Regex(
        name="trailing_spaces",
        expression=re.compile("\s+?$", re.MULTILINE),
        replacement="",
    ),
    Regex(
        name="extra_spaces",
        expression=re.compile("\s\s+?"),
        replacement=" ",
    ),
    Regex(
        name="crlf_newlines",
        expression=re.compile(r"\r\n"),
        replacement="\n",
    ),
    Regex(
        name="cr_newlines",
        expression=re.compile(r"\r"),
        replacement="\n",
    ),
    Regex(
        name="extra_newlines",
        expression=re.compile(r"\n\n+?"),
        replacement="\n",
    ),
)
