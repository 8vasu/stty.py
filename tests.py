# tests.py - Test suite for stty.py.
# Copyright (C) 2025 Soumendra Ganguly

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import stty
import os
import string
import tempfile

printable_ascii_chars = [chr(char) for char in range(32, 127)]

posix_circumflex_charlist = [*string.ascii_lowercase,
                             *string.ascii_uppercase,
                             "[", "\\", "]", "^", "_", "?"]

def print_result(name, passed):
    print(f"{name}: {'PASS' if passed else 'FAIL'}")

# 1. Test cc_str_to_bytes and cc_bytes_to_str.

def test_cc_conversion():
    for c in printable_ascii_chars:
        try:
            assert stty.cc_bytes_to_str(stty.cc_str_to_bytes(c)) == c
            print(f'test_cc_conversion: PASSED for "{c}"')
        except AssertionError:
            print(f'test_cc_conversion: FAILED for "{c}"')

    for c in posix_circumflex_charlist:
        try:
            C = c
            if c.islower():
                C = c.upper()
            assert stty.cc_bytes_to_str(stty.cc_str_to_bytes(f"^{c}")) == f"^{C}"
            print(f'test_cc_conversion: PASSED for "^{c}"')
        except AssertionError:
            print(f'test_cc_conversion: FAILED for "^{c}"')

    for s in ["^-", "undef"]:
        try:
            assert stty.cc_bytes_to_str(stty.cc_str_to_bytes(s)) == "undef"
            print(f'test_cc_conversion: PASSED for "{s}"')
        except AssertionError:
            print(f'test_cc_conversion: FAILED for "{s}"')

# 2. Test Stty creation from fd and attribute access.
def test_create_and_access():
    try:
        tty = stty.Stty(fd=0)
        # Access a few attributes
        _ = tty.echo
        _ = tty.icanon
        _ = tty.ispeed
        _ = tty.ospeed
        _ = tty.get()
        print_result("test_create_and_access", True)
    except Exception as e:
        print_result("test_create_and_access", False)
        print(e)

# 3. Test setting boolean attributes.
def test_set_boolean_1():
    try:
        tty = stty.Stty(fd=0)
        orig = tty.echo
        tty.echo = not orig
        assert tty.echo == (not orig)
        tty.echo = orig
        assert tty.echo == orig
        print_result("test_set_boolean_1", True)
    except Exception as e:
        print_result("test_set_boolean_1", False)
        print(e)

# 4. Test setting symbolic attributes (csize, tabdly, etc).
def test_set_symbolic():
    try:
        tty = stty.Stty(fd=0)
        orig = tty.csize
        tty.csize = stty.cs8
        assert tty.csize == "cs8"
        tty.csize = "cs7"
        assert tty.csize == "cs7"
        tty.csize = orig
        print_result("test_set_symbolic", True)
    except Exception as e:
        print_result("test_set_symbolic", False)
        print(e)

# 5. Test setting speed attributes.
def test_set_speed():
    try:
        tty = stty.Stty(fd=0)
        orig = tty.ispeed
        tty.ispeed = 9600
        assert tty.ispeed == 9600
        tty.ispeed = orig
        print_result("test_set_speed", True)
    except Exception as e:
        print_result("test_set_speed", False)
        print(e)

# 6. Test setting control character attributes.
def test_set_control_char():
    try:
        tty = stty.Stty(fd=0)
        orig = tty.intr
        tty.intr = "^C"
        assert tty.intr == "^C"
        tty.intr = orig
        print_result("test_set_control_char", True)
    except Exception as e:
        print_result("test_set_control_char", False)
        print(e)

# 7. Test setting non-canonical attributes.
def test_set_noncanon():
    try:
        tty = stty.Stty(fd=0)
        orig = tty.min
        tty.min = 1
        assert tty.min == 1
        tty.min = orig
        print_result("test_set_noncanon", True)
    except Exception as e:
        print_result("test_set_noncanon", False)
        print(e)

# 8. Test setting winsize attributes.
def test_set_winsize():
    try:
        tty = stty.Stty(fd=0)
        if hasattr(tty, "rows"):
            orig = tty.rows
            tty.rows = 40
            assert tty.rows == 40
            tty.rows = orig
        print_result("test_set_winsize", True)
    except Exception as e:
        print_result("test_set_winsize", False)
        print(e)

# 9. Test set() method for multiple attributes.
def test_set_multiple():
    try:
        tty = stty.Stty(fd=0)
        orig_echo = tty.echo
        orig_icanon = tty.icanon
        tty.set(echo=False, icanon=False)
        assert tty.echo == False and tty.icanon == False
        tty.set(echo=orig_echo, icanon=orig_icanon)
        print_result("test_set_multiple", True)
    except Exception as e:
        print_result("test_set_multiple", False)
        print(e)

