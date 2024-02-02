# stty.py - A Python library that works like stty(1).
# Copyright (C) 2024 Soumendra Ganguly

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

import sys
import termios
import copy
import json

__all__ = [
    "Stty", "NOW", "DRAIN", "FLUSH", "SPEEDS",
    "IFBOOL_A", "OFBOOL_A", "CFBOOL_A", "LFBOOL_A",
    "CS_A", "DLY_A", "SPEED_A", "WINSZ_A", "CC_A",
    "control"
]


def control(c):
    """Return the control character corresponding to c."""
    return bytes([ord(c) & 0x1F])


# Indices for termios attribute list.
_IFLAG = 0
_OFLAG = 1
_CFLAG = 2
_LFLAG = 3
_ISPEED = 4
_OSPEED = 5
_CC = 6

# Indices for termios winsize tuple.
_ROWS = 0
_COLS = 1

# Do we have termios.tcgetwinsize() and termios.tcsetwinsize()?
_HAVE_WINSZ = (hasattr(termios, "TIOCGWINSZ")
               and hasattr(termios, "TIOCSWINSZ")
               and hasattr(termios, "tcgetwinsize")
               and hasattr(termios, "tcsetwinsize"))

# All possible iflag boolean mask names.
_ifbool = [
    "IGNBRK", "BRKINT", "IGNPAR", "PARMRK", "INPCK", "ISTRIP",
    "INLCR", "IGNCR", "ICRNL", "IUCLC", "IXON", "IXANY",
    "IXOFF", "IMAXBEL"
]

# All possible oflag boolean mask names.
_ofbool = [
    "OPOST", "OLCUC", "ONLCR", "OCRNL",
    "ONOCR", "ONLRET", "OFILL", "OFDEL"
]

# All possible cflag boolean mask names.
_cfbool = [
    "CSTOPB", "CREAD", "PARENB", "PARODD",
    "HUPCL", "CLOCAL", "CIBAUD", "CRTSCTS"
]

# All possible lflag boolean mask names.
_lfbool = [
    "ISIG", "ICANON", "XCASE", "ECHO", "ECHOE", "ECHOK",
    "ECHONL", "ECHOCTL", "ECHOPRT", "ECHOKE", "FLUSHO",
    "NOFLSH", "TOSTOP", "PENDIN", "IEXTEN"
]

# Character size mask name (part of cflag)
# and names of all possible values.
_cs = {"CSIZE": ["CS5", "CS6", "CS7", "CS8"]}

# All possible delay mask names (parts of oflag)
# and names of all of their possible values.
_dly = {
    "CRDLY": ["CR0", "CR1", "CR2", "CR3"],
    "NLDLY": ["NL0", "NL1"],
    "TABDLY": ["TAB0", "TAB1", "TAB2", "TAB3"],
    "BSDLY": ["BS0", "BS1"],
    "FFDLY": ["FF0", "FF1"],
    "VTDLY": ["VT0", "VT1"]
}

# Names of all possible indices
# of the control character list.
_cc = [
    "VEOF", "VEOL", "VEOL2", "VERASE", "VERASE2", "VWERASE",
    "VKILL", "VREPRINT", "VINTR", "VQUIT", "VSUSP", "VDSUSP",
    "VSTART", "VSTOP", "VLNEXT", "VSTATUS", "VDISCARD", "VSWTCH"
]

# All possible Baud rate "indices".
_r = [
    0, 50, 75, 110, 134, 150, 200, 300, 600,
    1200, 1800, 2400, 4800, 9600, 19200, 38400,
    57600, 115200, 230400, 460800, 500000, 576000,
    921600, 1000000, 1152000, 1500000, 2000000,
    2500000, 3000000, 3500000, 4000000
]

# Keys of _bool_d are lowercase names of masks that take boolean values
# (for example one can turn ECHO on/off).
#
# Example element of _bool_d.items() is ("echo", (_LFLAG, termios.ECHO))
_bool_d = {}
for flag, masklist in [(_IFLAG, _ifbool),
                       (_OFLAG, _ofbool),
                       (_CFLAG, _cfbool),
                       (_LFLAG, _lfbool)]:
    for mask in masklist:
        if hasattr(termios, mask):
            _bool_d[mask.lower()] = (flag, getattr(termios, mask))

