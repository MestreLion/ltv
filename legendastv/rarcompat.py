# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

"""
    ZIP and RAR handling
"""

import logging
import zipfile

from . import util as u


# Declared before imports are done so alternatives can be logged
log = logging.getLogger(__name__)


rarfile = None
try:
    import rarfile  # uses "windows-1252" as default fallback charset
    log.debug("Handling RAR archives with rarfile")
    _rarmodule = 'rarfile'
except ImportError:
    pass  # avoid nested try/except blocks
if not rarfile:
    try:
        from unrar import rarfile
        log.debug("Handling RAR archives with unrar")
        _rarmodule = 'unrar'
    except LookupError:
        log.warning("UnRAR library not found, will not be able to extract RAR archives.")
        _rarmodule = 'unrar'
    except ImportError:
        log.warning("No RAR module found, will not be able to extract RAR archives.")
        _rarmodule = ""


class ArchiveFile:
    """Wrapper class to handle both RAR and ZIP files transparently"""
    def __new__(cls, file):
        if zipfile.is_zipfile(file):
            return zipfile.ZipFile(file, mode='r')
        if not rarfile:
            if _rarmodule == 'unrar':
                raise u.LegendasTVError(
                    "Could not find an UnRAR library to extract %r."
                    " Please install `libunrar.so`, `libunrar5` or equivalent.", file)
            raise u.LegendasTVError(
                "Missing RAR support to extract archive %r,"
                " please install python module `rarfile` or `unrar`.", file)
        if rarfile.is_rarfile(file):
            if _rarmodule == 'rarfile':
                # Early test for extraction tool availability
                # Would trigger on either RarFile() or extractall() depending on RAR type
                try:
                    rarfile.tool_setup()  # @UndefinedVariable
                except rarfile.RarCannotExec:  # @UndefinedVariable
                    raise u.LegendasTVError(
                        "Could not find a RAR extraction utility for %r."
                        " Please install either `unrar`, `unar` or `bsdtar`"
                        " to extract RAR archives.", file)
            return rarfile.RarFile(file, mode='r')
        raise u.LegendasTVError("Unsupported archive format, must be RAR or ZIP: %s", file)