# 10. Test save() and load().
def test_save_load():
    try:
        tty = stty.Stty(fd=0)
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            path = tf.name
        tty.save(path)
        tty2 = stty.Stty(path=path)
        d1 = tty.get()
        d2 = tty2.get()
        os.unlink(path)
        # Compare all keys
        for k in d1:
            assert d1[k] == d2[k]
        print_result("test_save_load", True)
    except Exception as e:
        print_result("test_save_load", False)
        print(e)

# 11. Test fromfd() and tofd().
def test_fromfd_tofd():
    try:
        tty = stty.Stty(fd=0)
        # Save current settings
        orig = tty.get()
        # Change something
        tty.echo = not tty.echo
        tty.tofd(0)
        # Restore
        for k, v in orig.items():
            setattr(tty, k, v)
        tty.tofd(0)
        print_result("test_fromfd_tofd", True)
    except Exception as e:
        print_result("test_fromfd_tofd", False)
        print(e)

# 12. Test openpty().
def test_openpty():
    try:
        tty = stty.Stty(fd=0)
        m, s, sname = tty.openpty()
        assert isinstance(m, int) and isinstance(s, int) and isinstance(sname, str)
        os.close(m)
        os.close(s)
        print_result("test_openpty", True)
    except Exception as e:
        print_result("test_openpty", False)
        print(e)

# 13. Test forkpty().
def test_forkpty():
    try:
        tty = stty.Stty(fd=0)
        pid, m, sname = tty.forkpty()
        if pid == 0:
            os._exit(0)  # Child exits immediately
        else:
            assert isinstance(pid, int) and isinstance(m, int) and isinstance(sname, str)
            os.waitpid(pid, 0)  # Wait for child to exit
            os.close(m)
        print_result("test_forkpty", True)
    except Exception as e:
        print_result("test_forkpty", False)
        print(e)

# 14. Test raw(), evenp(), oddp(), nl(), ek().
def test_modes():
    try:
        tty = stty.Stty(fd=0)
        tty.raw()
        tty.evenp()
        tty.oddp()
        tty.nl()
        tty.ek()
        print_result("test_modes", True)
    except Exception as e:
        print_result("test_modes", False)
        print(e)

# 15. Test settings_help_str and settings_help.
def test_settings_help():
    try:
        s = stty.settings_help_str()
        assert isinstance(s, str)
        print_result("test_settings_help", True)
    except Exception as e:
        print_result("test_settings_help", False)
        print(e)

# 16. Test error handling for invalid attribute.
def test_invalid_attribute():
    try:
        tty = stty.Stty(fd=0)
        try:
            tty.foobar = 1
            print_result("test_invalid_attribute", False)
        except AttributeError:
            print_result("test_invalid_attribute", True)
    except Exception as e:
        print_result("test_invalid_attribute", False)
        print(e)

# 17. Test setting a boolean attribute.
def test_set_boolean_2():
    try:
        tty = stty.Stty(fd=0)

        tty.echo = True
        assert tty.echo is True

        tty.echo = "this string evaluates to true"
        assert tty.echo is True

        tty.echo = False
        assert tty.echo is False

        tty.echo = None
        assert tty.echo is False

        print_result("test_set_boolean_2", True)
    except Exception as e:
        print_result("test_set_boolean_2", False)
        print(e)

# 18. Test error handling for set() with invalid attribute.
def test_set_invalid():
    try:
        tty = stty.Stty(fd=0)
        try:
            tty.set(foobar=1)
            print_result("test_set_invalid", False)
        except AttributeError:
            print_result("test_set_invalid", True)
    except Exception as e:
        print_result("test_set_invalid", False)
        print(e)

# 19. Test __repr__ and __str__.
def test_repr_str():
    try:
        tty = stty.Stty(fd=0)
        r = repr(tty)
        s = str(tty)
        assert isinstance(r, str)
        assert isinstance(s, str)
        print_result("test_repr_str", True)
    except Exception as e:
        print_result("test_repr_str", False)
        print(e)

# 20. Test settings dict.
def test_settings_dict():
    try:
        d = stty.settings
        assert isinstance(d, dict)
        print_result("test_settings_dict", True)
    except Exception as e:
        print_result("test_settings_dict", False)
        print(e)

# Run all tests.
test_cc_conversion()
test_create_and_access()
test_set_boolean_1()
test_set_symbolic()
test_set_speed()
test_set_control_char()
test_set_noncanon()
test_set_winsize()
test_set_multiple()
test_save_load()
test_fromfd_tofd()
test_openpty()
test_forkpty()
test_modes()
test_settings_help()
test_invalid_attribute()
test_set_boolean_2()
test_set_invalid()
test_repr_str()
test_settings_dict()