# Keys of _num_d are lowercase names for masks that take
# nonnegative integer values. For example, TABDLY can
# take the integer value TAB0. This loop will make sure
# that these integer values can be accessed using
# lowercase names. For example, stty.tab0 will be
# same as termios.TAB0.
#
# Example element of _num_d.items() is
# ("nldly", 3-element-tuple), where 3-element-tuple is
# (_OFLAG, termios.NLDLY,
# {stty.nl0: "nl0", stty.nl1: "nl1"}).
#
# Note again that the 3rd element of this example tuple
# is same as {termios.NL0: "nl0", termios.NL1: "nl1"}.
_num_d = {}
for flag, maskdict in [(_CFLAG, _cs), (_OFLAG, _dly)]:
    for mask, maskvalues in maskdict.items():
        if hasattr(termios, mask):
            # Values of mask that are available on
            # system; for example, if mask is CRDLY
            # and system only has CR0, CR1, then
            # avail == {termios.CR0: "cr0", termios.CR1: "cr1"} ==
            # {stty.cr0: "cr0", stty.cr1: "cr1"}.
            avail = {}
            for v in maskvalues:
                if hasattr(termios, v):
                    num_v = getattr(termios, v)
                    avail[num_v] = v.lower()

                    # Example explaining this setattr: it will
                    # define stty.cr0 to be same as termios.CR0.
                    setattr(sys.modules[__name__], v.lower(), num_v)
                    __all__.append(v.lower())

            _num_d[mask.lower()] = (flag, getattr(termios, mask),
                                    avail)

# Example element of _baud_d.items() is (50, termios.B50)
# Example element of _baud_d_inverse.items() is (termios.B50, 50)
_baud_d = {}
for n in _r:
    rate = f"B{n}"
    if hasattr(termios, rate):
        _baud_d[n] = getattr(termios, rate)

_baud_d_inverse = {v: k for k, v in _baud_d.items()}

# Example element of _cc_d.items() is ("eof", termios.VEOF)
_cc_d = {}
for s in _cc:
    if hasattr(termios, s):
        _cc_d[s[1:].lower()] = getattr(termios, s)

_noncanon_d = {"min": termios.VMIN, "time": termios.VTIME}

_speed_d = {"ispeed": _ISPEED, "ospeed": _OSPEED}

_winsz_d = {"rows": _ROWS, "cols": _COLS} if _HAVE_WINSZ else {}

# List of lowercase names of all Stty object
# attributes available on system (strings).
_available = [
    *_bool_d, *_num_d, *_speed_d,
    *_cc_d, *_noncanon_d, *_winsz_d
]

# The "action" constants for tcsetattr().
NOW = termios.TCSANOW
DRAIN = termios.TCSADRAIN
FLUSH = termios.TCSAFLUSH

IFBOOL_A = [mask.lower() for mask in _ifbool if hasattr(termios, mask)]
OFBOOL_A = [mask.lower() for mask in _ofbool if hasattr(termios, mask)]
CFBOOL_A = [mask.lower() for mask in _cfbool if hasattr(termios, mask)]
LFBOOL_A = [mask.lower() for mask in _lfbool if hasattr(termios, mask)]

CS_A = {mask.lower(): [(v.lower(), getattr(termios, v)) for v in _cs[mask] if hasattr(termios, v)]
        for mask in _cs if hasattr(termios, mask)},
DLY_A = {mask.lower(): [(v.lower(), getattr(termios, v)) for v in _dly[mask] if hasattr(termios, v)]
         for mask in _dly if hasattr(termios, mask)}

CC_A = [*_cc_d]
NONCANON_A = [*_noncanon_d]
SPEED_A = [*_speed_d]
WINSZ_A = [*_winsz_d]

SPEEDS = [*_baud_d]


