# This file is part of LegendasTV, see <https://github.com/MestreLion/legendastv>
# Copyright (C) 2020 Rodrigo Silva (MestreLion) <linux@rodrigosilva.com>
# License: GPLv3 or later, at your choice. See <http://www.gnu.org/licenses/gpl>

import logging
import os
import struct

import guessit

from . import util as u


log = logging.getLogger(__name__)


# Mimetype guessing
try:
    from gi.repository import Gio
    log.debug("Using mimetypes from Gio")

    def mimetype(filepath:str) -> str:
        """Return the guessed mimetype of a file based on extension or initial content.

        For paths with an extension, determine mimetype based solely on its
        extension. For extensionless files, try to perform a 1MB read and return
        'inode/directory' for directories and 'application/octet-stream' for unknown
        types and unreadable files (not found, broken symlinks or access denied).
        """
        mime = Gio.content_type_guess(filename=filepath, data=None)[0]
        if extension(filepath):
            return mime

        try:
            with open(filepath, 'rb') as f:
                return Gio.content_type_guess(filename=None, data=f.read(1024**2))[0]
        except IsADirectoryError:
            return 'inode/directory'  # same output as when filepath ends with '/'
        except (FileNotFoundError, PermissionError):
            return 'application/octet-stream'  # same as unknown types

except ImportError:
    import mimetypes
    log.debug("Using mimetypes from Standard Library")

    def mimetype(filepath:str) -> str:
        """Return the guessed mimetype of a file based on its extension.

        Return 'application/octet-stream' for unknown types and extensionless paths.
        """
        return (mimetypes.guess_type(filepath, strict=False)[0]
                or 'application/octet-stream')


# Most common video file extensions, not meant as a complete list.
# For performance reasons only, to avoid a perhaps expensive mimetype detection
# https://trac.opensubtitles.org/projects/opensubtitles/wiki/DevReadFirst#Videofilesextensions

# Either Gio, Stdlib or both consider a video (mimetype == 'video/...')
VIDEO_EXTENSIONS = [
    '3g2', '3gp', '3gp2', '3gpp', 'asf', 'asx', 'avi', 'divx', 'dv', 'flc',
    'fli', 'flv', 'gvp', 'm1v', 'm2ts', 'm4v', 'mkv', 'moov', 'mov', 'movie',
    'mp4', 'mpe', 'mpeg', 'mpg', 'mpv', 'mxf', 'nsv', 'ogm', 'ogv', 'qt', 'ram',
    'rm', 'rmvb', 'swf', 'ts', 'viv', 'vivo', 'vob', 'wm', 'wmv', 'wmx', 'wvx',
]
# Other extensions included in opensubtitles.org list, sans 'ps'
VIDEO_EXTENSIONS_EXTRA = [
    '60d', 'ajp', 'avchd', 'bik', 'bix', 'box', 'cam', 'dat', 'dmf', 'dvr-ms',
    'evo', 'flic', 'flx', 'gvi', 'h264', 'm2p', 'm2v', 'm4e', 'mjp', 'mjpeg',
    'mjpg', 'movhd', 'movx', 'mpv2', 'nut', 'omf', 'vfw', 'vid', 'video', 'vro',
    'wrap', 'wx', 'x264', 'xvid',
]


def extension(filepath:str) -> str:
    """Return the normalized filename extension: lowercase without leading dot

    Can be empty. Does not consider POSIX hidden files to be extensions.
    Example: extension('A.JPG') -> 'jpg'
    """
    return os.path.splitext(filepath)[1][1:].lower()


def is_video(filepath:str, strict:bool=True) -> bool:
    """Return True if filepath should be considered a video file.

    Determined by file extension and possibly its guessed mimetype.
    """
    ext = extension(filepath)

    if ext in VIDEO_EXTENSIONS or (not strict and ext in VIDEO_EXTENSIONS_EXTRA):
        return True

    return mimetype(filepath).split('/')[0] == 'video'


def video_hash(filepath:str) -> str:
    """Return the OpenSubtitles video file hash.

    https://trac.opensubtitles.org/projects/opensubtitles/wiki/HashSourceCodes
    """
    block = 65536
    fmt = f"<{block//8}Q"  # 8 bytes * 8KiB (unsigned long long)
    vhash = os.path.getsize(filepath) # initial value for hash is file size

    def partialhash(f):
        return sum(struct.unpack(fmt, f.read(block)))

    with open(filepath, "rb") as f:
        try:
            vhash += partialhash(f)
            f.seek(-block, os.SEEK_END)
            vhash += partialhash(f)
            vhash &= 0xFFFFFFFFFFFFFFFF  # cap at 64bit
        except (IOError, struct.error):
            raise u.LegendasTVError("File must be at least %d bytes to hash: %s",
                                    block, filepath)
    return f"{vhash:016x}"


def guess_info(filename:str) -> dict:
    return guessit.guessit(filename)
