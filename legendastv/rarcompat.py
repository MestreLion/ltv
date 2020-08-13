# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    ZIP and RAR handling
"""

import logging
import zipfile

from . import util as u


log = logging.getLogger(__name__)


def import_rarfile(file:str=""):
    """Import and return a properly configured rarfile module"""
    unrar   = None
    rarfile = None

    def fmsg(msg, nofile=""):
        if not file: return nofile
        return msg % (file,)

    # unrar
    try:
        import unrar.rarfile
        log.debug("Handling RAR archives with module unrar")
        return unrar.rarfile
    except LookupError:
        # unrar module is installed, but could not find UnRAR library
        unrar = True
    except ImportError:
        pass

    # rarfile
    try:
        import rarfile
        try:
            # Early test for extraction tool availability
            # Would trigger only on RarFile() or extractall() depending on RAR type
            rarfile.tool_setup()
            log.debug("Handling RAR archives with module rarfile")
            return rarfile
        except rarfile.RarCannotExec:
            # rarfile module is installed, but could not find UnRAR executable
            pass
    except ImportError:
        pass

    # No success. Handle the several failure cases

    if unrar:
        raise u.LegendasTVError(
            "Could not find an UnRAR library to extract %s."
            " Please install `libunrar.so`, `unrar.dll`, or equivalent.",
            fmsg("%r", "archives"))

    if rarfile:
        raise u.LegendasTVError(
            "Could not find a RAR extraction utility%s."
            " Please install either `unrar`, `unar` or `bsdtar`"
            " to extract RAR archives.",
             fmsg(" for %r"))

    raise u.LegendasTVError(
        "Missing UnRAR support to extract archive%s,"
        " please install python module `unrar` or `rarfile`.",
        fmsg(" %r", "s"))


class ArchiveFile:
    """Wrapper class to handle both RAR and ZIP files transparently"""
    rarfile = None

    def __new__(cls, file):
        if zipfile.is_zipfile(file):
            return zipfile.ZipFile(file, mode='r')

        if not cls.rarfile:
            cls.rarfile = import_rarfile()

        if cls.rarfile.is_rarfile(file):
            return cls.rarfile.RarFile(file, mode='r')

        raise u.LegendasTVError("Unsupported archive format, must be RAR or ZIP: %s", file)
