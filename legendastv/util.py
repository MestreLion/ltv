# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Globals and assorted utilities
"""

import logging
import typing as t


log = logging.getLogger(__name__)


class LegendasTVError(Exception):
    """Base class for custom exceptions, with errno and %-formatting for args.

    All modules in this package raise this (or a subclass) for all
    explicitely raised, business-logic, expected or handled exceptions
    """
    def __init__(self, msg: t.Any = "", *args, errno: int = 0):
        super().__init__(str(msg) % args)
        self.errno = errno


def toint(text, default=0):
    """Return <text> coerced to int, or <default> if not a numeric string"""
    if not text:
        return default
    try:
        return int(text)
    except ValueError:
        log.warning("Could not convert to integer, expected numeric string: %s", text)
        return text


def strip(text:str):
    """Return stripped <text> if it is not None"""
    if text is not None:
        return text.strip()


def clsrepr(obj:object, sig:str) -> str:
    return f"<{obj.__class__.__name__}({sig})>"


def fullrepr(obj:object, attrs:t.Iterable[str]) -> str:
    return clsrepr(obj, ', '.join(f"{__}={getattr(obj, __)!r}" for __ in attrs))
