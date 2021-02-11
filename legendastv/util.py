# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    Globals and assorted utilities
"""

import difflib
import logging
import typing as t

import guessit


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

def filtered(d, *keys, whitelist=True, exclude_nones=True):
    """Filter a dict, returning a copy with only (or all but) the selected keys"""
    if not keys:
        return d

    # For performance reasons, dict comprehension is repeated in each branch

    # Whitelist, only selected keys
    if whitelist:
        if exclude_nones:
            return {k: v for k, v in d.items() if k     in keys and v is not None}
        return     {k: v for k, v in d.items() if k     in keys}

    # Blacklist, all but the selected keys
    if exclude_nones:
        return     {k: v for k, v in d.items() if k not in keys and v is not None}
    return         {k: v for k, v in d.items() if k not in keys}


def clsrepr(obj:object, sig:str) -> str:
    return f"<{obj.__class__.__name__}({sig})>"


def fullrepr(obj:object, attrs:t.Iterable[str]) -> str:
    return clsrepr(obj, ', '.join(f"{__}={getattr(obj, __)!r}" for __ in attrs))


def guess_info(text:str) -> dict:
    """Guess all Video/Title-related info about a text and return as a Dictionary.

    For files, providing the full path yields more accurate results.
    """
    return guessit.guessit(text)


def similarity(text1, text2, ignorecase=True):
    """Return a float in [0,1] range representing the similarity of 2 strings"""
    if ignorecase:
        text1 = text1.lower()
        text2 = text2.lower()
    return difflib.SequenceMatcher(None, text1, text2).ratio()


def match_filter(objs, **attrs):
    def match(obj):
        for a, v in attrs.items():
            if v is None:
                continue
            if not hasattr(obj, a) or not getattr(obj, a) == v:
                return False
        return True
    return filter(match, objs)
