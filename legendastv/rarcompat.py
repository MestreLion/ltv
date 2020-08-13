# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    ZIP and RAR handling
"""

import ctypes.util
import logging
import os
import sys
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

    ### unrar
    # set to library inside package, if applicable
    if   os.name == "nt":          lib = 'unrar.dll',      'unrar.dll'  # Windows
    elif sys.platform == "darwin": lib = 'libunrar.dylib', 'unrar'      # macOS
    else:                          lib = 'libunrar.so',    'unrar'      # Linux (assumed)
    lib_path = os.path.join(os.path.dirname(__file__), lib[0])
    if (    not os.environ.get('UNRAR_LIB_PATH', None)  # Not already manually set
        and not ctypes.util.find_library(lib[1])        # Not installed in system
        and os.path.exists(lib_path)                    # Found in package
    ):
        os.environ['UNRAR_LIB_PATH'] = lib_path
    # import the module
    try:
        import unrar.rarfile
        log.debug("Handling RAR archives with module unrar")
        return unrar.rarfile
    except LookupError:
        # unrar module is installed, but could not find UnRAR library
        unrar = True
    except ImportError:
        pass

    ### rarfile
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
            " Please install `%s` or equivalent to extract RAR archives.",
            fmsg("%r", "archives"), lib[0])

    if rarfile:
        raise u.LegendasTVError(
            "Could not find an UnRAR extraction utility%s."
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
    errmsg = "Unsupported archive format, must be RAR or ZIP: %s"

    def __new__(cls, filepath:str):
        if zipfile.is_zipfile(filepath):
            return zipfile.ZipFile(filepath, mode='r')

        if not cls.rarfile:
            # Test if file is likely a RAR before trying to import an unrar module.
            # Cannot use rarfile.is_rarfile (yet), and do not use filetools.extension()
            # to avoid a circular import
            if not filepath.lower().endswith('.rar'):
                raise u.LegendasTVError(cls.errmsg, filepath)
            cls.rarfile = import_rarfile(filepath)

        if cls.rarfile.is_rarfile(filepath):
            return cls.rarfile.RarFile(filepath, mode='r')

        raise u.LegendasTVError(cls.errmsg, filepath)
