#!/usr/bin/python3

import stty
import string
import termios

printable_ascii_chars = [chr(char) for char in range(32, 127)]

posix_circumflex_charlist = [*string.ascii_lowercase,
                             *string.ascii_uppercase,
                             "[", "\\", "]", "^", "_", "?"]

for c in printable_ascii_chars:
    try:
        assert stty.cc_bytes_to_str(stty.cc_str_to_bytes(c)) == c
    except AssertionError:
        print(f'failed for "{c}"')

for c in posix_circumflex_charlist:
    try:
        C = c
        if c.islower():
            C = c.upper()
        assert stty.cc_bytes_to_str(stty.cc_str_to_bytes(f"^{c}")) == f"^{C}"
    except AssertionError:
        print(f'failed for "^{c}"')

for s in ["^-", "undef"]:
    assert stty.cc_bytes_to_str(stty.cc_str_to_bytes(s)) == "undef"