class Stty(object):
    """Manipulate termios and winsize in the style of stty(1)."""
    def __init__(self, fd=None, path=None, **opts):
        if fd == None and path == None:
            raise ValueError("fd or path must be provided")

        if fd != None and path != None:
            raise ValueError("only one of fd or path must be provided")

        if fd != None:
            self.fromfd(fd)

        if path != None:
            self.load(path)

        self.set(**opts)

    def __setattr__(self, name, value):
        if name == "_termios" or name == "_winsize":
            raise AttributeError(f"attribute '{name}' must not be "
                                 "directly modified")

        if name in _bool_d:
            x = _bool_d[name]
            if value:
                self._termios[x[0]] |= x[1]
            else:
                self._termios[x[0]] &= ~x[1]

            super().__setattr__(name, value)
            return

        if name in _num_d:
            if not isinstance(value, int):
                raise TypeError(f"value of attribute '{name}' must have "
                                "type 'int'")

            x = _num_d[name]
            if value not in x[2]:
                raise ValueError(f"unsupported value '{value}' for "
                                 f"attribute '{name}'")

            self._termios[x[0]] &= ~x[1]
            self._termios[x[0]] |= value

            super().__setattr__(name, x[2][value])
            return

        if name in _speed_d:
            if not isinstance(value, int):
                raise TypeError(f"value of attribute '{name}' must have "
                                "type 'int'")

            if value not in _baud_d:
                raise ValueError(f"unsupported value {value} for "
                                 f"attribute '{name}'")

            self._termios[_speed_d[name]] = _baud_d[value]

            super().__setattr__(name, value)
            return

        if name in _cc_d:
            if not isinstance(value, bytes):
                raise TypeError(f"value of attribute '{name}' must have "
                                "type 'bytes'")

            if len(value) != 1:
                raise ValueError(f"value of attribute '{name}' must have "
                                 "length equal to 1")

            self._termios[_CC][_cc_d[name]] = value

            super().__setattr__(name, value)
            return

        if name in _noncanon_d:
            if not isinstance(value, int):
                raise TypeError(f"value of attribute '{name}' must have "
                                "type 'int'")

            if value < 0:
                raise ValueError(f"expected Nonnegative value for "
                                 f"attribute '{name}'")

            self._termios[_CC][_noncanon_d[name]] = bytes([value])

            super().__setattr__(name, value)
            return

        if name in _winsz_d:
            if not isinstance(value, int):
                raise TypeError(f"value of attribute '{name}' must have "
                                "type 'int'")

            if value < 0:
                raise ValueError(f"expected Nonnegative value for "
                                 f"attribute '{name}'")

            self._winsize[_winsz_d[name]] = value

            super().__setattr__(name, value)
            return

        raise AttributeError(f"attribute '{name}' unsupported on platform")

    def __repr__(self):
        return ", ".join([f"{x}={getattr(self, x)}" for x in _available])

    def get(self):
        """Return dictionary of relevant attributes."""
        return {x: getattr(self, x) for x in _available}

    def set(self, **opts):
        """Set multiple attributes as named arguments."""
        excess = set(opts) - set(_available)
        if len(excess) > 0:
            raise AttributeError("attributes in the following set are "
                                 f"unsupported on this platform: {excess}")

        for x in opts:
            self.__setattr__(x, opts[x])

    def save(self, path=None):
        """Return deep copy of self or save JSON.
        This mimics "stty -g"."""
        if not path:
            return copy.deepcopy(self)

        d = self.get()
        d["_termios"] = self._termios
        d["_winsize"] = self._winsize

        with open(path, "w") as f:
            json.dump(d, f)

        return None

    def load(self, path):
        """Load termios and winsize from JSON file."""
        with open(path, "r") as f:
            d = json.load(f)

        if "_termios" not in d:
            raise ValueError("JSON file does not contain termios data")
        super().__setattr__("_termios", d["_termios"])
        d.pop("_termios")

        if _HAVE_WINSZ:
            if "_winsize" not in d:
                raise ValueError("JSON file does not contain winsize data")
            super().__setattr__("_winsize", d["_winsize"])
        else:
            super().__setattr__("_winsize", None)
        d.pop("_winsize", None)

        deficiency = set(_available) - set(d)
        if len(deficiency) > 0:
            raise ValueError("JSON file does not contain the following "
                             f"necessary attributes: {deficiency}")
        self.set(**d)

    def fromfd(self, fd):
        """Get settings from terminal."""
        super().__setattr__("_termios", termios.tcgetattr(fd))
        if _HAVE_WINSZ:
            super().__setattr__("_winsize", termios.tcgetwinsize(fd))
        else:
            super().__setattr__("_winsize", None)

        for name in _bool_d:
            x = _bool_d[name]
            value = True if (self._termios[x[0]] & x[1]) else False
            self.__setattr__(name, value)

        for name in _num_d:
            x = _num_d[name]
            y = self._termios[x[0]] & x[1]
            self.__setattr__(name, x[2][y])

        for name in _speed_d:
            x = self._termios[_speed_d[name]]
            self.__setattr__(name, _baud_d_inverse[x])

        for name in _cc_d:
            self.__setattr__(name, self._termios[_CC][_cc_d[name]])

        for name in _noncanon_d:
            self.__setattr__(name,
                             ord(self._termios[_CC][_noncanon_d[name]]))

        if self._winsize:
            for name in _winsz_d:
                self.__setattr__(name, self._winsize[_winsz_d[name]])

    def tofd(self, fd, when=NOW, apply_termios=True,
           apply_winsize=True):
        """Apply settings to terminal."""
        if apply_termios:
            termios.tcsetattr(fd, when, self._termios)
        if apply_winsize and self._winsize:
            termios.tcsetwinsize(fd, self._winsize)

    def evenp(self, plus=True):
        """Set/unset evenp combination mode."""
        if plus:
            self.set(parenb=True, csize=cs7, parodd=False)
        else:
            self.set(parenb=False, csize=cs8)

    def oddp(self, plus=True):
        """Set/unset oddp combination mode."""
        if plus:
            self.set(parenb=True, csize=cs7, parodd=True)
        else:
            self.set(parenb=False, csize=cs8)

    def raw(self):
        """Set raw combination mode."""
        for x in IFBOOL_A:
            self.__setattr__(x, False)
        for x in LFBOOL_A:
            self.__setattr__(x, False)
        self.set(opost=False, parenb=False,
                 csize=cs8, min=1, time=0)

    def nl(self, plus=True):
        """Set/unset nl combination mode."""
        if plus:
            self.icrnl = False
        else:
            self.set(icrnl=True, inlcr=False, igncr=False)

    def ek(self):
        """Set ek combination mode."""
        if hasattr(termios, "CERASE"):
            self.erase = termios.CERASE

        if hasattr(termios, "CKILL"):
            self.kill = termios.CKILL
